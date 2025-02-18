from datetime import datetime, time, timedelta

# TODO: need to support local working hours later. 
# TODO: need to skip weekends later.
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
