import pytest
from datetime import datetime, timedelta, timezone
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

 