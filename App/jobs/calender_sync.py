import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
from datetime import datetime, timedelta
import schedule
from typing import List, Dict
from queue import Queue, Empty
import threading
from dal.calender import merge_calendar_to_db

class CalendarSyncQueue:
    def __init__(self, num_consumers: int = 2):
        self.task_queue = Queue()
        self.num_consumers = num_consumers
        self.consumers = []
        self.should_stop = threading.Event()
        
    def consumer(self) -> None:
        while not self.should_stop.is_set():
            try:
                agent = self.task_queue.get(timeout=5)
                try:
                    merge_calendar_to_db(
                        agent["client_id"],
                        agent["agent_id"],
                        agent["calender_url"]
                    )
                except Exception as e:
                    print(f"Error syncing calendar for agent {agent['agent_id']}: {str(e)}")
                finally:
                    self.task_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                print(f"Consumer error: {str(e)}")
                time.sleep(5)

    def start_consumers(self) -> None:
        self.should_stop.clear()
        for _ in range(self.num_consumers):
            consumer = threading.Thread(target=self.consumer, daemon=True)
            consumer.start()
            self.consumers.append(consumer)

    def stop_consumers(self) -> None:
        self.should_stop.set()
        for consumer in self.consumers:
            consumer.join()
        self.consumers.clear()

def schedule_sync(agent_list: List[Dict[str, str]], interval_mins: int) -> None:
    sync_queue = CalendarSyncQueue()
    sync_queue.start_consumers()

    try:
        while True:
            print("Syncing calendars...")
            for agent in agent_list:
                if agent.get("last_sync") is None or agent.get("last_sync") < datetime.now() - timedelta(minutes=interval_mins):
                    agent["last_sync"] = datetime.now()
                    sync_queue.task_queue.put(agent)
            time.sleep(60)
    except KeyboardInterrupt:
        print("Shutting down calendar sync...")
        sync_queue.stop_consumers()

if __name__ == "__main__":
    agent_list = [
        {
            "client_id": "123",
            "agent_id": "456",
            "calender_url": "./test/data/test_calendar.ics", 
            "last_sync": None
        }
    ]
    # sync every 2 hours
    schedule_sync(agent_list, 2*60*60)