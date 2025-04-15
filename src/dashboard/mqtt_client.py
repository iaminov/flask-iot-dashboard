
import paho.mqtt.client as mqtt
import os
import logging
from typing import Callable
from .tasks import process_sensor_data

logger = logging.getLogger(__name__)

class MQTTClient:
    def __init__(self):
        self.client = mqtt.Client()
        self.broker_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
        self.broker_port = int(os.getenv('MQTT_BROKER_PORT', 1883))
        self.username = os.getenv('MQTT_USERNAME')
        self.password = os.getenv('MQTT_PASSWORD')
        self.topics = os.getenv('MQTT_TOPICS', 'sensors/+/+').split(',')
        
        self._setup_client()

    def _setup_client(self):
        """Configure MQTT client with callbacks and authentication."""
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        self.client.on_subscribe = self._on_subscribe

    def _on_connect(self, client, userdata, flags, rc):
        """Handle successful MQTT connection."""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            for topic in self.topics:
                client.subscribe(topic.strip())
                logger.info(f"Subscribed to topic: {topic.strip()}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")

    def _on_message(self, client, userdata, msg):
        """Process incoming MQTT messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            logger.debug(f"Received message on topic {topic}: {payload}")
            
            process_sensor_data.delay(topic, payload)
            
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def _on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnection."""
        if rc != 0:
            logger.warning("Unexpected MQTT disconnection. Attempting to reconnect...")

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Handle successful subscription."""
        logger.debug(f"Subscription confirmed with QoS: {granted_qos}")

    def connect(self):
        """Connect to MQTT broker."""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def start_loop(self):
        """Start MQTT client loop."""
        self.client.loop_forever()

    def stop(self):
        """Disconnect from MQTT broker."""
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")

    def publish(self, topic: str, payload: str, qos: int = 0):
        """Publish message to MQTT topic."""
        try:
            self.client.publish(topic, payload, qos)
            logger.debug(f"Published message to {topic}: {payload}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
