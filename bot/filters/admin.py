"""
Admin filter for the Telegram bot.
"""
from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message


class AdminFilter(BoundFilter):
    """
    Filter that checks if the user is an admin.
    """
    key = 'is_admin'
    
    def __init__(self, is_admin: bool = None):
        self.is_admin = is_admin
    
    async def check(self, message: Message) -> bool:
        # Simplified admin filter, assumes no admins for now
        # In a real setup, we would retrieve admin IDs from the config or database
        return False