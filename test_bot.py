"""
Simple test bot to verify credentials and connection.
"""
import os
import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, enums
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.command import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.client.default import DefaultBotProperties

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Check for bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Handlers
async def cmd_start(message: Message):
    """
    Handle /start command
    """
    await message.answer("Hello! This is a test bot for aiogram 3.x. Bot token is valid and working!")

async def cmd_help(message: Message):
    """
    Handle /help command
    """
    help_text = (
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/keyboard - Test inline keyboard"
    )
    await message.answer(help_text)

async def cmd_keyboard(message: Message):
    """
    Handle /keyboard command to test inline keyboard callbacks
    """
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Button 1", callback_data="test:1"),
            InlineKeyboardButton(text="Button 2", callback_data="test:2")
        ],
        [
            InlineKeyboardButton(text="Cancel", callback_data="cancel")
        ]
    ])
    await message.answer("Testing inline keyboard:", reply_markup=markup)

async def on_button_clicked(callback_query):
    """
    Handle callback queries from inline keyboard
    """
    await callback_query.answer()
    await callback_query.message.answer(f"You clicked: {callback_query.data}")

async def main():
    """Start the bot."""
    # Check if BOT_TOKEN is set
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable not set. Please set it before running this script.")
        return 1
    
    # Initialize bot and dispatcher with DefaultBotProperties for aiogram 3.7.0+
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=enums.ParseMode.HTML))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register handlers
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_keyboard, Command("keyboard"))
    
    # Register callback query handler
    dp.callback_query.register(on_button_clicked)

    # Start polling
    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error during bot polling: {e}")
    finally:
        await bot.session.close()
        logger.info("Bot session closed")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")