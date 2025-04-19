"""
Admin filter for the Telegram bot.
"""
from aiogram.dispatcher.filters import BoundFilter
from aiogram.types import Message

from bot.config import ADMIN_IDS


class AdminFilter(BoundFilter):
    """
    Filter that checks if the user is an admin.
    """
    key = 'is_admin'
    
    def __init__(self, is_admin: bool = None):
        self.is_admin = is_admin
    
    async def check(self, message: Message) -> bool:
        if self.is_admin is None:
            return False
        
        return (message.from_user.id in ADMIN_IDS) == self.is_admin