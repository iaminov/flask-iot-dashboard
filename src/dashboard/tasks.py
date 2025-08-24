
import os
import redis
import json
import pandas as pd
from datetime import datetime, timedelta
from celery import Celery
from celery.utils.log import get_task_logger
from typing import List, Dict, Any, Optional
from .models import SensorReading, SensorStats
from .realtime import emit_sensor_update
import time
import traceback

# Setup logging
logger = get_task_logger(__name__)

# Enhanced Celery configuration
celery_app = Celery('dashboard')
celery_app.conf.update({
    'broker_url': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    'result_backend': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
    'task_routes': {
        'src.dashboard.tasks.process_sensor_data': {'queue': 'sensor_data'},
        'src.dashboard.tasks.cleanup_old_data': {'queue': 'maintenance'},
    },
    'beat_schedule': {
        'cleanup-old-data': {
            'task': 'src.dashboard.tasks.cleanup_old_data',
            'schedule': 3600.0,  # Run every hour
        },
    },
})

# Redis client with connection pooling
class RedisManager:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self._client = None
        self._pool = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                self._pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=20,
                    retry_on_timeout=True,
                    socket_keepalive=True,
                    socket_keepalive_options={}
                )
                self._client = redis.Redis(connection_pool=self._pool)
                # Test connection
                self._client.ping()
                logger.info("Redis connection established successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self._client
    
    def is_connected(self) -> bool:
        try:
            self.client.ping()
            return True
        except:
            return False

redis_manager = RedisManager()

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_sensor_data(self, topic: str, payload: str):
    """Enhanced sensor data processing with comprehensive error handling."""
    start_time = time.time()
    
    try:
        logger.info(f"Processing sensor data from topic: {topic}")
        
        # Parse sensor reading
        reading = SensorReading.from_mqtt_payload(topic, payload)
        logger.debug(f"Parsed reading: {reading}")
        
        # Store operations
        store_raw_reading(reading)
        update_sensor_statistics(reading)
        
        # Emit real-time update
        emit_sensor_update(reading.to_dict())
        
        processing_time = time.time() - start_time
        logger.info(f"Successfully processed reading from sensor {reading.sensor_id}: "
                   f"{reading.value} {reading.unit} (Processing time: {processing_time:.3f}s)")
        
        return {
            'status': 'success',
            'sensor_id': reading.sensor_id,
            'processing_time': processing_time
        }
        
    except Exception as e:
        logger.error(f"Error processing sensor data: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        if self.request.retries < self.max_retries:
            retry_countdown = 2 ** self.request.retries * 60  # Exponential backoff
            logger.info(f"Retrying task in {retry_countdown} seconds (attempt {self.request.retries + 1})")
            raise self.retry(countdown=retry_countdown, exc=e)
        else:
            logger.error(f"Task failed after {self.max_retries} retries")
            raise

def store_raw_reading(reading: SensorReading) -> None:
    """Store raw sensor reading in Redis with TTL."""
    try:
        redis_client = redis_manager.client
        
        # Store in time-series format
        key = f"sensor:{reading.sensor_id}:readings"
        timestamp = int(reading.timestamp.timestamp())
        
        # Use Redis sorted set for time-series data
        redis_client.zadd(key, {json.dumps(reading.to_dict()): timestamp})
        
        # Set TTL for automatic cleanup (7 days)
        redis_client.expire(key, 7 * 24 * 3600)
        
        logger.debug(f"Stored raw reading for sensor {reading.sensor_id}")
        
    except Exception as e:
        logger.error(f"Error storing raw reading: {e}")
        raise

def update_sensor_statistics(reading: SensorReading) -> None:
    """Update sensor statistics with atomic operations."""
    try:
        redis_client = redis_manager.client
        stats_key = f"sensor:{reading.sensor_id}:stats"
        
        # Use Redis pipeline for atomic operations
        pipe = redis_client.pipeline()
        
        # Get current stats
        current_stats = redis_client.hgetall(stats_key)
        
        if current_stats:
            # Update existing stats
            count = int(current_stats.get(b'count', 0)) + 1
            min_val = min(float(current_stats.get(b'min_value', reading.value)), reading.value)
            max_val = max(float(current_stats.get(b'max_value', reading.value)), reading.value)
            
            # Calculate running average
            current_avg = float(current_stats.get(b'avg_value', reading.value))
            new_avg = ((current_avg * (count - 1)) + reading.value) / count
        else:
            # Initialize stats
            count = 1
            min_val = max_val = new_avg = reading.value
        
        # Update stats
        pipe.hset(stats_key, mapping={
            'sensor_id': reading.sensor_id,
            'min_value': min_val,
            'max_value': max_val,
            'avg_value': new_avg,
            'count': count,
            'last_reading': reading.timestamp.isoformat(),
            'sensor_type': reading.sensor_type,
            'unit': reading.unit,
            'location': reading.location or 'Unknown'
        })
        
        # Set TTL
        pipe.expire(stats_key, 30 * 24 * 3600)  # 30 days
        
        # Execute pipeline
        pipe.execute()
        
        logger.debug(f"Updated statistics for sensor {reading.sensor_id}: "
                    f"count={count}, avg={new_avg:.2f}, min={min_val}, max={max_val}")
        
    except Exception as e:
        logger.error(f"Error updating sensor statistics: {e}")
        raise

def get_all_sensor_stats() -> List[Dict[str, Any]]:
    """Retrieve statistics for all sensors with enhanced error handling."""
    try:
        redis_client = redis_manager.client
        
        # Find all sensor stats keys
        sensor_keys = redis_client.keys("sensor:*:stats")
        
        if not sensor_keys:
            logger.warning("No sensor statistics found")
            return []
        
        stats_list = []
        
        # Use pipeline for efficient bulk operations
        pipe = redis_client.pipeline()
        for key in sensor_keys:
            pipe.hgetall(key)
        
        results = pipe.execute()
        
        for i, stats_data in enumerate(results):
            if stats_data:
                try:
                    stats = {
                        'sensor_id': stats_data.get(b'sensor_id', b'').decode('utf-8'),
                        'min_value': float(stats_data.get(b'min_value', 0)),
                        'max_value': float(stats_data.get(b'max_value', 0)),
                        'avg_value': float(stats_data.get(b'avg_value', 0)),
                        'count': int(stats_data.get(b'count', 0)),
                        'last_reading': stats_data.get(b'last_reading', b'').decode('utf-8'),
                        'sensor_type': stats_data.get(b'sensor_type', b'').decode('utf-8'),
                        'unit': stats_data.get(b'unit', b'').decode('utf-8'),
                        'location': stats_data.get(b'location', b'').decode('utf-8')
                    }
                    stats_list.append(stats)
                except (ValueError, UnicodeDecodeError) as e:
                    logger.warning(f"Error parsing stats for key {sensor_keys[i]}: {e}")
                    continue
        
        logger.info(f"Retrieved statistics for {len(stats_list)} sensors")
        return stats_list
        
    except Exception as e:
        logger.error(f"Error retrieving sensor statistics: {e}")
        raise

def get_sensor_readings(sensor_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Retrieve sensor readings for the specified time period."""
    try:
        redis_client = redis_manager.client
        key = f"sensor:{sensor_id}:readings"
        
        # Calculate time range
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())
        
        # Get readings from sorted set
        raw_readings = redis_client.zrangebyscore(
            key, start_timestamp, end_timestamp, withscores=True
        )
        
        readings = []
        for reading_json, timestamp in raw_readings:
            try:
                reading_data = json.loads(reading_json)
                readings.append(reading_data)
            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing reading data: {e}")
                continue
        
        # Sort by timestamp
        readings.sort(key=lambda x: x.get('timestamp', ''))
        
        logger.info(f"Retrieved {len(readings)} readings for sensor {sensor_id} "
                   f"over {hours} hours")
        return readings
        
    except Exception as e:
        logger.error(f"Error retrieving sensor readings: {e}")
        return []

@celery_app.task
def cleanup_old_data():
    """Periodic task to clean up old sensor data."""
    try:
        redis_client = redis_manager.client
        cutoff_time = datetime.now() - timedelta(days=7)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        # Find all reading keys
        reading_keys = redis_client.keys("sensor:*:readings")
        
        cleaned_count = 0
        for key in reading_keys:
            # Remove old readings
            removed = redis_client.zremrangebyscore(key, 0, cutoff_timestamp)
            cleaned_count += removed
        
        logger.info(f"Cleanup completed: removed {cleaned_count} old readings")
        return {'cleaned_readings': cleaned_count}
        
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        raise
