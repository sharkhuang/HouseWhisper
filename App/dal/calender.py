from icalendar import Calendar
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Initialize SQLAlchemy
Base = declarative_base()

class CalendarEvent(Base):
    __tablename__ = 'calendar_events'
    
    calendar_id = Column(String, primary_key=True)
    client_id = Column(String)
    agent_id = Column(String)
    summary = Column(String)
    description = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)


# Global variables for engine and session
engine = None
session = None

def init_db():
    # Create database URL
    db_url = "sqlite:///calendar.db"  # Use SQLite for simplicity
    
    global engine, session
    if engine is None:
        # Create database engine and tables
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        
    # Create session factory
    Session = sessionmaker(bind=engine)
    
    return engine, Session()

def get_db():
    global engine, session
    if session is None:
        engine, session = init_db()

    print(session)
    return session

def close_db():
    global session
    if session:
        session.close()
        session = None
    
def sync_calendar_to_db(client_id: str, agent_id: str, calendar_path):
    """Sync calendar events to database"""
    
    cal = None
    with open(calendar_path, 'rb') as f:
        cal = Calendar.from_ical(f.read())

    session = get_db()
    # Process each event
    for component in cal.walk('VEVENT'):
        existing_event = session.query(CalendarEvent).filter_by(
            calendar_id=str(component.get('uid'))  # Convert vText to string
        ).first()
        if existing_event:
            continue

        event = CalendarEvent(
            calendar_id=component.get('uid'),
            client_id=client_id,
            agent_id=agent_id,
            summary=str(component.get('summary')),
            description=str(component.get('description', '')),
            start_time=component.get('dtstart').dt,
            end_time=component.get('dtend').dt if component.get('dtend') else None
        )
        
        session.add(event)
    
    # Commit changes
    session.commit()
    session.close()

def get_events():
    try:
        db = get_db()
        events = db.query(CalendarEvent).all()
        print(f"Query executed, found {len(events)} events")
        return events
    except Exception as e:
        print(f"Error in get_events: {str(e)}")
        return []