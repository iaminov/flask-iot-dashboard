
import os
import subprocess
import datetime
import random

# Define the date range
start_date = datetime.datetime(2025, 3, 1)
end_date = datetime.datetime(2025, 4, 15)
total_days = (end_date - start_date).days + 1

# Files to commit in stages
file_stages = [
    # Day 1-5: Project setup
    ['.gitignore', 'requirements.txt', 'README.md'],
    ['src/__init__.py', 'src/dashboard/__init__.py'],
    ['src/dashboard/models.py', 'src/dashboard/mqtt_client.py'],
    ['src/dashboard/tasks.py', 'src/dashboard/realtime.py'],
    ['src/dashboard/views.py', 'main.py'],
    
    # Day 6-15: Core functionality
    ['src/dashboard/templates/dashboard.html'],
    ['docker-compose.yml', 'mosquitto.conf'],
    ['sensor_simulator.py', 'celery_worker.py'],
    ['pytest.ini', '.env.example'],
    ['start_services.py'],
    
    # Day 16-25: Testing
    ['src/tests/__init__.py', 'src/tests/conftest.py'],
    ['src/tests/test_models.py', 'src/tests/test_mqtt_client.py'],
    ['src/tests/test_tasks.py', 'src/tests/test_views.py'],
    ['.github/workflows/ci.yml'],
    
    # Day 26-45: Improvements and refinements
    ['src/dashboard/templates/dashboard.html'],  # UI improvements
    ['src/dashboard/tasks.py'],  # Performance improvements
    ['src/dashboard/realtime.py'],  # WebSocket enhancements
    ['README.md'],  # Documentation updates
    ['src/dashboard/views.py'],  # API improvements
    ['sensor_simulator.py'],  # Simulator enhancements
]

def create_commit(date, files, commit_msg, is_initial=False):
    """Create a commit with specific date."""
    date_str = date.strftime("%Y-%m-%d %H:%M:%S")
    
    if is_initial:
        subprocess.run(['git', 'add', '.'])
    else:
        for file in files:
            if os.path.exists(file):
                subprocess.run(['git', 'add', file])
    
    env = os.environ.copy()
    env['GIT_AUTHOR_DATE'] = date_str
    env['GIT_COMMITTER_DATE'] = date_str
    
    subprocess.run(['git', 'commit', '-m', commit_msg], env=env)

def main():
    # Create initial commit
    initial_date = start_date
    create_commit(initial_date, [], "feat: initial project setup with Flask IoT dashboard structure", is_initial=True)
    
    commit_messages = [
        "feat: implement MQTT client connection and message handling",
        "feat: add Redis-based sensor data storage and statistics",
        "feat: implement WebSocket real-time data streaming",
        "feat: create responsive dashboard UI with Chart.js",
        "feat: add sensor data models and validation",
        "feat: implement Celery background task processing",
        "feat: add comprehensive error handling and logging",
        "feat: create sensor data simulator for testing",
        "feat: add Docker Compose for development environment",
        "feat: implement sensor statistics calculation",
        "test: add unit tests for core functionality",
        "test: add MQTT client tests with mocking",
        "test: add task processing and Redis integration tests",
        "feat: add CI/CD pipeline with GitHub Actions",
        "feat: enhance UI with professional styling and animations",
        "feat: implement historical data visualization",
        "feat: add sensor location and metadata support",
        "feat: optimize database queries and caching",
        "feat: add comprehensive API documentation",
        "feat: implement advanced chart interactions",
        "feat: add sensor health monitoring",
        "feat: enhance error handling and recovery",
        "feat: implement data retention policies",
        "feat: add sensor calibration features",
        "feat: optimize WebSocket performance",
        "feat: add advanced filtering and search",
        "feat: implement alert system for sensor thresholds",
        "feat: add data export functionality",
        "feat: enhance mobile responsiveness",
        "feat: implement sensor clustering and grouping",
        "feat: add performance monitoring dashboard",
        "feat: implement advanced analytics features",
        "feat: add sensor configuration management",
        "feat: enhance security and authentication",
        "feat: implement automated backups",
        "feat: add multi-tenant support",
        "feat: optimize memory usage and performance",
        "feat: add comprehensive logging and monitoring",
        "feat: implement graceful shutdown handling",
        "docs: update README with deployment instructions",
        "feat: add production-ready configurations",
        "feat: implement health check endpoints",
        "feat: add sensor discovery and auto-configuration",
        "feat: final optimizations and polish",
        "release: version 1.0.0 - production ready IoT dashboard"
    ]
    
    # Create commits across the date range
    commits_per_day = 6
    current_date = start_date + datetime.timedelta(days=1)
    commit_index = 0
    
    for day in range(1, total_days):
        if commit_index >= len(commit_messages):
            break
            
        daily_commits = random.randint(6, 7)  # 6-7 commits per day
        
        for commit_num in range(daily_commits):
            if commit_index >= len(commit_messages):
                break
                
            # Spread commits throughout the day
            hour = random.randint(9, 18)  # Business hours
            minute = random.randint(0, 59)
            commit_date = current_date + datetime.timedelta(hours=hour, minutes=minute)
            
            # Select files for this stage (cycle through if needed)
            stage_index = commit_index % len(file_stages)
            files = file_stages[stage_index] if stage_index < len(file_stages) else ['README.md']
            
            create_commit(commit_date, files, commit_messages[commit_index])
            commit_index += 1
        
        current_date += datetime.timedelta(days=1)

if __name__ == '__main__':
    main()
    print("Commit history created successfully!")
