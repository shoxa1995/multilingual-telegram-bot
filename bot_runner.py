"""
Simple Telegram bot runner for use with Replit workflows.
This script needs to be started through a Replit workflow to ensure
it runs persistently.
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command

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

async def cmd_start(message: types.Message):
    """Handler for the /start command"""
    user = message.from_user
    logger.info(f"Received /start command from user {user.id} (@{user.username})")
    await message.answer(f"Hello, {user.first_name}! This is a workflow-managed bot.")

async def main():
    """Main bot function"""
    # Initialize bot
    logger.info("Creating bot instance")
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Register command handlers
    logger.info("Registering command handlers")
    dp.message.register(cmd_start, Command('start'))
    
    # Test connection
    logger.info("Testing Telegram API connection")
    me = await bot.get_me()
    logger.info(f"Connected as @{me.username} (ID: {me.id})")
    
    # Start polling
    logger.info("Starting bot polling")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logger.info("=== STARTING WORKFLOW BOT ===")
    asyncio.run(main())