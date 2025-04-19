#!/usr/bin/env python3
"""
Working Telegram bot implementation for the booking system.
This script uses the simplified approach proven to work.
"""
import asyncio
import logging
import os
import signal
import sys
from contextlib import suppress

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot_working.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("working_bot")

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

async def main():
    """Main function to run the Telegram bot"""
    # Import required components
    from aiogram import Bot, Dispatcher, types, F
    from aiogram.filters import Command, CommandStart
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.enums import ParseMode
    from aiogram.client.default import DefaultBotProperties
    
    # Import bot token from config
    from bot.config import BOT_TOKEN, LANGUAGES
    
    # Import keyboards
    from bot.keyboards.reply import language_keyboard, main_menu_keyboard
    
    # Initialize the bot with DefaultBotProperties for aiogram 3.7.0+
    default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=BOT_TOKEN, default=default_bot_properties)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Test connection
    me = await bot.get_me()
    logger.info(f"Connected to Telegram as {me.username} (ID: {me.id})")
    
    # Simple text handler
    @dp.message(CommandStart())
    async def cmd_start(message: types.Message):
        logger.info(f"Received /start command from {message.from_user.id}")
        await message.answer(
            "👋 Welcome to the Appointment Booking Bot!\n\n"
            "Please select your language:",
            reply_markup=language_keyboard()
        )
    
    # Language selection handler
    @dp.message(lambda message: message.text in [lang for lang in LANGUAGES.values()])
    async def language_selection(message: types.Message):
        logger.info(f"Received language selection: {message.text}")
        
        # Find selected language code
        selected_lang = None
        for code, name in LANGUAGES.items():
            if name == message.text or name in message.text:  # More flexible matching
                selected_lang = code
                break
                
        if not selected_lang:
            await message.answer(
                "Please select a language from the keyboard.",
                reply_markup=language_keyboard()
            )
            return
            
        await message.answer(
            f"Language set to {message.text}.\n\n"
            "You can now use the main menu:",
            reply_markup=main_menu_keyboard(selected_lang)
        )
    
    # Help command handler
    @dp.message(Command("help"))
    async def cmd_help(message: types.Message):
        logger.info(f"Received /help command from {message.from_user.id}")
        await message.answer(
            "📚 <b>Appointment Booking Bot Help</b>\n\n"
            "This bot allows you to book appointments with our staff members.\n\n"
            "<b>Available commands:</b>\n"
            "/start - Start the bot or return to the main menu\n"
            "/book - Book an appointment\n"
            "/mybookings - View your existing bookings\n"
            "/language - Change your language\n"
            "/help - Show this help message\n\n"
            "<b>Booking process:</b>\n"
            "1. Select a staff member\n"
            "2. Choose a date from the calendar\n"
            "3. Pick an available time slot\n"
            "4. Confirm your booking\n"
            "5. Pay for the appointment (if required)\n\n"
            "After successful booking and payment, you'll receive a confirmation "
            "with a Zoom meeting link for your online appointment."
        )
    
    # Language command handler
    @dp.message(Command("language"))
    async def cmd_language(message: types.Message):
        logger.info(f"Received /language command from {message.from_user.id}")
        await message.answer(
            "Please select your language:",
            reply_markup=language_keyboard()
        )
    
    # Test command handler
    @dp.message(Command("test"))
    async def cmd_test(message: types.Message):
        logger.info(f"Received /test command from {message.from_user.id}")
        await message.answer("Test command received! The bot is working properly.")
    
    # Catch-all message handler for text messages
    @dp.message(F.content_type == "text")
    async def text_handler(message: types.Message):
        logger.info(f"Received text message: {message.text}")
        await message.answer(f"You said: {message.text}")
    
    try:
        # Start polling
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error during polling: {e}", exc_info=True)
    finally:
        # Close connections
        logger.info("Closing bot session...")
        await bot.session.close()

if __name__ == "__main__":
    try:
        with suppress(KeyboardInterrupt):
            asyncio.run(main())
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)