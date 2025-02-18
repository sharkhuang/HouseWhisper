## Homework

## start server:

```
uvicorn App.router:app --reload --host 0.0.0.0 --port 8000
```


## API test examples:
Note: the start_time is in UTC timezone
* http://localhost:8000/api/v1/agent-schedule/check-availability?client_id=123&agent_id=456&start_time=2025-02-17T17:30:00Z
* http://localhost:8000/api/v1/agent-schedule/find-available-timeslots?client_id=123&agent_id=456&start_time=2025-02-17T17:30:00Z&duration_minutes=30&num_slots=3
* http://localhost:8000/api/v1/agent-schedule/check-day-utilization?client_id=123&agent_id=456&start_time=2025-02-17T17:30:00Z


## calendar.db:

* init db:
```
python test/init_db.py
```

* sync calendars:
```
python jobs/calendar_sync.py
```