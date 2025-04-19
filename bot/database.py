"""
Database setup and models for the Telegram bot.
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text, ForeignKey, func, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
# For the migration to aiogram 3.x, we'll use synchronous SQLAlchemy
from sqlalchemy import create_engine  
from sqlalchemy.orm import Session
USING_ASYNC = False  # Force synchronous mode due to issues with asyncpg and sslmode

from bot.config import DB_URL

# Base class for SQLAlchemy models
Base = declarative_base()

# Set up global variables for session management
engine = None
async_session = None
sync_session_factory = None

# In aiogram 3.x migration, we'll use synchronous approach for simplicity
# Using async with psycopg2 is causing issues, so we'll use the synchronous approach
# until the migration is complete
try:
    # Use synchronous engine
    engine = create_engine(DB_URL, echo=True)
    sync_session_factory = sessionmaker(engine, expire_on_commit=False)
    USING_ASYNC = False
except Exception as e:
    print(f"Database initialization error: {e}")
    # Set up dummy session factory for code that depends on it
    sync_session_factory = None
    USING_ASYNC = False

# Create session functions that can be imported and used directly
def sync_session():
    """Create a new synchronous SQLAlchemy session"""
    if sync_session_factory is None:
        raise RuntimeError("Sync session factory not initialized")
    return sync_session_factory()


class TelegramUser(Base):
    """User model to store Telegram user information"""
    __tablename__ = 'telegram_users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    username = Column(String(100))
    language = Column(String(5), default='en')
    phone_number = Column(String(20))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    bookings = relationship("Booking", back_populates="user")

    def __repr__(self):
        return f"<TelegramUser(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


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

    schedules = relationship("StaffSchedule", back_populates="staff")
    bookings = relationship("Booking", back_populates="staff")

    def __repr__(self):
        return f"<Staff(id={self.id}, name={self.name})>"


class StaffSchedule(Base):
    """StaffSchedule model to store staff working hours"""
    __tablename__ = 'staff_schedules'

    id = Column(Integer, primary_key=True)
    staff_id = Column(Integer, ForeignKey('staff.id'), nullable=False)
    weekday = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = Column(String(5), nullable=False)  # "09:00"
    end_time = Column(String(5), nullable=False)  # "17:00"
    is_working_day = Column(Boolean, default=True)

    staff = relationship("Staff", back_populates="schedules")

    def __repr__(self):
        return f"<StaffSchedule(staff_id={self.staff_id}, weekday={self.weekday}, {self.start_time}-{self.end_time})>"


class BookingStatus(str, enum.Enum):
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
    user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)
    staff_id = Column(Integer, ForeignKey('staff.id'), nullable=False)
    booking_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING)
    price = Column(Integer, default=0)
    payment_id = Column(String(100))
    zoom_meeting_id = Column(String(100))
    zoom_join_url = Column(String(255))
    bitrix_event_id = Column(String(100))
    invoice_payload = Column(String(255))  # Telegram payment invoice payload
    invoice_url = Column(String(512))  # Telegram payment invoice URL for web browser payments
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("TelegramUser", back_populates="bookings")
    staff = relationship("Staff", back_populates="bookings")

    def __repr__(self):
        return f"<Booking(id={self.id}, user_id={self.user_id}, staff_id={self.staff_id}, date={self.booking_date})>"


async def init_db():
    """Initialize the database, creating tables if they don't exist"""
    try:
        # In aiogram 3.x migration, we're only using synchronous approach
        Base.metadata.create_all(engine)
        return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        # At this point, we're probably running in the Flask app context with SQLAlchemy already initialized
        # Just continue without error
        return False


def get_db():
    """Get database session (synchronous version)"""
    try:
        # Only use synchronous sessions for simplicity during migration
        return sync_session()
    except Exception as e:
        print(f"Database session error: {e}")
        return None


async def get_db_async():
    """Get database session (async-compatible wrapper)"""
    try:
        # Return a synchronous session, but in an async-compatible way
        session = sync_session()
        yield session
        session.close()
    except Exception as e:
        print(f"Database session error: {e}")
        # Return None in case of error
        yield None


def get_user_language(telegram_id: int) -> str:
    """Get user language from the database (synchronous version)"""
    with sync_session() as session:
        query = select(TelegramUser.language).where(TelegramUser.telegram_id == telegram_id)
        result = session.execute(query)
        language = result.scalar_one_or_none()
        return language
        
# Alias for i18n compatibility
get_user_language_sync = get_user_language


def get_or_create_user(user_data):
    """Get or create a user from Telegram user data (synchronous version)"""
    with sync_session() as session:
        # Check if user exists
        query = select(TelegramUser).where(TelegramUser.telegram_id == user_data.id)
        result = session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = TelegramUser(
                telegram_id=user_data.id,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                username=user_data.username,
                language=user_data.language_code if user_data.language_code in ('en', 'ru', 'uz') else 'en'
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        
        return user


def update_user_language(telegram_id: int, language: str):
    """Update user language in the database (synchronous version)"""
    with sync_session() as session:
        query = select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        result = session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.language = language
            session.commit()
            return True
        
        return False
        
        
# Async wrappers for backward compatibility
async def get_user_language_async(telegram_id: int) -> str:
    """Async wrapper for get_user_language"""
    return get_user_language(telegram_id)
    
    
async def get_or_create_user_async(user_data):
    """Async wrapper for get_or_create_user"""
    return get_or_create_user(user_data)
    
    
async def update_user_language_async(telegram_id: int, language: str):
    """Async wrapper for update_user_language"""
    return update_user_language(telegram_id, language)


def get_active_staff():
    """Get all active staff members (synchronous version)"""
    with sync_session() as session:
        query = select(Staff).where(Staff.is_active == True)
        result = session.execute(query)
        return result.scalars().all()


def get_staff_by_id(staff_id: int):
    """Get staff by ID (synchronous version)"""
    with sync_session() as session:
        query = select(Staff).where(Staff.id == staff_id)
        result = session.execute(query)
        return result.scalar_one_or_none()


def get_staff_schedule(staff_id: int):
    """Get staff schedule (synchronous version)"""
    with sync_session() as session:
        query = select(StaffSchedule).where(StaffSchedule.staff_id == staff_id)
        result = session.execute(query)
        return result.scalars().all()
        
        
# Async wrappers for backward compatibility
async def get_active_staff_async():
    """Async wrapper for get_active_staff"""
    return get_active_staff()
    
    
async def get_staff_by_id_async(staff_id: int):
    """Async wrapper for get_staff_by_id"""
    return get_staff_by_id(staff_id)
    
    
async def get_staff_schedule_async(staff_id: int):
    """Async wrapper for get_staff_schedule"""
    return get_staff_schedule(staff_id)


def create_booking(user_id: int, staff_id: int, booking_date: datetime, duration_minutes: int = 30, price: int = 0):
    """Create a new booking (synchronous version)"""
    with sync_session() as session:
        booking = Booking(
            user_id=user_id,
            staff_id=staff_id,
            booking_date=booking_date,
            duration_minutes=duration_minutes,
            status=BookingStatus.PENDING,
            price=price
        )
        session.add(booking)
        session.commit()
        session.refresh(booking)
        return booking


def get_user_bookings(telegram_id: int):
    """Get all bookings for a user (synchronous version)"""
    with sync_session() as session:
        user_query = select(TelegramUser).where(TelegramUser.telegram_id == telegram_id)
        user_result = session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return []
        
        booking_query = (
            select(Booking)
            .where(Booking.user_id == user.id)
            .order_by(Booking.booking_date.desc())
        )
        booking_result = session.execute(booking_query)
        return booking_result.scalars().all()


def get_booking_by_id(booking_id: int):
    """Get booking by ID (synchronous version)"""
    with sync_session() as session:
        query = select(Booking).where(Booking.id == booking_id)
        result = session.execute(query)
        return result.scalar_one_or_none()
        
        
# Async wrappers for backward compatibility
async def create_booking_async(user_id: int, staff_id: int, booking_date: datetime, duration_minutes: int = 30, price: int = 0):
    """Async wrapper for create_booking"""
    return create_booking(user_id, staff_id, booking_date, duration_minutes, price)
    
    
async def get_user_bookings_async(telegram_id: int):
    """Async wrapper for get_user_bookings"""
    return get_user_bookings(telegram_id)
    
    
async def get_booking_by_id_async(booking_id: int):
    """Async wrapper for get_booking_by_id"""
    return get_booking_by_id(booking_id)


def update_booking_payment_pending(booking_id: int, invoice_payload: str):
    """Update booking to payment pending status (synchronous version)"""
    with sync_session() as session:
        query = select(Booking).where(Booking.id == booking_id)
        result = session.execute(query)
        booking = result.scalar_one_or_none()
        
        if booking:
            booking.status = BookingStatus.PAYMENT_PENDING
            booking.invoice_payload = invoice_payload
            session.commit()
            return True
        
        return False


def update_booking_payment_completed(booking_id: int, payment_id: str):
    """Update booking after successful payment (synchronous version)"""
    with sync_session() as session:
        query = select(Booking).where(Booking.id == booking_id)
        result = session.execute(query)
        booking = result.scalar_one_or_none()
        
        if booking:
            booking.status = BookingStatus.CONFIRMED
            booking.payment_id = payment_id
            session.commit()
            return True
        
        return False


def cancel_booking(booking_id: int):
    """Cancel a booking (synchronous version)"""
    with sync_session() as session:
        query = select(Booking).where(Booking.id == booking_id)
        result = session.execute(query)
        booking = result.scalar_one_or_none()
        
        if booking:
            booking.status = BookingStatus.CANCELLED
            session.commit()
            return True
        
        return False
        
        
# Async wrappers for backward compatibility
async def update_booking_payment_pending_async(booking_id: int, invoice_payload: str):
    """Async wrapper for update_booking_payment_pending"""
    return update_booking_payment_pending(booking_id, invoice_payload)
    
    
async def update_booking_payment_completed_async(booking_id: int, payment_id: str):
    """Async wrapper for update_booking_payment_completed"""
    return update_booking_payment_completed(booking_id, payment_id)
    
    
async def cancel_booking_async(booking_id: int):
    """Async wrapper for cancel_booking"""
    return cancel_booking(booking_id)
    
    
def update_booking_status(booking_id: int, status: BookingStatus):
    """Update booking status to any valid status (synchronous version)"""
    with sync_session() as session:
        query = select(Booking).where(Booking.id == booking_id)
        result = session.execute(query)
        booking = result.scalar_one_or_none()
        
        if booking:
            booking.status = status
            session.commit()
            return True
        
        return False


async def update_booking_status_async(booking_id: int, status: BookingStatus):
    """Async wrapper for update_booking_status"""
    return update_booking_status(booking_id, status)