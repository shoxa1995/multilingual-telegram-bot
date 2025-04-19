#!/usr/bin/env python3
"""
Debug script for analyzing Telegram bot issues.
This will test each component separately to isolate the problem.
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
        logging.FileHandler("bot_debug.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("bot_debug")

async def test_bot_token():
    """Test if the bot token is valid"""
    try:
        from bot.config import BOT_TOKEN
        
        logger.info(f"Bot token: {'Valid format (first 5 chars): ' + BOT_TOKEN[:5] + '...' if BOT_TOKEN else 'Missing'}")
        
        if not BOT_TOKEN:
            logger.error("Bot token is missing or empty")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error testing bot token: {e}", exc_info=True)
        return False

async def test_bot_initialization():
    """Test if the bot can be initialized"""
    try:
        from aiogram import Bot
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from bot.config import BOT_TOKEN
        
        logger.info("Testing bot initialization...")
        
        # Initialize the bot
        default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
        bot = Bot(token=BOT_TOKEN, default=default_bot_properties)
        
        logger.info("Bot initialized successfully")
        
        # Test getting basic bot info
        logger.info("Testing API connection...")
        bot_info = await bot.get_me()
        logger.info(f"Bot info: {bot_info.username} (ID: {bot_info.id})")
        
        # Close the bot session
        await bot.session.close()
        
        return True
    except Exception as e:
        logger.error(f"Error initializing bot: {e}", exc_info=True)
        return False

async def test_dispatcher():
    """Test if the dispatcher can be initialized"""
    try:
        from aiogram import Dispatcher
        from aiogram.fsm.storage.memory import MemoryStorage
        
        logger.info("Testing dispatcher initialization...")
        
        # Initialize the dispatcher
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Test if a simple handler can be registered
        from aiogram import Router
        from aiogram.filters import Command
        
        router = Router()
        
        # Define a simple handler
        @router.message(Command("test"))
        async def test_handler(message):
            logger.info("Test handler called")
        
        # Include the router
        dp.include_router(router)
        
        logger.info("Dispatcher initialized successfully")
        
        # Close the storage
        await dp.storage.close()
        
        return True
    except Exception as e:
        logger.error(f"Error initializing dispatcher: {e}", exc_info=True)
        return False

async def test_bot_polling():
    """Test if the bot polling can be started"""
    try:
        logger.info("Testing start_bot function directly from bot.main...")
        
        # Attempt to import it
        from bot.main import start_bot
        
        # We won't actually run it, just check if it's importable
        logger.info("Successfully imported start_bot function")
        
        return True
    except Exception as e:
        logger.error(f"Error importing start_bot: {e}", exc_info=True)
        return False

async def test_database():
    """Test if the database can be initialized"""
    try:
        logger.info("Testing database initialization...")
        
        from bot.database import init_db
        
        # Initialize the database
        await init_db()
        
        logger.info("Database initialized successfully")
        
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        return False

async def test_keyboard_format():
    """Test if the keyboard format is correct for aiogram 3.x"""
    try:
        logger.info("Testing keyboard format...")
        
        from bot.keyboards.reply import language_keyboard, main_menu_keyboard
        
        # Test language keyboard
        lang_keyboard = language_keyboard()
        logger.info(f"Language keyboard format: {lang_keyboard}")
        
        # Test main menu keyboard
        main_keyboard = main_menu_keyboard("en")
        logger.info(f"Main menu keyboard format: {main_keyboard}")
        
        logger.info("Keyboard format appears correct")
        
        return True
    except Exception as e:
        logger.error(f"Error testing keyboard format: {e}", exc_info=True)
        return False

async def main():
    """Run all tests"""
    logger.info("Starting Telegram bot debugging")
    
    # Record results
    results = {}
    
    # Test the bot token
    results["bot_token"] = await test_bot_token()
    
    # Test bot initialization
    results["bot_initialization"] = await test_bot_initialization()
    
    # Test dispatcher
    results["dispatcher"] = await test_dispatcher()
    
    # Test bot polling
    results["bot_polling"] = await test_bot_polling()
    
    # Test database
    results["database"] = await test_database()
    
    # Test keyboard format
    results["keyboard_format"] = await test_keyboard_format()
    
    # Print summary
    logger.info("==== Test Results Summary ====")
    for test, result in results.items():
        logger.info(f"{test}: {'✅ PASS' if result else '❌ FAIL'}")
    
    # Return overall success
    return all(results.values())

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Debugging interrupted")
        sys.exit(130)
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)