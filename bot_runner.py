"""
Workflow-compatible Telegram bot runner for Replit.
This script is designed to be run as a persistent workflow in Replit.
It includes all the necessary handlers to respond to basic commands and
uses the full bot API for complete functionality.
"""
import asyncio
import logging
import os
import sys
import signal
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from aiogram.enums import ParseMode
from aiogram.utils.formatting import Text, Bold

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("workflow_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Bot token
BOT_TOKEN = '8126004060:AAH5J83MA5-YTe2JmtvcdAnZSrPeUi_apmY'

# Flag for graceful shutdown
should_exit = False

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    global should_exit
    logger.info(f"Received signal {sig}, shutting down gracefully...")
    should_exit = True

# Register signal handlers for graceful shutdown
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def cmd_start(message: types.Message):
    """Handler for the /start command"""
    user = message.from_user
    logger.info(f"Received /start command from user {user.id} (@{user.username})")
    
    # Create formatted message
    content = Text(
        "Hello, ", Bold(user.first_name), "! 👋\n\n",
        "Welcome to Go Study Online appointment booking bot. Use this bot to:\n",
        "• Book appointments with our specialists\n",
        "• Manage your bookings\n",
        "• Make secure payments\n",
        "• Receive reminders about your appointments\n\n",
        "Use /help to see available commands."
    )
    
    await message.answer(**content.as_kwargs())

async def cmd_help(message: types.Message):
    """Handler for the /help command"""
    content = Text(
        Bold("Available Commands:"), "\n\n",
        "/start - Start interacting with the bot\n",
        "/book - Book a new appointment\n",
        "/bookings - View your current bookings\n",
        "/cancel - Cancel a booking\n",
        "/language - Change your language preference\n",
        "/help - Show this help message"
    )
    
    await message.answer(**content.as_kwargs())

async def check_bot_connection():
    """Test connection to Telegram API and print bot info"""
    try:
        from aiogram.client.default import DefaultBotProperties
        
        # Create default properties for the bot
        default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
        
        # Initialize bot with properties in new aiogram 3.7+ style
        bot = Bot(token=BOT_TOKEN, default=default_properties)
        me = await bot.get_me()
        logger.info(f"✓ Successfully connected as @{me.username} (ID: {me.id})")
        logger.info(f"✓ Bot name: {me.first_name}")
        logger.info(f"✓ Is bot: {me.is_bot}")
        
        await bot.session.close()
        return True
    except Exception as e:
        logger.error(f"✗ Failed to connect to Telegram: {e}")
        return False

async def bot_polling_task(dispatcher, bot):
    """Task for running bot polling with shutdown handling"""
    try:
        logger.info("Starting polling in task...")
        await dispatcher.start_polling(bot, allowed_updates=[
            "message", "callback_query", "pre_checkout_query", "shipping_query"
        ])
    except Exception as e:
        logger.error(f"Polling error: {e}")
        raise

async def main():
    """Main bot function with shutdown handling"""
    # Check connection first
    if not await check_bot_connection():
        logger.error("Failed to connect to Telegram. Exiting.")
        return 1
    
    # Initialize bot with properties in new aiogram 3.7+ style
    from aiogram.client.default import DefaultBotProperties
    default_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
    bot = Bot(token=BOT_TOKEN, default=default_properties)
    dp = Dispatcher()
    
    # Register command handlers
    dp.message.register(cmd_start, Command('start'))
    dp.message.register(cmd_help, Command('help'))
    
    # Import full bot handlers if needed
    try:
        # Try to import handlers from the main bot implementation
        from bot.handlers import get_all_routers
        dp.include_router(get_all_routers())
        logger.info("Loaded full handler set from main bot implementation")
    except Exception as e:
        logger.warning(f"Couldn't load full handler set: {e}")
        logger.info("Using basic handlers only")
    
    # Create polling task
    polling_task = asyncio.create_task(bot_polling_task(dp, bot))
    
    # Main loop to manage the bot and handle shutdown
    try:
        # Check for graceful shutdown signal
        while not should_exit:
            # Monitor status and handle any maintenance tasks
            await asyncio.sleep(1)
            
            # Check if polling task has crashed
            if polling_task.done():
                error = polling_task.exception()
                if error:
                    logger.error(f"Polling task crashed with error: {error}")
                    break
                else:
                    logger.info("Polling task completed normally")
                    break
    except asyncio.CancelledError:
        logger.info("Main task was cancelled")
    finally:
        # Clean shutdown
        logger.info("Stopping bot...")
        if not polling_task.done():
            polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                logger.info("Polling task cancelled")
        
        # Close the bot session
        await bot.session.close()
        logger.info("Bot session closed")
    
    return 0

if __name__ == "__main__":
    try:
        logger.info("=== STARTING WORKFLOW BOT ===")
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}")
        sys.exit(1)