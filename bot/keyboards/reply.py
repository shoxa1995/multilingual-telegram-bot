"""
Reply keyboard markup generator for the Telegram bot.
Adapted for aiogram 3.x using the new keyboard syntax.
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from bot.middlewares.i18n import _
from bot.config import LANGUAGES

def language_keyboard() -> ReplyKeyboardMarkup:
    """
    Create a keyboard for language selection.
    """
    buttons = []
    for lang_code, lang_name in LANGUAGES.items():
        buttons.append([KeyboardButton(text=lang_name)])
        
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def contact_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with a button to share contact.
    """
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
    
    buttons = [
        [KeyboardButton(text=texts.get(lang, texts['en']), request_contact=True)],
        [KeyboardButton(text=cancel_texts.get(lang, cancel_texts['en']))]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )

def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """
    Create the main menu keyboard.
    """
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
    
    buttons = [
        [KeyboardButton(text=book_texts.get(lang, book_texts['en']))],
        [KeyboardButton(text=my_bookings_texts.get(lang, my_bookings_texts['en']))],
        [
            KeyboardButton(text=language_texts.get(lang, language_texts['en'])),
            KeyboardButton(text=help_texts.get(lang, help_texts['en']))
        ]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

def cancel_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """
    Create a keyboard with a cancel button.
    """
    cancel_texts = {
        'en': '❌ Cancel',
        'ru': '❌ Отмена',
        'uz': '❌ Bekor qilish'
    }
    
    buttons = [
        [KeyboardButton(text=cancel_texts.get(lang, cancel_texts['en']))]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )
