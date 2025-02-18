import pytest
from datetime import datetime, timedelta, timezone
from datetime import time
from dataclasses import dataclass

# Mock CalendarEvent class
@dataclass
class CalendarEvent:
    client_id: str
    agent_id: str
    start_time: datetime
    end_time: datetime

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

    if not events:
        for i in range(limit):
            slot = {
                "start": last_end_time,
                "end": last_end_time + duration_delta,
                "duration_minutes": duration_minutes
            }
            available_slots.append(slot)
            last_end_time = slot["end"]
        return available_slots
    else:
        while last_end_time + duration_delta <= events[0].start_time:
            slot = { "start": last_end_time, "end": last_end_time + duration_delta, "duration_minutes": duration_minutes}
            available_slots.append(slot)
            if len(available_slots) >= limit:
                return available_slots
            last_end_time = slot["end"]

    for event in events:
        if event.end_time <= start_time:
            continue

        if last_end_time >= event.start_time and last_end_time < event.end_time:
            last_end_time = event.end_time
            continue

        while last_end_time + duration_delta <= event.start_time:
            slot = {
                "start": last_end_time,
                "end": last_end_time+duration_delta,
                "duration_minutes": duration_minutes
            }
            available_slots.append(slot)
            if len(available_slots) >= limit:
                return available_slots

            last_end_time = slot["end"]

        last_end_time = max(last_end_time, event.end_time)

    return available_slots


def is_within_working_hours(dt: datetime) -> bool:
    """Check if datetime is within working hours (9AM-5PM UTC)"""
    work_start = time(9, 0)  # 9 AM UTC
    work_end = time(17, 0)   # 5 PM UTC
    return work_start <= dt.time() < work_end

def get_next_working_time(dt: datetime) -> datetime:
    """Get the next available working time"""
    work_start = time(9, 0)
    work_end = time(17, 0)
    
    # If before work hours, move to start of work day
    if dt.time() < work_start:
        return dt.replace(hour=9, minute=0, second=0, microsecond=0)
    
    # If after work hours, move to start of next work day
    if dt.time() >= work_end:
        next_day = dt + timedelta(days=1)
        return next_day.replace(hour=9, minute=0, second=0, microsecond=0)
    
    return dt

def find_slots_with_working_hours(events, start_time: datetime, duration_minutes: int, limit: int = 3):
    """
    Find available time slots between events where interval >= duration_minutes
    Only considers working hours (9AM-5PM UTC)
    
    Args:
        events: List of events sorted by start_time
        start_time: Starting time to search from
        duration_minutes: Required duration in minutes
        limit: Maximum number of slots to return
        
    Returns:
        List of dicts with start, end times and duration for available slots
    """
    available_slots = []
    duration_delta = timedelta(minutes=duration_minutes)
    
    # Ensure start_time is within working hours
    last_end_time = get_next_working_time(start_time)
    # Handle empty events list
    if not events:
        while len(available_slots) < limit:
            end_time = last_end_time + duration_delta
            
            # Check if both start and end are within working hours
            if is_within_working_hours(last_end_time) and is_within_working_hours(end_time):
                slot = {
                    "start": last_end_time,
                    "end": end_time,
                    "duration_minutes": duration_minutes
                }
                available_slots.append(slot)
                last_end_time = end_time
            else:
                last_end_time = get_next_working_time(end_time)
        return available_slots
    # Handle slots before first event
    if last_end_time < events[0].start_time:
        while (last_end_time + duration_delta <= events[0].start_time):
            potential_end = last_end_time + duration_delta
            
            if (is_within_working_hours(last_end_time) and 
                is_within_working_hours(potential_end)):
                slot = {
                    "start": last_end_time,
                    "end": potential_end,
                    "duration_minutes": duration_minutes
                }
                available_slots.append(slot)
                if len(available_slots) >= limit:
                    return available_slots
                last_end_time = potential_end
            else:
                last_end_time = get_next_working_time(potential_end)
    # Check intervals betwee
    print(f"last_end_time2: {last_end_time}")
    for event in events:
        if event.end_time <= last_end_time:
            continue
            
        if last_end_time >= event.start_time:
            last_end_time = max(last_end_time, event.end_time)
            continue
        print(f"last_end_time3: {last_end_time}")
        interval_start = get_next_working_time(last_end_time)
        while (interval_start + duration_delta <= event.start_time):
            potential_end = interval_start + duration_delta
            
            if (is_within_working_hours(interval_start) and 
                is_within_working_hours(potential_end)):
                slot = {
                    "start": interval_start,
                    "end": potential_end,
                    "duration_minutes": duration_minutes
                }
                available_slots.append(slot)
                if len(available_slots) >= limit:
                    return available_slots
                interval_start = potential_end
            else:
                interval_start = get_next_working_time(potential_end)
            
        last_end_time = event.end_time
    
    return available_slots


def create_event(start_time: datetime, duration_minutes: int) -> CalendarEvent:
    """Helper function to create a CalendarEvent"""
    end_time = start_time + timedelta(minutes=duration_minutes)
    return CalendarEvent(
        client_id="test_client",
        agent_id="test_agent",
        start_time=start_time,
        end_time=end_time
    )

class TestFindSlots:
    def test_no_events(self):
        """Test finding slots when there are no events"""
        start_time = datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc)
        duration_minutes = 30
        limit = 3
        
        slots = find_slots([], start_time, duration_minutes, limit)
        
        assert len(slots) == limit
        for i, slot in enumerate(slots):
            expected_start = start_time + i * timedelta(minutes=duration_minutes)
            expected_end = expected_start + timedelta(minutes=duration_minutes)
            assert slot["start"] == expected_start
            assert slot["end"] == expected_end
            assert slot["duration_minutes"] == duration_minutes

    def test_slots_between_events(self):
        """Test finding slots between two events"""
        start_time = datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc)
        events = [
            create_event(datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc), 60),  # 9:00-10:00
            create_event(datetime(2024, 3, 1, 11, 0, tzinfo=timezone.utc), 60)  # 11:00-12:00
        ]
        duration_minutes = 30
        
        slots = find_slots(events, start_time, duration_minutes)
        
        assert len(slots) == 2  # Should find 2 30-minute slots between 10:00 and 11:00
        assert slots[0]["start"] == datetime(2024, 3, 1, 10, 0, tzinfo=timezone.utc)
        assert slots[0]["end"] == datetime(2024, 3, 1, 10, 30, tzinfo=timezone.utc)
        assert slots[1]["start"] == datetime(2024, 3, 1, 10, 30, tzinfo=timezone.utc)
        assert slots[1]["end"] == datetime(2024, 3, 1, 11, 0, tzinfo=timezone.utc)

    def test_slots_between_events(self):
        """Test finding slots between 3 events"""
        start_time = datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc)
        events = [
            create_event(datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc), 60),  # 9:00-10:00
            create_event(datetime(2024, 3, 1, 11, 0, tzinfo=timezone.utc), 60), # 11:00-12:00
            create_event(datetime(2024, 3, 1, 12, 30, tzinfo=timezone.utc), 30)  # 12:30-13:00
        ]
        duration_minutes = 30
        
        slots = find_slots(events, start_time, duration_minutes, limit=3)
        assert len(slots) == 3  # Should find 3 30-minute slots between 10:00 and 11:00
        assert slots[0]["start"] == datetime(2024, 3, 1, 10, 0, tzinfo=timezone.utc)
        assert slots[0]["end"] == datetime(2024, 3, 1, 10, 30, tzinfo=timezone.utc)
        assert slots[1]["start"] == datetime(2024, 3, 1, 10, 30, tzinfo=timezone.utc)
        assert slots[1]["end"] == datetime(2024, 3, 1, 11, 0, tzinfo=timezone.utc)
        assert slots[2]["start"] == datetime(2024, 3, 1, 12, 0, tzinfo=timezone.utc)
        assert slots[2]["end"] == datetime(2024, 3, 1, 12, 30, tzinfo=timezone.utc)


    def test_slots_before_events(self):
        """Test finding slots before events"""
        start_time = datetime(2024, 3, 1, 8, 0, tzinfo=timezone.utc)
        events = [
            create_event(datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc), 60),  # 9:00-10:00
            create_event(datetime(2024, 3, 1, 11, 0, tzinfo=timezone.utc), 60), # 11:00-12:00
            create_event(datetime(2024, 3, 1, 12, 30, tzinfo=timezone.utc), 30)  # 12:30-13:00
        ]
        duration_minutes = 30
        
        slots = find_slots(events, start_time, duration_minutes, limit=3)
        assert len(slots) == 3  # Should find 3 30-minute slots between 10:00 and 11:00
        assert slots[0]["start"] == datetime(2024, 3, 1, 8, 0, tzinfo=timezone.utc)
        assert slots[0]["end"] == datetime(2024, 3, 1, 8, 30, tzinfo=timezone.utc)
        assert slots[1]["start"] == datetime(2024, 3, 1, 8, 30, tzinfo=timezone.utc)
        assert slots[1]["end"] == datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc)
        assert slots[2]["start"] == datetime(2024, 3, 1, 10, 0, tzinfo=timezone.utc)
        assert slots[2]["end"] == datetime(2024, 3, 1, 10, 30, tzinfo=timezone.utc)

    def test_respect_limit(self):
        """Test that the function respects the slot limit"""
        start_time = datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc)
        events = [
            create_event(datetime(2024, 3, 1, 11, 0, tzinfo=timezone.utc), 120)  # 11:00-12:00
        ]
        duration_minutes = 30
        limit = 3
        
        slots = find_slots(events, start_time, duration_minutes, limit)
        
        assert len(slots) == limit  # Should only return 3 slots even though more are available
        assert slots[0]["start"] == start_time
        assert slots[0]["end"] == start_time + timedelta(minutes=duration_minutes)


    def test_find_slots_with_working_hours(self):
        """Test finding slots with working hours"""
        start_time = datetime(2024, 3, 1, 8, 0, tzinfo=timezone.utc)

        duration_minutes = 30
        limit = 3
        slots = find_slots_with_working_hours([], start_time, duration_minutes, limit)
        assert len(slots) == limit
        assert slots[0]["start"] == datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc)
        assert slots[0]["end"] == datetime(2024, 3, 1, 9, 30, tzinfo=timezone.utc)


    def test_find_slots_with_working_hour_in_second_day(self):
        #Test finding slots with working hours
        start_time = datetime(2024, 3, 1, 16, 45, tzinfo=timezone.utc)

        duration_minutes = 30
        limit = 3
        slots = find_slots_with_working_hours([], start_time, duration_minutes, limit)
        assert len(slots) == limit
        assert slots[0]["start"] == datetime(2024, 3, 2, 9, 0, tzinfo=timezone.utc)
        assert slots[0]["end"] == datetime(2024, 3, 2, 9, 30, tzinfo=timezone.utc)
 
    def test_find_slots_with_working_hours_in_second_day_after_event(self):
        #Test finding slots with working hours
        start_time = datetime(2024, 3, 1, 16, 30, tzinfo=timezone.utc)
        events = [
            create_event(datetime(2024, 3, 1, 16, 15, tzinfo=timezone.utc), 30),  # 16:15-16:45
            create_event(datetime(2024, 3, 2, 11, 0, tzinfo=timezone.utc), 30),  # 16:15-16:45
        ]
        duration_minutes = 30
        limit = 3
        slots = find_slots_with_working_hours(events, start_time, duration_minutes, limit)
        assert len(slots) == limit
        assert slots[0]["start"] == datetime(2024, 3, 2, 9, 0, tzinfo=timezone.utc)
        assert slots[0]["end"] == datetime(2024, 3, 2, 9, 30, tzinfo=timezone.utc)
 