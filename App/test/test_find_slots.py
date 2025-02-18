import pytest
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from App.api.agent_schedule import find_slots
from App.dal.calendar import CalendarEvent

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

    def test_slots_before_first_event(self):
        """Test finding slots before the first event"""
        start_time = datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc)
        event_start = datetime(2024, 3, 1, 10, 0, tzinfo=timezone.utc)
        duration_minutes = 30
        
        events = [create_event(event_start, 60)]
        slots = find_slots(events, start_time, duration_minutes)
        
        assert len(slots) == 2  # Should find 2 30-minute slots before 10:00
        assert slots[0]["start"] == start_time
        assert slots[0]["end"] == start_time + timedelta(minutes=duration_minutes)
        assert slots[1]["start"] == start_time + timedelta(minutes=duration_minutes)
        assert slots[1]["end"] == start_time + timedelta(minutes=duration_minutes*2)

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

    def test_no_available_slots(self):
        """Test when there are no available slots between events"""
        start_time = datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc)
        events = [
            create_event(datetime(2024, 3, 1, 9, 0, tzinfo=timezone.utc), 60),  # 9:00-10:00
            create_event(datetime(2024, 3, 1, 10, 0, tzinfo=timezone.utc), 60)  # 10:00-11:00
        ]
        duration_minutes = 30
        
        slots = find_slots(events, start_time, duration_minutes)
        
        assert len(slots) == 0  # Should find no slots

 