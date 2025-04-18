"""
Bitrix24 API integration for the Telegram bot.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import aiohttp

from bot.config import BITRIX24_WEBHOOK_URL

logger = logging.getLogger(__name__)

async def create_bitrix_event(
    user_id: str,
    name: str,
    start_time: datetime,
    duration_minutes: int,
    phone: Optional[str] = None,
    zoom_link: Optional[str] = None
) -> Optional[str]:
    """
    Create a calendar event in Bitrix24.
    
    Args:
        user_id: Bitrix24 user ID
        name: Event name/title
        start_time: Start time
        duration_minutes: Duration in minutes
        phone: Customer phone number
        zoom_link: Zoom meeting link
        
    Returns:
        Event ID if successful, None otherwise
    """
    if not BITRIX24_WEBHOOK_URL:
        logger.error("Bitrix24 webhook URL not configured")
        return None
        
    if not user_id:
        logger.error("Bitrix24 user ID not provided")
        return None
    
    try:
        # Calculate end time
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Format datetime for Bitrix24 API
        start_formatted = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        end_formatted = end_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Prepare description with phone and Zoom link
        description = ""
        if phone:
            description += f"Phone: {phone}\n"
        if zoom_link:
            description += f"Zoom link: {zoom_link}\n"
        
        # Prepare API request
        api_url = f"{BITRIX24_WEBHOOK_URL}/calendar.event.add"
        
        data = {
            "type": "user",
            "ownerId": user_id,
            "name": name,
            "dateFrom": start_formatted,
            "dateTo": end_formatted,
            "description": description,
            "attendees": [user_id],  # Owner as attendee
            "remind": [{"type": "min", "count": 15}]  # 15-minute reminder
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Check if request was successful
                    if result.get("result"):
                        return str(result["result"])
                    else:
                        logger.error(f"Bitrix24 API error: {result.get('error')}")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create Bitrix24 event: {response.status} - {error_text}")
                    return None
    except Exception as e:
        logger.exception(f"Error creating Bitrix24 event: {e}")
        return None

async def update_bitrix_event(
    user_id: str,
    event_id: str,
    start_time: datetime,
    duration_minutes: int
) -> bool:
    """
    Update an existing calendar event in Bitrix24.
    
    Args:
        user_id: Bitrix24 user ID
        event_id: Event ID to update
        start_time: New start time
        duration_minutes: New duration in minutes
        
    Returns:
        True if successful, False otherwise
    """
    if not BITRIX24_WEBHOOK_URL:
        logger.error("Bitrix24 webhook URL not configured")
        return False
        
    if not user_id or not event_id:
        logger.error("Bitrix24 user ID or event ID not provided")
        return False
    
    try:
        # Calculate end time
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Format datetime for Bitrix24 API
        start_formatted = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        end_formatted = end_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Prepare API request
        api_url = f"{BITRIX24_WEBHOOK_URL}/calendar.event.update"
        
        data = {
            "id": event_id,
            "dateFrom": start_formatted,
            "dateTo": end_formatted
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Check if request was successful
                    if result.get("result"):
                        return True
                    else:
                        logger.error(f"Bitrix24 API error: {result.get('error')}")
                        return False
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to update Bitrix24 event: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.exception(f"Error updating Bitrix24 event: {e}")
        return False
