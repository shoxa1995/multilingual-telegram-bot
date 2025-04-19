"""
Payment handlers for Telegram payments integration.
"""
import logging
from typing import Dict, Any

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, PreCheckoutQuery, LabeledPrice, CallbackQuery, SuccessfulPayment
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from bot.database import (
    get_user_language_async, 
    get_booking_by_id_async, 
    update_booking_payment_completed_async,
    Booking,
    sync_session
)
from bot.utils.payment import CLICK_PAYMENT_TOKEN, process_pre_checkout, process_successful_payment
from bot.middlewares.i18n import _, i18n
from bot.utils.zoom import create_zoom_meeting
from bot.utils.bitrix24 import create_bitrix_event
from bot.utils.notify import notify_admin_about_booking

logger = logging.getLogger(__name__)

async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    """
    Handle pre-checkout queries.
    This is called when a user confirms payment but before they're charged.
    """
    try:
        # Process the pre-checkout query
        booking_success = await process_pre_checkout(pre_checkout_query)
        
        if booking_success:
            # Answer with OK to confirm we're ready to accept payment
            await pre_checkout_query.answer(ok=True)
            logger.info(f"Pre-checkout query approved: {pre_checkout_query.id}")
        else:
            # Answer with error if booking validation failed
            await pre_checkout_query.answer(
                ok=False,
                error_message="Sorry, your booking is no longer available. Please try again."
            )
            logger.warning(f"Pre-checkout query rejected: {pre_checkout_query.id}")
    except Exception as e:
        # Handle any errors
        logger.exception(f"Error in pre_checkout_handler: {e}")
        await pre_checkout_query.answer(
            ok=False,
            error_message="Sorry, an error occurred while processing your payment. Please try again later."
        )

async def successful_payment_handler(message: Message, state: FSMContext):
    """
    Handle successful payments.
    This is called when a payment is successfully completed.
    """
    payment = message.successful_payment
    
    try:
        # Get language for user
        language = await get_user_language_async(message.from_user.id)
        i18n.current_locale = language
        
        # Log payment information
        logger.info(f"Received successful payment: {payment.telegram_payment_charge_id}")
        
        # Extract booking ID from payload
        if not payment.invoice_payload.startswith("booking:"):
            logger.error(f"Invalid payment payload format: {payment.invoice_payload}")
            await message.answer(_("There was an error processing your payment. Please contact support."))
            return
            
        booking_id = int(payment.invoice_payload.split(":")[1])
        
        # Process successful payment
        payment_success = await process_successful_payment(
            booking_id=booking_id,
            telegram_payment_charge_id=payment.telegram_payment_charge_id
        )
        
        if payment_success:
            # Get booking information
            booking = await get_booking_by_id_async(booking_id)
            
            if not booking:
                logger.error(f"Booking not found for successful payment: {booking_id}")
                await message.answer(_("There was an error processing your booking. Please contact support."))
                return
            
            # Update booking status
            await update_booking_payment_completed_async(
                booking_id=booking_id,
                payment_id=payment.telegram_payment_charge_id
            )
            
            # Create Zoom meeting with error handling
            try:
                zoom_result = await create_zoom_meeting(
                    topic=f"Appointment with {booking.staff.name}",
                    start_time=booking.booking_date,
                    duration_minutes=booking.duration_minutes,
                    user_email=booking.user.email if hasattr(booking.user, 'email') else None
                )
                
                if zoom_result and 'join_url' in zoom_result:
                    # Update booking with Zoom meeting info
                    with sync_session() as session:
                        query = select(Booking).where(Booking.id == booking_id)
                        result = session.execute(query)
                        booking_obj = result.scalar_one_or_none()
                        if booking_obj:
                            booking_obj.zoom_meeting_id = zoom_result.get('id')
                            booking_obj.zoom_join_url = zoom_result.get('join_url')
                            session.commit()
                            logger.info(f"Updated booking {booking_id} with Zoom meeting info")
                else:
                    logger.warning(f"Zoom meeting creation failed for booking {booking_id}")
            except Exception as e:
                logger.exception(f"Error creating Zoom meeting: {e}")
            
            # Create Bitrix24 event with error handling
            try:
                bitrix_result = await create_bitrix_event(
                    user_id=booking.user.telegram_id,
                    name=f"Appointment: {booking.user.first_name or 'Client'} - {booking.staff.name}",
                    start_time=booking.booking_date,
                    duration_minutes=booking.duration_minutes,
                    responsible_id=booking.staff.bitrix_user_id if booking.staff.bitrix_user_id else None
                )
                
                if bitrix_result and 'event_id' in bitrix_result:
                    # Update booking with Bitrix event info
                    with sync_session() as session:
                        query = select(Booking).where(Booking.id == booking_id)
                        result = session.execute(query)
                        booking_obj = result.scalar_one_or_none()
                        if booking_obj:
                            booking_obj.bitrix_event_id = bitrix_result.get('event_id')
                            session.commit()
                            logger.info(f"Updated booking {booking_id} with Bitrix event info")
                else:
                    logger.warning(f"Bitrix event creation failed for booking {booking_id}")
            except Exception as e:
                logger.exception(f"Error creating Bitrix event: {e}")
            
            # Notify admin about new booking
            await notify_admin_about_booking(booking)
            
            # Send confirmation message
            await message.answer(
                _(
                    "<b>Payment Successful!</b>\n\n"
                    "Your appointment has been confirmed. Thank you for your payment of {amount}.\n\n"
                    "<b>Booking Details:</b>\n"
                    "Staff: {staff_name}\n"
                    "Date: {booking_date}\n"
                    "Duration: {duration} minutes\n\n"
                    "We look forward to seeing you! You can manage your bookings using the /my_bookings command."
                ).format(
                    amount=f"{payment.total_amount / 100:.2f} {payment.currency}",
                    staff_name=booking.staff.name,
                    booking_date=booking.booking_date.strftime("%Y-%m-%d %H:%M"),
                    duration=booking.duration_minutes
                ),
                parse_mode="HTML"
            )
            
            # Reset state
            await state.clear()
        else:
            # Payment processing failed
            logger.error(f"Payment processing failed for booking: {booking_id}")
            await message.answer(_("There was an error processing your payment. Please contact support."))
    except Exception as e:
        # Handle any errors
        logger.exception(f"Error in successful_payment_handler: {e}")
        await message.answer(_("There was an error processing your payment. Please contact support."))

def register_payment_handlers(router: Router):
    """
    Register payment handlers.
    """
    # Pre-checkout handler
    router.pre_checkout_query.register(pre_checkout_handler)
    
    # Successful payment handler
    router.message.register(successful_payment_handler, F.successful_payment)