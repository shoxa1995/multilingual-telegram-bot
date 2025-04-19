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
import time
from contextlib import suppress

# Configure detailed logging
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

async def main():
    """Main function that starts and manages the bot"""
    # Print startup message
    print("Starting Telegram Bot Workflow...")
    logger.info("Telegram bot workflow script starting...")
    logger.info("Starting Telegram bot workflow")
    
    max_retries = 5
    retry_count = 0
    
    while not should_exit and retry_count < max_retries:
        try:
            logger.info(f"Starting bot attempt {retry_count + 1}/{max_retries}")
            
            # Import required components
            from aiogram import Bot, Dispatcher, types
            from aiogram.filters import Command
            from aiogram.client.default import DefaultBotProperties
            from aiogram.enums import ParseMode
            
            # Get token from environment
            bot_token = os.environ.get("BOT_TOKEN")
            if not bot_token:
                logger.error("BOT_TOKEN environment variable not set. Telegram bot will not start.")
                break
            
            # Initialize bot with proper settings for aiogram 3.7.0+
            default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
            bot = Bot(token=bot_token, default=default_bot_properties)
            
            # Initialize dispatcher
            dp = Dispatcher()
            
            # Basic command handlers
            @dp.message(Command("start"))
            async def cmd_start(message):
                logger.info(f"Received /start from {message.from_user.id}")
                await message.answer(
                    "👋 Welcome to the Appointment Booking Bot!\n\n"
                    "Please select your preferred language:",
                    reply_markup=types.ReplyKeyboardMarkup(
                        keyboard=[
                            [types.KeyboardButton(text="English 🇬🇧")],
                            [types.KeyboardButton(text="Русский 🇷🇺")],
                            [types.KeyboardButton(text="O'zbekcha 🇺🇿")]
                        ],
                        resize_keyboard=True,
                        one_time_keyboard=True
                    )
                )
            
            @dp.message(Command("help"))
            async def cmd_help(message):
                logger.info(f"Received /help from {message.from_user.id}")
                await message.answer(
                    "📚 <b>Bot Help</b>\n\n"
                    "Available commands:\n"
                    "/start - Start the bot\n"
                    "/help - Show this help message\n"
                    "/test - Test if the bot is responding\n"
                    "/book - Book an appointment\n"
                    "/mybookings - View your bookings\n"
                    "/language - Change language"
                )
            
            @dp.message(Command("test"))
            async def cmd_test(message):
                logger.info(f"Received /test from {message.from_user.id}")
                await message.answer("✅ Test command received! The bot is working properly.")
            
            # Text message handler for any other messages
            @dp.message()
            async def echo(message):
                logger.info(f"Received message: {message.text} from {message.from_user.id}")
                await message.answer(f"You said: {message.text}")
            
            # Get bot info and verify connection
            me = await bot.get_me()
            logger.info(f"Successfully connected to Telegram as {me.username} (ID: {me.id})")
            
            # Create a PID file for the running bot
            pid = os.getpid()
            with open("telegram_bot_workflow.pid", "w") as f:
                f.write(str(pid))
            logger.info(f"Bot PID: {pid} - starting bot polling...")
            
            # Start bot polling
            await dp.start_polling(bot)
            
            # If we get here, the bot has exited gracefully
            logger.info("Bot polling stopped gracefully")
            
            # Wait a bit before deciding if we need to restart
            if not should_exit:
                logger.info("Waiting 5 seconds before considering restart...")
                await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"Error running bot: {e}", exc_info=True)
            retry_count += 1
            
            # Wait with exponential backoff before retrying
            if not should_exit and retry_count < max_retries:
                wait_time = min(60, 2 ** retry_count)
                logger.info(f"Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
                await asyncio.sleep(wait_time)
        
    logger.info("Bot workflow terminated")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by Keyboard Interrupt")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)