from icalendar import Calendar
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, date
from sqlalchemy.types import TypeDecorator  
import os
# Initialize SQLAlchemy
Base = declarative_base()

class UTCDateTime(TypeDecorator):
    """Automatically convert naive datetime to UTC and store with timezone info"""
    impl = DateTime(timezone=True)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
            
        # Convert date to datetime if necessary
        if isinstance(value, date) and not isinstance(value, datetime):
            value = datetime.combine(value, datetime.min.time())
            
        # Now handle timezone
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc)


class CalendarEvent(Base):
    __tablename__ = 'calendar_events'
    
    calendar_id = Column(String, primary_key=True)
    client_id = Column(String, index=True)
    agent_id = Column(String, index=True)
    summary = Column(String)
    description = Column(String)
    start_time = Column(UTCDateTime, index=True)
    end_time = Column(UTCDateTime)

    # Create combined index
    __table_args__ = (
        Index('idx_client_agent_start', 'client_id', 'agent_id', 'start_time'),
    )
    __table_args__ = (
        Index('idx_client_agent_start_end', 'client_id', 'agent_id', 'end_time'),
    )

# Global variables for engine and session
engine = None
session = None

def init_db():
    # Create database URL using absolute path
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'calendar.db'))
    db_url = f"sqlite:///{db_path}"
    
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
            end_time=component.get('dtend').dt
        )
        
        session.add(event)
    
    # Commit changes
    session.commit()
    session.close()

def get_agent_events(client_id: str, agent_id: str, start_time: datetime = None, end_time: datetime = None):
    try:
        max_events = 100
        db = get_db()
        query = db.query(CalendarEvent).filter_by(client_id=client_id, agent_id=agent_id)
        if start_time:
            query = query.filter(CalendarEvent.start_time >= start_time)
        if end_time:
            query = query.filter(CalendarEvent.end_time <= end_time)
        
        events = query.order_by(CalendarEvent.start_time.asc()).limit(max_events).all()
        return events
    except Exception as e:
        print(f"Error in get_events: {str(e)}")
        return []