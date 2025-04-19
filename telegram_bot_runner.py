#!/usr/bin/env python3
"""
Robust Telegram bot runner for Replit environment.
This script starts the Telegram bot and handles graceful restarts/shutdowns.
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
        logging.FileHandler("telegram_bot_workflow.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("telegram_bot_workflow")

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

async def run_bot_polling():
    """Run the bot polling directly"""
    try:
        # Import the bot and dispatcher
        from bot.main import bot, dp, start_bot
        
        # Write a PID file for monitoring
        with open("telegram_bot.pid", "w") as pid_file:
            pid_file.write(str(os.getpid()))
        
        logger.info(f"Bot PID: {os.getpid()} - starting bot polling...")
        
        # Start the bot
        await start_bot()
        
        return 0
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
        return 1

async def main():
    """Main entry point with restart capability"""
    max_retries = 5
    retry_count = 0
    
    logger.info("Starting Telegram bot workflow")
    
    while retry_count < max_retries and not should_exit:
        try:
            logger.info(f"Starting bot attempt {retry_count + 1}/{max_retries}")
            
            exit_code = await run_bot_polling()
            
            if exit_code == 0 or should_exit:
                logger.info("Bot exited cleanly")
                break
            
            retry_count += 1
            wait_time = min(30, 2 ** retry_count)  # Exponential backoff
            logger.info(f"Bot exited with error. Waiting {wait_time}s before restarting...")
            await asyncio.sleep(wait_time)
            
        except Exception as e:
            logger.error(f"Unhandled exception in bot runner: {e}", exc_info=True)
            retry_count += 1
            wait_time = min(30, 2 ** retry_count)
            logger.info(f"Restarting in {wait_time}s...")
            await asyncio.sleep(wait_time)
    
    logger.info("Bot workflow has terminated")

if __name__ == "__main__":
    logger.info("Telegram bot workflow script starting...")
    
    try:
        with suppress(KeyboardInterrupt):
            asyncio.run(main())
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)