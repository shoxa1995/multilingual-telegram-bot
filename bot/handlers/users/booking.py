"""
Booking handlers for the Telegram bot.
Manages the appointment booking flow.
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.utils.exceptions import MessageNotModified

from bot.database import Session, User, Staff, Booking, BookingStatus
from bot.keyboards.reply import main_menu_keyboard, cancel_keyboard, contact_keyboard
from bot.keyboards.inline import (
    staff_selection_keyboard, staff_profile_keyboard, calendar_keyboard,
    time_slots_keyboard, confirmation_keyboard, staff_cb, date_cb, time_cb,
    confirm_cb, navigation_cb
)
from bot.middlewares.i18n import _, i18n
from bot.states.booking import BookingStates
from bot.utils.calendar import format_date_for_user
from bot.utils.zoom import create_zoom_meeting
from bot.utils.bitrix24 import create_bitrix_event
from bot.utils.payment import generate_payment_link, check_payment_status
from bot.utils.notify import notify_admin_about_booking

logger = logging.getLogger(__name__)

async def cmd_book(message: types.Message):
    """
    Handle /book command.
    Start the booking process.
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
    
    # Start booking process
    await message.answer(
        _("Please select a staff member to book an appointment with:"),
        reply_markup=staff_selection_keyboard()
    )

async def cancel_booking(message: types.Message, state: FSMContext):
    """
    Cancel the booking process.
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
    
    # Reset state
    await state.finish()
    
    # Send cancellation message
    await message.answer(
        _("Booking process cancelled. You can start again using /book command."),
        reply_markup=main_menu_keyboard(language)
    )

async def cancel_booking_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    Cancel the booking process from callback query.
    """
    # Get user language
    session = Session()
    try:
        user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()
        language = user.language if user else 'en'
    finally:
        session.close()
    
    # Set current locale
    i18n.current_locale = language
    
    # Reset state
    await state.finish()
    
    # Edit message to show cancellation
    try:
        await callback.message.edit_text(
            _("Booking process cancelled. You can start again using /book command.")
        )
    except MessageNotModified:
        pass
    
    # Answer callback
    await callback.answer()
    
    # Send main menu
    await callback.message.answer(
        _("You can make a new booking or check your existing ones:"),
        reply_markup=main_menu_keyboard(language)
    )

async def back_to_staff_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    Go back to staff selection.
    """
    # Answer callback
    await callback.answer()
    
    # Edit message to show staff selection
    await callback.message.edit_text(
        _("Please select a staff member to book an appointment with:"),
        reply_markup=staff_selection_keyboard()
    )

async def staff_selection_callback(callback: types.CallbackQuery, callback_data: Dict[str, Any], state: FSMContext):
    """
    Handle staff selection.
    """
    staff_id = int(callback_data["id"])
    action = callback_data["action"]
    
    # Answer callback
    await callback.answer()
    
    if action == "select":
        # Get staff information
        session = Session()
        try:
            staff = session.query(Staff).filter(Staff.id == staff_id).first()
            
            if not staff:
                await callback.message.edit_text(
                    _("Staff member not found. Please try again."),
                    reply_markup=staff_selection_keyboard()
                )
                return
                
            # Get user language
            user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()
            language = user.language if user else 'en'
            
            # Set current locale
            i18n.current_locale = language
            
            # Store selected staff in state
            await state.update_data(staff_id=staff_id)
            
            # Get description in user's language
            description_field = f"description_{language}"
            description = getattr(staff, description_field, staff.description_en)
            
            # Format price
            price_formatted = f"{staff.price/100:.2f}" if staff.price else "Free"
            
            # Show staff profile
            profile_text = _(
                "<b>{name}</b>\n\n"
                "{description}\n\n"
                "<b>Price:</b> {price}"
            ).format(
                name=staff.name,
                description=description or _("No description available."),
                price=price_formatted
            )
            
            # If staff has photo, send photo with caption
            if staff.photo_url:
                # We'll just send a message here since we can't send photos directly
                # In a real implementation, you would send a photo with the profile text
                await callback.message.edit_text(
                    f"{profile_text}\n\n{_('Photo available')}: {staff.photo_url}",
                    reply_markup=staff_profile_keyboard(staff_id),
                    parse_mode=types.ParseMode.HTML
                )
            else:
                # Send text only
                await callback.message.edit_text(
                    profile_text,
                    reply_markup=staff_profile_keyboard(staff_id),
                    parse_mode=types.ParseMode.HTML
                )
                
        finally:
            session.close()
            
    elif action == "book":
        # Store selected staff in state
        await state.update_data(staff_id=staff_id)
        
        # Set state to calendar selection
        await BookingStates.select_date.set()
        
        # Show calendar
        await callback.message.edit_text(
            _("Please select a date for your appointment:"),
            reply_markup=calendar_keyboard(staff_id)
        )

async def calendar_navigation_callback(callback: types.CallbackQuery, callback_data: Dict[str, Any], state: FSMContext):
    """
    Handle calendar navigation (prev/next month).
    """
    direction = callback_data["direction"]
    parts = direction.split(':')
    
    if len(parts) != 2:
        await callback.answer(_("Invalid navigation data."))
        return
        
    nav_direction, staff_id = parts
    staff_id = int(staff_id)
    
    # Get the current calendar date from state if available
    data = await state.get_data()
    current_date = data.get("calendar_date")
    
    if not current_date:
        current_date = datetime.now()
    else:
        # Parse stored date
        current_date = datetime.fromisoformat(current_date)
    
    # Calculate new date based on direction
    if nav_direction == "prev":
        # Go to previous month
        if current_date.month == 1:
            new_date = datetime(current_date.year - 1, 12, 1)
        else:
            new_date = datetime(current_date.year, current_date.month - 1, 1)
    else:  # next
        # Go to next month
        if current_date.month == 12:
            new_date = datetime(current_date.year + 1, 1, 1)
        else:
            new_date = datetime(current_date.year, current_date.month + 1, 1)
    
    # Store the new date in state
    await state.update_data(calendar_date=new_date.isoformat())
    
    # Answer callback
    await callback.answer()
    
    # Show updated calendar
    await callback.message.edit_text(
        _("Please select a date for your appointment:"),
        reply_markup=calendar_keyboard(staff_id, new_date)
    )

async def date_selection_callback(callback: types.CallbackQuery, callback_data: Dict[str, Any], state: FSMContext):
    """
    Handle date selection from calendar.
    """
    action = callback_data["action"]
    
    if action == "select":
        year = int(callback_data["year"])
        month = int(callback_data["month"])
        day = int(callback_data["day"])
        
        # Store selected date in state
        selected_date = datetime(year, month, day)
        await state.update_data(
            selected_date=selected_date.isoformat(),
            selected_year=year,
            selected_month=month,
            selected_day=day
        )
        
        # Get staff ID from state
        data = await state.get_data()
        staff_id = data.get("staff_id")
        
        if not staff_id:
            await callback.message.edit_text(
                _("Error: Staff member not selected. Please start over."),
                reply_markup=staff_selection_keyboard()
            )
            return
            
        # Set state to time selection
        await BookingStates.select_time.set()
        
        # Answer callback
        await callback.answer()
        
        # Show time slots
        await callback.message.edit_text(
            _("Please select a time for your appointment on {date}:").format(
                date=format_date_for_user(selected_date)
            ),
            reply_markup=time_slots_keyboard(staff_id, year, month, day)
        )
    elif action == "back":
        # Go back to staff profile
        data = await state.get_data()
        staff_id = data.get("staff_id")
        
        if not staff_id:
            await callback.message.edit_text(
                _("Error: Staff member not selected. Please start over."),
                reply_markup=staff_selection_keyboard()
            )
            return
            
        # Set state to staff selection
        await BookingStates.select_staff.set()
        
        # Answer callback
        await callback.answer()
        
        # Show staff selection
        await callback.message.edit_text(
            _("Please select a staff member to book an appointment with:"),
            reply_markup=staff_selection_keyboard()
        )

async def time_selection_callback(callback: types.CallbackQuery, callback_data: Dict[str, Any], state: FSMContext):
    """
    Handle time selection.
    """
    action = callback_data["action"]
    
    if action == "select":
        hour = int(callback_data["hour"])
        minute = int(callback_data["minute"])
        
        # Get data from state
        data = await state.get_data()
        selected_date = datetime.fromisoformat(data.get("selected_date"))
        staff_id = data.get("staff_id")
        
        # Create booking datetime
        booking_datetime = selected_date.replace(hour=hour, minute=minute)
        
        # Store selected time in state
        await state.update_data(
            selected_hour=hour,
            selected_minute=minute,
            booking_datetime=booking_datetime.isoformat()
        )
        
        # Get staff and user information
        session = Session()
        try:
            staff = session.query(Staff).filter(Staff.id == staff_id).first()
            user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()
            
            if not staff or not user:
                await callback.message.edit_text(
                    _("Error: Could not find staff member or user. Please start over."),
                    reply_markup=staff_selection_keyboard()
                )
                return
                
            # Set current locale
            i18n.current_locale = user.language
            
            # Check if user has phone number
            if not user.phone_number:
                # We need to collect phone number before confirming booking
                await BookingStates.enter_phone.set()
                
                # Answer callback
                await callback.answer()
                
                # Ask for phone number
                await callback.message.edit_text(
                    _("Please provide your phone number to continue with booking.\n\n"
                      "You can use the button below to share your contact.")
                )
                
                await callback.message.answer(
                    _("Share your phone number:"),
                    reply_markup=contact_keyboard(user.language)
                )
                return
                
            # Set state to confirmation
            await BookingStates.confirm.set()
            
            # Format price
            price_formatted = f"{staff.price/100:.2f}" if staff.price else _("Free")
            
            # Answer callback
            await callback.answer()
            
            # Show booking summary
            summary_text = _(
                "<b>Booking Summary</b>\n\n"
                "<b>Staff:</b> {staff_name}\n"
                "<b>Date:</b> {date}\n"
                "<b>Time:</b> {time}\n"
                "<b>Price:</b> {price}\n\n"
                "Please confirm your booking."
            ).format(
                staff_name=staff.name,
                date=format_date_for_user(booking_datetime),
                time=f"{hour:02d}:{minute:02d}",
                price=price_formatted
            )
            
            await callback.message.edit_text(
                summary_text,
                reply_markup=confirmation_keyboard(),
                parse_mode=types.ParseMode.HTML
            )
            
        finally:
            session.close()

async def process_phone_number(message: types.Message, state: FSMContext):
    """
    Process phone number from user.
    """
    # Check for cancel command
    cancel_texts = {
        'en': 'Cancel',
        'ru': 'Отмена',
        'uz': 'Bekor qilish'
    }
    
    if message.text and message.text in cancel_texts.values():
        await cancel_booking(message, state)
        return
    
    # Get phone number
    if message.contact:
        phone_number = message.contact.phone_number
    else:
        # Try to parse phone number from text
        if not message.text:
            # Get user language
            session = Session()
            try:
                user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
                language = user.language if user else 'en'
            finally:
                session.close()
            
            # Set current locale
            i18n.current_locale = language
            
            await message.answer(
                _("Please provide a valid phone number or use the button to share your contact."),
                reply_markup=contact_keyboard(language)
            )
            return
            
        # Simple validation - should be improved in a real app
        phone_number = message.text.strip()
        if not phone_number.startswith('+') and not phone_number.isdigit():
            # Get user language
            session = Session()
            try:
                user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
                language = user.language if user else 'en'
            finally:
                session.close()
            
            # Set current locale
            i18n.current_locale = language
            
            await message.answer(
                _("Please provide a valid phone number."),
                reply_markup=contact_keyboard(language)
            )
            return
    
    # Save phone number to user
    session = Session()
    try:
        user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
        if user:
            user.phone_number = phone_number
            session.commit()
            
            # Set current locale
            i18n.current_locale = user.language
            
            # Get booking data
            data = await state.get_data()
            booking_datetime = datetime.fromisoformat(data.get("booking_datetime"))
            staff_id = data.get("staff_id")
            
            # Get staff
            staff = session.query(Staff).filter(Staff.id == staff_id).first()
            
            if not staff:
                await message.answer(
                    _("Error: Could not find staff member. Please start over."),
                    reply_markup=main_menu_keyboard(user.language)
                )
                await state.finish()
                return
                
            # Set state to confirmation
            await BookingStates.confirm.set()
            
            # Format price
            price_formatted = f"{staff.price/100:.2f}" if staff.price else _("Free")
            
            # Show booking summary
            summary_text = _(
                "<b>Booking Summary</b>\n\n"
                "<b>Staff:</b> {staff_name}\n"
                "<b>Date:</b> {date}\n"
                "<b>Time:</b> {time}\n"
                "<b>Price:</b> {price}\n\n"
                "Please confirm your booking."
            ).format(
                staff_name=staff.name,
                date=format_date_for_user(booking_datetime),
                time=f"{booking_datetime.hour:02d}:{booking_datetime.minute:02d}",
                price=price_formatted
            )
            
            await message.answer(
                summary_text,
                reply_markup=confirmation_keyboard(),
                parse_mode=types.ParseMode.HTML
            )
    finally:
        session.close()

async def confirmation_callback(callback: types.CallbackQuery, callback_data: Dict[str, Any], state: FSMContext):
    """
    Handle booking confirmation.
    """
    action = callback_data["action"]
    
    if action == "confirm":
        # Get data from state
        data = await state.get_data()
        booking_datetime = datetime.fromisoformat(data.get("booking_datetime"))
        staff_id = data.get("staff_id")
        
        # Get user and staff
        session = Session()
        try:
            user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()
            staff = session.query(Staff).filter(Staff.id == staff_id).first()
            
            if not user or not staff:
                await callback.message.edit_text(
                    _("Error: Could not find user or staff. Please start over."),
                    reply_markup=staff_selection_keyboard()
                )
                return
                
            # Set current locale
            i18n.current_locale = user.language
            
            # Create booking record
            booking = Booking(
                user_id=user.id,
                staff_id=staff_id,
                booking_date=booking_datetime,
                status=BookingStatus.PENDING,
                price=staff.price
            )
            session.add(booking)
            session.commit()
            
            # Store booking ID in state
            await state.update_data(booking_id=booking.id)
            
            # Answer callback
            await callback.answer()
            
            # Check if payment is required
            if staff.price > 0:
                # Update booking status
                booking.status = BookingStatus.PAYMENT_PENDING
                session.commit()
                
                # Set state to payment
                await BookingStates.payment.set()
                
                # Generate payment link
                payment_link = generate_payment_link(booking.id, staff.price, f"Appointment with {staff.name}")
                
                # Show payment instructions
                payment_text = _(
                    "<b>Payment Required</b>\n\n"
                    "Your booking has been created, but payment is required to confirm it.\n\n"
                    "<b>Amount:</b> {price}\n\n"
                    "Please use the link below to complete your payment:"
                ).format(
                    price=f"{staff.price/100:.2f}"
                )
                
                await callback.message.edit_text(
                    payment_text,
                    parse_mode=types.ParseMode.HTML
                )
                
                # Send payment button
                await callback.message.answer(
                    _("Click the button below to pay:"),
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton(
                            _("💳 Pay Now"),
                            url=payment_link
                        )
                    )
                )
                
                # Send instruction for after payment
                await callback.message.answer(
                    _("After completing payment, please press the button below to check payment status:"),
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton(
                            _("🔄 Check Payment Status"),
                            callback_data=f"check_payment:{booking.id}"
                        )
                    )
                )
            else:
                # No payment required, confirm booking directly
                # Update booking status
                booking.status = BookingStatus.CONFIRMED
                session.commit()
                
                # Create Zoom meeting
                meeting_info = await create_zoom_meeting(
                    f"Appointment with {staff.name}",
                    booking_datetime,
                    30  # Duration in minutes
                )
                
                if meeting_info:
                    booking.zoom_meeting_id = meeting_info.get("id")
                    booking.zoom_join_url = meeting_info.get("join_url")
                    session.commit()
                
                # Create Bitrix24 event
                event_id = await create_bitrix_event(
                    staff.bitrix_user_id,
                    f"Appointment with {user.first_name} {user.last_name or ''}",
                    booking_datetime,
                    30,  # Duration in minutes
                    user.phone_number,
                    booking.zoom_join_url
                )
                
                if event_id:
                    booking.bitrix_event_id = event_id
                    session.commit()
                
                # Reset state
                await state.finish()
                
                # Show confirmation
                confirmation_text = _(
                    "<b>Booking Confirmed</b>\n\n"
                    "Your appointment has been successfully booked.\n\n"
                    "<b>Staff:</b> {staff_name}\n"
                    "<b>Date:</b> {date}\n"
                    "<b>Time:</b> {time}\n"
                ).format(
                    staff_name=staff.name,
                    date=format_date_for_user(booking_datetime),
                    time=f"{booking_datetime.hour:02d}:{booking_datetime.minute:02d}"
                )
                
                # Add Zoom link if available
                if booking.zoom_join_url:
                    confirmation_text += _(
                        "\n<b>Zoom Meeting Link:</b>\n{zoom_link}"
                    ).format(
                        zoom_link=booking.zoom_join_url
                    )
                    
                await callback.message.edit_text(
                    confirmation_text,
                    parse_mode=types.ParseMode.HTML
                )
                
                # Send message with main menu
                await callback.message.answer(
                    _("Thank you for booking. You can view your bookings using /mybookings command."),
                    reply_markup=main_menu_keyboard(user.language)
                )
                
                # Notify admin about new booking
                await notify_admin_about_booking(booking)
                
        finally:
            session.close()
            
    elif action == "cancel":
        # Cancel booking
        await cancel_booking_callback(callback, state)

async def check_payment_status_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    Check payment status for a booking.
    """
    # Extract booking ID from callback data
    booking_id = int(callback.data.split(':')[1])
    
    # Get user
    session = Session()
    try:
        user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        
        if not user or not booking:
            await callback.answer(_("Booking not found."))
            return
            
        # Set current locale
        i18n.current_locale = user.language
        
        # Check payment status
        payment_status = await check_payment_status(booking.payment_id)
        
        if payment_status == "paid":
            # Payment successful, confirm booking
            booking.status = BookingStatus.CONFIRMED
            session.commit()
            
            # Get staff
            staff = session.query(Staff).filter(Staff.id == booking.staff_id).first()
            
            # Create Zoom meeting
            meeting_info = await create_zoom_meeting(
                f"Appointment with {staff.name if staff else 'Staff'}",
                booking.booking_date,
                30  # Duration in minutes
            )
            
            if meeting_info:
                booking.zoom_meeting_id = meeting_info.get("id")
                booking.zoom_join_url = meeting_info.get("join_url")
                session.commit()
            
            # Create Bitrix24 event
            event_id = await create_bitrix_event(
                staff.bitrix_user_id if staff else None,
                f"Appointment with {user.first_name} {user.last_name or ''}",
                booking.booking_date,
                30,  # Duration in minutes
                user.phone_number,
                booking.zoom_join_url
            )
            
            if event_id:
                booking.bitrix_event_id = event_id
                session.commit()
            
            # Reset state
            await state.finish()
            
            # Answer callback
            await callback.answer(_("Payment successful!"))
            
            # Show confirmation
            confirmation_text = _(
                "<b>Payment Successful</b>\n\n"
                "Your booking has been confirmed.\n\n"
                "<b>Staff:</b> {staff_name}\n"
                "<b>Date:</b> {date}\n"
                "<b>Time:</b> {time}\n"
            ).format(
                staff_name=staff.name if staff else _("Staff"),
                date=format_date_for_user(booking.booking_date),
                time=f"{booking.booking_date.hour:02d}:{booking.booking_date.minute:02d}"
            )
            
            # Add Zoom link if available
            if booking.zoom_join_url:
                confirmation_text += _(
                    "\n<b>Zoom Meeting Link:</b>\n{zoom_link}"
                ).format(
                    zoom_link=booking.zoom_join_url
                )
                
            await callback.message.edit_text(
                confirmation_text,
                parse_mode=types.ParseMode.HTML
            )
            
            # Send message with main menu
            await callback.message.answer(
                _("Thank you for booking. You can view your bookings using /mybookings command."),
                reply_markup=main_menu_keyboard(user.language)
            )
            
            # Notify admin about new booking
            await notify_admin_about_booking(booking)
            
        elif payment_status == "pending":
            # Payment still pending
            await callback.answer(_("Payment is still pending. Please wait or try again later."))
        else:
            # Payment failed or cancelled
            await callback.answer(_("Payment failed or was cancelled. Please try again."))
            
            # Give option to try again
            await callback.message.edit_text(
                _("Payment failed or was cancelled. Would you like to try again?"),
                reply_markup=types.InlineKeyboardMarkup(row_width=2).add(
                    types.InlineKeyboardButton(
                        _("💳 Try Again"),
                        callback_data=f"retry_payment:{booking_id}"
                    ),
                    types.InlineKeyboardButton(
                        _("❌ Cancel Booking"),
                        callback_data="cancel"
                    )
                )
            )
            
    finally:
        session.close()

async def retry_payment_callback(callback: types.CallbackQuery, state: FSMContext):
    """
    Retry payment for a booking.
    """
    # Extract booking ID from callback data
    booking_id = int(callback.data.split(':')[1])
    
    # Get user and booking
    session = Session()
    try:
        user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()
        booking = session.query(Booking).filter(Booking.id == booking_id).first()
        
        if not user or not booking:
            await callback.answer(_("Booking not found."))
            return
            
        # Set current locale
        i18n.current_locale = user.language
        
        # Get staff
        staff = session.query(Staff).filter(Staff.id == booking.staff_id).first()
        
        if not staff:
            await callback.answer(_("Staff not found."))
            return
            
        # Set state to payment
        await BookingStates.payment.set()
        await state.update_data(booking_id=booking.id)
        
        # Generate new payment link
        payment_link = generate_payment_link(booking.id, staff.price, f"Appointment with {staff.name}")
        
        # Answer callback
        await callback.answer()
        
        # Show payment instructions
        payment_text = _(
            "<b>Payment Required</b>\n\n"
            "Your booking has been created, but payment is required to confirm it.\n\n"
            "<b>Amount:</b> {price}\n\n"
            "Please use the link below to complete your payment:"
        ).format(
            price=f"{staff.price/100:.2f}"
        )
        
        await callback.message.edit_text(
            payment_text,
            parse_mode=types.ParseMode.HTML
        )
        
        # Send payment button
        await callback.message.answer(
            _("Click the button below to pay:"),
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    _("💳 Pay Now"),
                    url=payment_link
                )
            )
        )
        
        # Send instruction for after payment
        await callback.message.answer(
            _("After completing payment, please press the button below to check payment status:"),
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(
                    _("🔄 Check Payment Status"),
                    callback_data=f"check_payment:{booking.id}"
                )
            )
        )
        
    finally:
        session.close()

def register_booking_handlers(dp: Dispatcher):
    """
    Register booking handlers.
    """
    # Book command
    dp.register_message_handler(cmd_book, Command("book"), state="*")
    
    # Cancel booking
    dp.register_message_handler(cancel_booking, lambda msg: msg.text in ['❌ Cancel', '❌ Отмена', '❌ Bekor qilish'], state="*")
    dp.register_callback_query_handler(cancel_booking_callback, lambda c: c.data == 'cancel', state="*")
    
    # Back to staff
    dp.register_callback_query_handler(back_to_staff_callback, lambda c: c.data == 'back_to_staff', state="*")
    
    # Staff selection
    dp.register_callback_query_handler(staff_selection_callback, staff_cb.filter(), state="*")
    
    # Calendar navigation
    dp.register_callback_query_handler(calendar_navigation_callback, navigation_cb.filter(), state=BookingStates.select_date)
    
    # Date selection
    dp.register_callback_query_handler(date_selection_callback, date_cb.filter(), state=BookingStates.select_date)
    
    # Time selection
    dp.register_callback_query_handler(time_selection_callback, time_cb.filter(), state=BookingStates.select_time)
    
    # Phone number collection
    dp.register_message_handler(process_phone_number, content_types=[types.ContentType.CONTACT, types.ContentType.TEXT], state=BookingStates.enter_phone)
    
    # Booking confirmation
    dp.register_callback_query_handler(confirmation_callback, confirm_cb.filter(), state=BookingStates.confirm)
    
    # Payment status check
    dp.register_callback_query_handler(check_payment_status_callback, lambda c: c.data.startswith('check_payment:'), state=BookingStates.payment)
    
    # Retry payment
    dp.register_callback_query_handler(retry_payment_callback, lambda c: c.data.startswith('retry_payment:'), state="*")
