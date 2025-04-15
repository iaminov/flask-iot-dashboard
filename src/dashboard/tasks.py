
import os
import redis
import json
import pandas as pd
from datetime import datetime, timedelta
from celery import Celery
from .models import SensorReading, SensorStats
from .realtime import emit_sensor_update
import logging

logger = logging.getLogger(__name__)

celery_app = Celery('dashboard')
celery_app.conf.broker_url = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
celery_app.conf.result_backend = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')

redis_client = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

@celery_app.task(bind=True, max_retries=3)
def process_sensor_data(self, topic: str, payload: str):
    """Process incoming sensor data and update aggregates."""
    try:
        reading = SensorReading.from_mqtt_payload(topic, payload)
        
        store_raw_reading(reading)
        update_sensor_statistics(reading)
        emit_sensor_update(reading.to_dict())
        
        logger.info(f"Processed reading from sensor {reading.sensor_id}: {reading.value} {reading.unit}")
        
    except Exception as e:
        logger.error(f"Error processing sensor data: {e}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task in 60 seconds (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60, exc=e)

def store_raw_reading(reading: SensorReading):
    """Store raw sensor reading in Redis with expiration."""
    key = f"reading:{reading.sensor_id}:{int(reading.timestamp.timestamp())}"
    redis_client.setex(key, timedelta(days=7), json.dumps(reading.to_dict()))

def update_sensor_statistics(reading: SensorReading):
    """Update running statistics for sensor."""
    stats_key = f"stats:{reading.sensor_id}"
    
    try:
        existing_stats = redis_client.get(stats_key)
        if existing_stats:
            stats_data = json.loads(existing_stats)
            stats = SensorStats(
                sensor_id=stats_data['sensor_id'],
                min_value=min(stats_data['min_value'], reading.value),
                max_value=max(stats_data['max_value'], reading.value),
                avg_value=((stats_data['avg_value'] * stats_data['count']) + reading.value) / (stats_data['count'] + 1),
                count=stats_data['count'] + 1,
                last_reading=reading.timestamp
            )
        else:
            stats = SensorStats(
                sensor_id=reading.sensor_id,
                min_value=reading.value,
                max_value=reading.value,
                avg_value=reading.value,
                count=1,
                last_reading=reading.timestamp
            )
        
        redis_client.setex(stats_key, timedelta(days=30), json.dumps(stats.to_dict()))
        
    except Exception as e:
        logger.error(f"Error updating sensor statistics: {e}")

@celery_app.task
def cleanup_old_readings():
    """Remove expired sensor readings from Redis."""
    try:
        cutoff_time = datetime.now() - timedelta(days=7)
        cutoff_timestamp = int(cutoff_time.timestamp())
        
        for key in redis_client.scan_iter(match="reading:*"):
            key_parts = key.decode().split(':')
            if len(key_parts) == 3:
                timestamp = int(key_parts[2])
                if timestamp < cutoff_timestamp:
                    redis_client.delete(key)
                    
        logger.info("Completed cleanup of old sensor readings")
        
    except Exception as e:
        logger.error(f"Error during cleanup task: {e}")

def get_sensor_readings(sensor_id: str, hours: int = 24) -> list[dict]:
    """Retrieve recent readings for a sensor."""
    try:
        start_time = datetime.now() - timedelta(hours=hours)
        start_timestamp = int(start_time.timestamp())
        
        pattern = f"reading:{sensor_id}:*"
        readings = []
        
        for key in redis_client.scan_iter(match=pattern):
            key_parts = key.decode().split(':')
            if len(key_parts) == 3:
                timestamp = int(key_parts[2])
                if timestamp >= start_timestamp:
                    reading_data = redis_client.get(key)
                    if reading_data:
                        readings.append(json.loads(reading_data))
        
        return sorted(readings, key=lambda x: x['timestamp'])
        
    except Exception as e:
        logger.error(f"Error retrieving sensor readings: {e}")
        return []

def get_all_sensor_stats() -> list[dict]:
    """Get statistics for all sensors."""
    try:
        stats = []
        for key in redis_client.scan_iter(match="stats:*"):
            stats_data = redis_client.get(key)
            if stats_data:
                stats.append(json.loads(stats_data))
        
        return sorted(stats, key=lambda x: x['sensor_id'])
        
    except Exception as e:
        logger.error(f"Error retrieving sensor statistics: {e}")
        return []
