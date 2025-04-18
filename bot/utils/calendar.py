"""
Calendar utility functions for the Telegram bot.
"""
import datetime
from datetime import datetime, timedelta
from typing import List, Optional

from bot.database import StaffSchedule, Booking
from bot.config import DEFAULT_SLOT_DURATION

def parse_time_string(time_str: str) -> tuple:
    """
    Parse time string in format "HH:MM" to hours and minutes.
    
    Args:
        time_str: Time string in format "HH:MM"
        
    Returns:
        Tuple of (hours, minutes)
    """
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])

def format_date_for_user(date: datetime) -> str:
    """
    Format date for display to user.
    
    Args:
        date: Datetime object
        
    Returns:
        Formatted date string (e.g. "Monday, 01 Jan 2023")
    """
    return date.strftime("%A, %d %b %Y")

def get_available_slots(
    schedule: StaffSchedule,
    bookings: List[Booking],
    date: datetime,
    slot_duration: int = DEFAULT_SLOT_DURATION
) -> List[datetime]:
    """
    Get available time slots for a staff schedule.
    
    Args:
        schedule: StaffSchedule object with working hours
        bookings: List of existing bookings
        date: Date to check
        slot_duration: Duration of each slot in minutes
        
    Returns:
        List of datetime objects representing available slots
    """
    # Parse schedule times
    start_hour, start_minute = parse_time_string(schedule.start_time)
    end_hour, end_minute = parse_time_string(schedule.end_time)
    
    # Create start and end datetime objects
    start_time = date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    end_time = date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
    
    # Generate all possible time slots
    all_slots = []
    current_slot = start_time
    
    while current_slot + timedelta(minutes=slot_duration) <= end_time:
        all_slots.append(current_slot)
        current_slot += timedelta(minutes=slot_duration)
    
    # Remove booked slots
    available_slots = all_slots.copy()
    
    for booking in bookings:
        booking_time = booking.booking_date
        booking_end = booking_time + timedelta(minutes=booking.duration_minutes or slot_duration)
        
        # Remove slots that overlap with this booking
        for slot in all_slots:
            slot_end = slot + timedelta(minutes=slot_duration)
            
            # Check if this slot overlaps with the booking
            if max(slot, booking_time) < min(slot_end, booking_end):
                if slot in available_slots:
                    available_slots.remove(slot)
    
    # Return available slots
    return available_slots
