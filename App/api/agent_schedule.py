from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from App.dal.calender import CalendarEvent
from App.dal.calender import get_db
from App.dal.calender import get_events
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
        
        """
        # Business hours check (assuming 9 AM to 5 PM)
        if local_start_time.hour < 9 or local_end_time.hour >= 17:
            return {
                "available": False,
                "reason": "Requested time is outside business hours (9 AM - 5 PM)"
            }
        """

        print(f"start_time: {start_time}")
        print(f"end_time: {end_time}")
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
                        "type": event.event_type
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

    

@agent_schedule_router.post("/find-available-times")
async def find_available_times(client: str,
    agent_id: str,
    time_ranges: List[datetime],
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
    pass

@agent_schedule_router.get("/check-day-utilization")
async def check_day_utilization(client: str,
    agent_id: str,
    date: datetime):
    pass

# Example endpoint
@agent_schedule_router.get("/")
async def get_schedules():
    events = get_events()
    for event in events:
        print(f"event: {event.calendar_id}")
    return {"message": "Agent schedules endpoint" , "events": events}