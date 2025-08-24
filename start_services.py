
import subprocess
import time
import os
import sys
import threading

def start_mosquitto():
    """Start Mosquitto MQTT broker if not already running."""
    try:
        result = subprocess.run(['pgrep', 'mosquitto'], capture_output=True)
        if result.returncode != 0:
            print("Starting Mosquitto MQTT broker...")
            subprocess.Popen(['mosquitto', '-d', '-p', '1883'])
            time.sleep(2)
            print("✓ Mosquitto MQTT broker started")
        else:
            print("✓ Mosquitto MQTT broker already running")
    except Exception as e:
        print(f"✗ Error starting Mosquitto: {e}")

def start_sensor_simulator():
    """Start sensor simulator in background thread."""
    def run_simulator():
        try:
            time.sleep(3)  # Wait for MQTT broker to be ready
            print("Starting sensor simulator...")
            from sensor_simulator import SensorSimulator
            simulator = SensorSimulator()
            simulator.start_simulation()
        except Exception as e:
            print(f"✗ Error starting sensor simulator: {e}")
    
    simulator_thread = threading.Thread(target=run_simulator, daemon=True)
    simulator_thread.start()
    print("✓ Sensor simulator started in background")

if __name__ == '__main__':
    start_mosquitto()
    start_sensor_simulator()
    print("✓ All services started successfully!")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down services...")
