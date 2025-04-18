"""
Bot handlers package for handling incoming messages and callbacks.
"""
from aiogram import Dispatcher

from bot.handlers.users import register_user_handlers

def register_all_handlers(dp: Dispatcher):
    """
    Register all handlers.
    """
    register_user_handlers(dp)
