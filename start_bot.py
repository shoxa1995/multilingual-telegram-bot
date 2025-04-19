#!/usr/bin/env python
"""
Standalone runner for the Telegram bot with enhanced error handling.
This script runs the bot in polling mode so it can respond to messages.
"""
import asyncio
import logging
import os
import sys
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Handle graceful shutdown
shutdown_event = asyncio.Event()

def signal_handler(sig, frame):
    """Handle signals for graceful shutdown"""
    logger.info(f"Received signal {sig}, shutting down...")
    shutdown_event.set()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main entry point for the bot runner"""
    try:
        # Import the start_bot function
        from bot.main import start_bot
        
        # Create a task for the bot
        bot_task = asyncio.create_task(start_bot())
        
        # Wait for shutdown signal or bot completion
        await shutdown_event.wait()
        
        # Cancel the bot task when shutdown is requested
        logger.info("Shutting down bot...")
        bot_task.cancel()
        
        try:
            await bot_task
        except asyncio.CancelledError:
            logger.info("Bot task cancelled")
            
        return 0
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        return 1

if __name__ == "__main__":
    # Check if BOT_TOKEN is set
    if not os.environ.get("BOT_TOKEN"):
        logger.error("BOT_TOKEN environment variable not set. Telegram bot will not start.")
        sys.exit(1)
        
    logger.info("Starting Telegram bot polling...")
    
    try:
        # Run the bot with proper asyncio handling
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt!")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)