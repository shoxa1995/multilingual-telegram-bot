#!/usr/bin/env python3
"""
Ultra simple bot implementation to ensure basic functionality works.
This script should work regardless of the project structure.
"""
import asyncio
import logging
import os
import sys

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ultra_simple.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ultra_simple")

# Get the bot token from environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set")
    sys.exit(1)

async def main():
    try:
        # Import aiogram components
        from aiogram import Bot, Dispatcher, types
        from aiogram.filters import Command
        from aiogram.enums import ParseMode
        from aiogram.client.default import DefaultBotProperties
        
        # Initialize bot with proper DefaultBotProperties for 3.7.0+
        logger.info("Initializing bot...")
        default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
        bot = Bot(token=BOT_TOKEN, default=default_bot_properties)
        
        # Initialize dispatcher
        dp = Dispatcher()
        
        # Basic command handlers
        @dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            logger.info(f"Received /start from {message.from_user.id}")
            await message.answer("👋 Hello! The bot is working! Try /help for more info.")
            
        @dp.message(Command("help"))
        async def cmd_help(message: types.Message):
            logger.info(f"Received /help from {message.from_user.id}")
            await message.answer(
                "📚 <b>Bot Help</b>\n\n"
                "Available commands:\n"
                "/start - Start the bot\n"
                "/help - Show this help message\n"
                "/test - Test if the bot is responding"
            )
            
        @dp.message(Command("test"))
        async def cmd_test(message: types.Message):
            logger.info(f"Received /test from {message.from_user.id}")
            await message.answer("✅ Test command received! The bot is working.")
            
        # Text message handler
        @dp.message()
        async def echo(message: types.Message):
            logger.info(f"Received message: {message.text} from {message.from_user.id}")
            await message.answer(f"You said: {message.text}")
        
        # Get basic bot info
        me = await bot.get_me()
        logger.info(f"Successfully connected to Telegram as {me.username} (ID: {me.id})")
        
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in main function: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        # Run the bot
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)