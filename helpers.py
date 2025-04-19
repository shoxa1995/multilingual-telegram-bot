"""
Helper functions for the bot.
"""
from bot.middlewares.i18n import _, get_user_language

async def translate_message(message_text, user=None, language=None):
    """
    Translate a message for a specific user or language.
    """
    if language is None and user is not None:
        language = await get_user_language(user)
    elif language is None:
        language = 'en'  # Default language
    
    return _(message_text, language)