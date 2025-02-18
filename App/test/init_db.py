import sys
import os
import pytz
from datetime import datetime, timedelta, timezone

# Get the absolute path to the project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))

# Add project root to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"Added {project_root} to Python path")

from App.dal.calendar import (
    sync_calendar_to_db,
    get_agent_events    
)

def main():
    calendar_path = f"{current_dir}/data/test_calendar.ics"
    
    # Sync calendar to database
    sync_calendar_to_db("123", "456", calendar_path)
    
    # Retrieve and print events
    events = get_agent_events("123", "456", datetime.now(timezone.utc) - timedelta(days=100), datetime.now(timezone.utc) + timedelta(days=100))
    for event in events:
        print(f"Calendar ID: {event.calendar_id}")
        print(f"Client ID: {event.client_id}")
        print(f"Agent ID: {event.agent_id}")
        print(f"Event: {event.summary}")
        print(f"Time: {event.start_time} - {event.end_time}")
        print("---")
    
if __name__ == "__main__":
    main()