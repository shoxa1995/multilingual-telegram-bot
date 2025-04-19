"""
Payment utilities for the Telegram bot.
Handles Telegram payments integration with Click UZ.
"""
import uuid
from typing import Optional

from aiogram import Bot
from aiogram.types import LabeledPrice, ShippingOption

from bot.config import CLICK_MERCHANT_ID, CLICK_SERVICE_ID, CLICK_SECRET_KEY
from bot.database import (
    get_booking_by_id, get_staff_by_id, update_booking_payment_pending,
    update_booking_payment_completed
)


async def create_invoice(bot: Bot, chat_id: int, booking_id: int) -> Optional[str]:
    """
    Create a payment invoice for a booking and send it to the user.
    Returns the invoice payload if successful, None otherwise.
    """
    # Get the booking details
    booking = await get_booking_by_id(booking_id)
    if not booking:
        return None
    
    # Get the staff details
    staff = await get_staff_by_id(booking.staff_id)
    if not staff:
        return None
    
    # Generate a unique invoice payload
    invoice_payload = f"booking_{booking_id}_{uuid.uuid4().hex[:8]}"
    
    # Format the booking date
    booking_date_str = booking.booking_date.strftime("%Y-%m-%d %H:%M")
    
    # Create the invoice
    await bot.send_invoice(
        chat_id=chat_id,
        title=f"Booking with {staff.name}",
        description=f"Appointment on {booking_date_str} ({booking.duration_minutes} minutes)",
        payload=invoice_payload,
        provider_token=CLICK_MERCHANT_ID,  # Click UZ merchant ID is used as the provider token
        currency="UZS",  # Uzbekistan Som
        prices=[
            LabeledPrice(
                label=f"Appointment with {staff.name}", 
                amount=booking.price
            )
        ],
        start_parameter="booking_payment",
        need_name=True,
        need_phone_number=True,
        need_email=True,
        need_shipping_address=False,
        is_flexible=False,
        disable_notification=False,
        protect_content=True,
        provider_data=f'{{"service_id":"{CLICK_SERVICE_ID}"}}',  # Click UZ service ID
    )
    
    # Update the booking to payment pending status
    success = await update_booking_payment_pending(booking_id, invoice_payload)
    if not success:
        return None
    
    return invoice_payload


async def verify_payment(payment_id: str, invoice_payload: str) -> Optional[int]:
    """
    Verify a payment and update the booking status.
    Returns the booking ID if successful, None otherwise.
    """
    # Extract the booking ID from the invoice payload
    # Format: booking_ID_uuid
    try:
        booking_id = int(invoice_payload.split('_')[1])
    except (IndexError, ValueError):
        return None
    
    # Update the booking status to confirmed
    success = await update_booking_payment_completed(booking_id, payment_id)
    if not success:
        return None
    
    return booking_id