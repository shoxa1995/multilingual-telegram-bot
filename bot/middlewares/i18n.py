"""
Internationalization middleware for the Telegram bot.
"""
import gettext
import os
from typing import Any, Dict, Tuple

from aiogram import Dispatcher
from aiogram.contrib.middlewares.i18n import I18nMiddleware as BaseI18nMiddleware
from aiogram.types import Message, CallbackQuery, User

from bot.config import LOCALES_DIR, I18N_DOMAIN, DEFAULT_LANGUAGE, LANGUAGES


class I18nMiddleware(BaseI18nMiddleware):
    """
    Internationalization middleware.
    """
    async def get_user_locale(self, action: str, args: Tuple[Any]) -> str:
        """
        Get the user's locale from the database or from the message.
        """
        from bot.database import get_user_language
        
        user = None
        if isinstance(args[0], Message):
            user = args[0].from_user
        elif isinstance(args[0], CallbackQuery):
            user = args[0].from_user
        
        if user:
            # Try to get the user's language from the database
            db_language = await get_user_language(user.id)
            if db_language:
                return db_language
            
            # Fallback to the user's Telegram language
            if user.language_code in LANGUAGES:
                return user.language_code
        
        # Fallback to default language
        return DEFAULT_LANGUAGE


# Initialize i18n middleware
i18n = I18nMiddleware(I18N_DOMAIN, LOCALES_DIR)
_ = i18n.gettext


def setup_middleware(dp: Dispatcher):
    """
    Set up the i18n middleware.
    """
    dp.middleware.setup(i18n)
    
    # Ensure the locales directory exists
    os.makedirs(LOCALES_DIR, exist_ok=True)