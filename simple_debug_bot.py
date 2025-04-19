#!/usr/bin/env python
"""
Simple debug bot with comprehensive error reporting.
"""
import asyncio
import logging
import sys
import traceback
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.exceptions import TelegramAPIError

# Set up very detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simple_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Get specific loggers
logging.getLogger('aiogram').setLevel(logging.DEBUG)
logging.getLogger('asyncio').setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)

# Bot token from environment or direct assignment
BOT_TOKEN = '8126004060:AAH5J83MA5-YTe2JmtvcdAnZSrPeUi_apmY'

async def cmd_start(message: types.Message):
    """Handler for the /start command"""
    user = message.from_user
    logger.info(f"Received /start command from user {user.id} (@{user.username})")
    await message.answer(f"Hello, {user.first_name}! I'm a test bot.")

async def main():
    """Main bot function with extensive error handling"""
    try:
        # Log environment info
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Running in directory: {os.getcwd()}")
        
        # Initialize bot with error tracking
        logger.info("Creating bot instance")
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        
        # Register command handlers
        logger.info("Registering command handlers")
        dp.message.register(cmd_start, Command('start'))
        
        # Test connection to Telegram API
        logger.info("Testing Telegram API connection")
        try:
            me = await bot.get_me()
            logger.info(f"Successfully connected as @{me.username} (ID: {me.id}, Name: {me.first_name})")
        except TelegramAPIError as api_error:
            logger.error(f"Telegram API Error: {api_error}")
            raise
        
        # Start polling with extensive error handling
        logger.info("Starting bot polling")
        try:
            await dp.start_polling(bot, allowed_updates=['message', 'callback_query'])
        except Exception as polling_error:
            logger.error(f"Error during polling: {polling_error}")
            logger.debug("Exception details:", exc_info=True)
            raise
    except Exception as e:
        logger.critical(f"Fatal error in main function: {e}")
        logger.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    logger.info("=== STARTING SIMPLE DEBUG BOT ===")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped manually")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        logger.debug(traceback.format_exc())
