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

    bookings = relationship("Booking", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"


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
    invoice_payload = Column(String(255))  # Telegram payment invoice payload
    invoice_url = Column(String(512))  # Telegram payment invoice URL for web browser payments
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    user = relationship("User", back_populates="bookings")
    staff = relationship("Staff", back_populates="bookings")

    def __repr__(self):
        return f"<Booking(id={self.id}, user_id={self.user_id}, staff_id={self.staff_id}, date={self.booking_date})>"


async def init_db():
    """Initialize the database, creating tables if they don't exist"""
    try:
        if USING_ASYNC:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        else:
            # Synchronous fallback
            Base.metadata.create_all(engine)
    except Exception as e:
        print(f"Database initialization error: {e}")
        # At this point, we're probably running in the Flask app context with SQLAlchemy already initialized
        # Just continue without error


async def get_db():
    """Get database session"""
    try:
        if USING_ASYNC:
            async with async_session() as session:
                yield session
        else:
            # Synchronous fallback
            with sync_session() as session:
                yield session
    except Exception as e:
        print(f"Database session error: {e}")
        # Return None in case of error
        yield None


async def get_user_language(telegram_id: int) -> str:
    """Get user language from the database"""
    async with async_session() as session:
        query = select(User.language).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        language = result.scalar_one_or_none()
        return language


async def get_or_create_user(user_data):
    """Get or create a user from Telegram user data"""
    async with async_session() as session:
        # Check if user exists
        query = select(User).where(User.telegram_id == user_data.id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # Create new user
            user = User(
                telegram_id=user_data.id,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                username=user_data.username,
                language=user_data.language_code if user_data.language_code in ('en', 'ru', 'uz') else 'en'
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        
        return user


async def update_user_language(telegram_id: int, language: str):
    """Update user language in the database"""
    async with async_session() as session:
        query = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(query)
        user = result.scalar_one_or_none()
        
        if user:
            user.language = language
            await session.commit()
            return True
        
        return False


async def get_active_staff():
    """Get all active staff members"""
    async with async_session() as session:
        query = select(Staff).where(Staff.is_active == True)
        result = await session.execute(query)
        return result.scalars().all()


async def get_staff_by_id(staff_id: int):
    """Get staff by ID"""
    async with async_session() as session:
        query = select(Staff).where(Staff.id == staff_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()


async def get_staff_schedule(staff_id: int):
    """Get staff schedule"""
    async with async_session() as session:
        query = select(StaffSchedule).where(StaffSchedule.staff_id == staff_id)
        result = await session.execute(query)
        return result.scalars().all()


async def create_booking(user_id: int, staff_id: int, booking_date: datetime, duration_minutes: int = 30, price: int = 0):
    """Create a new booking"""
    async with async_session() as session:
        booking = Booking(
            user_id=user_id,
            staff_id=staff_id,
            booking_date=booking_date,
            duration_minutes=duration_minutes,
            status=BookingStatus.PENDING,
            price=price
        )
        session.add(booking)
        await session.commit()
        await session.refresh(booking)
        return booking


async def get_user_bookings(telegram_id: int):
    """Get all bookings for a user"""
    async with async_session() as session:
        user_query = select(User).where(User.telegram_id == telegram_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return []
        
        booking_query = (
            select(Booking)
            .where(Booking.user_id == user.id)
            .order_by(Booking.booking_date.desc())
        )
        booking_result = await session.execute(booking_query)
        return booking_result.scalars().all()


async def get_booking_by_id(booking_id: int):
    """Get booking by ID"""
    async with async_session() as session:
        query = select(Booking).where(Booking.id == booking_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()


async def update_booking_payment_pending(booking_id: int, invoice_payload: str):
    """Update booking to payment pending status"""
    async with async_session() as session:
        query = select(Booking).where(Booking.id == booking_id)
        result = await session.execute(query)
        booking = result.scalar_one_or_none()
        
        if booking:
            booking.status = BookingStatus.PAYMENT_PENDING
            booking.invoice_payload = invoice_payload
            await session.commit()
            return True
        
        return False


async def update_booking_payment_completed(booking_id: int, payment_id: str):
    """Update booking after successful payment"""
    async with async_session() as session:
        query = select(Booking).where(Booking.id == booking_id)
        result = await session.execute(query)
        booking = result.scalar_one_or_none()
        
        if booking:
            booking.status = BookingStatus.CONFIRMED
            booking.payment_id = payment_id
            await session.commit()
            return True
        
        return False


async def cancel_booking(booking_id: int):
    """Cancel a booking"""
    async with async_session() as session:
        query = select(Booking).where(Booking.id == booking_id)
        result = await session.execute(query)
        booking = result.scalar_one_or_none()
        
        if booking:
            booking.status = BookingStatus.CANCELLED
            await session.commit()
            return True
        
        return False