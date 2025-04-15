
import pytest
from unittest.mock import MagicMock, patch, call
from src.dashboard.mqtt_client import MQTTClient

class TestMQTTClient:
    @patch('src.dashboard.mqtt_client.mqtt.Client')
    def test_init(self, mock_mqtt_client):
        """Test MQTT client initialization."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        client = MQTTClient()
        
        assert client.broker_host == 'localhost'
        assert client.broker_port == 1883
        mock_mqtt_client.assert_called_once()

    @patch.dict('os.environ', {
        'MQTT_BROKER_HOST': 'test.broker.com',
        'MQTT_BROKER_PORT': '8883',
        'MQTT_USERNAME': 'testuser',
        'MQTT_PASSWORD': 'testpass',
        'MQTT_TOPICS': 'test/topic1,test/topic2'
    })
    @patch('src.dashboard.mqtt_client.mqtt.Client')
    def test_init_with_env_vars(self, mock_mqtt_client):
        """Test MQTT client initialization with environment variables."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        client = MQTTClient()
        
        assert client.broker_host == 'test.broker.com'
        assert client.broker_port == 8883
        assert client.username == 'testuser'
        assert client.password == 'testpass'
        assert client.topics == ['test/topic1', 'test/topic2']

    @patch('src.dashboard.mqtt_client.mqtt.Client')
    def test_connect_success(self, mock_mqtt_client):
        """Test successful MQTT connection."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        mock_client_instance.connect.return_value = 0
        
        client = MQTTClient()
        result = client.connect()
        
        assert result is True
        mock_client_instance.connect.assert_called_once_with('localhost', 1883, 60)

    @patch('src.dashboard.mqtt_client.mqtt.Client')
    def test_connect_failure(self, mock_mqtt_client):
        """Test MQTT connection failure."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        mock_client_instance.connect.side_effect = Exception("Connection failed")
        
        client = MQTTClient()
        result = client.connect()
        
        assert result is False

    @patch('src.dashboard.mqtt_client.process_sensor_data')
    @patch('src.dashboard.mqtt_client.mqtt.Client')
    def test_on_message(self, mock_mqtt_client, mock_process_task):
        """Test MQTT message processing."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        mock_process_task.delay = MagicMock()
        
        client = MQTTClient()
        
        mock_msg = MagicMock()
        mock_msg.topic = "sensors/temp_01/temperature"
        mock_msg.payload.decode.return_value = '{"value": 23.5}'
        
        client._on_message(None, None, mock_msg)
        
        mock_process_task.delay.assert_called_once_with(
            "sensors/temp_01/temperature", 
            '{"value": 23.5}'
        )

    @patch('src.dashboard.mqtt_client.mqtt.Client')
    def test_on_connect_success(self, mock_mqtt_client):
        """Test successful connection callback."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        client = MQTTClient()
        client._on_connect(mock_client_instance, None, None, 0)
        
        expected_calls = [call('sensors/+/+')]
        mock_client_instance.subscribe.assert_has_calls(expected_calls)

    @patch('src.dashboard.mqtt_client.mqtt.Client')
    def test_publish(self, mock_mqtt_client):
        """Test message publishing."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        client = MQTTClient()
        client.publish("test/topic", "test message", 1)
        
        mock_client_instance.publish.assert_called_once_with("test/topic", "test message", 1)
