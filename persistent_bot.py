#!/usr/bin/env python3
"""
Ultra simple bot implementation with auto-restart capability.
"""
import asyncio
import logging
import os
import signal
import sys
import time

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("persistent_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("persistent_bot")

# Flag to indicate if shutdown was requested
shutdown_requested = False

def signal_handler(sig, frame):
    """Handle termination signals gracefully"""
    global shutdown_requested
    logger.info(f"Received signal {sig}, shutting down...")
    shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

async def run_bot():
    """Run the actual bot with error handling"""
    try:
        from aiogram import Bot, Dispatcher, types
        from aiogram.filters import Command
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        
        # Get bot token from environment
        bot_token = os.environ.get("BOT_TOKEN")
        if not bot_token:
            logger.error("BOT_TOKEN environment variable not set")
            return False
        
        # Initialize bot with proper settings
        logger.info("Initializing bot...")
        default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
        bot = Bot(token=bot_token, default=default_bot_properties)
        
        # Initialize dispatcher
        dp = Dispatcher()
        
        # Define handlers
        @dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            logger.info(f"Received /start from {message.from_user.id}")
            await message.answer("👋 <b>Hello!</b> Welcome to the bot. Use /help to see available commands.")
        
        @dp.message(Command("help"))
        async def cmd_help(message: types.Message):
            logger.info(f"Received /help from {message.from_user.id}")
            await message.answer(
                "📚 <b>Available commands:</b>\n"
                "/start - Start the bot\n"
                "/help - Show this help message\n"
                "/test - Test if the bot is responding"
            )
        
        @dp.message(Command("test"))
        async def cmd_test(message: types.Message):
            logger.info(f"Received /test from {message.from_user.id}")
            await message.answer("✅ Test successful! The bot is working properly.")
        
        # Default message handler
        @dp.message()
        async def echo(message: types.Message):
            logger.info(f"Received message: {message.text} from {message.from_user.id}")
            await message.answer(f"You said: {message.text}")
        
        # Get bot info
        me = await bot.get_me()
        logger.info(f"Successfully connected to Telegram as {me.username} (ID: {me.id})")
        
        # Run polling with proper handling for interruption
        logger.info(f"Bot PID: {os.getpid()} - starting bot polling...")
        
        try:
            # Use a custom polling approach with manual shutdown handling
            polling_task = asyncio.create_task(dp.start_polling(bot))
            
            # Keep the bot running until shutdown is requested
            while not shutdown_requested:
                await asyncio.sleep(1)
                
            # Cancel polling task
            logger.info("Shutdown requested, stopping polling...")
            polling_task.cancel()
            
        except asyncio.CancelledError:
            logger.info("Polling was cancelled")
        except Exception as e:
            logger.error(f"Error during polling: {e}", exc_info=True)
            return False
        finally:
            await bot.session.close()
            logger.info("Bot session closed")
        
        return True
    
    except Exception as e:
        logger.error(f"Error in run_bot: {e}", exc_info=True)
        return False

async def main_loop():
    """Main loop with restart capability"""
    retry_count = 0
    max_retries = 10
    
    while not shutdown_requested and retry_count < max_retries:
        logger.info(f"Starting bot attempt {retry_count + 1}/{max_retries}")
        
        try:
            success = await run_bot()
            if shutdown_requested:
                logger.info("Shutdown requested, exiting main loop")
                break
                
            if success:
                # If the bot ran successfully but then exited, reset retry count
                logger.info("Bot exited successfully, restarting...")
                retry_count = 0
            else:
                # Bot encountered an error
                retry_count += 1
                logger.warning(f"Bot failed to run properly, retrying ({retry_count}/{max_retries})...")
                
            # Wait before restarting
            await asyncio.sleep(5)
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Error in main loop: {e}", exc_info=True)
            await asyncio.sleep(5)
    
    if retry_count >= max_retries:
        logger.critical(f"Reached maximum retries ({max_retries}), giving up")

if __name__ == "__main__":
    try:
        logger.info(f"Starting persistent bot (PID: {os.getpid()})...")
        with open("persistent_bot.pid", "w") as f:
            f.write(str(os.getpid()))
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info("Bot shutdown complete")