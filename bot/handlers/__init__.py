"""
Bot handlers package for handling incoming messages and callbacks.
"""
from aiogram import Router

from bot.handlers.users import register_user_handlers

def get_all_routers() -> Router:
    """
    Get main router with all sub-routers included.
    This is the aiogram 3.x approach to handler registration.
    """
    main_router = Router()
    
    # Include user handlers
    user_router = Router()
    register_user_handlers(user_router)
    main_router.include_router(user_router)
    
    return main_router
