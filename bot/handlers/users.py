"""
User handlers for the Telegram bot.
Handles user interaction, booking, and payments.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Union

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice,
    PreCheckoutQuery, ContentType
)
from aiogram.dispatcher.filters import Command, Text
from aiogram.utils.callback_data import CallbackData

from bot.middlewares.i18n import _
from bot.states.booking import BookingStates
from bot.database import (
    get_or_create_user, update_user_language, get_active_staff,
    get_staff_by_id, get_staff_schedule, create_booking,
    get_user_bookings, get_booking_by_id, cancel_booking
)
from bot.utils.payments import create_invoice, verify_payment
from bot.keyboards.user import (
    get_language_keyboard, get_main_menu_keyboard,
    get_staff_selection_keyboard, get_date_selection_keyboard,
    get_time_selection_keyboard, get_booking_confirmation_keyboard,
    get_booking_actions_keyboard
)
from bot.config import LANGUAGES

logger = logging.getLogger(__name__)

# Callback data factories
staff_callback = CallbackData("staff", "id")
date_callback = CallbackData("date", "value")
time_callback = CallbackData("time", "value")
booking_callback = CallbackData("booking", "action", "id")
language_callback = CallbackData("language", "code")


async def cmd_start(message: Message, state: FSMContext):
    """
    Handle /start command - initialize the bot for the user
    """
    # Reset any active state
    await state.finish()
    
    # Get or create user
    user = await get_or_create_user(message.from_user)
    
    # Welcome message
    await message.answer(
        _(
            "👋 Welcome to our Booking Bot!\n\n"
            "Here you can book appointments with our specialists.\n\n"
            "Use /book to make a new booking\n"
            "Use /mybookings to view your existing bookings\n"
            "Use /language to change the language\n"
            "Use /help to get assistance"
        ),
        reply_markup=get_main_menu_keyboard()
    )


async def cmd_help(message: Message):
    """
    Handle /help command - show help information
    """
    await message.answer(
        _(
            "📚 Bot Commands:\n\n"
            "/start - Start the bot\n"
            "/book - Book an appointment\n"
            "/mybookings - View your bookings\n"
            "/language - Change language\n"
            "/help - Show this help message\n\n"
            "If you need additional assistance, please contact our support."
        )
    )


async def cmd_language(message: Message):
    """
    Handle /language command - change user language
    """
    await message.answer(
        _("🌐 Please select your preferred language:"),
        reply_markup=get_language_keyboard()
    )


async def language_callback_handler(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    """
    Handle language selection
    """
    lang_code = callback_data["code"]
    
    # Update user language
    success = await update_user_language(callback_query.from_user.id, lang_code)
    
    if success:
        # Get language name
        lang_name = LANGUAGES.get(lang_code, lang_code)
        
        await callback_query.message.edit_text(
            _("✅ Language changed to {language}").format(language=lang_name)
        )
    else:
        await callback_query.message.edit_text(
            _("❌ Failed to update language. Please try again later.")
        )
    
    await callback_query.answer()


async def cmd_book(message: Message, state: FSMContext):
    """
    Handle /book command - start booking process
    """
    # Reset any active state
    await state.finish()
    
    # Get active staff members
    staff_members = await get_active_staff()
    
    if not staff_members:
        await message.answer(_("❌ Sorry, no specialists are available at the moment. Please try again later."))
        return
    
    # Show staff selection
    await message.answer(
        _("👨‍⚕️ Please select a specialist for your appointment:"),
        reply_markup=get_staff_selection_keyboard(staff_members)
    )
    
    # Set state
    await BookingStates.selecting_staff.set()


async def staff_selection_handler(callback_query: CallbackQuery, callback_data: Dict[str, str], state: FSMContext):
    """
    Handle staff selection
    """
    staff_id = int(callback_data["id"])
    
    # Get staff details
    staff = await get_staff_by_id(staff_id)
    
    if not staff:
        await callback_query.message.edit_text(
            _("❌ Specialist not found. Please try again.")
        )
        await callback_query.answer()
        return
    
    # Store staff selection in state
    await state.update_data(staff_id=staff_id)
    
    # Get available dates (next 7 days)
    today = datetime.now().date()
    dates = [today + timedelta(days=i) for i in range(7)]
    
    # Show date selection
    await callback_query.message.edit_text(
        _("📅 Selected specialist: {name}\n\nPlease select a date for your appointment:").format(name=staff.name),
        reply_markup=get_date_selection_keyboard(dates)
    )
    
    # Update state
    await BookingStates.selecting_date.set()
    
    await callback_query.answer()


async def date_selection_handler(callback_query: CallbackQuery, callback_data: Dict[str, str], state: FSMContext):
    """
    Handle date selection
    """
    date_str = callback_data["value"]
    
    try:
        # Parse date
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Store date selection in state
        await state.update_data(date=date_str)
        
        # Get state data
        data = await state.get_data()
        staff_id = data.get("staff_id")
        
        # Get staff details
        staff = await get_staff_by_id(staff_id)
        
        if not staff:
            await callback_query.message.edit_text(
                _("❌ Specialist not found. Please try again.")
            )
            await callback_query.answer()
            return
        
        # Get staff schedule
        schedules = await get_staff_schedule(staff_id)
        
        # Find schedule for selected weekday
        weekday = selected_date.weekday()  # 0=Monday, 6=Sunday
        
        available_times = []
        for schedule in schedules:
            if schedule.weekday == weekday and schedule.is_working_day:
                # Generate available time slots (every 30 minutes)
                start_hour, start_minute = map(int, schedule.start_time.split(":"))
                end_hour, end_minute = map(int, schedule.end_time.split(":"))
                
                current_time = datetime(
                    selected_date.year, selected_date.month, selected_date.day,
                    start_hour, start_minute
                )
                end_time = datetime(
                    selected_date.year, selected_date.month, selected_date.day,
                    end_hour, end_minute
                )
                
                while current_time < end_time:
                    available_times.append(current_time.strftime("%H:%M"))
                    current_time += timedelta(minutes=30)
        
        if not available_times:
            await callback_query.message.edit_text(
                _("❌ No available time slots for this date. Please select another date.")
            )
            await callback_query.answer()
            return
        
        # Show time selection
        await callback_query.message.edit_text(
            _(
                "🕒 Selected specialist: {name}\n"
                "Selected date: {date}\n\n"
                "Please select a time for your appointment:"
            ).format(name=staff.name, date=selected_date.strftime("%Y-%m-%d")),
            reply_markup=get_time_selection_keyboard(available_times)
        )
        
        # Update state
        await BookingStates.selecting_time.set()
        
    except ValueError:
        await callback_query.message.edit_text(
            _("❌ Invalid date format. Please try again.")
        )
    
    await callback_query.answer()


async def time_selection_handler(callback_query: CallbackQuery, callback_data: Dict[str, str], state: FSMContext):
    """
    Handle time selection
    """
    time_str = callback_data["value"]
    
    # Store time selection in state
    await state.update_data(time=time_str)
    
    # Get state data
    data = await state.get_data()
    staff_id = data.get("staff_id")
    date_str = data.get("date")
    
    # Get staff details
    staff = await get_staff_by_id(staff_id)
    
    if not staff or not date_str:
        await callback_query.message.edit_text(
            _("❌ Missing booking information. Please start again.")
        )
        await callback_query.answer()
        return
    
    # Combine date and time
    try:
        booking_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        
        # Show booking confirmation
        await callback_query.message.edit_text(
            _(
                "📝 Booking Summary:\n\n"
                "Specialist: {name}\n"
                "Date: {date}\n"
                "Time: {time}\n"
                "Duration: 30 minutes\n"
                "Price: {price} UZS\n\n"
                "Would you like to confirm this booking?"
            ).format(
                name=staff.name,
                date=date_str,
                time=time_str,
                price=staff.price
            ),
            reply_markup=get_booking_confirmation_keyboard()
        )
        
        # Update state with full datetime and price
        await state.update_data(
            booking_datetime=booking_datetime.isoformat(),
            price=staff.price
        )
        
        # Update state
        await BookingStates.confirming_booking.set()
        
    except ValueError:
        await callback_query.message.edit_text(
            _("❌ Invalid date or time format. Please try again.")
        )
    
    await callback_query.answer()


async def booking_confirmation_handler(callback_query: CallbackQuery, state: FSMContext):
    """
    Handle booking confirmation
    """
    # Get state data
    data = await state.get_data()
    staff_id = data.get("staff_id")
    booking_datetime_str = data.get("booking_datetime")
    price = data.get("price", 0)
    
    if not staff_id or not booking_datetime_str:
        await callback_query.message.edit_text(
            _("❌ Missing booking information. Please start again.")
        )
        await callback_query.answer()
        return
    
    # Get staff details
    staff = await get_staff_by_id(staff_id)
    
    if not staff:
        await callback_query.message.edit_text(
            _("❌ Specialist not found. Please try again.")
        )
        await callback_query.answer()
        return
    
    # Parse booking datetime
    booking_datetime = datetime.fromisoformat(booking_datetime_str)
    
    # Get user
    user = await get_or_create_user(callback_query.from_user)
    
    # Create booking
    booking = await create_booking(
        user_id=user.id,
        staff_id=staff_id,
        booking_date=booking_datetime,
        duration_minutes=30,
        price=price
    )
    
    if not booking:
        await callback_query.message.edit_text(
            _("❌ Failed to create booking. Please try again later.")
        )
        await callback_query.answer()
        return
    
    # Generate payment link if price > 0
    if price > 0:
        # Proceed to payment
        await callback_query.message.edit_text(
            _(
                "✅ Booking created! Proceeding to payment...\n\n"
                "You will receive a payment invoice shortly."
            )
        )
        
        # Create payment invoice
        invoice_payload = await create_invoice(
            bot=callback_query.bot,
            chat_id=callback_query.from_user.id,
            booking_id=booking.id
        )
        
        if not invoice_payload:
            await callback_query.message.edit_text(
                _(
                    "❌ Failed to create payment invoice. Your booking has been created "
                    "but you will need to pay later. View your bookings with /mybookings."
                )
            )
    else:
        # Free booking
        await callback_query.message.edit_text(
            _(
                "✅ Booking confirmed!\n\n"
                "Your appointment has been scheduled for {date} at {time} with {name}.\n\n"
                "You can view your bookings with /mybookings."
            ).format(
                date=booking_datetime.strftime("%Y-%m-%d"),
                time=booking_datetime.strftime("%H:%M"),
                name=staff.name
            )
        )
    
    # Reset state
    await state.finish()
    
    await callback_query.answer()


async def cmd_my_bookings(message: Message):
    """
    Handle /mybookings command - show user's bookings
    """
    # Get user's bookings
    bookings = await get_user_bookings(message.from_user.id)
    
    if not bookings:
        await message.answer(
            _("📅 You don't have any bookings yet. Use /book to make a new booking.")
        )
        return
    
    # Display bookings
    response = _("📅 Your bookings:\n\n")
    
    for booking in bookings:
        staff = await get_staff_by_id(booking.staff_id)
        staff_name = staff.name if staff else _("Unknown specialist")
        
        status_text = {
            "pending": _("⏳ Pending"),
            "payment_pending": _("💰 Payment pending"),
            "confirmed": _("✅ Confirmed"),
            "cancelled": _("❌ Cancelled"),
            "completed": _("✓ Completed")
        }.get(booking.status.value, booking.status.value)
        
        response += _(
            "🔹 Booking #{id}\n"
            "   With: {name}\n"
            "   Date: {date}\n"
            "   Status: {status}\n"
        ).format(
            id=booking.id,
            name=staff_name,
            date=booking.booking_date.strftime("%Y-%m-%d %H:%M"),
            status=status_text
        )
        
        # Add action buttons for active bookings
        if booking.status.value in ["pending", "payment_pending", "confirmed"]:
            await message.answer(
                response,
                reply_markup=get_booking_actions_keyboard(booking.id)
            )
            response = ""
    
    if response:
        await message.answer(response)


async def booking_action_handler(callback_query: CallbackQuery, callback_data: Dict[str, str]):
    """
    Handle booking actions (cancel, pay, etc.)
    """
    action = callback_data["action"]
    booking_id = int(callback_data["id"])
    
    # Get booking details
    booking = await get_booking_by_id(booking_id)
    
    if not booking:
        await callback_query.message.edit_text(
            _("❌ Booking not found. Please try again.")
        )
        await callback_query.answer()
        return
    
    # Get staff details
    staff = await get_staff_by_id(booking.staff_id)
    staff_name = staff.name if staff else _("Unknown specialist")
    
    if action == "cancel":
        # Cancel booking
        success = await cancel_booking(booking_id)
        
        if success:
            await callback_query.message.edit_text(
                _(
                    "✅ Booking #{id} with {name} on {date} has been cancelled."
                ).format(
                    id=booking_id,
                    name=staff_name,
                    date=booking.booking_date.strftime("%Y-%m-%d %H:%M")
                )
            )
        else:
            await callback_query.message.edit_text(
                _("❌ Failed to cancel booking. Please try again later.")
            )
    
    elif action == "pay":
        # Create payment invoice
        invoice_payload = await create_invoice(
            bot=callback_query.bot,
            chat_id=callback_query.from_user.id,
            booking_id=booking_id
        )
        
        if invoice_payload:
            await callback_query.message.edit_text(
                _("💰 Payment invoice has been sent.")
            )
        else:
            await callback_query.message.edit_text(
                _("❌ Failed to create payment invoice. Please try again later.")
            )
    
    await callback_query.answer()


async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """
    Handle pre-checkout query (validate payment before processing)
    """
    # Always approve for now (additional validation could be added here)
    await pre_checkout_query.bot.answer_pre_checkout_query(
        pre_checkout_query.id,
        ok=True
    )


async def successful_payment_handler(message: Message):
    """
    Handle successful payment
    """
    payment = message.successful_payment
    
    # Verify and update booking
    booking_id = await verify_payment(
        payment_id=payment.telegram_payment_charge_id,
        invoice_payload=payment.invoice_payload
    )
    
    if booking_id:
        # Get booking details
        booking = await get_booking_by_id(booking_id)
        
        if booking:
            # Get staff details
            staff = await get_staff_by_id(booking.staff_id)
            staff_name = staff.name if staff else _("Unknown specialist")
            
            await message.answer(
                _(
                    "✅ Payment successful!\n\n"
                    "Your appointment with {name} on {date} at {time} has been confirmed.\n\n"
                    "Thank you for your booking!"
                ).format(
                    name=staff_name,
                    date=booking.booking_date.strftime("%Y-%m-%d"),
                    time=booking.booking_date.strftime("%H:%M")
                )
            )
            return
    
    # If verification failed or booking not found
    await message.answer(
        _(
            "✅ Payment received, but there was an issue updating your booking.\n"
            "Please contact support with your payment ID: {payment_id}"
        ).format(payment_id=payment.telegram_payment_charge_id)
    )


def register_user_handlers(dp: Dispatcher):
    """
    Register all user-related handlers
    """
    # Basic commands
    dp.register_message_handler(cmd_start, Command("start"), state="*")
    dp.register_message_handler(cmd_help, Command("help"))
    dp.register_message_handler(cmd_language, Command("language"))
    dp.register_message_handler(cmd_book, Command("book"), state="*")
    dp.register_message_handler(cmd_my_bookings, Command("mybookings"))
    
    # Language selection
    dp.register_callback_query_handler(
        language_callback_handler,
        language_callback.filter()
    )
    
    # Booking process
    dp.register_callback_query_handler(
        staff_selection_handler,
        staff_callback.filter(),
        state=BookingStates.selecting_staff
    )
    dp.register_callback_query_handler(
        date_selection_handler,
        date_callback.filter(),
        state=BookingStates.selecting_date
    )
    dp.register_callback_query_handler(
        time_selection_handler,
        time_callback.filter(),
        state=BookingStates.selecting_time
    )
    dp.register_callback_query_handler(
        booking_confirmation_handler,
        Text(equals="confirm_booking"),
        state=BookingStates.confirming_booking
    )
    
    # Booking actions
    dp.register_callback_query_handler(
        booking_action_handler,
        booking_callback.filter()
    )
    
    # Payments
    dp.register_pre_checkout_query_handler(
        pre_checkout_handler
    )
    dp.register_message_handler(
        successful_payment_handler,
        content_types=ContentType.SUCCESSFUL_PAYMENT
    )