"""
Zoom API integration for the Telegram bot.
"""
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import aiohttp
import jwt

from bot.config import ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET, ZOOM_ACCOUNT_EMAIL

logger = logging.getLogger(__name__)

# Cache for access token
ACCESS_TOKEN = None
TOKEN_EXPIRY = 0

async def get_zoom_access_token() -> Optional[str]:
    """
    Get a Zoom access token using the OAuth2 flow.
    
    Returns:
        Access token string or None if failed
    """
    global ACCESS_TOKEN, TOKEN_EXPIRY
    
    # Check if we have a valid cached token
    current_time = int(time.time())
    if ACCESS_TOKEN and TOKEN_EXPIRY > current_time + 60:  # 60-second buffer
        return ACCESS_TOKEN
    
    # No valid token, need to get a new one
    if not ZOOM_CLIENT_ID or not ZOOM_CLIENT_SECRET:
        logger.error("Zoom API credentials not configured")
        return None
    
    try:
        auth_url = "https://zoom.us/oauth/token"
        auth_str = f"{ZOOM_CLIENT_ID}:{ZOOM_CLIENT_SECRET}"
        
        # In a real implementation, we would use base64 encoding
        # For simplicity, we'll use the raw string
        headers = {
            "Authorization": f"Basic {auth_str}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "account_credentials",
            "account_id": ZOOM_ACCOUNT_EMAIL
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(auth_url, headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    ACCESS_TOKEN = result.get("access_token")
                    expires_in = result.get("expires_in", 3600)
                    TOKEN_EXPIRY = current_time + expires_in
                    return ACCESS_TOKEN
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to get Zoom access token: {response.status} - {error_text}")
                    return None
    except Exception as e:
        logger.exception(f"Error getting Zoom access token: {e}")
        return None

async def create_zoom_meeting(
    topic: str,
    start_time: datetime,
    duration_minutes: int,
    user_email: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Create a Zoom meeting.
    
    Args:
        topic: Meeting topic/title
        start_time: Start time of the meeting
        duration_minutes: Duration in minutes
        user_email: Optional email address for the participant (for registration)
        
    Returns:
        Dictionary with meeting details or None if failed
    """
    # Get access token
    access_token = await get_zoom_access_token()
    if not access_token:
        logger.error("Failed to get Zoom access token")
        return None
    
    try:
        # Format datetime for Zoom API
        formatted_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        # API endpoint
        api_url = f"https://api.zoom.us/v2/users/{ZOOM_ACCOUNT_EMAIL}/meetings"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Meeting data
        meeting_data = {
            "topic": topic,
            "type": 2,  # Scheduled meeting
            "start_time": formatted_time,
            "duration": duration_minutes,
            "timezone": "UTC",
            "settings": {
                "host_video": True,
                "participant_video": True,
                "join_before_host": True,
                "mute_upon_entry": True,
                "waiting_room": False,
                "approval_type": 2,  # No registration required
                "audio": "both",
                "auto_recording": "none"
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, headers=headers, json=meeting_data) as response:
                if response.status == 201:
                    result = await response.json()
                    return {
                        "id": result.get("id"),
                        "join_url": result.get("join_url"),
                        "start_url": result.get("start_url"),
                        "password": result.get("password")
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to create Zoom meeting: {response.status} - {error_text}")
                    return None
    except Exception as e:
        logger.exception(f"Error creating Zoom meeting: {e}")
        return None

async def update_zoom_meeting(
    meeting_id: str,
    start_time: datetime,
    duration_minutes: int
) -> bool:
    """
    Update an existing Zoom meeting.
    
    Args:
        meeting_id: Zoom meeting ID
        start_time: New start time
        duration_minutes: New duration in minutes
        
    Returns:
        True if successful, False otherwise
    """
    # Get access token
    access_token = await get_zoom_access_token()
    if not access_token:
        logger.error("Failed to get Zoom access token")
        return False
    
    try:
        # Format datetime for Zoom API
        formatted_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        
        # API endpoint
        api_url = f"https://api.zoom.us/v2/meetings/{meeting_id}"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Meeting data
        meeting_data = {
            "start_time": formatted_time,
            "duration": duration_minutes
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.patch(api_url, headers=headers, json=meeting_data) as response:
                if response.status == 204:
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to update Zoom meeting: {response.status} - {error_text}")
                    return False
    except Exception as e:
        logger.exception(f"Error updating Zoom meeting: {e}")
        return False
