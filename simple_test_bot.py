#!/usr/bin/env python3
"""
Ultra-simple test bot to verify Telegram connectivity.
"""
import asyncio
import logging
import os
import sys

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("simple_test.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("simple_test")

async def main():
    try:
        # Import required components
        from aiogram import Bot, Dispatcher, types
        from aiogram.filters import Command
        
        # Import bot token from config
        from bot.config import BOT_TOKEN
        
        # Initialize the bot
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()
        
        # Define a simple command handler
        @dp.message(Command("test"))
        async def test_command(message: types.Message):
            logger.info(f"Received test command from {message.from_user.id}")
            await message.answer("Test response from simplified bot!")
            
        @dp.message(Command("start"))
        async def start_command(message: types.Message):
            logger.info(f"Received start command from {message.from_user.id}")
            await message.answer("Hello from simplified test bot!")
        
        # Test a direct message send
        logger.info("Testing direct message send to Telegram...")
        try:
            owner_info = await bot.get_me()
            logger.info(f"Bot info: {owner_info.username} (ID: {owner_info.id})")
            
            # Try to get recent updates
            logger.info("Getting recent updates...")
            updates = await bot.get_updates(limit=10)
            logger.info(f"Received {len(updates)} updates")
            for update in updates:
                logger.info(f"Update: {update}")
                
            # Start polling
            logger.info("Starting polling...")
            await dp.start_polling(bot, allowed_updates=["message"])
        except Exception as e:
            logger.error(f"Error in test_direct_message: {e}", exc_info=True)
            
        return True
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
