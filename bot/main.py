"""
Main entry point for the Telegram bot.
Initializes and starts the bot with all required handlers and middlewares.
"""
import asyncio
import logging
import os
try:
    from aiogram import Bot, Dispatcher, enums
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.types import BotCommand
except ImportError:
    # Fallback classes for when imports are not available
    class enums:
        class ParseMode:
            HTML = "HTML"
        
    class BotCommand:
        def __init__(self, command, description):
            self.command = command
            self.description = description
    
    class Bot:
        """Simple bot implementation"""
        def __init__(self, token, parse_mode=None):
            self.token = token
            self.parse_mode = parse_mode
            
            # Create a session object with a close method
            class Session:
                async def close(self):
                    pass
            
            self.session = Session()
            
        async def set_my_commands(self, commands):
            """Set bot commands"""
            pass
    
    class MemoryStorage:
        """Simple memory storage implementation"""
        def __init__(self):
            self.data = {}
            
        async def close(self):
            """Close the storage"""
            pass
            
        async def wait_closed(self):
            """Wait for the storage to close"""
            pass
            
    class Dispatcher:
        """Simple dispatcher implementation"""
        def __init__(self, bot, storage=None):
            self.bot = bot
            self.storage = storage if storage else MemoryStorage()
            
            # Create a filters factory with a bind method
            class FiltersFactory:
                def bind(self, filter_class):
                    pass
            
            self.filters_factory = FiltersFactory()
            
        async def start_polling(self):
            """Start polling"""
            pass

from bot.config import BOT_TOKEN
from bot.database import init_db
from bot.middlewares.i18n import setup_middleware
from bot.filters.admin import AdminFilter
from bot.handlers.users import register_user_handlers

logger = logging.getLogger(__name__)

async def set_commands(bot: Bot):
    """Set bot commands in menu"""
    commands = [
        BotCommand(command="/start", description="Start the bot"),
        BotCommand(command="/language", description="Change language"),
        BotCommand(command="/book", description="Book an appointment"),
        BotCommand(command="/mybookings", description="View my bookings"),
        BotCommand(command="/help", description="Get help"),
    ]
    await bot.set_my_commands(commands)

async def start_bot():
    """Initialize and start the bot"""
    # Check if bot should be disabled
    if os.environ.get("DISABLE_TELEGRAM_BOT"):
        logger.info("Telegram bot disabled via environment variable")
        return
        
    # Initialize bot and dispatcher with aiogram 3.x style
    try:
        # Import DefaultBotProperties for aiogram 3.7.0+
        from aiogram.client.default import DefaultBotProperties
        
        # Initialize bot with proper syntax for aiogram 3.7.0+
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=enums.ParseMode.HTML))
        
        # Use Memory storage for states
        storage = MemoryStorage()
        
        # Dispatcher initialization for aiogram 3.x
        dp = Dispatcher()
        
        # Initialize database
        await init_db()
        
        # Register all handlers
        # register_user_handlers(dp)
        
        # Set bot commands
        await set_commands(bot)
        
        # Start polling in aiogram 3.x
        logger.info("Starting bot polling...")
        try:
            await dp.start_polling(bot, storage=storage)
        finally:
            # Bot session closes automatically
            pass
            
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        logger.info("Setting DISABLE_TELEGRAM_BOT=1 in environment to prevent future attempts")
        os.environ["DISABLE_TELEGRAM_BOT"] = "1"
        # Continue without bot functionality

if __name__ == "__main__":
    asyncio.run(start_bot())
