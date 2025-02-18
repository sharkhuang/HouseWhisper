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
        
        conflicts = query.order_by(CalendarEvent.start_time.asc()).all()
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
  
    last_end_time = start_time if start_time else datetime.now(timezone.utc)

    if start_time < events[0].start_time:
        while start_time + duration_delta < events[0].start_time:
            slot = { "start": start_time, "end": start_time + duration_delta, "duration_minutes": duration_minutes}
            print("slot")
            print(slot)
            available_slots.append(slot)
            if len(available_slots) >= limit:
                return available_slots
            last_end_time = slot["end"]
            start_time = slot["end"]
    # Check intervals between events

    for event in events:
        if event.end_time <= start_time:
            continue

        if last_end_time >= event.start_time and last_end_time < event.end_time:
            last_end_time = event.end_time
            continue

        interval_start = last_end_time
        interval_end = event.start_time
        # If interval is large enough
        while interval_end - interval_start >= duration_delta:
            available_slot = {
                "start": interval_start,
                "end": interval_end,
                "duration_minutes": duration_minutes
            }
            available_slots.append(available_slot)
            if len(available_slots) >= limit:
                break
            interval_start = interval_end
            interval_end = interval_start + duration_delta

        last_end_time = max(last_end_time, event.end_time)

    return available_slots

@agent_schedule_router.get("/find-available-timeslots")
async def find_available_timeslots(client_id: str,
    agent_id: str,
    start_time: datetime = None,
    end_time: datetime = None,
    duration_minutes: int = 30,
    num_slots: int = 3):
    """
    Find available time slots within given time ranges
    
    Parameters:
    - client_id: Unique identifier for the client
    - agent_id: Unique identifier for the agent
    - start_time: The specific date to check
    - end_time: The specific date to check
    - duration_minutes: Desired meeting duration in minutes (default: 30)
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

        if available_slots is None or len(available_slots) < num_slots:    
            # if no enough available slots, find the potential earliest slot in the next 5 days
            start_time = end_time
            end_time = start_time + timedelta(days=5)
            events = get_agent_events(client_id, agent_id, start_time, end_time)
            available_slots = find_slots(events, start_time, duration_minutes, num_slots-len(available_slots))
            if available_slots is None or len(available_slots) == 0:
                return {
                    "message": f"No available slots in the search range and 5 days later",
                }
            else:
                return {
                    "available_slots": available_slots,
                    "earliest_slot": available_slots[0]["start"],
                    "events": events
                }
        else:
            return {
                "available_slots": available_slots,
                "earliest_slot": available_slots[0]["start"],
                "events": events
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
    start_time: datetime = None,
    days: int = 1):
    """
    Check the utilization of an agent's calendar for a specific day
    
    Args:
        client_id: Unique identifier for the client
        agent_id: Unique identifier for the agent
        start_time: The specific date to check
        days: The number of days to check
    
    Returns:
        Dict containing utilization information
    """
    try:
        # Get all events for the agent on the specific date
        if start_time is None:
            start_time = datetime.now(timezone.utc)

        utilization_list = []
        for i in range(days):
            end_time = start_time + timedelta(days=1)
            events = get_agent_events(client_id, agent_id, start_time, end_time)
            # Calculate total utilization for the day
            total_utilization = 0
            for event in events:
                total_utilization += (event.end_time - event.start_time).total_seconds() / 60
        
            total_minutes = 8 * 60 # 8 hours per day    
            utilization_percentage = round((total_utilization / total_minutes) * 100)
            utilization = {
                "start_time": start_time,
                "end_time": end_time,
                "utilization_percentage": utilization_percentage,
                "events": events
            }
            utilization_list.append(utilization)

            start_time = end_time
        return {
            "utilization": utilization_list,
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
    if start_time is None:
        start_time = datetime.now(timezone.utc)
    if end_time is None:
        end_time = start_time + timedelta(days=7)
    events = get_agent_events(client_id, agent_id, start_time, end_time)
    return {"message": "Agent schedules endpoint" , "events": events}