import logging
import os

from flask import Flask
from flask_socketio import SocketIO

# Initialize SocketIO
socketio = SocketIO(cors_allowed_origins="*", logger=True, engineio_logger=True)


def create_app(config_name=None):
    """Application factory pattern with enhanced configuration."""
    app = Flask(__name__)

    # Configuration
    app.config.update(
        {
            "SECRET_KEY": os.getenv(
                "SECRET_KEY", "dev-secret-key-change-in-production"
            ),
            "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "MQTT_BROKER_HOST": os.getenv("MQTT_BROKER_HOST", "localhost"),
            "MQTT_BROKER_PORT": int(os.getenv("MQTT_BROKER_PORT", 1883)),
            "MQTT_USERNAME": os.getenv("MQTT_USERNAME"),
            "MQTT_PASSWORD": os.getenv("MQTT_PASSWORD"),
            "MQTT_TOPICS": os.getenv("MQTT_TOPICS", "sensors/+/+").split(","),
            "CELERY_BROKER_URL": os.getenv(
                "CELERY_BROKER_URL", "redis://localhost:6379/0"
            ),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "ENVIRONMENT": os.getenv("FLASK_ENV", "development"),
        }
    )

    # Enhanced logging configuration
    setup_logging(app)

    # Initialize SocketIO with app
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode="threading",
        logger=app.config["ENVIRONMENT"] == "development",
        engineio_logger=app.config["ENVIRONMENT"] == "development",
    )

    # Register blueprints
    from .views import main_bp

    app.register_blueprint(main_bp)

    # Register error handlers
    register_error_handlers(app)

    # Register SocketIO handlers
    from . import realtime

    # Health check endpoint
    @app.route("/health")
    def health_check():
        return {"status": "healthy", "version": "1.0.0"}, 200

    app.logger.info(
        f"Flask application created successfully (Environment: {app.config['ENVIRONMENT']})"
    )

    return app


def setup_logging(app):
    """Configure enhanced logging."""
    log_level = getattr(logging, app.config["LOG_LEVEL"].upper(), logging.INFO)

    # Remove default handlers
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Configure app logger
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[console_handler],
    )


def register_error_handlers(app):
    """Register enhanced error handlers."""

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 error: {error}")
        return {"error": "Resource not found"}, 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}")
        return {"error": "Internal server error"}, 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {error}", exc_info=True)
        return {"error": "An unexpected error occurred"}, 500
