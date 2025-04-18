"""
Start command handler for the Telegram bot.
Handles initial interaction and language selection.
"""
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, Command
from aiogram.utils.exceptions import CantParseEntities

from bot.database import Session, User
from bot.keyboards.reply import language_keyboard, main_menu_keyboard
from bot.keyboards.inline import staff_selection_keyboard
from bot.middlewares.i18n import _, i18n
from bot.config import LANGUAGES

async def cmd_start(message: types.Message, state: FSMContext):
    """
    Handle /start command.
    Welcome the user and ask for language selection.
    """
    # Reset state
    await state.finish()
    
    # Get or create user in database
    session = Session()
    try:
        user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
        
        if not user:
            # Create new user
            user = User(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
                language='en'  # Default language
            )
            session.add(user)
            session.commit()
            
            # Welcome message with language selection
            await message.answer(
                "👋 Welcome to the Appointment Booking Bot!\n\n"
                "Please select your language:",
                reply_markup=language_keyboard()
            )
        else:
            # Existing user, show welcome back message in their language
            i18n.current_locale = user.language
            
            await message.answer(
                _("👋 Welcome back to the Appointment Booking Bot!\n\n"
                  "You can book appointments with our staff members, view your existing "
                  "bookings, and more."),
                reply_markup=main_menu_keyboard(user.language)
            )
    finally:
        session.close()

async def language_selection(message: types.Message):
    """
    Handle language selection from the keyboard.
    """
    # Find selected language code
    selected_lang = None
    for code, name in LANGUAGES.items():
        if name == message.text:
            selected_lang = code
            break
            
    if not selected_lang:
        # Invalid language selected
        await message.answer(
            "Please select a language from the keyboard.",
            reply_markup=language_keyboard()
        )
        return
        
    # Update user language in database
    session = Session()
    try:
        user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
        
        if user:
            user.language = selected_lang
            session.commit()
            
            # Set current locale
            i18n.current_locale = selected_lang
            
            # Send welcome message in selected language
            await message.answer(
                _("👋 Welcome to the Appointment Booking Bot!\n\n"
                  "You can book appointments with our staff members, view your existing "
                  "bookings, and more."),
                reply_markup=main_menu_keyboard(selected_lang)
            )
        else:
            # User not found, create new user
            user = User(
                telegram_id=message.from_user.id,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                username=message.from_user.username,
                language=selected_lang
            )
            session.add(user)
            session.commit()
            
            # Set current locale
            i18n.current_locale = selected_lang
            
            # Send welcome message in selected language
            await message.answer(
                _("👋 Welcome to the Appointment Booking Bot!\n\n"
                  "You can book appointments with our staff members, view your existing "
                  "bookings, and more."),
                reply_markup=main_menu_keyboard(selected_lang)
            )
    finally:
        session.close()

async def cmd_language(message: types.Message):
    """
    Handle /language command to change language.
    """
    await message.answer(
        "Please select your language:",
        reply_markup=language_keyboard()
    )

async def cmd_help(message: types.Message):
    """
    Handle /help command.
    """
    # Get user language
    session = Session()
    try:
        user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
        language = user.language if user else 'en'
    finally:
        session.close()
        
    # Set current locale
    i18n.current_locale = language
    
    # Send help message
    help_message = _(
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
    
    try:
        await message.answer(help_message, reply_markup=main_menu_keyboard(language))
    except CantParseEntities:
        # Fallback if there's an issue with message formatting
        await message.answer(
            "📚 Appointment Booking Bot Help\n\n"
            "This bot allows you to book appointments with our staff members.\n\n"
            "Available commands:\n"
            "/start - Start the bot or return to the main menu\n"
            "/book - Book an appointment\n"
            "/mybookings - View your existing bookings\n"
            "/language - Change your language\n"
            "/help - Show this help message",
            reply_markup=main_menu_keyboard(language)
        )

async def text_handler(message: types.Message):
    """
    Handle text messages for main menu buttons.
    """
    # Get user language
    session = Session()
    try:
        user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
        language = user.language if user else 'en'
    finally:
        session.close()
    
    # Set current locale
    i18n.current_locale = language
    
    # Define text constants for menu buttons
    book_texts = {
        'en': '📅 Book Appointment',
        'ru': '📅 Записаться на прием',
        'uz': '📅 Qabulga yozilish'
    }
    
    my_bookings_texts = {
        'en': '📋 My Bookings',
        'ru': '📋 Мои записи',
        'uz': '📋 Mening qabullarim'
    }
    
    language_texts = {
        'en': '🌐 Change Language',
        'ru': '🌐 Изменить язык',
        'uz': '🌐 Tilni o\'zgartirish'
    }
    
    help_texts = {
        'en': '❓ Help',
        'ru': '❓ Помощь',
        'uz': '❓ Yordam'
    }
    
    # Check which button was pressed
    text = message.text
    
    if text in [book_texts.get(lang) for lang in book_texts]:
        # Book appointment button
        await message.answer(
            _("Please select a staff member to book an appointment with:"),
            reply_markup=staff_selection_keyboard()
        )
    elif text in [my_bookings_texts.get(lang) for lang in my_bookings_texts]:
        # My bookings button - trigger /mybookings command
        dispatcher = Dispatcher.get_current()
        await dispatcher.current_state().reset_state()
        await message.answer(
            _("Loading your bookings...")
        )
        # Forward to /mybookings command
        message.text = "/mybookings"
        await dispatcher.process_update(types.Update(update_id=0, message=message))
    elif text in [language_texts.get(lang) for lang in language_texts]:
        # Change language button
        await message.answer(
            "Please select your language:",
            reply_markup=language_keyboard()
        )
    elif text in [help_texts.get(lang) for lang in help_texts]:
        # Help button
        await cmd_help(message)
    else:
        # Unknown text
        await message.answer(
            _("I don't understand that command. Please use the menu buttons or commands."),
            reply_markup=main_menu_keyboard(language)
        )

def register_start_handlers(dp: Dispatcher):
    """
    Register all start and general command handlers.
    """
    # Start command
    dp.register_message_handler(cmd_start, CommandStart(), state="*")
    
    # Language command and selection
    dp.register_message_handler(cmd_language, Command("language"), state="*")
    for lang_name in LANGUAGES.values():
        dp.register_message_handler(language_selection, lambda msg, text=lang_name: msg.text == text, state="*")
    
    # Help command
    dp.register_message_handler(cmd_help, Command("help"), state="*")
    
    # Text handler for main menu buttons
    dp.register_message_handler(text_handler, content_types=types.ContentTypes.TEXT, state="*")
