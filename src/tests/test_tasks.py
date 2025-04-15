
import pytest
import json
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.dashboard.tasks import process_sensor_data, store_raw_reading, update_sensor_statistics
from src.dashboard.models import SensorReading

class TestTasks:
    @patch('src.dashboard.tasks.emit_sensor_update')
    @patch('src.dashboard.tasks.update_sensor_statistics')
    @patch('src.dashboard.tasks.store_raw_reading')
    def test_process_sensor_data_success(self, mock_store, mock_update, mock_emit, mock_redis):
        """Test successful sensor data processing."""
        topic = "sensors/temp_01/temperature"
        payload = json.dumps({
            'sensor_id': 'temp_01',
            'value': 23.5,
            'unit': '°C',
            'timestamp': '2024-01-01T12:00:00'
        })
        
        task = MagicMock()
        task.request.retries = 0
        task.max_retries = 3
        
        process_sensor_data(task, topic, payload)
        
        mock_store.assert_called_once()
        mock_update.assert_called_once()
        mock_emit.assert_called_once()

    @patch('src.dashboard.tasks.SensorReading.from_mqtt_payload')
    def test_process_sensor_data_invalid_payload(self, mock_from_mqtt, mock_redis):
        """Test processing invalid sensor data."""
        mock_from_mqtt.side_effect = ValueError("Invalid format")
        
        task = MagicMock()
        task.request.retries = 0
        task.max_retries = 3
        task.retry.side_effect = Exception("Retry called")
        
        with pytest.raises(Exception, match="Retry called"):
            process_sensor_data(task, "test/topic", "invalid")

    def test_store_raw_reading(self, mock_redis):
        """Test storing raw sensor reading."""
        reading = SensorReading(
            sensor_id='temp_01',
            sensor_type='temperature',
            value=23.5,
            unit='°C',
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        store_raw_reading(reading)
        
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args
        assert 'reading:temp_01:' in args[0][0]

    def test_update_sensor_statistics_new_sensor(self, mock_redis):
        """Test updating statistics for new sensor."""
        mock_redis.get.return_value = None
        
        reading = SensorReading(
            sensor_id='temp_01',
            sensor_type='temperature',
            value=23.5,
            unit='°C',
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        update_sensor_statistics(reading)
        
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args
        assert args[0][0] == 'stats:temp_01'

    def test_update_sensor_statistics_existing_sensor(self, mock_redis):
        """Test updating statistics for existing sensor."""
        existing_stats = {
            'sensor_id': 'temp_01',
            'min_value': 20.0,
            'max_value': 25.0,
            'avg_value': 22.5,
            'count': 2,
            'last_reading': '2024-01-01T11:00:00'
        }
        mock_redis.get.return_value = json.dumps(existing_stats)
        
        reading = SensorReading(
            sensor_id='temp_01',
            sensor_type='temperature',
            value=26.0,
            unit='°C',
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        update_sensor_statistics(reading)
        
        mock_redis.setex.assert_called_once()
        stored_data = json.loads(mock_redis.setex.call_args[0][2])
        assert stored_data['max_value'] == 26.0
        assert stored_data['count'] == 3
