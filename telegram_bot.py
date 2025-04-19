#!/usr/bin/env python3
"""
Standalone Telegram bot runner that is workflow-compatible.
This script initializes and runs the bot independently.
"""
import asyncio
import logging
import os
import signal
import sys
import time
from contextlib import suppress

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("telegram_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("telegram_bot")

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

async def run_bot():
    """Run the Telegram bot with proper error handling"""
    try:
        from bot.main import bot, dp
        from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
        
        # Setup the dispatcher with the bot commands
        from bot.handlers import get_all_routers
        dp.include_router(get_all_routers())
        
        # Set up command list
        from aiogram.types import BotCommand
        from aiogram.enums import BotCommandScopeType
        
        # Define commands
        commands = [
            BotCommand(command="start", description="Start the bot"),
            BotCommand(command="help", description="Show help information"),
            BotCommand(command="book", description="Book an appointment"),
            BotCommand(command="mybookings", description="View your bookings"),
            BotCommand(command="language", description="Change language")
        ]
        
        # Set commands
        await bot.set_my_commands(commands=commands)
        
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot, allowed_updates=["message", "callback_query", "pre_checkout_query"])
        
    except Exception as e:
        logger.error(f"Error in run_bot: {e}", exc_info=True)
        return 1
    
    return 0

async def main():
    """Main entry point with retry logic"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries and not should_exit:
        try:
            logger.info(f"Starting Telegram bot (attempt {retry_count+1}/{max_retries})...")
            exit_code = await run_bot()
            
            # If clean exit or asked to exit, break out
            if exit_code == 0 or should_exit:
                logger.info("Bot exited normally.")
                break
                
            # Otherwise, retry with backoff
            retry_count += 1
            wait_time = min(30, 2 ** retry_count)  # Exponential backoff, max 30 seconds
            logger.info(f"Bot exited with error. Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            logger.error(f"Unhandled exception in main loop: {e}", exc_info=True)
            retry_count += 1
            wait_time = min(30, 2 ** retry_count)
            logger.info(f"Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
    
    logger.info("Telegram bot service stopped.")
    
if __name__ == "__main__":
    try:
        with suppress(KeyboardInterrupt):
            asyncio.run(main())
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)