"""
Database models for the Admin Panel.
"""
from sqlalchemy import Boolean, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from admin.database import Base
from bot.database import TelegramUser, Staff, Booking, StaffSchedule, BookingStatus

class AdminUser(Base):
    """
    Admin user model for authentication.
    """
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    last_login = Column(DateTime, nullable=True)

# We'll reuse the models from the bot's database
# Importing them here for reference
