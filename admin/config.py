"""
Configuration settings for the Admin Panel.
Loads environment variables and defines constants.
"""
import os
from pathlib import Path

# Admin panel configuration
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")  # Default for development

# JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-for-jwt")  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database configuration
DB_URL = os.getenv("DATABASE_URL", "sqlite:///booking.db")

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Pagination
ITEMS_PER_PAGE = 10

# Default working hours
DEFAULT_WORKING_HOURS = {
    0: ("09:00", "17:00"),  # Monday
    1: ("09:00", "17:00"),  # Tuesday
    2: ("09:00", "17:00"),  # Wednesday
    3: ("09:00", "17:00"),  # Thursday
    4: ("09:00", "17:00"),  # Friday
    5: None,               # Saturday - Off
    6: None                # Sunday - Off
}
