"""
User handlers package for handling user messages.
"""
from aiogram import Dispatcher

from bot.handlers.users.start import register_start_handlers
from bot.handlers.users.booking import register_booking_handlers
from bot.handlers.users.my_bookings import register_my_bookings_handlers

def register_user_handlers(dp: Dispatcher):
    """
    Register all user-related handlers.
    """
    register_start_handlers(dp)
    register_booking_handlers(dp)
    register_my_bookings_handlers(dp)
