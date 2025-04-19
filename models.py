import enum
from datetime import datetime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from main import db

# User model for admin panel authentication
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f'<User {self.username}>'

# Telegram user model
class TelegramUser(db.Model):
    __tablename__ = 'telegram_users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.Integer, unique=True, nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    username = db.Column(db.String(100))
    language = db.Column(db.String(5), default='en')
    phone_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    
    # Relationship
    bookings = relationship("Booking", back_populates="user")
    
    def __repr__(self):
        return f'<TelegramUser {self.first_name} {self.last_name}>'

# Staff model to store information about staff members
class Staff(db.Model):
    __tablename__ = 'staff'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bitrix_user_id = db.Column(db.String(50))
    description_en = db.Column(db.Text)
    description_ru = db.Column(db.Text)
    description_uz = db.Column(db.Text)
    photo_url = db.Column(db.String(255))
    price = db.Column(db.Integer, default=0)  # Price in smallest currency unit
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    
    # Relationships
    schedules = relationship("StaffSchedule", back_populates="staff", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="staff")
    
    def __repr__(self):
        return f'<Staff {self.name}>'

# StaffSchedule model to store staff working hours
class StaffSchedule(db.Model):
    __tablename__ = 'staff_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    weekday = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.String(5), nullable=False)  # "09:00"
    end_time = db.Column(db.String(5), nullable=False)  # "17:00"
    is_working_day = db.Column(db.Boolean, default=True)
    
    # Relationship
    staff = relationship("Staff", back_populates="schedules")
    
    def __repr__(self):
        return f'<StaffSchedule {self.staff.name if self.staff else "Unknown"} - Day {self.weekday}>'

# Enum for booking status
class BookingStatus(enum.Enum):
    PENDING = "pending"
    PAYMENT_PENDING = "payment_pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

# Booking model to store appointment bookings
class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('telegram_users.id'), nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.PENDING)
    price = db.Column(db.Integer, default=0)
    payment_id = db.Column(db.String(100))
    zoom_meeting_id = db.Column(db.String(100))
    zoom_join_url = db.Column(db.String(255))
    bitrix_event_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, onupdate=func.now())
    
    # Relationships
    user = relationship("TelegramUser", back_populates="bookings")
    staff = relationship("Staff", back_populates="bookings")
    
    def __repr__(self):
        return f'<Booking {self.id} - {self.user.first_name if self.user else "Unknown"} with {self.staff.name if self.staff else "Unknown"}>'