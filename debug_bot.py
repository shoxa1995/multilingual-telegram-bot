#!/usr/bin/env python
"""
Debug script for Telegram bot connection.
"""
import asyncio
import logging
import sys
import traceback
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.exceptions import TelegramAPIError

# Configure very detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def cmd_start(message: types.Message):
    """Simple start command handler"""
    logger.info(f"Received /start command from user {message.from_user.id}")
    await message.answer('Debug bot is working! Reply received.')

async def main():
    """Main function with extensive error handling"""
    # The token you provided
    token = '8126004060:AAH5J83MA5-YTe2JmtvcdAnZSrPeUi_apmY'
    
    try:
        logger.info("Initializing bot with token")
        bot = Bot(token=token)
        dp = Dispatcher()
        
        # Register the command handler
        dp.message.register(cmd_start, Command('start'))
        
        # Test connection to Telegram
        logger.info("Testing connection to Telegram API...")
        try:
            me = await bot.get_me()
            logger.info(f"Bot connected successfully: @{me.username} (ID: {me.id})")
        except TelegramAPIError as api_error:
            logger.error(f"Telegram API Error: {api_error}")
            return
        except Exception as conn_error:
            logger.error(f"Connection error: {conn_error}")
            traceback.print_exc()
            return
            
        # Start polling with careful error handling
        try:
            logger.info("Starting polling...")
            await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
        except KeyboardInterrupt:
            logger.info("Polling stopped by user")
        except Exception as polling_error:
            logger.error(f"Polling error: {polling_error}")
            traceback.print_exc()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    logger.info("Starting debug bot script")
    try:
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        traceback.print_exc()