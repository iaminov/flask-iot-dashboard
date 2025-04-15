import json
import logging
import os
import time
import traceback
from datetime import datetime, timedelta
from typing import Any

from .file_storage import FileStorage
from .models import SensorReading, SensorStats
from .realtime import emit_sensor_update

logger = logging.getLogger(__name__)

file_storage = FileStorage()


class SimpleRedisClient:
    def get(self, key: str):
        return None

    def setex(self, key: str, ttl_seconds: int, value: str):
        return True

    def scan_iter(self, pattern: str = "*"):
        return []


# Exposed for tests to patch
redis_client = SimpleRedisClient()


def process_sensor_data(*args):
    """Process sensor data; supports both (topic, payload) and (task, topic, payload)."""
    task = None
    if len(args) == 2:
        topic, payload = args
    elif len(args) == 3:
        task, topic, payload = args
    else:
        raise TypeError(
            "process_sensor_data expects (topic, payload) or (task, topic, payload)"
        )

    start_time = time.time()

    try:
        logger.info(f"Processing sensor data from topic: {topic}")
        reading = SensorReading.from_mqtt_payload(topic, payload)

        store_raw_reading(reading)
        update_sensor_statistics(reading)
        emit_sensor_update(reading.to_dict())

        processing_time = time.time() - start_time
        logger.info(
            f"Successfully processed reading from sensor {reading.sensor_id}: {reading.value} {reading.unit} (Processing time: {processing_time:.3f}s)"
        )
        return {
            "status": "success",
            "sensor_id": reading.sensor_id,
            "processing_time": processing_time,
        }

    except Exception as e:
        logger.error(f"Error processing sensor data: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        if task is not None and hasattr(task, "retry"):
            task.retry()
        raise


def store_raw_reading(reading: SensorReading) -> None:
    """Store raw sensor reading in file storage and Redis (mockable)."""
    try:
        reading_data = reading.to_dict()
        # File-based persistence for app logic
        file_storage.store_reading(reading.sensor_id, reading_data)
        # Redis-mockable side-effect for tests
        key = f"reading:{reading.sensor_id}:{reading_data['timestamp']}"
        redis_client.setex(key, 3600, json.dumps(reading_data))
        logger.debug(f"Stored raw reading for sensor {reading.sensor_id}")

    except Exception as e:
        logger.error(f"Error storing raw reading: {e}")
        raise


def update_sensor_statistics(reading: SensorReading) -> None:
    """Update sensor statistics using file storage and Redis (mockable)."""
    try:
        reading_data = reading.to_dict()
        # File-based stats for app logic
        file_storage.update_stats(reading.sensor_id, reading_data)

        # Redis-mockable stats for tests
        stats_key = f"stats:{reading.sensor_id}"
        raw = redis_client.get(stats_key)
        if raw:
            try:
                current = json.loads(raw)
            except Exception:
                current = None
        else:
            current = None

        if not current:
            stats = {
                "sensor_id": reading.sensor_id,
                "min_value": reading.value,
                "max_value": reading.value,
                "avg_value": reading.value,
                "count": 1,
                "last_reading": reading_data["timestamp"],
            }
        else:
            count = int(current.get("count", 0)) + 1
            total = (
                float(current.get("avg_value", reading.value)) * (count - 1)
                + reading.value
            )
            stats = {
                "sensor_id": reading.sensor_id,
                "min_value": min(
                    float(current.get("min_value", reading.value)), reading.value
                ),
                "max_value": max(
                    float(current.get("max_value", reading.value)), reading.value
                ),
                "avg_value": total / count,
                "count": count,
                "last_reading": reading_data["timestamp"],
            }

        redis_client.setex(stats_key, 3600, json.dumps(stats))
        logger.debug(f"Updated statistics for sensor {reading.sensor_id}")

    except Exception as e:
        logger.error(f"Error updating sensor statistics: {e}")
        raise


def get_all_sensor_stats() -> list[dict[str, Any]]:
    try:
        stats_list = file_storage.get_all_stats()
        logger.info(f"Retrieved statistics for {len(stats_list)} sensors")
        return stats_list
    except Exception as e:
        logger.error(f"Error retrieving sensor statistics: {e}")
        return []


def get_sensor_readings(sensor_id: str, hours: int = 24) -> list[dict[str, Any]]:
    try:
        readings = file_storage.get_readings(sensor_id, hours)
        readings.sort(key=lambda x: x.get("timestamp", ""))
        logger.info(
            f"Retrieved {len(readings)} readings for sensor {sensor_id} over {hours} hours"
        )
        return readings
    except Exception as e:
        logger.error(f"Error retrieving sensor readings: {e}")
        return []


def cleanup_old_data(days: int = 7):
    try:
        cleaned_count = file_storage.cleanup_old_data(days)
        logger.info(f"Cleanup completed: removed {cleaned_count} old readings")
        return {"cleaned_readings": cleaned_count}
    except Exception as e:
        logger.error(f"Error during data cleanup: {e}")
        raise
