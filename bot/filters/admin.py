"""
Admin filter for the Telegram bot.
Checks if the user is in the list of admin IDs.
"""
from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

from bot.config import ADMIN_IDS

class AdminFilter(BoundFilter):
    """
    Check if the user is an admin.
    """
    key = 'is_admin'
    
    def __init__(self, is_admin: bool = True):
        self.is_admin = is_admin
        
    async def check(self, obj: types.Message | types.CallbackQuery) -> bool:
        """
        Check if the user is an admin.
        """
        if isinstance(obj, types.CallbackQuery):
            user_id = obj.from_user.id
        else:
            user_id = obj.from_user.id
            
        is_admin = user_id in ADMIN_IDS
        return is_admin == self.is_admin
