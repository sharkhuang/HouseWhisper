from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from App.dal.calender import CalendarEvent
from App.dal.calender import get_db
from App.dal.calender import get_agent_events
# Create the router with a prefix
agent_schedule_router = APIRouter(
    prefix="/agent-schedule",
    tags=["agent-schedule"]
)

@agent_schedule_router.get("/check-availability")
async def check_availability(client_id: str,
    agent_id: str,
    start_time: datetime,
    duration_minutes: int = 30):
    """
    Check if an agent is available for a given time slot.
    
    Args:
        client: Client identifier requesting the availability check
        agent_id: The ID of the agent to check
        start_time: The requested start time
        duration_minutes: Duration of the requested slot in minutes
    
    Returns:
        Dict containing availability status and any conflicts
    """
    try:
        # Calculate end time
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        db = get_db()
        query = db.query(CalendarEvent).filter(
            and_(
                CalendarEvent.client_id == client_id,
                CalendarEvent.agent_id == agent_id,
                or_(
                    # Event starts during requested slot
                    and_(
                        CalendarEvent.start_time >= start_time,
                        CalendarEvent.start_time < end_time
                    ),
                    # Event ends during requested slot
                    and_(
                        CalendarEvent.end_time > start_time,
                        CalendarEvent.end_time <= end_time
                    ),
                    # Event encompasses requested slot
                    and_(
                        CalendarEvent.start_time <= start_time,
                        CalendarEvent.end_time >= end_time
                    )
                )
            )
        )
        
        conflicts = query.all()
        if conflicts:
            return {
                "available": False,
                "reason": "Time slot conflicts with existing appointments",
                "conflicts": [
                    {
                        "start": event.start_time,
                        "end": event.end_time,
                    } for event in conflicts
                ]
            }
            
        return {
                "available": True,
                "slot": {
                    "start": start_time,
                    "end": end_time,
                    "duration_minutes": duration_minutes
                }
            }
            
    except Exception as e:
        return {
            "available": False,
            "reason": "Internal error checking availability",
            "error": str(e)
        }

    
def find_slots(events, start_time: datetime, duration_minutes: int, limit: int = 3):
    """
    Find available time slots between events where interval >= duration_minutes
    Args:
        events: List of events sorted by start_time
        duration_minutes: Required duration in minutes
        limit: Maximum number of slots to return
    Returns:
        List of tuples (start_time, end_time) representing available slots
    """
    available_slots = []
    duration_delta = timedelta(minutes=duration_minutes)
    # Initialize with first event's end time
    last_end_time = start_time
    # Check intervals between events
    for event in events:
        interval_start = last_end_time
        interval_end = event.start_time
        
        # If interval is large enough
        if interval_end - interval_start >= duration_delta:
            available_slots.append((interval_start, interval_end))
            if len(available_slots) >= limit:
                break
                
        last_end_time = max(last_end_time, event.end_time)
    
    if len(available_slots) < limit:
        for i in range(limit - len(available_slots)):
            available_slots.append((last_end_time, last_end_time + duration_delta))
            last_end_time += duration_delta 

    return available_slots[:limit]

@agent_schedule_router.get("/find-available-timeslots")
async def find_available_timeslots(client_id: str,
    agent_id: str,
    start_time: datetime = None,
    end_time: datetime = None,
    duration_minutes: int = 60,
    num_slots: int = 3):
    """
    Find available time slots within given time ranges
    
    Parameters:
    - client: Unique identifier for the client
    - agent_id: Unique identifier for the agent
    - time_ranges: List of time ranges to search within
    - duration_minutes: Desired meeting duration in minutes (default: 60)
    - num_slots: Number of available slots to return (default: 3)
    
    Returns:
    - available_slots: List of available time slots
    """
    try:
        # Get all events for the agent
        if start_time is None:
            start_time = datetime.now(timezone.utc)
        if end_time is None:
            end_time = start_time + timedelta(days=1)

        events = get_agent_events(client_id, agent_id, start_time, end_time)
        available_slots = find_slots(events, start_time, duration_minutes, num_slots)
        return {
            "available_slots": available_slots
        }
    
    except Exception as e:
        return {
            "available": False,
            "reason": "Internal error checking availability",
            "error": str(e)
        }

@agent_schedule_router.get("/check-day-utilization")
async def check_day_utilization(client_id: str,
    agent_id: str,
    date: datetime = None):
    """
    Check the utilization of an agent's calendar for a specific day
    
    Args:
        client_id: Unique identifier for the client
        agent_id: Unique identifier for the agent
        date: The specific date to check
    
    Returns:
        Dict containing utilization information
    """
    try:
        # Get all events for the agent on the specific date
        print(f"Checking utilization for {agent_id} on {date}")
        if date is None:
            date = datetime.now(timezone.utc)

        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date + timedelta(days=1), datetime.min.time())

        events = get_agent_events(client_id, agent_id, start_time, end_time)
        
        # Calculate total utilization for the day
        total_utilization = 0
        for event in events:
            total_utilization += (event.end_time - event.start_time).total_seconds() / 60
        
        total_minutes = 8 * 60 # 8 hours per day    
        utilization_percentage = round((total_utilization / total_minutes) * 100)
        return {
            "utilization_percentage": utilization_percentage,
            "events": events
        }
    except Exception as e:
        return {
            "available": False,
            "reason": "Internal error checking utilization",
            "error": str(e)
        }
    

# Example endpoint
@agent_schedule_router.get("/")
async def get_schedules(client_id: str, agent_id: str, start_time: datetime = None, end_time: datetime = None):
    events = get_agent_events(client_id, agent_id, start_time, end_time)
    return {"message": "Agent schedules endpoint" , "events": events}