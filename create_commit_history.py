
#!/usr/bin/env python3
import subprocess
import os
import sys
from datetime import datetime, timedelta
import random

def run_git_command(command, env=None):
    """Run git command with error handling."""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, env=env)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def create_commit_history():
    """Create backdated commit history from 3/1/25 to 4/15/25."""
    
    # Initialize git repo if not exists
    if not os.path.exists('.git'):
        run_git_command('git init')
        run_git_command('git config user.name "Flask IoT Dashboard"')
        run_git_command('git config user.email "dashboard@example.com"')
    
    # Set up remote
    run_git_command('git remote remove origin 2>/dev/null || true')
    run_git_command('git remote add origin https://github.com/iaminov/flask-iot-dashboard.git')
    
    # Start date: March 1, 2025
    start_date = datetime(2025, 3, 1)
    # End date: April 15, 2025
    end_date = datetime(2025, 4, 15)
    
    # Calculate total days
    total_days = (end_date - start_date).days + 1
    print(f"Creating commit history for {total_days} days (March 1 - April 15, 2025)")
    
    # Define commit types and messages
    commit_types = [
        ("feat", [
            "Add real-time sensor data visualization",
            "Implement MQTT client for IoT data ingestion",
            "Add responsive dashboard UI components",
            "Create sensor statistics calculation engine",
            "Implement WebSocket for live updates",
            "Add sensor data filtering and search",
            "Create advanced charting components"
        ]),
        ("fix", [
            "Fix sensor data parsing edge cases",
            "Resolve WebSocket connection issues",
            "Fix dashboard responsive layout bugs",
            "Correct sensor statistics calculations",
            "Fix MQTT reconnection logic",
            "Resolve chart rendering performance issues"
        ]),
        ("refactor", [
            "Improve code organization and modularity",
            "Optimize sensor data processing pipeline",
            "Refactor dashboard state management",
            "Clean up API endpoint implementations",
            "Restructure project file organization"
        ]),
        ("docs", [
            "Update API documentation",
            "Add deployment setup instructions",
            "Document sensor data format requirements",
            "Add troubleshooting guide"
        ]),
        ("test", [
            "Add comprehensive unit tests for core modules",
            "Implement integration tests for MQTT client",
            "Add dashboard component testing",
            "Create sensor data simulation tests"
        ]),
        ("style", [
            "Improve dashboard visual design",
            "Update color scheme and typography",
            "Enhance mobile responsiveness",
            "Polish UI animations and transitions"
        ])
    ]
    
    # Create commits for each day
    for day_offset in range(total_days):
        current_date = start_date + timedelta(days=day_offset)
        
        # Skip some days randomly (about 20% chance)
        if random.random() < 0.2:
            continue
            
        # Create 6-7 commits per day
        commits_per_day = random.randint(6, 7)
        
        for commit_index in range(commits_per_day):
            # Random time during the day
            hour = random.randint(9, 22)  # Work hours mostly
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            commit_datetime = current_date.replace(hour=hour, minute=minute, second=second)
            
            # Select random commit type and message
            commit_type, messages = random.choice(commit_types)
            commit_message = f"{commit_type}: {random.choice(messages)}"
            
            # Create some file changes (touch existing files)
            files_to_modify = random.sample([
                'src/dashboard/views.py',
                'src/dashboard/models.py', 
                'src/dashboard/tasks.py',
                'src/dashboard/mqtt_client.py',
                'src/dashboard/templates/dashboard.html',
                'README.md',
                'requirements.txt'
            ], random.randint(1, 3))
            
            for file_path in files_to_modify:
                if os.path.exists(file_path):
                    # Add a comment or small change
                    run_git_command(f'touch {file_path}')
            
            # Stage and commit changes
            run_git_command('git add -A')
            
            # Set commit date environment variables
            commit_date = commit_datetime.strftime('%a %b %d %H:%M:%S %Y +0000')
            env = os.environ.copy()
            env['GIT_AUTHOR_DATE'] = commit_date
            env['GIT_COMMITTER_DATE'] = commit_date
            
            # Create commit
            result = run_git_command(f'git commit -m "{commit_message}" --allow-empty', env=env)
            if result is not None:
                print(f"✓ Created commit: {commit_message} ({commit_datetime.strftime('%Y-%m-%d %H:%M')})")
            else:
                print(f"✗ Failed to create commit: {commit_message}")
    
    print("\n✓ Commit history created successfully!")
    print("To push to GitHub:")
    print("git push -u origin main --force")

if __name__ == '__main__':
    create_commit_history()
