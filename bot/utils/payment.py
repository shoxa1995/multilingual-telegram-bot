"""
Payment integration with Telegram Payments API and Click.uz provider.
"""
import logging
import os
from typing import Optional, Dict, Any, Tuple

from aiogram import Bot
from aiogram.types import LabeledPrice, PreCheckoutQuery

# Initialize logger
logger = logging.getLogger(__name__)

# Import payment token from config
from bot.config import PAYMENT_PROVIDER_TOKEN

# Use the token from config, which already handles environment variables
CLICK_PAYMENT_TOKEN = PAYMENT_PROVIDER_TOKEN

# Log which token we're using (test or live)
if CLICK_PAYMENT_TOKEN and "TEST" in CLICK_PAYMENT_TOKEN:
    logging.info("Using Telegram Payments TEST mode")
else:
    logging.info("Using Telegram Payments LIVE mode")

def generate_payment_link(booking_id: int, amount: int, description: str) -> str:
    """
    Legacy function for backward compatibility.
    This is kept to maintain compatibility with existing code.
    In the new implementation, we use Telegram's Payment API directly instead of external links.
    
    Args:
        booking_id: Booking ID
        amount: Payment amount in smallest currency unit
        description: Payment description
        
    Returns:
        A placeholder URL (should not be used)
    """
    logger.warning("generate_payment_link is deprecated. Use create_invoice instead.")
    return f"https://t.me/your_bot?start=payment_{booking_id}"

async def create_invoice(bot: Bot, chat_id: int, booking_id: int, amount: int, 
                   description: str, title: str = "Appointment Booking") -> Dict:
    """
    Create a payment invoice using Telegram Payments API.
    
    Args:
        bot: Telegram Bot instance
        chat_id: Chat ID where to send the invoice
        booking_id: Booking ID to include in the invoice
        amount: Payment amount in smallest currency unit (e.g., tiyin)
        description: Description of the payment
        title: Title of the invoice
        
    Returns:
        Sent message object
    """
    try:
        # Create a labeled price
        prices = [LabeledPrice(label="Appointment", amount=amount)]
        
        # Create unique invoice payload
        payload = f"booking:{booking_id}"
        
        # Send the invoice
        result = await bot.send_invoice(
            chat_id=chat_id,
            title=title,
            description=description,
            payload=payload,
            provider_token=CLICK_PAYMENT_TOKEN,
            currency="UZS",  # Uzbekistan Som
            prices=prices,
            max_tip_amount=5000,  # Optional tip, 50 UZS max
            suggested_tip_amounts=[500, 1000, 2000],  # Suggested tip amounts
            start_parameter=f"booking_{booking_id}",
            provider_data=None,
            photo_url=None,
            photo_size=None,
            photo_width=None,
            photo_height=None,
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            send_phone_number_to_provider=False,
            send_email_to_provider=False,
            is_flexible=False,
            disable_notification=False,
            protect_content=False,
            reply_to_message_id=None,
            allow_sending_without_reply=True,
            reply_markup=None,
            request_timeout=None
        )
        
        return result
    except Exception as e:
        logger.exception(f"Error creating payment invoice: {e}")
        return None

async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery) -> bool:
    """
    Process a pre-checkout query from Telegram Payments API.
    
    Args:
        pre_checkout_query: Pre-checkout query object
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from bot.database import get_booking_by_id_async, update_booking_payment_pending_async
        
        # Extract booking ID from payload
        payload = pre_checkout_query.invoice_payload
        
        if not payload.startswith("booking:"):
            logger.error(f"Invalid payload format: {payload}")
            return False
        
        booking_id = int(payload.split(":")[1])
        
        # Verify the booking exists and is in a valid state
        booking = await get_booking_by_id_async(booking_id)
        if not booking:
            logger.error(f"Booking {booking_id} not found during pre-checkout")
            return False
            
        # Update booking status to payment_pending
        result = await update_booking_payment_pending_async(booking_id, payload)
        if not result:
            logger.error(f"Failed to update booking {booking_id} status to payment_pending")
            return False
            
        # At this point, the booking is valid and ready to accept payment
        logger.info(f"Pre-checkout validated for booking {booking_id}")
        return True
    except Exception as e:
        logger.exception(f"Error processing pre-checkout: {e}")
        return False

async def process_successful_payment(booking_id: int, telegram_payment_charge_id: str) -> bool:
    """
    Process a successful payment from Telegram Payments API.
    
    Args:
        booking_id: Booking ID
        telegram_payment_charge_id: Telegram payment charge ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from bot.database import update_booking_payment_completed_async
        
        logger.info(f"Payment successful for booking {booking_id}: {telegram_payment_charge_id}")
        
        # Update booking status in database
        result = await update_booking_payment_completed_async(
            booking_id=booking_id,
            payment_id=telegram_payment_charge_id
        )
        
        if not result:
            logger.error(f"Failed to update booking {booking_id} status after payment")
            return False
            
        # Return True to indicate success
        return True
    except Exception as e:
        logger.exception(f"Error processing successful payment: {e}")
        return False

async def check_payment_status(booking_id: int) -> str:
    """
    Check the status of a payment for a booking.
    Queries the database to determine the current payment status.
    
    Args:
        booking_id: Booking ID to check
        
    Returns:
        Status string: "paid", "pending", or "failed"
    """
    try:
        from bot.database import get_booking_by_id_async
        
        if not booking_id:
            logger.error("No booking ID provided for payment status check")
            return "failed"
        
        # Get booking from database
        booking = await get_booking_by_id_async(booking_id)
        
        if not booking:
            logger.error(f"Booking {booking_id} not found when checking payment status")
            return "failed"
        
        # Check booking status
        if booking.status == "confirmed" and booking.payment_id:
            return "paid"
        elif booking.status == "payment_pending":
            return "pending"
        else:
            return "failed"
            
    except Exception as e:
        logger.exception(f"Error checking payment status for booking {booking_id}: {e}")
        return "failed"
