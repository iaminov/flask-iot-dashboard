
import pytest
import json
from unittest.mock import patch

class TestViews:
    def test_dashboard_view(self, client):
        """Test main dashboard view."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'IoT Sensor Dashboard' in response.data

    @patch('src.dashboard.views.get_all_sensor_stats')
    def test_api_sensors(self, mock_get_stats, client):
        """Test sensors API endpoint."""
        mock_stats = [
            {
                'sensor_id': 'temp_01',
                'min_value': 20.0,
                'max_value': 25.0,
                'avg_value': 22.5,
                'count': 10,
                'last_reading': '2024-01-01T12:00:00'
            }
        ]
        mock_get_stats.return_value = mock_stats
        
        response = client.get('/api/sensors')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'sensors' in data
        assert len(data['sensors']) == 1
        assert data['sensors'][0]['sensor_id'] == 'temp_01'

    @patch('src.dashboard.views.get_sensor_readings')
    def test_api_sensor_readings(self, mock_get_readings, client):
        """Test sensor readings API endpoint."""
        mock_readings = [
            {
                'sensor_id': 'temp_01',
                'value': 23.5,
                'timestamp': '2024-01-01T12:00:00'
            }
        ]
        mock_get_readings.return_value = mock_readings
        
        response = client.get('/api/sensors/temp_01/readings')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'readings' in data
        assert len(data['readings']) == 1

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

    def test_not_found(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent')
        assert response.status_code == 404
        
        data = json.loads(response.data)
        assert 'error' in data
