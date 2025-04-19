"""
User handlers package for handling user messages.
"""
from aiogram import Router

from bot.handlers.users.start import register_start_handlers
# Commenting out handlers that need to be migrated to aiogram 3.x
# from bot.handlers.users.booking import register_booking_handlers
# from bot.handlers.users.my_bookings import register_my_bookings_handlers

def register_user_handlers(router: Router):
    """
    Register all user-related handlers.
    """
    # Register start handlers (migrated to aiogram 3.x)
    register_start_handlers(router)
    
    # These handlers need to be migrated to aiogram 3.x
    # register_booking_handlers(router)
    # register_my_bookings_handlers(router)
