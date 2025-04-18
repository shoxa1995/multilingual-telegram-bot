"""
Reply keyboard markup generator for the Telegram bot.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.middlewares.i18n import _
from bot.config import LANGUAGES

def language_keyboard() -> ReplyKeyboardMarkup:
    """
    Create a keyboard for language selection.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    
    for lang_code, lang_name in LANGUAGES.items():
        markup.add(KeyboardButton(lang_name))
        
    return markup

def contact_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with a button to share contact.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    
    texts = {
        'en': 'Share my phone number',
        'ru': 'Поделиться моим номером',
        'uz': 'Telefon raqamimni ulashish'
    }
    
    cancel_texts = {
        'en': 'Cancel',
        'ru': 'Отмена',
        'uz': 'Bekor qilish'
    }
    
    markup.add(KeyboardButton(texts.get(lang, texts['en']), request_contact=True))
    markup.add(KeyboardButton(cancel_texts.get(lang, cancel_texts['en'])))
    
    return markup

def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """
    Create the main menu keyboard.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    
    book_texts = {
        'en': '📅 Book Appointment',
        'ru': '📅 Записаться на прием',
        'uz': '📅 Qabulga yozilish'
    }
    
    my_bookings_texts = {
        'en': '📋 My Bookings',
        'ru': '📋 Мои записи',
        'uz': '📋 Mening qabullarim'
    }
    
    language_texts = {
        'en': '🌐 Change Language',
        'ru': '🌐 Изменить язык',
        'uz': '🌐 Tilni o\'zgartirish'
    }
    
    help_texts = {
        'en': '❓ Help',
        'ru': '❓ Помощь',
        'uz': '❓ Yordam'
    }
    
    # Add buttons
    markup.add(KeyboardButton(book_texts.get(lang, book_texts['en'])))
    markup.add(KeyboardButton(my_bookings_texts.get(lang, my_bookings_texts['en'])))
    markup.row(
        KeyboardButton(language_texts.get(lang, language_texts['en'])),
        KeyboardButton(help_texts.get(lang, help_texts['en']))
    )
    
    return markup

def cancel_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with a cancel button.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    
    cancel_texts = {
        'en': '❌ Cancel',
        'ru': '❌ Отмена',
        'uz': '❌ Bekor qilish'
    }
    
    markup.add(KeyboardButton(cancel_texts.get(lang, cancel_texts['en'])))
    
    return markup
