"""
Main entry point for the Telegram bot.
Initializes and starts the bot with all required handlers and middlewares.
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.types import BotCommand, ParseMode

from bot.config import BOT_TOKEN, REDIS_HOST, REDIS_PORT, REDIS_DB
from bot.database import init_db
from bot.middlewares.i18n import i18n, setup_middleware
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
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    
    # Use Redis for state storage
    storage = RedisStorage2(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    dp = Dispatcher(bot, storage=storage)
    
    # Set up middlewares
    setup_middleware(dp)
    
    # Register filters
    dp.filters_factory.bind(AdminFilter)
    
    # Initialize database
    await init_db()
    
    # Register handlers
    register_user_handlers(dp)
    
    # Set bot commands
    await set_commands(bot)
    
    # Start polling
    logger.info("Starting bot polling...")
    try:
        await dp.start_polling()
    finally:
        await bot.session.close()
        await dp.storage.close()
        await dp.storage.wait_closed()

if __name__ == "__main__":
    asyncio.run(start_bot())
