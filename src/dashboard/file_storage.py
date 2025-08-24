
import json
import os
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FileStorage:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.sensors_file = os.path.join(data_dir, "sensors.json")
        self.readings_file = os.path.join(data_dir, "readings.json")
        self.stats_file = os.path.join(data_dir, "stats.json")
        self.lock = threading.Lock()
        
        # Create data directory
        os.makedirs(data_dir, exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize storage files if they don't exist."""
        for file_path in [self.sensors_file, self.readings_file, self.stats_file]:
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    json.dump({}, f)
    
    def _read_file(self, file_path: str) -> Dict[str, Any]:
        """Safely read JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _write_file(self, file_path: str, data: Dict[str, Any]):
        """Safely write JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def store_reading(self, sensor_id: str, reading_data: Dict[str, Any]):
        """Store a sensor reading."""
        with self.lock:
            readings = self._read_file(self.readings_file)
            
            if sensor_id not in readings:
                readings[sensor_id] = []
            
            # Add timestamp if not present
            if 'timestamp' not in reading_data:
                reading_data['timestamp'] = datetime.now().isoformat()
            
            readings[sensor_id].append(reading_data)
            
            # Keep only last 1000 readings per sensor
            readings[sensor_id] = readings[sensor_id][-1000:]
            
            self._write_file(self.readings_file, readings)
    
    def get_readings(self, sensor_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get readings for a sensor within the specified hours."""
        with self.lock:
            readings = self._read_file(self.readings_file)
            
            if sensor_id not in readings:
                return []
            
            # Filter by time
            cutoff_time = datetime.now() - timedelta(hours=hours)
            filtered_readings = []
            
            for reading in readings[sensor_id]:
                try:
                    reading_time = datetime.fromisoformat(reading['timestamp'].replace('Z', '+00:00'))
                    if reading_time >= cutoff_time:
                        filtered_readings.append(reading)
                except (ValueError, KeyError):
                    continue
            
            return filtered_readings
    
    def update_stats(self, sensor_id: str, reading_data: Dict[str, Any]):
        """Update sensor statistics."""
        with self.lock:
            stats = self._read_file(self.stats_file)
            
            value = reading_data.get('value', 0)
            
            if sensor_id not in stats:
                stats[sensor_id] = {
                    'sensor_id': sensor_id,
                    'min_value': value,
                    'max_value': value,
                    'avg_value': value,
                    'count': 1,
                    'last_reading': reading_data.get('timestamp', datetime.now().isoformat()),
                    'sensor_type': reading_data.get('type', ''),
                    'unit': reading_data.get('unit', ''),
                    'location': reading_data.get('location', 'Unknown')
                }
            else:
                current_stats = stats[sensor_id]
                count = current_stats['count'] + 1
                
                # Update stats
                current_stats['min_value'] = min(current_stats['min_value'], value)
                current_stats['max_value'] = max(current_stats['max_value'], value)
                current_stats['avg_value'] = ((current_stats['avg_value'] * (count - 1)) + value) / count
                current_stats['count'] = count
                current_stats['last_reading'] = reading_data.get('timestamp', datetime.now().isoformat())
                
            self._write_file(self.stats_file, stats)
    
    def get_all_stats(self) -> List[Dict[str, Any]]:
        """Get statistics for all sensors."""
        with self.lock:
            stats = self._read_file(self.stats_file)
            return list(stats.values())
    
    def cleanup_old_data(self, days: int = 7):
        """Clean up old readings."""
        with self.lock:
            readings = self._read_file(self.readings_file)
            cutoff_time = datetime.now() - timedelta(days=days)
            
            cleaned_count = 0
            for sensor_id in readings:
                original_count = len(readings[sensor_id])
                readings[sensor_id] = [
                    r for r in readings[sensor_id]
                    if datetime.fromisoformat(r['timestamp'].replace('Z', '+00:00')) >= cutoff_time
                ]
                cleaned_count += original_count - len(readings[sensor_id])
            
            self._write_file(self.readings_file, readings)
            logger.info(f"Cleaned up {cleaned_count} old readings")
            return cleaned_count

# Global storage instance
file_storage = FileStorage()
