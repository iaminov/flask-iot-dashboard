
from dataclasses import dataclass
from datetime import datetime
from typing import Any
import json

@dataclass
class SensorReading:
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime
    location: str | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            'sensor_id': self.sensor_id,
            'sensor_type': self.sensor_type,
            'value': self.value,
            'unit': self.unit,
            'timestamp': self.timestamp.isoformat(),
            'location': self.location,
            'metadata': self.metadata or {}
        }

    @classmethod
    def from_mqtt_payload(cls, topic: str, payload: str) -> 'SensorReading':
        """Parse MQTT message into SensorReading object."""
        try:
            data = json.loads(payload)
            topic_parts = topic.split('/')
            
            return cls(
                sensor_id=data.get('sensor_id', topic_parts[1] if len(topic_parts) > 1 else 'unknown'),
                sensor_type=data.get('type', topic_parts[2] if len(topic_parts) > 2 else 'unknown'),
                value=float(data['value']),
                unit=data.get('unit', ''),
                timestamp=datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else datetime.now(),
                location=data.get('location'),
                metadata=data.get('metadata')
            )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise ValueError(f"Invalid sensor data format: {e}")

@dataclass
class SensorStats:
    sensor_id: str
    min_value: float
    max_value: float
    avg_value: float
    count: int
    last_reading: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            'sensor_id': self.sensor_id,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'avg_value': round(self.avg_value, 2),
            'count': self.count,
            'last_reading': self.last_reading.isoformat()
        }
