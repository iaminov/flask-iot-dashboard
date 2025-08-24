
import json
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt
import os
import threading

class SensorSimulator:
    def __init__(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.sensors = [
            {'id': 'temp_living_room', 'type': 'temperature', 'unit': '°C', 'location': 'Living Room'},
            {'id': 'temp_bedroom', 'type': 'temperature', 'unit': '°C', 'location': 'Bedroom'},
            {'id': 'temp_kitchen', 'type': 'temperature', 'unit': '°C', 'location': 'Kitchen'},
            {'id': 'hum_living_room', 'type': 'humidity', 'unit': '%', 'location': 'Living Room'},
            {'id': 'hum_bedroom', 'type': 'humidity', 'unit': '%', 'location': 'Bedroom'},
            {'id': 'hum_kitchen', 'type': 'humidity', 'unit': '%', 'location': 'Kitchen'},
        ]
        self.running = False
        
    def connect(self):
        broker_host = os.getenv('MQTT_BROKER_HOST', '0.0.0.0')
        broker_port = int(os.getenv('MQTT_BROKER_PORT', 1883))
        
        try:
            self.client.connect(broker_host, broker_port, 60)
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def generate_sensor_data(self, sensor):
        if sensor['type'] == 'temperature':
            base_temp = 22.0
            if 'bedroom' in sensor['location'].lower():
                base_temp = 20.0
            elif 'kitchen' in sensor['location'].lower():
                base_temp = 24.0
            value = base_temp + random.uniform(-3.0, 5.0)
        else:  # humidity
            base_humidity = 50.0
            if 'kitchen' in sensor['location'].lower():
                base_humidity = 60.0
            value = base_humidity + random.uniform(-15.0, 20.0)
            value = max(0, min(100, value))  # Clamp to 0-100%
            
        return {
            'sensor_id': sensor['id'],
            'type': sensor['type'],
            'value': round(value, 1),
            'unit': sensor['unit'],
            'location': sensor['location'],
            'timestamp': datetime.now().isoformat(),
            'metadata': {
                'simulated': True,
                'quality': 'good'
            }
        }
    
    def start_simulation(self):
        if not self.connect():
            return
            
        print("Starting sensor simulation...")
        self.running = True
        
        while self.running:
            for sensor in self.sensors:
                if not self.running:
                    break
                    
                data = self.generate_sensor_data(sensor)
                topic = f"sensors/{sensor['id']}/{sensor['type']}"
                payload = json.dumps(data)
                
                try:
                    result = self.client.publish(topic, payload)
                    if result.rc == mqtt.MQTT_ERR_SUCCESS:
                        print(f"✓ Published: {topic} -> {data['value']} {data['unit']} ({data['location']})")
                    else:
                        print(f"✗ Failed to publish to {topic}")
                except Exception as e:
                    print(f"Error publishing to {topic}: {e}")
            
            time.sleep(5)  # Send data every 5 seconds
    
    def stop(self):
        self.running = False
        self.client.disconnect()

if __name__ == '__main__':
    simulator = SensorSimulator()
    try:
        simulator.start_simulation()
    except KeyboardInterrupt:
        print("\nStopping sensor simulation...")
        simulator.stop()
