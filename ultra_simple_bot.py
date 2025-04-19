#!/usr/bin/env python3
"""
Ultra simple bot implementation to ensure basic functionality works.
This script should work regardless of the project structure.
"""
import asyncio
import logging
import os
import signal
import sys

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ultra_simple.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ultra_simple_bot")

# Hardcoded bot token for testing (replace with your actual token)
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Signal handling
shutdown_requested = False

def signal_handler(sig, frame):
    global shutdown_requested
    logger.info(f"Received signal {sig}, shutting down...")
    shutdown_requested = True

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def main():
    try:
        # Import required aiogram components
        from aiogram import Bot, Dispatcher, types
        from aiogram.filters import Command
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        
        # If no token is available, exit
        if not BOT_TOKEN:
            logger.error("No BOT_TOKEN provided")
            return
        
        # Initialize bot with proper settings
        logger.info("Initializing bot...")
        default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
        bot = Bot(token=BOT_TOKEN, default=default_bot_properties)
        
        # Initialize dispatcher
        dp = Dispatcher()
        
        # Define handlers
        @dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            logger.info(f"Received /start from {message.from_user.id}")
            await message.answer(
                "👋 <b>Welcome!</b>\n\n"
                "This is a ultra-simplified bot for testing.\n"
                "Use /help to see available commands."
            )
        
        @dp.message(Command("help"))
        async def cmd_help(message: types.Message):
            logger.info(f"Received /help from {message.from_user.id}")
            await message.answer(
                "📋 <b>Available commands:</b>\n\n"
                "/start - Start the bot\n"
                "/help - Show this help message\n"
                "/test - Test if the bot is working"
            )
        
        @dp.message(Command("test"))
        async def cmd_test(message: types.Message):
            logger.info(f"Received /test from {message.from_user.id}")
            await message.answer("✅ Bot is working!")
        
        # Default message handler
        @dp.message()
        async def echo(message: types.Message):
            logger.info(f"Received message: {message.text} from {message.from_user.id}")
            await message.answer(f"You said: {message.text}")
        
        # Get bot info
        me = await bot.get_me()
        logger.info(f"Bot connected: @{me.username} (ID: {me.id})")
        
        # Start polling with shutdown handling
        polling_task = asyncio.create_task(dp.start_polling(bot))
        
        # Keep the bot running until shutdown is requested
        while not shutdown_requested:
            await asyncio.sleep(1)
            
        # Cancel polling task
        polling_task.cancel()
        
        # Close bot session
        await bot.session.close()
        logger.info("Bot shutdown complete")
        
    except Exception as e:
        logger.error(f"Error in main function: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        # Write PID to file for management
        with open("ultra_simple_bot.pid", "w") as f:
            f.write(str(os.getpid()))
            
        logger.info(f"Starting ultra simple bot (PID: {os.getpid()})...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)