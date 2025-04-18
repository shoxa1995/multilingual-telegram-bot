"""
Internationalization middleware for the Telegram bot.
Handles language selection and translation of bot messages.
"""
from pathlib import Path
from typing import Tuple, Any

from aiogram import Dispatcher, types
from aiogram.contrib.middlewares.i18n import I18nMiddleware

from bot.config import I18N_DOMAIN, LOCALES_DIR, DEFAULT_LANGUAGE
from bot.database import Session, User

class CustomI18nMiddleware(I18nMiddleware):
    """
    Custom I18n middleware to use user's language from the database.
    """
    async def get_user_locale(self, action: str, args: Tuple[Any]) -> str:
        """
        Get user's locale from database.
        If user not found, use default language.
        """
        user = types.User.get_current()
        if user is None:
            return DEFAULT_LANGUAGE
            
        # Get user from database
        session = Session()
        try:
            db_user = session.query(User).filter(User.telegram_id == user.id).first()
            if db_user and db_user.language:
                return db_user.language
        finally:
            session.close()
            
        # If no language is set, use default language
        return DEFAULT_LANGUAGE

# Create I18n middleware instance
i18n = CustomI18nMiddleware(I18N_DOMAIN, LOCALES_DIR)

# Alias for gettext method
_ = i18n.gettext

def setup_middleware(dp: Dispatcher):
    """
    Setup the I18n middleware for the dispatcher
    """
    # Setup middleware
    dp.middleware.setup(i18n)
    
    return i18n
