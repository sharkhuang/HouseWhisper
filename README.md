## Homework


## In calendar.db:

```
python test/init_db.py
```


## start server:

```
uvicorn App.router:app --reload --host 0.0.0.0 --port 8000
```


## API test examples:
* http://localhost:8000/api/v1/agent-schedule/check-availability?client_id=123&agent_id=456&start_time=2025-02-17 19:00:00-08:00
