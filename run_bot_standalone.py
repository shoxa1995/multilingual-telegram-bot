#!/usr/bin/env python3
"""
Standalone Telegram bot runner that handles specific Replit environment issues.
"""
import asyncio
import logging
import os
import signal
import sys
import time
from contextlib import suppress

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("standalone_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("standalone_bot")

# Signal handling
should_exit = False

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    global should_exit
    logger.info(f"Received signal {sig}, stopping bot...")
    should_exit = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def setup_and_run_bot():
    """Set up and run the bot manually"""
    try:
        # Import required components
        from aiogram import Bot, Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        from aiogram.enums import ParseMode
        from aiogram.client.default import DefaultBotProperties

        # Import bot token from config
        from bot.config import BOT_TOKEN
        
        # Import database initialization
        from bot.database import init_db
        
        # Import necessary components for handlers
        from bot.handlers import get_all_routers
        
        # Initialize the bot with HTML parsing
        logger.info("Initializing bot...")
        default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
        bot = Bot(token=BOT_TOKEN, default=default_bot_properties)
        
        # Test the connection
        me = await bot.get_me()
        logger.info(f"Successfully connected to Telegram as {me.username} (ID: {me.id})")
        
        # Initialize database
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized")
        
        # Set up the dispatcher with memory storage
        logger.info("Setting up dispatcher...")
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Register all handlers
        logger.info("Registering handlers...")
        dp.include_router(get_all_routers())
        
        # Set up bot commands
        from aiogram.types import BotCommand
        commands = [
            BotCommand(command="start", description="Start the bot"),
            BotCommand(command="help", description="Show help information"),
            BotCommand(command="book", description="Book an appointment"),
            BotCommand(command="mybookings", description="View your bookings"),
            BotCommand(command="language", description="Change language")
        ]
        await bot.set_my_commands(commands)
        
        # Start polling
        logger.info("Starting bot polling...")
        try:
            await dp.start_polling(
                bot,
                allowed_updates=["message", "callback_query", "pre_checkout_query"],
                close_bot_session=True
            )
        finally:
            logger.info("Closing bot session...")
            await bot.session.close()
            
        return True
    except Exception as e:
        logger.error(f"Error in setup_and_run_bot: {e}", exc_info=True)
        return False

async def main():
    """Main function with retry logic"""
    max_retries = 3
    retry_count = 0
    
    while not should_exit and retry_count < max_retries:
        try:
            logger.info(f"Starting bot (attempt {retry_count + 1}/{max_retries})...")
            success = await setup_and_run_bot()
            
            if success or should_exit:
                logger.info("Bot exited normally")
                break
                
            # If we get here, something went wrong but didn't throw an exception
            retry_count += 1
            wait_time = min(30, 2 ** retry_count)  # Exponential backoff, max 30 seconds
            logger.info(f"Bot exited unexpectedly. Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            logger.error(f"Unhandled exception in main loop: {e}", exc_info=True)
            retry_count += 1
            wait_time = min(30, 2 ** retry_count)
            logger.info(f"Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
    
    logger.info("Bot service terminated")

if __name__ == "__main__":
    logger.info("Starting standalone bot runner")
    
    try:
        with suppress(KeyboardInterrupt):
            asyncio.run(main())
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)