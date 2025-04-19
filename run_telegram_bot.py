#!/usr/bin/env python3
"""
Standalone Telegram bot runner script that can be used with Replit workflows.
This script will initialize and start the bot in long-polling mode.
"""
import asyncio
import logging
import os
import signal
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
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
    """Run the Telegram bot with error handling"""
    try:
        # Import the bot module
        from bot.main import start_bot
        
        # Start the bot
        await start_bot()
        return 0
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        return 1

if __name__ == "__main__":
    logger.info("Starting Telegram bot runner...")
    
    # Run the bot
    try:
        exit_code = asyncio.run(run_bot())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)
