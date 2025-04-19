"""
Notification utilities for the Telegram bot.
"""
import logging
from datetime import datetime
from typing import List, Optional

from aiogram import Bot
from aiogram import enums

from bot.config import ADMIN_IDS
from bot.database import Session, Booking, TelegramUser, Staff
from bot.utils.calendar import format_date_for_user

logger = logging.getLogger(__name__)

async def notify_admin_about_booking(booking: Booking) -> None:
    """
    Notify admins about a new booking.
    
    Args:
        booking: Booking object
    """
    if not ADMIN_IDS:
        logger.warning("No admin IDs configured, skipping admin notification")
        return
    
    session = Session()
    try:
        # Get user and staff
        user = session.query(TelegramUser).filter(TelegramUser.id == booking.user_id).first()
        staff = session.query(Staff).filter(Staff.id == booking.staff_id).first()
        
        if not user or not staff:
            logger.error(f"Could not find user or staff for booking {booking.id}")
            return
        
        # Format message
        message = (
            f"🆕 <b>New Booking</b>\n\n"
            f"<b>Booking ID:</b> {booking.id}\n"
            f"<b>User:</b> {user.first_name} {user.last_name or ''} (@{user.username or 'no_username'})\n"
            f"<b>Phone:</b> {user.phone_number or 'Not provided'}\n"
            f"<b>Staff:</b> {staff.name}\n"
            f"<b>Date:</b> {format_date_for_user(booking.booking_date)}\n"
            f"<b>Time:</b> {booking.booking_date.strftime('%H:%M')}\n"
            f"<b>Status:</b> Confirmed\n"
        )
        
        # Add Zoom link if available
        if booking.zoom_join_url:
            message += f"<b>Zoom Link:</b> {booking.zoom_join_url}\n"
        
        # Get bot instance
        bot = Bot.get_current()
        
        # Send notification to all admins
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception as e:
                logger.exception(f"Failed to send notification to admin {admin_id}: {e}")
    
    except Exception as e:
        logger.exception(f"Error notifying admins about booking: {e}")
    finally:
        session.close()

async def notify_admin_about_reschedule(booking: Booking, old_date: datetime) -> None:
    """
    Notify admins about a rescheduled booking.
    
    Args:
        booking: Booking object with updated date
        old_date: Previous booking date
    """
    if not ADMIN_IDS:
        logger.warning("No admin IDs configured, skipping admin notification")
        return
    
    session = Session()
    try:
        # Get user and staff
        user = session.query(TelegramUser).filter(TelegramUser.id == booking.user_id).first()
        staff = session.query(Staff).filter(Staff.id == booking.staff_id).first()
        
        if not user or not staff:
            logger.error(f"Could not find user or staff for booking {booking.id}")
            return
        
        # Format message
        message = (
            f"🔄 <b>Booking Rescheduled</b>\n\n"
            f"<b>Booking ID:</b> {booking.id}\n"
            f"<b>User:</b> {user.first_name} {user.last_name or ''} (@{user.username or 'no_username'})\n"
            f"<b>Phone:</b> {user.phone_number or 'Not provided'}\n"
            f"<b>Staff:</b> {staff.name}\n"
            f"<b>Old Date:</b> {format_date_for_user(old_date)}\n"
            f"<b>Old Time:</b> {old_date.strftime('%H:%M')}\n"
            f"<b>New Date:</b> {format_date_for_user(booking.booking_date)}\n"
            f"<b>New Time:</b> {booking.booking_date.strftime('%H:%M')}\n"
        )
        
        # Get bot instance
        bot = Bot.get_current()
        
        # Send notification to all admins
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception as e:
                logger.exception(f"Failed to send notification to admin {admin_id}: {e}")
    
    except Exception as e:
        logger.exception(f"Error notifying admins about reschedule: {e}")
    finally:
        session.close()

async def notify_admin_about_cancellation(booking: Booking) -> None:
    """
    Notify admins about a cancelled booking.
    
    Args:
        booking: Cancelled booking object
    """
    if not ADMIN_IDS:
        logger.warning("No admin IDs configured, skipping admin notification")
        return
    
    session = Session()
    try:
        # Get user and staff
        user = session.query(TelegramUser).filter(TelegramUser.id == booking.user_id).first()
        staff = session.query(Staff).filter(Staff.id == booking.staff_id).first()
        
        if not user or not staff:
            logger.error(f"Could not find user or staff for booking {booking.id}")
            return
        
        # Format message
        message = (
            f"❌ <b>Booking Cancelled</b>\n\n"
            f"<b>Booking ID:</b> {booking.id}\n"
            f"<b>User:</b> {user.first_name} {user.last_name or ''} (@{user.username or 'no_username'})\n"
            f"<b>Phone:</b> {user.phone_number or 'Not provided'}\n"
            f"<b>Staff:</b> {staff.name}\n"
            f"<b>Date:</b> {format_date_for_user(booking.booking_date)}\n"
            f"<b>Time:</b> {booking.booking_date.strftime('%H:%M')}\n"
        )
        
        # Get bot instance
        bot = Bot.get_current()
        
        # Send notification to all admins
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=message,
                    parse_mode=enums.ParseMode.HTML
                )
            except Exception as e:
                logger.exception(f"Failed to send notification to admin {admin_id}: {e}")
    
    except Exception as e:
        logger.exception(f"Error notifying admins about cancellation: {e}")
    finally:
        session.close()
