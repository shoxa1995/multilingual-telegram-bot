#!/usr/bin/env python3
"""
Ultra simple bot implementation with auto-restart capability.
"""
import asyncio
import logging
import os
import sys
import signal
import time
from contextlib import suppress

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("persistent_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("persistent_bot")

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

# Get the bot token from environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set")
    sys.exit(1)

async def run_bot():
    """Run the actual bot with error handling"""
    try:
        # Import aiogram components
        from aiogram import Bot, Dispatcher, types
        from aiogram.filters import Command
        from aiogram.enums import ParseMode
        from aiogram.client.default import DefaultBotProperties

        # Initialize bot with proper DefaultBotProperties for 3.7.0+
        logger.info("Initializing bot...")
        default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
        bot = Bot(token=BOT_TOKEN, default=default_bot_properties)
        
        # Initialize dispatcher
        dp = Dispatcher()
        
        # Basic command handlers
        @dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            logger.info(f"Received /start from {message.from_user.id}")
            await message.answer("👋 Hello! The bot is working! Try /help for more info.")
            
        @dp.message(Command("help"))
        async def cmd_help(message: types.Message):
            logger.info(f"Received /help from {message.from_user.id}")
            await message.answer(
                "📚 <b>Bot Help</b>\n\n"
                "Available commands:\n"
                "/start - Start the bot\n"
                "/help - Show this help message\n"
                "/test - Test if the bot is responding"
            )
            
        @dp.message(Command("test"))
        async def cmd_test(message: types.Message):
            logger.info(f"Received /test from {message.from_user.id}")
            await message.answer("✅ Test command received! The bot is working.")
            
        # Text message handler
        @dp.message()
        async def echo(message: types.Message):
            logger.info(f"Received message: {message.text} from {message.from_user.id}")
            await message.answer(f"You said: {message.text}")
        
        # Get basic bot info
        me = await bot.get_me()
        logger.info(f"Successfully connected to Telegram as {me.username} (ID: {me.id})")
        
        # Start polling with graceful shutdown capability
        logger.info("Starting bot polling...")
        try:
            # This structure ensures we can interrupt polling 
            await dp.start_polling(bot)
        except asyncio.CancelledError:
            logger.info("Polling was cancelled")
        finally:
            # Close bot session
            logger.info("Closing bot session...")
            await bot.session.close()
            
        logger.info("Bot polling stopped gracefully")
        return True
    except Exception as e:
        logger.error(f"Error in run_bot: {e}", exc_info=True)
        return False

async def main_loop():
    """Main loop with restart capability"""
    max_retry_count = 5
    retry_count = 0
    
    while not should_exit and retry_count < max_retry_count:
        # Run the bot
        success = await run_bot()
        
        if should_exit:
            break
            
        if success:
            # Bot exited normally, reset retry count
            retry_count = 0
            logger.info("Bot exited successfully, restarting...")
        else:
            # Bot exited with an error, increase retry count
            retry_count += 1
            wait_time = min(60, 2 ** retry_count)  # Exponential backoff
            logger.warning(f"Bot exited with error. Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retry_count})")
            await asyncio.sleep(wait_time)
            
    if retry_count >= max_retry_count:
        logger.error(f"Exceeded maximum retry count ({max_retry_count}). Giving up.")
        
    logger.info("Bot service terminated")

if __name__ == "__main__":
    # Write PID to file
    with open("bot_running.pid", "w") as f:
        f.write(str(os.getpid()))
    logger.info(f"Starting persistent bot (PID: {os.getpid()})")
    
    try:
        # Suppress KeyboardInterrupt to allow graceful shutdown
        with suppress(KeyboardInterrupt):
            asyncio.run(main_loop())
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
