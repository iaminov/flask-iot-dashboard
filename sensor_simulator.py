
import json
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt
import os

class SensorSimulator:
    def __init__(self):
        self.client = mqtt.Client()
        self.sensors = [
            {'id': 'temp_01', 'type': 'temperature', 'unit': '°C', 'location': 'Living Room'},
            {'id': 'temp_02', 'type': 'temperature', 'unit': '°C', 'location': 'Bedroom'},
            {'id': 'hum_01', 'type': 'humidity', 'unit': '%', 'location': 'Living Room'},
            {'id': 'hum_02', 'type': 'humidity', 'unit': '%', 'location': 'Bedroom'},
        ]
        
    def connect(self):
        broker_host = os.getenv('MQTT_BROKER_HOST', 'localhost')
        broker_port = int(os.getenv('MQTT_BROKER_PORT', 1883))
        
        try:
            self.client.connect(broker_host, broker_port, 60)
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def generate_sensor_data(self, sensor):
        if sensor['type'] == 'temperature':
            value = random.uniform(18.0, 28.0)
        else:
            value = random.uniform(30.0, 70.0)
            
        return {
            'sensor_id': sensor['id'],
            'type': sensor['type'],
            'value': round(value, 1),
            'unit': sensor['unit'],
            'location': sensor['location'],
            'timestamp': datetime.now().isoformat()
        }
    
    def start_simulation(self):
        if not self.connect():
            return
            
        print("Starting sensor simulation...")
        
        while True:
            for sensor in self.sensors:
                data = self.generate_sensor_data(sensor)
                topic = f"sensors/{sensor['id']}/{sensor['type']}"
                payload = json.dumps(data)
                
                self.client.publish(topic, payload)
                print(f"Published: {topic} -> {data['value']} {data['unit']}")
            
            time.sleep(10)

if __name__ == '__main__':
    simulator = SensorSimulator()
    try:
        simulator.start_simulation()
    except KeyboardInterrupt:
        print("\nStopping sensor simulation...")
