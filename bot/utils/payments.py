"""
Payment utilities for the Telegram bot.
Handles Telegram payments integration with Click UZ.
"""
import uuid
import os
from typing import Optional

from aiogram import Bot
from aiogram.types import LabeledPrice, ShippingOption

from bot.database import (
    get_booking_by_id, get_staff_by_id, update_booking_payment_pending,
    update_booking_payment_completed
)

# Click UZ payment provider tokens from Telegram Bot Father
CLICK_LIVE_TOKEN = os.environ.get("CLICK_LIVE_TOKEN", "333605228:LIVE:18486_1A5B4FF440980100E5F5C1D745DFCB165C5E2A37")
CLICK_TEST_TOKEN = os.environ.get("CLICK_TEST_TOKEN", "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065")

# Use test token by default, can be configured to use live token in production
PAYMENT_PROVIDER_TOKEN = CLICK_TEST_TOKEN


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
        provider_token=PAYMENT_PROVIDER_TOKEN,  # Click UZ token from Bot Father
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
        protect_content=True
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