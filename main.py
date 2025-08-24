
import os
import logging
import threading
import subprocess
from src.dashboard import create_app, socketio
from src.dashboard.mqtt_client import MQTTClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def start_mqtt_client():
    """Start MQTT client in separate thread."""
    mqtt_client = MQTTClient()
    if mqtt_client.connect():
        logger.info("Starting MQTT client loop")
        mqtt_client.start_loop()
    else:
        logger.error("Failed to start MQTT client")

def main():
    """Main application entry point."""
    # Start MQTT broker
    logger.info("Starting MQTT broker...")
    try:
        result = subprocess.run(['pgrep', 'mosquitto'], capture_output=True)
        if result.returncode != 0:
            subprocess.Popen(['mosquitto', '-d', '-p', '1883'])
            import time
            time.sleep(2)
            logger.info("MQTT broker started")
    except Exception as e:
        logger.warning(f"Could not start MQTT broker: {e}")
    
    # Start sensor simulator
    def start_simulator():
        import time
        time.sleep(3)  # Give MQTT broker time to start
        try:
            from sensor_simulator import SensorSimulator
            simulator = SensorSimulator()
            simulator.start_simulation()
        except Exception as e:
            logger.error(f"Error starting sensor simulator: {e}")
    
    simulator_thread = threading.Thread(target=start_simulator, daemon=True)
    simulator_thread.start()
    logger.info("Sensor simulator started")
    
    app = create_app()
    
    mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
    mqtt_thread.start()
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Flask-SocketIO server on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()
