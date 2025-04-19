#!/usr/bin/env python3
"""
Workflow-compatible Telegram bot runner for Replit.
This script is a standalone service that runs the Telegram bot
in polling mode without depending on the Flask application.
"""

import asyncio
import logging
import os
import signal
import sys
from contextlib import suppress

try:
    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.filters.command import Command
except ImportError:
    print("Error: aiogram package not found. Make sure to install it with 'pip install aiogram'")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Check for bot token
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set. Please set it and try again.")
    sys.exit(1)

# Signal handling for graceful shutdown
should_exit = False

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    global should_exit
    logger.info(f"Received signal {sig}, stopping bot...")
    should_exit = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main function that starts and manages the bot"""
    try:
        # Initialize bot with DefaultBotProperties for HTML parsing
        default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
        bot = Bot(token=BOT_TOKEN, default=default_properties)
        
        # Get bot info
        me = await bot.get_me()
        logger.info(f"Starting bot @{me.username} (ID: {me.id})")
        
        # Import the main bot module only after we've confirmed we can connect
        try:
            from bot.main import start_bot
            
            # Run the bot's main start function which handles all the setup
            await start_bot()
        except Exception as e:
            logger.error(f"Error starting bot from bot.main module: {e}")
            # Start a minimal bot if the main module fails
            logger.info("Falling back to minimal bot functionality")
            
            # Create a dispatcher and register minimal handlers
            from aiogram.fsm.storage.memory import MemoryStorage
            storage = MemoryStorage()
            dp = Dispatcher(storage=storage)
            
            # Register basic command handlers
            @dp.message(Command("start"))
            async def cmd_start(message):
                await message.answer("👋 Hello! I'm running in fallback mode. Please contact the administrator.")
            
            @dp.message(Command("help"))
            async def cmd_help(message):
                await message.answer("❓ This is a fallback mode with limited functionality.")
            
            # Start polling
            await dp.start_polling(bot)
            
    except Exception as e:
        logger.error(f"Critical bot error: {e}")
        return 1
    finally:
        # Clean up resources
        with suppress(Exception):
            await bot.session.close()
        logger.info("Bot stopped")
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        sys.exit(1)