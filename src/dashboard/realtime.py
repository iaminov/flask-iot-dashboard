import logging

from flask_socketio import emit

from . import socketio

logger = logging.getLogger(__name__)


def emit_sensor_update(sensor_data: dict):
    """Emit sensor data update to all connected clients."""
    try:
        socketio.emit("sensor_update", sensor_data, broadcast=True)
        logger.debug(f"Emitted sensor update for {sensor_data.get('sensor_id')}")
    except Exception as e:
        logger.error(f"Error emitting sensor update: {e}")


@socketio.on("connect")
def handle_connect():
    """Handle client connection."""
    logger.info("Client connected to WebSocket")
    emit("status", {"message": "Connected to IoT Dashboard"})


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection."""
    logger.info("Client disconnected from WebSocket")


@socketio.on("request_sensor_data")
def handle_sensor_data_request(data):
    """Handle client request for historical sensor data."""
    try:
        sensor_id = data.get("sensor_id")
        hours = data.get("hours", 24)

        from .tasks import get_sensor_readings

        readings = get_sensor_readings(sensor_id, hours)

        emit("sensor_history", {"sensor_id": sensor_id, "readings": readings})

        logger.debug(f"Sent historical data for sensor {sensor_id}")

    except Exception as e:
        logger.error(f"Error handling sensor data request: {e}")
        emit("error", {"message": "Failed to retrieve sensor data"})


@socketio.on("request_all_stats")
def handle_stats_request():
    """Handle client request for all sensor statistics."""
    try:
        from .tasks import get_all_sensor_stats

        stats = get_all_sensor_stats()

        emit(
            "sensor_stats", {"sensors": stats}
        )  # Changed key to match frontend expectation
        logger.debug(f"Sent sensor statistics to client: {len(stats)} sensors")

    except Exception as e:
        logger.error(f"Error handling stats request: {e}")
        emit("error", {"message": "Failed to retrieve sensor statistics"})
