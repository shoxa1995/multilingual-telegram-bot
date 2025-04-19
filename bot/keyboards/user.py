"""
Keyboard utilities for the user interface.
"""
from datetime import date, datetime
from typing import List, Dict, Any

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
)

from bot.middlewares.i18n import _
from bot.config import LANGUAGES
from bot.handlers.users import (
    staff_callback, date_callback, time_callback, booking_callback, language_callback
)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """
    Create a keyboard with language options.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for lang_code, lang_name in LANGUAGES.items():
        keyboard.add(
            InlineKeyboardButton(
                lang_name,
                callback_data=language_callback.new(code=lang_code)
            )
        )
    
    return keyboard


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Create the main menu keyboard.
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    keyboard.add(
        KeyboardButton(_("📅 Book Appointment")),
        KeyboardButton(_("👁️ My Bookings")),
    )
    keyboard.add(
        KeyboardButton(_("🌐 Change Language")),
        KeyboardButton(_("❓ Help")),
    )
    
    return keyboard


def get_staff_selection_keyboard(staff_list: List[Any]) -> InlineKeyboardMarkup:
    """
    Create a keyboard with staff members.
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    for staff in staff_list:
        keyboard.add(
            InlineKeyboardButton(
                staff.name,
                callback_data=staff_callback.new(id=staff.id)
            )
        )
    
    return keyboard


def get_date_selection_keyboard(dates: List[date]) -> InlineKeyboardMarkup:
    """
    Create a keyboard with available dates.
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Get day names in the current language
    days = [
        _("Monday"), _("Tuesday"), _("Wednesday"), 
        _("Thursday"), _("Friday"), _("Saturday"), _("Sunday")
    ]
    
    for d in dates:
        date_str = d.strftime("%Y-%m-%d")
        day_name = days[d.weekday()]
        
        # Format: "Mon, Apr 19"
        display_text = f"{day_name[:3]}, {d.strftime('%b %d')}"
        
        keyboard.add(
            InlineKeyboardButton(
                display_text,
                callback_data=date_callback.new(value=date_str)
            )
        )
    
    return keyboard


def get_time_selection_keyboard(times: List[str]) -> InlineKeyboardMarkup:
    """
    Create a keyboard with available time slots.
    """
    keyboard = InlineKeyboardMarkup(row_width=3)
    
    buttons = []
    for time_str in times:
        buttons.append(
            InlineKeyboardButton(
                time_str,
                callback_data=time_callback.new(value=time_str)
            )
        )
    
    # Add buttons in rows of 3
    keyboard.add(*buttons)
    
    return keyboard


def get_booking_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Create a keyboard for booking confirmation.
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(
            _("✅ Confirm"),
            callback_data="confirm_booking"
        ),
        InlineKeyboardButton(
            _("❌ Cancel"),
            callback_data="cancel"
        )
    )
    
    return keyboard


def get_booking_actions_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    """
    Create a keyboard with booking actions.
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    keyboard.add(
        InlineKeyboardButton(
            _("💰 Pay"),
            callback_data=booking_callback.new(action="pay", id=booking_id)
        ),
        InlineKeyboardButton(
            _("❌ Cancel"),
            callback_data=booking_callback.new(action="cancel", id=booking_id)
        )
    )
    
    return keyboard