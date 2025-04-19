#!/usr/bin/env python
"""
Persistent Telegram bot runner with complete error handling.
"""
import asyncio
import logging
import os
import sys
import signal
import traceback
import time
from datetime import datetime

# Configure detailed logging
log_file = "persistent_bot.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Flag to control the bot's running state
running = True

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    global running
    logger.info(f"Received signal {sig}, shutting down...")
    running = False

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def run_bot():
    """Run the actual bot with error handling"""
    try:
        # Import the bot starting function
        from bot.main import start_bot
        
        # Start the bot
        logger.info("Starting the Telegram bot...")
        await start_bot()
    except Exception as e:
        logger.error(f"Error in bot execution: {e}")
        traceback.print_exc()
        return False
    return True

async def main_loop():
    """Main loop with restart capability"""
    global running
    max_restart_count = 5
    restart_count = 0
    
    while running and restart_count < max_restart_count:
        start_time = datetime.now()
        logger.info(f"Starting bot attempt {restart_count + 1}/{max_restart_count}")
        
        success = await run_bot()
        
        if not running:
            logger.info("Shutdown requested, exiting cleanly")
            break
            
        # If the bot crashed within 10 seconds of starting, count it as a rapid failure
        run_time = (datetime.now() - start_time).total_seconds()
        if run_time < 10:
            restart_count += 1
            logger.warning(f"Bot crashed after only {run_time:.2f} seconds. Attempt {restart_count}/{max_restart_count}")
            await asyncio.sleep(5)  # Short delay before retry
        else:
            # If it ran for a good amount of time, reset the counter
            restart_count = 0
            logger.info(f"Bot stopped after running for {run_time:.2f} seconds. Restarting...")
            await asyncio.sleep(1)
    
    if restart_count >= max_restart_count:
        logger.error("Maximum restart attempts reached. Giving up.")
    
    logger.info("Bot service exiting")

if __name__ == "__main__":
    # Record start time in PID file
    with open("bot.pid", "w") as f:
        f.write(f"{os.getpid()}\n")
        f.write(f"Started at {datetime.now().isoformat()}\n")
    
    logger.info(f"Bot runner starting with PID {os.getpid()}")
    
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, exiting")
    except Exception as e:
        logger.critical(f"Critical error in main runner: {e}")
        traceback.print_exc()
