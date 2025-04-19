"""
Simple translation utility for the Telegram bot.
"""
import gettext
import os
from functools import lru_cache
from typing import Dict, Optional, Any

from bot.config import LOCALES_DIR, I18N_DOMAIN, DEFAULT_LANGUAGE, LANGUAGES

# Ensure the locales directory exists
os.makedirs(LOCALES_DIR, exist_ok=True)

# Dictionary to store gettext translations
_translations: Dict[str, gettext.GNUTranslations] = {}


class I18n:
    """
    Internationalization helper for aiogram 3.x.
    Simplified version that maintains compatibility with middlewares.
    """
    
    def __init__(self, domain: str = I18N_DOMAIN, path: str = LOCALES_DIR, default_locale: str = DEFAULT_LANGUAGE):
        self.domain = domain
        self.path = path
        self.default_locale = default_locale
        self.current_locale = default_locale
        
    async def get_locale(self, user_id: Optional[int] = None) -> str:
        """
        Get locale for user
        """
        if user_id is not None:
            # Try to get user's language from database
            from bot.database import get_user_language
            language = await get_user_language(user_id)
            if language:
                return language
        
        # Return default language
        return self.default_locale
    
    def gettext(self, text: str, locale: Optional[str] = None) -> str:
        """
        Get localized text
        """
        if locale is None:
            locale = self.current_locale
            
        translation = get_translation(locale)
        return translation.gettext(text)


# Create i18n instance for importing
i18n = I18n()


@lru_cache(maxsize=128)
def get_translation(language: str):
    """
    Get a translation for a specific language.
    """
    if language not in _translations:
        try:
            # Try to load translation for the language
            translation = gettext.translation(
                I18N_DOMAIN, 
                LOCALES_DIR, 
                languages=[language]
            )
            _translations[language] = translation
        except FileNotFoundError:
            # Fallback to default language
            try:
                translation = gettext.translation(
                    I18N_DOMAIN, 
                    LOCALES_DIR, 
                    languages=[DEFAULT_LANGUAGE]
                )
                _translations[language] = translation
            except FileNotFoundError:
                # Fallback to NullTranslation if no translations are found
                translation = gettext.NullTranslations()
                _translations[language] = translation
    
    return _translations[language]


def _(text: str, language: str = DEFAULT_LANGUAGE) -> str:
    """
    Translate text into the specified language.
    """
    translation = get_translation(language)
    return translation.gettext(text)


async def get_user_language(user):
    """
    Get the language for a user, either from the database or from the user's Telegram settings.
    """
    from bot.database import get_user_language
    
    if not user:
        return DEFAULT_LANGUAGE
    
    # Try to get the user's language from the database
    db_language = await get_user_language(user.id)
    if db_language:
        return db_language
    
    # Fallback to the user's Telegram language
    if user.language_code in LANGUAGES:
        return user.language_code
    
    # Fallback to default language
    return DEFAULT_LANGUAGE


def setup_middleware(dp):
    """
    Placeholder for middleware setup to maintain API compatibility.
    """
    # No middleware is used, but we keep this function for API compatibility
    pass