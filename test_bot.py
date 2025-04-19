"""
Simple test bot to verify credentials and connection.
"""
import os
import asyncio
from aiogram import Bot, Dispatcher, enums
from aiogram.filters.command import Command
from aiogram.types import Message

# Check for bot token
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Handler
async def cmd_start(message: Message):
    """
    Handle /start command
    """
    await message.answer("Hello! I'm a test bot and I'm working correctly!")

async def main():
    """Start the bot."""
    # Initialize bot and dispatcher
    from aiogram.client.default import DefaultBotProperties
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=enums.ParseMode.HTML))
    dp = Dispatcher()

    # Register the handler for /start command
    dp.message.register(cmd_start, Command("start"))

    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")