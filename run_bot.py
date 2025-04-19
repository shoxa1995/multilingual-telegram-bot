#!/usr/bin/env python
"""
Standalone runner for the Telegram bot.
This script can be run separately from the Flask application
to start the bot's polling mechanism without threading issues.
"""
import asyncio
import logging
import os
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for the bot runner"""
    try:
        from bot.main import start_bot
        await start_bot()
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return 1
    return 0

if __name__ == "__main__":
    # Check if BOT_TOKEN is set
    if not os.environ.get("BOT_TOKEN"):
        logger.error("BOT_TOKEN environment variable not set. Telegram bot will not start.")
        sys.exit(1)
        
    logger.info("Starting Telegram bot with aiogram 3.x")
    
    try:
        # Run the bot
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)