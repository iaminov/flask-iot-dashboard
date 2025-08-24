
import subprocess
import time
import os
import sys

def start_redis():
    """Start Redis server if not already running."""
    try:
        result = subprocess.run(['pgrep', 'redis-server'], capture_output=True)
        if result.returncode != 0:
            print("Starting Redis server...")
            subprocess.Popen(['redis-server', '--daemonize', 'yes', '--port', '6379', '--dir', '/tmp'])
            time.sleep(2)
            print("Redis server started")
        else:
            print("Redis server already running")
    except Exception as e:
        print(f"Error starting Redis: {e}")

def start_mosquitto():
    """Start Mosquitto MQTT broker if not already running."""
    try:
        result = subprocess.run(['pgrep', 'mosquitto'], capture_output=True)
        if result.returncode != 0:
            print("Starting Mosquitto MQTT broker...")
            subprocess.Popen(['mosquitto', '-d', '-p', '1883'])
            time.sleep(2)
            print("Mosquitto MQTT broker started")
        else:
            print("Mosquitto MQTT broker already running")
    except Exception as e:
        print(f"Error starting Mosquitto: {e}")

def start_sensor_simulator():
    """Start sensor simulator in background."""
    try:
        print("Starting sensor simulator...")
        subprocess.Popen([sys.executable, 'sensor_simulator.py'])
        time.sleep(1)
        print("Sensor simulator started")
    except Exception as e:
        print(f"Error starting sensor simulator: {e}")

if __name__ == '__main__':
    start_redis()
    start_mosquitto()
    start_sensor_simulator()
    print("All services started successfully!")
