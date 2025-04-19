"""
Payment integration with Telegram Payments API and Click.uz provider.
"""
import logging
import os
from typing import Optional, Dict, Any, Tuple

from aiogram import Bot
from aiogram.types import LabeledPrice, PreCheckoutQuery

# Telegram Payment Provider tokens from BotFather
# Use TEST token for development and LIVE token for production
CLICK_PAYMENT_TOKEN_TEST = "398062629:TEST:999999999_F91D8F69C042267444B74CC0B3C747757EB0E065"
CLICK_PAYMENT_TOKEN_LIVE = "333605228:LIVE:18486_1A5B4FF440980100E5F5C1D745DFCB165C5E2A37"

# Use test token by default, switch to live token in production
CLICK_PAYMENT_TOKEN = CLICK_PAYMENT_TOKEN_TEST

# Set to True to use live token
USE_LIVE_PAYMENTS = False
if USE_LIVE_PAYMENTS:
    CLICK_PAYMENT_TOKEN = CLICK_PAYMENT_TOKEN_LIVE

logger = logging.getLogger(__name__)

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
