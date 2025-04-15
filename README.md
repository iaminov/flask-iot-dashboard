
# Flask IoT Dashboard

A real-time IoT sensor data dashboard that ingests MQTT sensor data, processes it with Celery workers, and provides live updates to clients via WebSockets.

## Features

- Real-time MQTT sensor data ingestion
- Background data processing with Celery
- Live WebSocket updates to dashboard clients
- Redis-based data storage and caching
- RESTful API endpoints
- Responsive web dashboard with Chart.js visualizations
- Comprehensive test coverage
- CI/CD pipeline with GitHub Actions

## Architecture

```
MQTT Broker → MQTT Client → Celery Tasks → Redis → WebSocket → Dashboard
```

- **MQTT Client**: Subscribes to sensor topics and forwards messages to Celery
- **Celery Workers**: Process raw sensor data and update statistics
- **Redis**: Stores sensor readings and aggregated statistics
- **WebSocket Layer**: Pushes real-time updates to connected clients
- **Dashboard**: Interactive web interface with live charts

## Tech Stack

- **Backend**: Python 3.11+, Flask, Flask-SocketIO
- **Message Queue**: Celery with Redis broker
- **Data Storage**: Redis
- **MQTT**: paho-mqtt client
- **Frontend**: HTML5, CSS3, JavaScript, Chart.js, Socket.IO
- **Testing**: pytest with comprehensive test coverage
- **CI/CD**: GitHub Actions

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/iaminov/flask-iot-dashboard.git
   cd flask-iot-dashboard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start Redis server**
   ```bash
   redis-server
   ```

5. **Start Celery worker**
   ```bash
   python celery_worker.py
   ```

6. **Run the application**
   ```bash
   python main.py
   ```

The dashboard will be available at `http://localhost:5000`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MQTT_BROKER_HOST` | MQTT broker hostname | `localhost` |
| `MQTT_BROKER_PORT` | MQTT broker port | `1883` |
| `MQTT_USERNAME` | MQTT username | - |
| `MQTT_PASSWORD` | MQTT password | - |
| `MQTT_TOPICS` | Comma-separated MQTT topics | `sensors/+/+` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `SECRET_KEY` | Flask secret key | Required in production |
| `PORT` | Server port | `5000` |

## MQTT Message Format

Sensors should publish JSON messages in the following format:

```json
{
  "sensor_id": "temp_01",
  "type": "temperature",
  "value": 23.5,
  "unit": "°C",
  "timestamp": "2024-01-01T12:00:00Z",
  "location": "Room A",
  "metadata": {
    "calibrated": true
  }
}
```

Required fields: `value`
Optional fields: `sensor_id`, `type`, `unit`, `timestamp`, `location`, `metadata`

## API Endpoints

- `GET /` - Dashboard interface
- `GET /api/sensors` - Get all sensor statistics
- `GET /api/sensors/{sensor_id}/readings?hours=24` - Get sensor readings
- `GET /health` - Health check endpoint

## WebSocket Events

**Client to Server:**
- `request_sensor_data` - Request historical data for a sensor
- `request_all_stats` - Request statistics for all sensors

**Server to Client:**
- `sensor_update` - Real-time sensor reading update
- `sensor_history` - Historical sensor data response
- `sensor_stats` - All sensor statistics response

## Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

## Deployment

The application is ready for production deployment on platforms like Replit, Heroku, or any cloud provider supporting Python applications.

For production:
1. Set environment variables
2. Use a production WSGI server (gunicorn included)
3. Deploy Redis instance
4. Run Celery workers separately
5. Configure MQTT broker access

## Development

1. **Code formatting**
   ```bash
   black src/ *.py
   isort src/ *.py
   ```

2. **Linting**
   ```bash
   flake8 src/ *.py
   ```

3. **Run tests**
   ```bash
   pytest -v
   ```

## Project Structure

```
flask-iot-dashboard/
├── src/
│   ├── dashboard/
│   │   ├── __init__.py          # Flask app factory
│   │   ├── mqtt_client.py       # MQTT client implementation
│   │   ├── tasks.py             # Celery tasks
│   │   ├── realtime.py          # WebSocket handlers
│   │   ├── views.py             # Flask routes
│   │   ├── models.py            # Data models
│   │   └── templates/
│   │       └── dashboard.html   # Dashboard interface
│   └── tests/                   # Test suite
├── main.py                      # Application entry point
├── celery_worker.py            # Celery worker entry point
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## License

MIT License - see LICENSE file for details.
