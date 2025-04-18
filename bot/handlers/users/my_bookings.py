"""
My bookings handler for the Telegram bot.
Allows users to view, reschedule, and cancel their bookings.
"""
from datetime import datetime
from typing import Dict, Any

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.utils.exceptions import MessageNotModified

from bot.database import Session, User, Booking, Staff, BookingStatus
from bot.keyboards.reply import main_menu_keyboard
from bot.keyboards.inline import (
    my_bookings_keyboard, booking_actions_keyboard, calendar_keyboard,
    time_slots_keyboard, cancel_booking_confirmation_keyboard,
    booking_cb, navigation_cb, date_cb, time_cb
)
from bot.middlewares.i18n import _, i18n
from bot.states.booking import RescheduleStates
from bot.utils.calendar import format_date_for_user
from bot.utils.zoom import update_zoom_meeting
from bot.utils.bitrix24 import update_bitrix_event
from bot.utils.notify import notify_admin_about_reschedule, notify_admin_about_cancellation

async def cmd_my_bookings(message: types.Message, state: FSMContext):
    """
    Handle /mybookings command.
    Show a list of user's bookings.
    """
    # Reset state
    await state.finish()
    
    # Get user bookings
    session = Session()
    try:
        user = session.query(User).filter(User.telegram_id == message.from_user.id).first()
        
        if not user:
            await message.answer(
                "You don't have any bookings yet. Please use /book to make a booking."
            )
            return
            
        # Set current locale
        i18n.current_locale = user.language
        
        # Get active bookings
        bookings = session.query(Booking).join(Staff).filter(
            Booking.user_id == user.id,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PAYMENT_PENDING]),
            Booking.booking_date >= datetime.now()
        ).order_by(Booking.booking_date).all()
        
        if not bookings:
            await message.answer(
                _("You don't have any upcoming bookings. Use /book to make a new booking."),
                reply_markup=main_menu_keyboard(user.language)
            )
            return
            
        # Show booking list
        await message.answer(
            _("Your upcoming bookings:"),
            reply_markup=my_bookings_keyboard(bookings)
        )
        
    finally:
        session.close()

async def view_booking_callback(callback: types.CallbackQuery, callback_data: Dict[str, Any], state: FSMContext):
    """
    Show details of a selected booking.
    """
    booking_id = int(callback_data["id"])
    action = callback_data["action"]
    
    # Answer callback
    await callback.answer()
    
    if action == "view":
        if booking_id == 0:
            # This is a back action to the bookings list
            await cmd_my_bookings(callback.message, state)
            return
            
        # Get booking details
        session = Session()
        try:
            user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()
            booking = session.query(Booking).join(Staff).filter(
                Booking.id == booking_id,
                Booking.user_id == user.id
            ).first()
            
            if not booking:
                await callback.message.edit_text(
                    _("Booking not found."),
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton(_("Back to Bookings"), callback_data=booking_cb.new(id=0, action="back"))
                    )
                )
                return
                
            # Set current locale
            i18n.current_locale = user.language
            
            # Format booking details
            staff_name = booking.staff.name if booking.staff else _("Unknown Staff")
            booking_date = format_date_for_user(booking.booking_date)
            booking_time = f"{booking.booking_date.hour:02d}:{booking.booking_date.minute:02d}"
            
            status_texts = {
                BookingStatus.PENDING: _("⏳ Pending"),
                BookingStatus.PAYMENT_PENDING: _("💰 Payment Pending"),
                BookingStatus.CONFIRMED: _("✅ Confirmed"),
                BookingStatus.CANCELLED: _("❌ Cancelled"),
                BookingStatus.COMPLETED: _("✓ Completed")
            }
            
            status_text = status_texts.get(booking.status, _("Unknown"))
            
            details_text = _(
                "<b>Booking Details</b>\n\n"
                "<b>Staff:</b> {staff_name}\n"
                "<b>Date:</b> {date}\n"
                "<b>Time:</b> {time}\n"
                "<b>Status:</b> {status}\n"
            ).format(
                staff_name=staff_name,
                date=booking_date,
                time=booking_time,
                status=status_text
            )
            
            # Add Zoom link if available and booking is confirmed
            if booking.status == BookingStatus.CONFIRMED and booking.zoom_join_url:
                details_text += _(
                    "\n<b>Zoom Meeting Link:</b>\n{zoom_link}\n"
                ).format(
                    zoom_link=booking.zoom_join_url
                )
                
            # Show booking details
            await callback.message.edit_text(
                details_text,
                reply_markup=booking_actions_keyboard(booking_id),
                parse_mode=types.ParseMode.HTML
            )
            
        finally:
            session.close()
            
    elif action == "back":
        # Go back to bookings list
        await cmd_my_bookings(callback.message, state)
        
    elif action == "reschedule":
        # Store booking ID in state
        await state.update_data(reschedule_booking_id=booking_id)
        
        # Set state to reschedule date selection
        await RescheduleStates.select_date.set()
        
        # Get booking and staff info
        session = Session()
        try:
            booking = session.query(Booking).filter(Booking.id == booking_id).first()
            
            if not booking:
                await callback.message.edit_text(
                    _("Booking not found."),
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton(_("Back to Bookings"), callback_data=booking_cb.new(id=0, action="back"))
                    )
                )
                return
                
            staff_id = booking.staff_id
            
            # Show calendar for rescheduling
            await callback.message.edit_text(
                _("Please select a new date for your appointment:"),
                reply_markup=calendar_keyboard(staff_id)
            )
            
        finally:
            session.close()
            
    elif action == "cancel":
        # Show cancellation confirmation
        await callback.message.edit_text(
            _("Are you sure you want to cancel this booking?"),
            reply_markup=cancel_booking_confirmation_keyboard(booking_id)
        )
        
    elif action == "confirm_cancel":
        # Cancel the booking
        session = Session()
        try:
            user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()
            booking = session.query(Booking).filter(
                Booking.id == booking_id,
                Booking.user_id == user.id
            ).first()
            
            if not booking:
                await callback.message.edit_text(
                    _("Booking not found."),
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton(_("Back to Bookings"), callback_data=booking_cb.new(id=0, action="back"))
                    )
                )
                return
                
            # Set current locale
            i18n.current_locale = user.language
            
            # Update booking status
            booking.status = BookingStatus.CANCELLED
            session.commit()
            
            # Notify admin about cancellation
            await notify_admin_about_cancellation(booking)
            
            # Show confirmation
            await callback.message.edit_text(
                _("Your booking has been cancelled."),
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton(_("Back to Bookings"), callback_data=booking_cb.new(id=0, action="back"))
                )
            )
            
        finally:
            session.close()

async def reschedule_date_callback(callback: types.CallbackQuery, callback_data: Dict[str, Any], state: FSMContext):
    """
    Handle date selection for rescheduling.
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
        
        # Get booking ID from state
        data = await state.get_data()
        booking_id = data.get("reschedule_booking_id")
        
        # Get staff ID
        session = Session()
        try:
            booking = session.query(Booking).filter(Booking.id == booking_id).first()
            
            if not booking:
                await callback.message.edit_text(
                    _("Booking not found."),
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton(_("Back to Bookings"), callback_data=booking_cb.new(id=0, action="back"))
                    )
                )
                return
                
            staff_id = booking.staff_id
            
            # Set state to time selection
            await RescheduleStates.select_time.set()
            
            # Answer callback
            await callback.answer()
            
            # Show time slots
            await callback.message.edit_text(
                _("Please select a new time for your appointment on {date}:").format(
                    date=format_date_for_user(selected_date)
                ),
                reply_markup=time_slots_keyboard(staff_id, year, month, day)
            )
            
        finally:
            session.close()
            
    elif action == "back":
        # Go back to booking details
        data = await state.get_data()
        booking_id = data.get("reschedule_booking_id")
        
        # Reset state
        await state.finish()
        
        # Show booking details again
        await callback.answer()
        await callback.message.edit_text(
            _("Loading booking details..."),
            reply_markup=types.InlineKeyboardMarkup()
        )
        
        # Create a new callback to view the booking
        new_callback_data = booking_cb.new(id=booking_id, action="view")
        callback.data = new_callback_data
        
        # Process the new callback
        await view_booking_callback(callback, {"id": booking_id, "action": "view"}, state)

async def reschedule_time_callback(callback: types.CallbackQuery, callback_data: Dict[str, Any], state: FSMContext):
    """
    Handle time selection for rescheduling.
    """
    action = callback_data["action"]
    
    if action == "select":
        hour = int(callback_data["hour"])
        minute = int(callback_data["minute"])
        
        # Get data from state
        data = await state.get_data()
        selected_date = datetime.fromisoformat(data.get("selected_date"))
        booking_id = data.get("reschedule_booking_id")
        
        # Create new booking datetime
        new_booking_datetime = selected_date.replace(hour=hour, minute=minute)
        
        # Update booking
        session = Session()
        try:
            user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()
            booking = session.query(Booking).filter(
                Booking.id == booking_id,
                Booking.user_id == user.id
            ).first()
            
            if not booking:
                await callback.message.edit_text(
                    _("Booking not found."),
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton(_("Back to Bookings"), callback_data=booking_cb.new(id=0, action="back"))
                    )
                )
                return
                
            # Set current locale
            i18n.current_locale = user.language
            
            # Store old date for notification
            old_date = booking.booking_date
            
            # Update booking date
            booking.booking_date = new_booking_datetime
            session.commit()
            
            # Update Zoom meeting if exists
            if booking.zoom_meeting_id:
                await update_zoom_meeting(
                    booking.zoom_meeting_id,
                    new_booking_datetime,
                    30  # Duration in minutes
                )
                
            # Update Bitrix24 event if exists
            if booking.bitrix_event_id and booking.staff and booking.staff.bitrix_user_id:
                await update_bitrix_event(
                    booking.staff.bitrix_user_id,
                    booking.bitrix_event_id,
                    new_booking_datetime,
                    30  # Duration in minutes
                )
                
            # Reset state
            await state.finish()
            
            # Answer callback
            await callback.answer(_("Booking rescheduled successfully!"))
            
            # Show confirmation
            await callback.message.edit_text(
                _("Your booking has been rescheduled to {date} at {time}.").format(
                    date=format_date_for_user(new_booking_datetime),
                    time=f"{hour:02d}:{minute:02d}"
                ),
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton(_("View Updated Booking"), callback_data=booking_cb.new(id=booking_id, action="view"))
                )
            )
            
            # Notify admin about reschedule
            await notify_admin_about_reschedule(booking, old_date)
            
        finally:
            session.close()

def register_my_bookings_handlers(dp: Dispatcher):
    """
    Register my bookings handlers.
    """
    # My bookings command
    dp.register_message_handler(cmd_my_bookings, Command("mybookings"), state="*")
    
    # Booking actions
    dp.register_callback_query_handler(view_booking_callback, booking_cb.filter(), state="*")
    
    # Reschedule handlers
    dp.register_callback_query_handler(reschedule_date_callback, date_cb.filter(), state=RescheduleStates.select_date)
    dp.register_callback_query_handler(reschedule_time_callback, time_cb.filter(), state=RescheduleStates.select_time)
