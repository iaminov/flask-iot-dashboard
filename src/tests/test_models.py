import json
from datetime import datetime

import pytest

from src.dashboard.models import SensorReading, SensorStats


class TestSensorReading:
    def test_from_mqtt_payload_valid(self):
        topic = "sensors/temp_01/temperature"
        payload = json.dumps(
            {
                "sensor_id": "temp_01",
                "type": "temperature",
                "value": 23.5,
                "unit": "°C",
                "timestamp": "2024-01-01T12:00:00",
                "location": "Room A",
            }
        )

        reading = SensorReading.from_mqtt_payload(topic, payload)

        assert reading.sensor_id == "temp_01"
        assert reading.sensor_type == "temperature"
        assert reading.value == 23.5
        assert reading.unit == "°C"
        assert reading.location == "Room A"

    def test_from_mqtt_payload_minimal(self):
        topic = "sensors/temp_01/temperature"
        payload = json.dumps({"value": 25.0})

        reading = SensorReading.from_mqtt_payload(topic, payload)

        assert reading.sensor_id == "temp_01"
        assert reading.sensor_type == "temperature"
        assert reading.value == 25.0
        assert isinstance(reading.timestamp, datetime)

    def test_from_mqtt_payload_invalid_json(self):
        topic = "sensors/temp_01/temperature"
        payload = "invalid json"

        with pytest.raises(ValueError, match="Invalid sensor data format"):
            SensorReading.from_mqtt_payload(topic, payload)

    def test_from_mqtt_payload_missing_value(self):
        topic = "sensors/temp_01/temperature"
        payload = json.dumps({"sensor_id": "temp_01"})

        with pytest.raises(ValueError, match="Invalid sensor data format"):
            SensorReading.from_mqtt_payload(topic, payload)

    def test_to_dict(self):
        reading = SensorReading(
            sensor_id="temp_01",
            sensor_type="temperature",
            value=23.5,
            unit="°C",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            location="Room A",
        )

        result = reading.to_dict()

        assert result["sensor_id"] == "temp_01"
        assert result["value"] == 23.5
        assert result["timestamp"] == "2024-01-01T12:00:00"


class TestSensorStats:
    def test_to_dict(self):
        stats = SensorStats(
            sensor_id="temp_01",
            min_value=20.0,
            max_value=25.0,
            avg_value=22.5,
            count=10,
            last_reading=datetime(2024, 1, 1, 12, 0, 0),
        )

        result = stats.to_dict()

        assert result["sensor_id"] == "temp_01"
        assert result["avg_value"] == 22.5
        assert result["count"] == 10
