"""
User handlers package for handling user messages.
"""
from aiogram import Router

from bot.handlers.users.start import register_start_handlers
from bot.handlers.users.booking import register_booking_handlers
from bot.handlers.users.payment import register_payment_handlers
# Still need to migrate to aiogram 3.x
# from bot.handlers.users.my_bookings import register_my_bookings_handlers

def register_user_handlers(router: Router):
    """
    Register all user-related handlers.
    """
    # Register start handlers (migrated to aiogram 3.x)
    register_start_handlers(router)
    
    # Register booking handlers (migrated to aiogram 3.x)
    register_booking_handlers(router)
    
    # Register payment handlers (migrated to aiogram 3.x)
    register_payment_handlers(router)
    
    # Still need to migrate to aiogram 3.x
    # register_my_bookings_handlers(router)
