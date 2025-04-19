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
        # Import the start_bot function directly
        from bot.main import start_bot
        
        # Let the bot module handle all the initialization and polling
        await start_bot()
        return 0
        
    except Exception as e:
        logger.error(f"Error in run_bot: {e}", exc_info=True)
        return 1

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