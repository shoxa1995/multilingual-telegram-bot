"""
Booking handlers for the Telegram bot.
Manages the appointment booking flow.
"""
import logging
from datetime import datetime, timedelta
import uuid
from typing import Dict, Any, Optional

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramAPIError

from bot.database import (
    get_or_create_user_async, get_user_language_async, 
    get_active_staff_async, get_staff_by_id_async, 
    get_staff_schedule_async, update_user_language_async,
    create_booking_async, get_booking_by_id_async,
    update_booking_payment_pending_async, update_booking_payment_completed_async,
    cancel_booking_async
)
from bot.keyboards.reply import main_menu_keyboard, cancel_keyboard, contact_keyboard
from bot.keyboards.inline import (
    staff_selection_keyboard, staff_profile_keyboard, calendar_keyboard,
    time_slots_keyboard, confirmation_keyboard
)
from bot.middlewares.i18n import _, i18n
from bot.states.booking import BookingStates
from bot.utils.calendar import format_date_for_user
from bot.utils.zoom import create_zoom_meeting
from bot.utils.bitrix24 import create_bitrix_event
from bot.utils.payment import generate_payment_link, check_payment_status, create_invoice
from bot.utils.notify import notify_admin_about_booking

logger = logging.getLogger(__name__)

async def cmd_book(message: Message, state: FSMContext):
    """
    Handle /book command.
    Start the booking process.
    """
    # Get user language
    user = await get_or_create_user_async({
        'id': message.from_user.id,
        'first_name': message.from_user.first_name,
        'last_name': message.from_user.last_name,
        'username': message.from_user.username
    })
    language = user.language if user else 'en'
    
    # Set current locale
    i18n.current_locale = language
    
    # Set state
    await state.set_state(BookingStates.select_staff)
    
    # Start booking process
    await message.answer(
        _("Please select a staff member to book an appointment with:"),
        reply_markup=await staff_selection_keyboard()
    )

async def cancel_booking(message: Message, state: FSMContext):
    """
    Cancel the booking process.
    """
    # Get user language
    language = await get_user_language_async(message.from_user.id)
    
    # Set current locale
    i18n.current_locale = language
    
    # Reset state
    await state.clear()
    
    # Send cancellation message
    await message.answer(
        _("Booking process cancelled. You can start again using /book command."),
        reply_markup=main_menu_keyboard(language)
    )

async def cancel_booking_callback(callback: CallbackQuery, state: FSMContext):
    """
    Cancel the booking process from callback query.
    """
    # Get user language
    language = await get_user_language_async(callback.from_user.id)
    
    # Set current locale
    i18n.current_locale = language
    
    # Reset state
    await state.clear()
    
    # Edit message to show cancellation
    try:
        await callback.message.edit_text(
            _("Booking process cancelled. You can start again using /book command.")
        )
    except TelegramAPIError:
        pass
    
    # Answer callback
    await callback.answer()
    
    # Send main menu
    await callback.message.answer(
        _("You can make a new booking or check your existing ones:"),
        reply_markup=main_menu_keyboard(language)
    )

async def back_to_staff_callback(callback: CallbackQuery, state: FSMContext):
    """
    Go back to staff selection.
    """
    # Answer callback
    await callback.answer()
    
    # Edit message to show staff selection
    await callback.message.edit_text(
        _("Please select a staff member to book an appointment with:"),
        reply_markup=await staff_selection_keyboard()
    )

async def staff_selection_callback(callback: CallbackQuery, state: FSMContext):
    """
    Handle staff selection.
    """
    # Extract data from callback
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer(_("Invalid staff selection data."))
        return
    
    action = parts[1]
    staff_id = int(parts[2])
    
    # Answer callback
    await callback.answer()
    
    if action == "select":
        # Get staff information
        staff = await get_staff_by_id_async(staff_id)
        
        if not staff:
            await callback.message.edit_text(
                _("Staff member not found. Please try again."),
                reply_markup=await staff_selection_keyboard()
            )
            return
            
        # Get user language
        language = await get_user_language_async(callback.from_user.id)
        
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
                parse_mode="HTML"
            )
        else:
            # Send text only
            await callback.message.edit_text(
                profile_text,
                reply_markup=staff_profile_keyboard(staff_id),
                parse_mode="HTML"
            )
            
    elif action == "book":
        # Store selected staff in state
        await state.update_data(staff_id=staff_id)
        
        # Set state to calendar selection
        await state.set_state(BookingStates.select_date)
        
        # Show calendar
        await callback.message.edit_text(
            _("Please select a date for your appointment:"),
            reply_markup=calendar_keyboard(staff_id)
        )

async def calendar_navigation_callback(callback: CallbackQuery, state: FSMContext):
    """
    Handle calendar navigation (prev/next month).
    """
    # Extract data from callback
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer(_("Invalid navigation data."))
        return
    
    nav_direction = parts[1]
    staff_id = int(parts[2])
    
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

async def date_selection_callback(callback: CallbackQuery, state: FSMContext):
    """
    Handle date selection from calendar.
    """
    # Extract data from callback
    parts = callback.data.split(":")
    if len(parts) < 5:
        await callback.answer(_("Invalid date selection data."))
        return
    
    action = parts[1]
    
    if action == "select":
        year = int(parts[2])
        month = int(parts[3])
        day = int(parts[4])
        
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
                reply_markup=await staff_selection_keyboard()
            )
            return
            
        # Set state to time selection
        await state.set_state(BookingStates.select_time)
        
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
                reply_markup=await staff_selection_keyboard()
            )
            return
            
        # Set state to staff selection
        await state.set_state(BookingStates.select_staff)
        
        # Answer callback
        await callback.answer()
        
        # Show staff selection
        await callback.message.edit_text(
            _("Please select a staff member to book an appointment with:"),
            reply_markup=await staff_selection_keyboard()
        )

async def time_selection_callback(callback: CallbackQuery, state: FSMContext):
    """
    Handle time selection.
    """
    # Extract data from callback
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer(_("Invalid time selection data."))
        return
    
    action = parts[1]
    
    if action == "select":
        hour = int(parts[2])
        minute = int(parts[3])
        
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
        staff = await get_staff_by_id_async(staff_id)
        user = await get_or_create_user_async({
            'id': callback.from_user.id,
            'first_name': callback.from_user.first_name,
            'last_name': callback.from_user.last_name,
            'username': callback.from_user.username
        })
        
        if not staff or not user:
            await callback.message.edit_text(
                _("Error: Could not find staff member or user. Please start over."),
                reply_markup=await staff_selection_keyboard()
            )
            return
            
        # Set current locale
        i18n.current_locale = user.language
        
        # Check if user has phone number
        if not user.phone_number:
            # We need to collect phone number before confirming booking
            await state.set_state(BookingStates.enter_phone)
            
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
        await state.set_state(BookingStates.confirm)
        
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
            parse_mode="HTML"
        )

async def process_phone_number(message: Message, state: FSMContext):
    """
    Process phone number from user.
    """
    # Check for cancel command
    cancel_texts = [
        'Cancel', 'Отмена', 'Bekor qilish',
        '❌ Cancel', '❌ Отмена', '❌ Bekor qilish'
    ]
    
    if message.text and message.text in cancel_texts:
        await cancel_booking(message, state)
        return
    
    # Get phone number
    if message.content_type == "contact":
        phone_number = message.contact.phone_number
    else:
        # Try to parse phone number from text
        if not message.text:
            # Get user language
            language = await get_user_language_async(message.from_user.id)
            
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
            language = await get_user_language_async(message.from_user.id)
            
            # Set current locale
            i18n.current_locale = language
            
            await message.answer(
                _("Please provide a valid phone number in international format (+998XXXXXXXXX) or use the button to share your contact."),
                reply_markup=contact_keyboard(language)
            )
            return
    
    # Save phone number to database
    # In a real application, you would update the user's phone number in the database
    # For this example, we'll just store it in state
    await state.update_data(phone_number=phone_number)
    
    # Get data from state
    data = await state.get_data()
    staff_id = data.get("staff_id")
    booking_datetime = datetime.fromisoformat(data.get("booking_datetime"))
    
    # Get staff information
    staff = await get_staff_by_id_async(staff_id)
    
    if not staff:
        # Get user language
        language = await get_user_language_async(message.from_user.id)
        
        # Set current locale
        i18n.current_locale = language
        
        await message.answer(
            _("Error: Could not find staff member. Please start over."),
            reply_markup=main_menu_keyboard(language)
        )
        await state.clear()
        return
    
    # Set state to confirmation
    await state.set_state(BookingStates.confirm)
    
    # Format price
    price_formatted = f"{staff.price/100:.2f}" if staff.price else _("Free")
    
    # Get user language
    language = await get_user_language_async(message.from_user.id)
    
    # Set current locale
    i18n.current_locale = language
    
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
        parse_mode="HTML"
    )

async def confirmation_callback(callback: CallbackQuery, state: FSMContext):
    """
    Handle booking confirmation.
    """
    # Extract data from callback
    parts = callback.data.split(":")
    if len(parts) < 2:
        await callback.answer(_("Invalid confirmation data."))
        return
    
    action = parts[1]
    
    if action == "confirm":
        # Get data from state
        data = await state.get_data()
        staff_id = data.get("staff_id")
        booking_datetime = datetime.fromisoformat(data.get("booking_datetime"))
        
        # Get staff and user information
        staff = await get_staff_by_id_async(staff_id)
        user = await get_or_create_user_async({
            'id': callback.from_user.id,
            'first_name': callback.from_user.first_name,
            'last_name': callback.from_user.last_name,
            'username': callback.from_user.username
        })
        
        if not staff or not user:
            await callback.message.edit_text(
                _("Error: Could not find staff member or user. Please start over."),
                reply_markup=await staff_selection_keyboard()
            )
            return
        
        # Set current locale
        i18n.current_locale = user.language
        
        # Create booking in database
        booking = await create_booking_async(
            user_id=user.id,
            staff_id=staff.id,
            booking_date=booking_datetime,
            duration_minutes=30,
            price=staff.price
        )
        
        if not booking:
            await callback.message.edit_text(
                _("Error: Could not create booking. Please try again later."),
                reply_markup=main_menu_keyboard(user.language)
            )
            await state.clear()
            return
        
        # Answer callback
        await callback.answer()
        
        # Check if payment is required
        if staff.price > 0:
            # Create a unique invoice payload
            invoice_payload = f"booking:{booking.id}"
            
            # Update booking with invoice payload
            await update_booking_payment_pending_async(booking.id, invoice_payload)
            
            # Set state to payment
            await state.set_state(BookingStates.payment)
            
            # Show payment instructions
            payment_text = _(
                "<b>Payment Required</b>\n\n"
                "Your booking has been created, but payment is required to confirm it."
            )
            
            await callback.message.edit_text(
                payment_text,
                parse_mode="HTML"
            )
            
            # Get bot instance directly from the callback
            current_bot = callback.bot
            
            # Send payment invoice
            payment_description = _("Appointment with {staff_name} on {date}").format(
                staff_name=staff.name,
                date=booking.booking_date.strftime("%Y-%m-%d %H:%M")
            )
            
            try:
                # Send the invoice directly
                await create_invoice(
                    bot=current_bot,
                    chat_id=callback.from_user.id,
                    booking_id=booking.id,
                    amount=staff.price,
                    description=payment_description,
                    title=_("Appointment Booking")
                )
                
                # Also provide a backup method to check payment status
                await callback.message.answer(
                    _("If you close this payment dialog, you can check your payment status using this button:"),
                    reply_markup={
                        "inline_keyboard": [[{
                            "text": _("Check Payment Status"),
                            "callback_data": f"check_payment:{booking.id}"
                        }]]
                    }
                )
            except Exception as e:
                logger.exception(f"Failed to create invoice: {e}")
                
                # Fallback to old payment method
                payment_link = generate_payment_link(booking.id, staff.price, f"Appointment with {staff.name}")
                
                await callback.message.answer(
                    _("Unable to create payment invoice. Please contact support or try again later."),
                    reply_markup={
                        "inline_keyboard": [[{
                            "text": _("Check Payment Status"),
                            "callback_data": f"check_payment:{booking.id}"
                        }]]
                    }
                )
        else:
            # No payment required, confirm booking directly
            # Create Zoom meeting
            zoom_meeting_id, zoom_join_url = await create_zoom_meeting(
                topic=f"Appointment with {staff.name}",
                start_time=booking_datetime,
                duration_minutes=30,
                email=user.email  # Assuming user has email
            )
            
            # Create Bitrix24 event
            bitrix_event_id = await create_bitrix_event(
                title=f"Appointment with {user.first_name}",
                description=f"Telegram user: @{user.username}",
                start_time=booking_datetime,
                duration_minutes=30,
                responsible_id=staff.bitrix_user_id
            )
            
            # Update booking to confirmed
            # In a real application, you would update the booking with Zoom and Bitrix24 information
            # For this example, we'll just complete the booking
            await update_booking_payment_completed_async(
                booking_id=booking.id,
                payment_id="free"
            )
            
            # Notify admin about new booking
            await notify_admin_about_booking(booking)
            
            # Send confirmation message
            confirmation_text = _(
                "<b>Booking Confirmed</b>\n\n"
                "Your appointment has been scheduled successfully!\n\n"
                "<b>Staff:</b> {staff_name}\n"
                "<b>Date:</b> {date}\n"
                "<b>Time:</b> {time}\n"
                "<b>Status:</b> Confirmed\n\n"
                "Thank you for booking with us. You can manage your bookings using /my_bookings command."
            ).format(
                staff_name=staff.name,
                date=format_date_for_user(booking_datetime),
                time=f"{booking_datetime.hour:02d}:{booking_datetime.minute:02d}"
            )
            
            await callback.message.edit_text(
                confirmation_text,
                parse_mode="HTML"
            )
            
            # Clear state
            await state.clear()
    elif action == "cancel":
        await cancel_booking_callback(callback, state)

async def check_payment_status_callback(callback: CallbackQuery, state: FSMContext):
    """
    Check payment status for a booking.
    """
    # Extract booking ID from callback data
    parts = callback.data.split(":")
    if len(parts) < 2:
        await callback.answer(_("Invalid payment check data."))
        return
    
    booking_id = int(parts[1])
    
    # Get booking from database
    booking = await get_booking_by_id_async(booking_id)
    
    if not booking:
        await callback.answer(_("Booking not found."))
        return
    
    # Answer callback
    await callback.answer(_("Checking payment status..."), show_alert=True)
    
    # Get user language
    language = await get_user_language_async(callback.from_user.id)
    
    # Set current locale
    i18n.current_locale = language
    
    # Check payment status
    payment_status = await check_payment_status(booking.payment_id)
    
    if payment_status == "paid":
        # Update booking status to confirmed
        await update_booking_payment_completed_async(
            booking_id=booking.id,
            payment_id=booking.payment_id or "paid"
        )
        
        # Get staff information
        staff = await get_staff_by_id_async(booking.staff_id)
        
        # Create Zoom meeting
        zoom_meeting_id, zoom_join_url = await create_zoom_meeting(
            topic=f"Appointment with {staff.name}",
            start_time=booking.booking_date,
            duration_minutes=booking.duration_minutes,
            email=None  # You might want to get user email or use a default
        )
        
        # Create Bitrix24 event
        bitrix_event_id = await create_bitrix_event(
            title=f"Appointment with {booking.user.first_name}",
            description=f"Telegram user: @{booking.user.username}",
            start_time=booking.booking_date,
            duration_minutes=booking.duration_minutes,
            responsible_id=staff.bitrix_user_id
        )
        
        # Notify admin about new confirmed booking
        await notify_admin_about_booking(booking)
        
        # Send confirmation message
        confirmation_text = _(
            "<b>Payment Successful</b>\n\n"
            "Your payment has been received and your appointment is now confirmed!\n\n"
            "<b>Staff:</b> {staff_name}\n"
            "<b>Date:</b> {date}\n"
            "<b>Time:</b> {time}\n"
            "<b>Status:</b> Confirmed\n\n"
            "Thank you for booking with us. You can manage your bookings using /my_bookings command."
        ).format(
            staff_name=staff.name,
            date=format_date_for_user(booking.booking_date),
            time=f"{booking.booking_date.hour:02d}:{booking.booking_date.minute:02d}"
        )
        
        await callback.message.edit_text(
            confirmation_text,
            parse_mode="HTML"
        )
        
        # Clear state
        await state.clear()
    elif payment_status == "pending":
        await callback.message.edit_text(
            _(
                "<b>Payment Pending</b>\n\n"
                "Your payment is still being processed. Please check again in a few minutes.\n\n"
                "If you haven't completed the payment yet, please use the button below."
            ),
            parse_mode="HTML",
            reply_markup={
                "inline_keyboard": [
                    [{
                        "text": _("Check Again"),
                        "callback_data": f"check_payment:{booking_id}"
                    }],
                    [{
                        "text": _("Retry Payment"),
                        "callback_data": f"retry_payment:{booking_id}"
                    }]
                ]
            }
        )
    else:  # failed
        await callback.message.edit_text(
            _(
                "<b>Payment Failed</b>\n\n"
                "We couldn't confirm your payment. Please try again.\n\n"
                "If you're having trouble, you can cancel this booking and start over."
            ),
            parse_mode="HTML",
            reply_markup={
                "inline_keyboard": [
                    [{
                        "text": _("Retry Payment"),
                        "callback_data": f"retry_payment:{booking_id}"
                    }],
                    [{
                        "text": _("Cancel Booking"),
                        "callback_data": "cancel"
                    }]
                ]
            }
        )

async def retry_payment_callback(callback: CallbackQuery, state: FSMContext):
    """
    Retry payment for a booking.
    """
    # Extract booking ID from callback data
    parts = callback.data.split(":")
    if len(parts) < 2:
        await callback.answer(_("Invalid retry payment data."))
        return
    
    booking_id = int(parts[1])
    
    # Get booking from database
    booking = await get_booking_by_id_async(booking_id)
    
    if not booking:
        await callback.answer(_("Booking not found."))
        return
    
    # Get staff information
    staff = await get_staff_by_id_async(booking.staff_id)
    
    if not staff:
        await callback.answer(_("Staff member not found."))
        return
    
    # Get user language
    language = await get_user_language_async(callback.from_user.id)
    
    # Set current locale
    i18n.current_locale = language
    
    # Answer callback
    await callback.answer()
    
    # Set state to payment
    await state.set_state(BookingStates.payment)
    
    # Show payment instructions
    payment_text = _(
        "<b>Payment Required</b>\n\n"
        "Your booking has been created, but payment is required to confirm it."
    )
    
    await callback.message.edit_text(
        payment_text,
        parse_mode="HTML"
    )
    
    # Get bot instance directly from the callback
    current_bot = callback.bot
    
    # Send payment invoice
    payment_description = _("Appointment with {staff_name} on {date}").format(
        staff_name=staff.name,
        date=booking.booking_date.strftime("%Y-%m-%d %H:%M")
    )
    
    try:
        # Send the invoice directly
        await create_invoice(
            bot=current_bot,
            chat_id=callback.from_user.id,
            booking_id=booking.id,
            amount=staff.price,
            description=payment_description,
            title=_("Appointment Booking")
        )
        
        # Also provide a backup method to check payment status
        await callback.message.answer(
            _("If you close this payment dialog, you can check your payment status using this button:"),
            reply_markup={
                "inline_keyboard": [[{
                    "text": _("Check Payment Status"),
                    "callback_data": f"check_payment:{booking.id}"
                }]]
            }
        )
    except Exception as e:
        logger.exception(f"Failed to create invoice: {e}")
        
        # Fallback to old payment method
        payment_link = generate_payment_link(booking.id, staff.price, f"Appointment with {staff.name}")
        
        await callback.message.answer(
            _("Unable to create payment invoice. Please contact support or try again later."),
            reply_markup={
                "inline_keyboard": [[{
                    "text": _("Check Payment Status"),
                    "callback_data": f"check_payment:{booking.id}"
                }]]
            }
        )

def register_booking_handlers(router: Router):
    """
    Register booking handlers.
    """
    # Booking start
    router.message.register(cmd_book, Command("book"))
    
    # Cancel booking
    router.message.register(cancel_booking, F.text.in_([
        '❌ Cancel', '❌ Отмена', '❌ Bekor qilish', 
        'Cancel', 'Отмена', 'Bekor qilish'
    ]))
    router.callback_query.register(cancel_booking_callback, F.data == "cancel")
    
    # Staff selection navigation
    router.callback_query.register(back_to_staff_callback, F.data == "back_to_staff")
    
    # Staff selection
    router.callback_query.register(staff_selection_callback, F.data.startswith("staff:"))
    
    # Calendar navigation
    router.callback_query.register(calendar_navigation_callback, F.data.startswith("nav:"), BookingStates.select_date)
    
    # Date selection
    router.callback_query.register(date_selection_callback, F.data.startswith("date:"), BookingStates.select_date)
    
    # Time selection
    router.callback_query.register(time_selection_callback, F.data.startswith("time:"), BookingStates.select_time)
    
    # Process phone number
    router.message.register(process_phone_number, BookingStates.enter_phone)
    
    # Confirmation
    router.callback_query.register(confirmation_callback, F.data.startswith("confirm:"), BookingStates.confirm)
    
    # Payment status check
    router.callback_query.register(check_payment_status_callback, F.data.startswith("check_payment:"), BookingStates.payment)
    
    # Retry payment
    router.callback_query.register(retry_payment_callback, F.data.startswith("retry_payment:"))