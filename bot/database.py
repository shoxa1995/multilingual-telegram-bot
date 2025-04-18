"""
Database setup and models for the Telegram bot.
"""
import datetime
import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from sqlalchemy.sql import func

from bot.config import DB_URL

Base = declarative_base()

class User(Base):
    """User model to store Telegram user information"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    username = Column(String(100))
    language = Column(String(5), default='en')
    phone_number = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    bookings = relationship("Booking", back_populates="user")
    
    def __repr__(self):
        return f"User(telegram_id={self.telegram_id}, language={self.language})"

class Staff(Base):
    """Staff model to store information about staff members"""
    __tablename__ = 'staff'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    bitrix_user_id = Column(String(50))
    description_en = Column(Text)
    description_ru = Column(Text)
    description_uz = Column(Text)
    photo_url = Column(String(255))
    price = Column(Integer, default=0)  # Price in smallest currency unit
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    schedules = relationship("StaffSchedule", back_populates="staff")
    bookings = relationship("Booking", back_populates="staff")
    
    def __repr__(self):
        return f"Staff(id={self.id}, name={self.name})"

class StaffSchedule(Base):
    """StaffSchedule model to store staff working hours"""
    __tablename__ = 'staff_schedules'
    
    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey('staff.id'), nullable=False)
    weekday = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(5), nullable=False)  # "09:00"
    end_time = Column(String(5), nullable=False)  # "17:00"
    
    # Relationships
    staff = relationship("Staff", back_populates="schedules")
    
    def __repr__(self):
        return f"StaffSchedule(staff_id={self.staff_id}, weekday={self.weekday})"

class BookingStatus(enum.Enum):
    """Enum for booking status"""
    PENDING = "pending"
    PAYMENT_PENDING = "payment_pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class Booking(Base):
    """Booking model to store appointment bookings"""
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    staff_id = Column(Integer, ForeignKey('staff.id'), nullable=False)
    booking_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    price = Column(Integer, default=0)
    payment_id = Column(String(100))
    zoom_meeting_id = Column(String(100))
    zoom_join_url = Column(String(255))
    bitrix_event_id = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    staff = relationship("Staff", back_populates="bookings")
    
    def __repr__(self):
        return f"Booking(id={self.id}, user_id={self.user_id}, date={self.booking_date})"

# Create engine and session factory
engine = create_engine(DB_URL)
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

async def init_db():
    """Initialize the database, creating tables if they don't exist"""
    Base.metadata.create_all(engine)
    return engine
