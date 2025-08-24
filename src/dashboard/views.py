
from flask import Blueprint, render_template, jsonify, request
from .tasks import get_all_sensor_stats, get_sensor_readings
import logging

logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    """Main dashboard view."""
    return render_template('dashboard.html')

@main_bp.route('/api/sensors')
def api_sensors():
    """API endpoint to get all sensor statistics."""
    try:
        stats = get_all_sensor_stats()
        return jsonify({'sensors': stats})
    except Exception as e:
        logger.error(f"Error in /api/sensors endpoint: {e}")
        return jsonify({'error': 'Failed to retrieve sensor data'}), 500

@main_bp.route('/api/sensors/<sensor_id>/readings')
def api_sensor_readings(sensor_id):
    """API endpoint to get readings for a specific sensor."""
    try:
        hours = request.args.get('hours', 24, type=int)
        readings = get_sensor_readings(sensor_id, hours)
        return jsonify({'readings': readings})
    except Exception as e:
        logger.error(f"Error in /api/sensors/{sensor_id}/readings endpoint: {e}")
        return jsonify({'error': 'Failed to retrieve sensor readings'}), 500

@main_bp.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

@main_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Resource not found'}), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({'error': 'Internal server error'}), 500
