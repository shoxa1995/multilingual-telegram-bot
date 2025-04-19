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
        # Extract booking ID from payload
        payload = pre_checkout_query.invoice_payload
        
        if not payload.startswith("booking:"):
            logger.error(f"Invalid payload format: {payload}")
            return False
        
        booking_id = int(payload.split(":")[1])
        
        # Here you would validate the booking exists and is still valid
        # For now, we'll just return True
        
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
        # Here you would update the booking to confirmed status
        # For now, we'll just return True and log the payment
        
        logger.info(f"Payment successful for booking {booking_id}: {telegram_payment_charge_id}")
        
        # Return True to indicate success
        return True
    except Exception as e:
        logger.exception(f"Error processing successful payment: {e}")
        return False

async def check_payment_status(payment_id: Optional[str]) -> str:
    """
    Check the status of a payment with Telegram Payments API.
    
    Args:
        payment_id: Payment ID to check
        
    Returns:
        Status string: "paid", "pending", or "failed"
    """
    if not payment_id:
        return "failed"
    
    # With Telegram Payments API, payment is considered successful once the 
    # successful_payment handler is called. In this simplified implementation, 
    # we'll return "paid" if a payment ID exists, since we should only store a 
    # payment ID after receiving a successful_payment from Telegram.
    
    return "paid"
