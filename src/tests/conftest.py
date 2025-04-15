
import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch
from src.dashboard import create_app

@pytest.fixture
def app():
    """Create test Flask application."""
    test_config = {
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
    }
    
    app = create_app()
    app.config.update(test_config)
    
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('src.dashboard.tasks.redis_client') as mock:
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.scan_iter.return_value = []
        yield mock

@pytest.fixture
def mock_celery():
    """Mock Celery app."""
    with patch('src.dashboard.tasks.celery_app') as mock:
        yield mock

@pytest.fixture
def sample_sensor_data():
    """Sample sensor data for testing."""
    return {
        'sensor_id': 'temp_01',
        'type': 'temperature',
        'value': 23.5,
        'unit': '°C',
        'timestamp': '2024-01-01T12:00:00',
        'location': 'Room A',
        'metadata': {'calibrated': True}
    }
