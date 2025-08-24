import os
import json
import pandas as pd
from datetime import datetime, timedelta
from celery import Celery
from celery.utils.log import get_task_logger
from typing import List, Dict, Any, Optional
from .models import SensorReading, SensorStats
from .realtime import emit_sensor_update
from .file_storage import file_storage
import time
import traceback
import logging

# Setup logging
logger = logging.getLogger(__name__)

# File storage instance
file_storage = FileStorage()

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

        # Removed Celery retry logic as it's not used in the file-based approach
        raise

def store_raw_reading(reading: SensorReading) -> None:
    """Store raw sensor reading in file storage."""
    try:
        reading_data = reading.to_dict()
        file_storage.store_reading(reading.sensor_id, reading_data)
        logger.debug(f"Stored raw reading for sensor {reading.sensor_id}")

    except Exception as e:
        logger.error(f"Error storing raw reading: {e}")
        raise

def update_sensor_statistics(reading: SensorReading) -> None:
    """Update sensor statistics using file storage."""
    try:
        reading_data = reading.to_dict()
        file_storage.update_stats(reading.sensor_id, reading_data)

        logger.debug(f"Updated statistics for sensor {reading.sensor_id}")

    except Exception as e:
        logger.error(f"Error updating sensor statistics: {e}")
        raise

def get_all_sensor_stats() -> List[Dict[str, Any]]:
    """Retrieve statistics for all sensors."""
    try:
        stats_list = file_storage.get_all_stats()
        logger.info(f"Retrieved statistics for {len(stats_list)} sensors")
        return stats_list

    except Exception as e:
        logger.error(f"Error retrieving sensor statistics: {e}")
        return []

def get_sensor_readings(sensor_id: str, hours: int = 24) -> List[Dict[str, Any]]:
    """Retrieve sensor readings for the specified time period."""
    try:
        readings = file_storage.get_readings(sensor_id, hours)

        # Sort by timestamp
        readings.sort(key=lambda x: x.get('timestamp', ''))

        logger.info(f"Retrieved {len(readings)} readings for sensor {sensor_id} "
                   f"over {hours} hours")
        return readings

    except Exception as e:
        logger.error(f"Error retrieving sensor readings: {e}")
        return []

def cleanup_old_data(days: int = 7):
    """Clean up old sensor data."""
    try:
        cleaned_count = file_storage.cleanup_old_data(days)
        logger.info(f"Cleanup completed: removed {cleaned_count} old readings")
        return {'cleaned_readings': cleaned_count}

    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        raise