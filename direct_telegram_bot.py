#!/usr/bin/env python3
"""
Direct Telegram bot implementation using only basic aiogram features.
This is a completely standalone script without any dependencies on other project modules.
"""
import asyncio
import logging
import os
import sys

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("direct_telegram_bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("direct_telegram_bot")

# Get token from environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set")
    sys.exit(1)

# Language dictionary for translated texts
TEXTS = {
    "en": {
        "welcome": "👋 Welcome to the Appointment Booking Bot!",
        "select_language": "Please select your preferred language:",
        "help_message": "📚 <b>Bot Help</b>\n\nAvailable commands:\n/start - Start the bot\n/help - Show this help message\n/test - Test if the bot is responding",
        "test_response": "✅ Test successful! The bot is working properly.",
    },
    "ru": {
        "welcome": "👋 Добро пожаловать в Бот для записи на прием!",
        "select_language": "Пожалуйста, выберите предпочитаемый язык:",
        "help_message": "📚 <b>Справка по боту</b>\n\nДоступные команды:\n/start - Запустить бота\n/help - Показать эту справку\n/test - Проверить, работает ли бот",
        "test_response": "✅ Тест успешен! Бот работает правильно.",
    },
    "uz": {
        "welcome": "👋 Qabulga yozilish botiga xush kelibsiz!",
        "select_language": "Iltimos, tilni tanlang:",
        "help_message": "📚 <b>Bot Yordam</b>\n\nMavjud buyruqlar:\n/start - Botni ishga tushirish\n/help - Ushbu yordam xabarini ko'rsatish\n/test - Bot ishlayotganini tekshirish",
        "test_response": "✅ Test muvaffaqiyatli! Bot to'g'ri ishlayapti.",
    }
}

async def main():
    try:
        # Import required components
        from aiogram import Bot, Dispatcher, types, F
        from aiogram.filters import Command
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        
        # Initialize bot with proper settings for aiogram 3.7.0+
        logger.info("Initializing bot...")
        default_bot_properties = DefaultBotProperties(parse_mode=ParseMode.HTML)
        bot = Bot(token=BOT_TOKEN, default=default_bot_properties)
        
        # Initialize dispatcher
        dp = Dispatcher()
        
        # Define handlers
        @dp.message(Command("start"))
        async def cmd_start(message: types.Message):
            logger.info(f"Received /start from {message.from_user.id}")
            
            # Create language selection keyboard
            markup = types.ReplyKeyboardMarkup(
                keyboard=[
                    [types.KeyboardButton(text="English 🇬🇧")],
                    [types.KeyboardButton(text="Русский 🇷🇺")],
                    [types.KeyboardButton(text="O'zbekcha 🇺🇿")]
                ],
                resize_keyboard=True,
                one_time_keyboard=True
            )
            
            # Send welcome message with language selection
            await message.answer(
                TEXTS["en"]["welcome"] + "\n\n" + TEXTS["en"]["select_language"],
                reply_markup=markup
            )
        
        @dp.message(F.text.contains("English"))
        async def english_selected(message: types.Message):
            logger.info(f"English language selected by {message.from_user.id}")
            await message.answer(TEXTS["en"]["welcome"])
            
        @dp.message(F.text.contains("Русский"))
        async def russian_selected(message: types.Message):
            logger.info(f"Russian language selected by {message.from_user.id}")
            await message.answer(TEXTS["ru"]["welcome"])
            
        @dp.message(F.text.contains("O'zbekcha") | F.text.contains("Ўзбекча"))
        async def uzbek_selected(message: types.Message):
            logger.info(f"Uzbek language selected by {message.from_user.id}")
            await message.answer(TEXTS["uz"]["welcome"])
        
        @dp.message(Command("help"))
        async def cmd_help(message: types.Message):
            logger.info(f"Received /help from {message.from_user.id}")
            await message.answer(TEXTS["en"]["help_message"])
        
        @dp.message(Command("test"))
        async def cmd_test(message: types.Message):
            logger.info(f"Received /test from {message.from_user.id}")
            await message.answer(TEXTS["en"]["test_response"])
        
        # Default message handler
        @dp.message()
        async def echo(message: types.Message):
            logger.info(f"Received message: {message.text} from {message.from_user.id}")
            await message.answer(f"You said: {message.text}")
        
        # Get bot info and verify connection
        me = await bot.get_me()
        logger.info(f"Successfully connected to Telegram as {me.username} (ID: {me.id})")
        
        # Start polling
        logger.info("Starting bot polling...")
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"Error during polling: {e}", exc_info=True)
        finally:
            await bot.session.close()
            logger.info("Bot polling finished, session closed")
            
    except Exception as e:
        logger.error(f"Error in main function: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        logger.info("Starting direct Telegram bot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by keyboard interrupt")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)