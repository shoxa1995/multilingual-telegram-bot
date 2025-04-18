"""
Payment integration with Click.uz for the Telegram bot.
"""
import hashlib
import logging
import time
from typing import Optional, Dict, Any

import aiohttp

from bot.config import CLICK_MERCHANT_ID, CLICK_SERVICE_ID, CLICK_SECRET_KEY

logger = logging.getLogger(__name__)

def generate_payment_link(booking_id: int, amount: int, description: str) -> str:
    """
    Generate a payment link for Click.uz.
    
    Args:
        booking_id: Booking ID
        amount: Payment amount in smallest currency unit (e.g., tiyin)
        description: Payment description
        
    Returns:
        Payment URL
    """
    if not CLICK_MERCHANT_ID or not CLICK_SERVICE_ID:
        logger.error("Click.uz credentials not configured")
        return "#"  # Return a dummy link if not configured
    
    # Create payment link
    # In real implementation, this would generate a proper payment link
    # For now, we'll return a simple URL with parameters
    return (
        f"https://my.click.uz/services/pay"
        f"?service_id={CLICK_SERVICE_ID}"
        f"&merchant_id={CLICK_MERCHANT_ID}"
        f"&amount={amount / 100}"  # Convert to regular currency units
        f"&transaction_param={booking_id}"
        f"&return_url=https://t.me/YourBotUsername"  # Replace with your bot username
        f"&card_type=uzcard"
    )

async def check_payment_status(payment_id: Optional[str]) -> str:
    """
    Check the status of a payment with Click.uz.
    
    Args:
        payment_id: Payment ID to check
        
    Returns:
        Status string: "paid", "pending", or "failed"
    """
    if not payment_id:
        return "failed"
    
    if not CLICK_MERCHANT_ID or not CLICK_SERVICE_ID or not CLICK_SECRET_KEY:
        logger.error("Click.uz credentials not configured")
        return "failed"
    
    try:
        # In a real implementation, this would make an API call to Click.uz
        # to check the payment status
        # For this example, we'll simulate a successful payment
        
        # Generate signature
        timestamp = int(time.time())
        sign_string = f"{CLICK_SERVICE_ID}{CLICK_SECRET_KEY}{timestamp}"
        signature = hashlib.md5(sign_string.encode('utf-8')).hexdigest()
        
        # Call Click.uz API
        api_url = "https://api.click.uz/v2/merchant/payment/status"
        
        headers = {
            "Content-Type": "application/json",
            "Auth": f"{CLICK_SERVICE_ID}:{signature}:{timestamp}"
        }
        
        data = {
            "payment_id": payment_id,
            "service_id": CLICK_SERVICE_ID
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Check status code
                    if result.get("status") == 0:
                        return "paid"
                    elif result.get("status") in [1, 2]:
                        return "pending"
                    else:
                        return "failed"
                else:
                    logger.error(f"Failed to check payment status: {response.status}")
                    return "failed"
                    
    except Exception as e:
        logger.exception(f"Error checking payment status: {e}")
        return "failed"
    
    # For demo purposes, assume payment is successful
    return "paid"
