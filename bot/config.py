"""
Configuration settings for the Telegram bot.
Loads environment variables and defines constants.
"""
import os
from pathlib import Path

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Redis configuration for FSM
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Database configuration
DB_URL = os.getenv("DATABASE_URL", "sqlite:///booking.db")

# Bitrix24 API configuration
BITRIX24_WEBHOOK_URL = os.getenv("BITRIX24_WEBHOOK_URL")

# Zoom API configuration
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
ZOOM_ACCOUNT_EMAIL = os.getenv("ZOOM_ACCOUNT_EMAIL")

# Click UZ payment provider tokens (from Telegram BotFather)
CLICK_LIVE_TOKEN = os.getenv("CLICK_LIVE_TOKEN", "333605228:LIVE:18486_1A5B4FF440980100E5F5C1D745DFCB165C5E2A37")
CLICK_TEST_TOKEN = os.getenv("CLICK_TEST_TOKEN", "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065")
# Use test token by default in development
PAYMENT_PROVIDER_TOKEN = CLICK_TEST_TOKEN

# Admin IDs (comma-separated list of Telegram user IDs)
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(","))) if os.getenv("ADMIN_IDS") else []

# Time slot configuration (in minutes)
DEFAULT_SLOT_DURATION = 30  # Default duration of a time slot

# Base directory
BASE_DIR = Path(__file__).parent.parent

# I18n configuration
I18N_DOMAIN = 'messages'
LOCALES_DIR = BASE_DIR / 'locales'

# Supported languages
LANGUAGES = {
    'en': 'English 🇬🇧',
    'ru': 'Русский 🇷🇺',
    'uz': 'O\'zbekcha 🇺🇿'
}

# Default language
DEFAULT_LANGUAGE = 'en'
