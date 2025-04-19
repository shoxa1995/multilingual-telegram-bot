"""
Inline keyboard markup generator for the Telegram bot.
"""
import calendar
import datetime
from typing import List, Dict, Union, Optional
from datetime import datetime, timedelta

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData

from bot.middlewares.i18n import _
from bot.database import sync_session, Staff, Booking, StaffSchedule, BookingStatus
from bot.utils.calendar import get_available_slots

# Define callback data patterns - updated for aiogram 3.x
# In aiogram 3.x, CallbackData classes need to properly set prefixes
class StaffCallbackFactory(CallbackData, prefix="staff"):
    """Staff callback data factory"""
    id: int
    action: str = "select"

class DateCallbackFactory(CallbackData, prefix="date"):
    """Date callback data factory"""
    year: int
    month: int
    day: int
    action: str = "select"

class TimeCallbackFactory(CallbackData, prefix="time"):
    """Time callback data factory"""
    hour: int
    minute: int
    action: str = "select"

class BookingCallbackFactory(CallbackData, prefix="booking"):
    """Booking callback data factory"""
    id: int
    action: str

class NavigationCallbackFactory(CallbackData, prefix="nav"):
    """Navigation callback data factory"""
    direction: str

class ConfirmCallbackFactory(CallbackData, prefix="confirm"):
    """Confirmation callback data factory"""
    action: str

# For backward compatibility, we'll keep these simple aliases
# Note: in aiogram 3.x, we don't initialize these directly, we'll use them as classes
# In aiogram 3.x, we use these factories differently
# For backward compatibility with the existing code, we'll create helper functions

def staff_cb(id: int, action: str = "select"):
    """Helper function for aiogram 3.x callback data creation"""
    return StaffCallbackFactory(id=id, action=action).pack()
    
def date_cb(year: int, month: int, day: int, action: str = "select"):
    """Helper function for aiogram 3.x callback data creation"""
    return DateCallbackFactory(year=year, month=month, day=day, action=action).pack()
    
def time_cb(hour: int, minute: int, action: str = "select"):
    """Helper function for aiogram 3.x callback data creation"""
    return TimeCallbackFactory(hour=hour, minute=minute, action=action).pack()
    
def booking_cb(id: int, action: str):
    """Helper function for aiogram 3.x callback data creation"""
    return BookingCallbackFactory(id=id, action=action).pack()
    
def navigation_cb(direction: str):
    """Helper function for aiogram 3.x callback data creation"""
    return NavigationCallbackFactory(direction=direction).pack()
    
def confirm_cb(action: str):
    """Helper function for aiogram 3.x callback data creation"""
    return ConfirmCallbackFactory(action=action).pack()

def staff_selection_keyboard() -> InlineKeyboardMarkup:
    """Create a keyboard with staff members to select from."""
    markup = InlineKeyboardMarkup(row_width=1)
    
    session = sync_session()
    try:
        # Get all active staff members
        staff_members = session.query(Staff).filter(Staff.is_active == True).all()
        
        for staff in staff_members:
            markup.add(
                InlineKeyboardButton(
                    text=staff.name,
                    callback_data=staff_cb(id=staff.id, action='select')
                )
            )
            
    finally:
        session.close()
        
    # Add cancel button
    markup.add(
        InlineKeyboardButton(
            text=_('❌ Cancel'),
            callback_data='cancel'
        )
    )
    
    return markup

def staff_profile_keyboard(staff_id: int) -> InlineKeyboardMarkup:
    """Create a keyboard for staff profile view."""
    markup = InlineKeyboardMarkup(row_width=2)
    
    # Add book button
    markup.add(
        InlineKeyboardButton(
            text=_('📅 Book Appointment'),
            callback_data=staff_cb(id=staff_id, action='book')
        )
    )
    
    # Add back and cancel buttons
    markup.row(
        InlineKeyboardButton(
            text=_('⬅️ Back'),
            callback_data='back_to_staff'
        ),
        InlineKeyboardButton(
            text=_('❌ Cancel'),
            callback_data='cancel'
        )
    )
    
    return markup

def calendar_keyboard(staff_id: int, current_date: datetime = None) -> InlineKeyboardMarkup:
    """Create a calendar keyboard for selecting a date."""
    if current_date is None:
        current_date = datetime.now()
        
    markup = InlineKeyboardMarkup(row_width=7)
    
    # Get the year and month
    year = current_date.year
    month = current_date.month
    
    # Add month and year display
    month_names = {
        'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 
               'August', 'September', 'October', 'November', 'December'],
        'ru': ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь', 'Июль', 
               'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'],
        'uz': ['Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 
               'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr']
    }
    
    # Default to English if translation not available
    month_name = month_names.get('en', month_names['en'])[month - 1]
    
    markup.add(
        InlineKeyboardButton(
            text=f"{month_name} {year}",
            callback_data='ignore'
        )
    )
    
    # Add day names row
    days_of_week = {
        'en': ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'],
        'ru': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
        'uz': ['Du', 'Se', 'Ch', 'Pa', 'Ju', 'Sh', 'Ya']
    }
    
    # Default to English if translation not available
    days = days_of_week.get('en', days_of_week['en'])
    
    # Add days of week as header
    markup.row(*[InlineKeyboardButton(text=day, callback_data='ignore') for day in days])
    
    # Get the calendar for the current month
    cal = calendar.monthcalendar(year, month)
    
    # Get available days for this staff member in this month
    session = sync_session()
    try:
        staff = session.query(Staff).filter(Staff.id == staff_id).first()
        if not staff:
            return markup  # Return empty calendar if staff doesn't exist
            
        # Get staff schedule
        staff_schedules = session.query(StaffSchedule).filter(StaffSchedule.staff_id == staff_id).all()
        
        # Get all bookings for this staff in this month
        start_date = datetime(year, month, 1)
        if month == 12:  # Handle December
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
            
        bookings = session.query(Booking).filter(
            Booking.staff_id == staff_id,
            Booking.booking_date >= start_date,
            Booking.booking_date < end_date,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PAYMENT_PENDING])
        ).all()
        
    finally:
        session.close()
    
    # Calculate which days have available slots
    available_days = set()
    today = datetime.now().date()
    
    for week in cal:
        for day in week:
            if day == 0:  # Day doesn't exist in this month
                continue
                
            check_date = datetime(year, month, day).date()
            
            # Skip past days
            if check_date < today:
                continue
                
            # Check if this day has available slots
            weekday = check_date.weekday()  # 0 = Monday, 6 = Sunday
            
            # Check if staff works on this day
            day_schedules = [s for s in staff_schedules if s.weekday == weekday]
            
            if day_schedules:
                # This is a working day, check for available slots
                day_date = datetime(year, month, day)
                
                # Get day's bookings
                day_bookings = [b for b in bookings if b.booking_date.date() == day_date.date()]
                
                # If we have any available slots, mark the day as available
                has_slots = False
                
                for schedule in day_schedules:
                    slots = get_available_slots(schedule, day_bookings, day_date)
                    if slots:
                        has_slots = True
                        break
                        
                if has_slots:
                    available_days.add(day)
    
    # Add day buttons
    for week in cal:
        row = []
        for day in week:
            if day == 0:  # Day doesn't exist in this month
                row.append(InlineKeyboardButton(text=' ', callback_data='ignore'))
            else:
                # Check if day is in the past
                check_date = datetime(year, month, day).date()
                if check_date < today:
                    # Past day - show as unavailable
                    row.append(InlineKeyboardButton(text=f"{day}", callback_data='ignore'))
                elif day in available_days:
                    # Available day
                    row.append(
                        InlineKeyboardButton(
                            text=f"{day}",
                            callback_data=date_cb.new(
                                year=year, month=month, day=day, action='select'
                            )
                        )
                    )
                else:
                    # Unavailable day
                    row.append(InlineKeyboardButton(text=f"{day}", callback_data='ignore'))
                    
        markup.row(*row)
    
    # Add navigation buttons
    prev_month = current_date - timedelta(days=1)
    next_month = datetime(year, month, 1) + timedelta(days=32)
    next_month = datetime(next_month.year, next_month.month, 1)
    
    markup.row(
        InlineKeyboardButton(
            text=_('◀️ Previous'),
            callback_data=navigation_cb.new(direction=f'prev:{staff_id}')
        ),
        InlineKeyboardButton(
            text=_('▶️ Next'),
            callback_data=navigation_cb.new(direction=f'next:{staff_id}')
        )
    )
    
    # Add back and cancel buttons
    markup.row(
        InlineKeyboardButton(
            text=_('⬅️ Back'),
            callback_data=staff_cb.new(id=staff_id, action='select')
        ),
        InlineKeyboardButton(
            text=_('❌ Cancel'),
            callback_data='cancel'
        )
    )
    
    return markup

def time_slots_keyboard(staff_id: int, year: int, month: int, day: int) -> InlineKeyboardMarkup:
    """Create keyboard with available time slots for the selected date."""
    markup = InlineKeyboardMarkup(row_width=3)
    
    selected_date = datetime(year, month, day)
    weekday = selected_date.weekday()  # 0=Monday, 6=Sunday
    
    session = sync_session()
    try:
        # Get staff schedules for this day
        schedules = session.query(StaffSchedule).filter(
            StaffSchedule.staff_id == staff_id,
            StaffSchedule.weekday == weekday
        ).all()
        
        # Get bookings for this day
        bookings = session.query(Booking).filter(
            Booking.staff_id == staff_id,
            Booking.booking_date >= datetime(year, month, day),
            Booking.booking_date < datetime(year, month, day) + timedelta(days=1),
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PAYMENT_PENDING])
        ).all()
        
        # Get available time slots
        all_slots = []
        for schedule in schedules:
            slots = get_available_slots(schedule, bookings, selected_date)
            all_slots.extend(slots)
            
        # Sort slots by time
        all_slots.sort()
        
        # Add time slot buttons
        for slot in all_slots:
            hour, minute = slot.hour, slot.minute
            markup.insert(
                InlineKeyboardButton(
                    text=f"{hour:02d}:{minute:02d}",
                    callback_data=time_cb.new(hour=hour, minute=minute, action='select')
                )
            )
            
    finally:
        session.close()
        
    # Add back and cancel buttons
    markup.row(
        InlineKeyboardButton(
            text=_('⬅️ Back'),
            callback_data=date_cb.new(year=0, month=0, day=0, action='back')
        ),
        InlineKeyboardButton(
            text=_('❌ Cancel'),
            callback_data='cancel'
        )
    )
    
    return markup

def confirmation_keyboard() -> InlineKeyboardMarkup:
    """Create a confirmation keyboard."""
    markup = InlineKeyboardMarkup(row_width=2)
    
    markup.row(
        InlineKeyboardButton(
            text=_('✅ Confirm'),
            callback_data=confirm_cb.new(action='confirm')
        ),
        InlineKeyboardButton(
            text=_('❌ Cancel'),
            callback_data=confirm_cb.new(action='cancel')
        )
    )
    
    return markup

def my_bookings_keyboard(bookings: List[Booking]) -> InlineKeyboardMarkup:
    """Create a keyboard with user's bookings."""
    markup = InlineKeyboardMarkup(row_width=1)
    
    for booking in bookings:
        # Format booking date/time
        booking_time = booking.booking_date.strftime('%d.%m.%Y %H:%M')
        staff_name = booking.staff.name if booking.staff else 'Unknown'
        
        markup.add(
            InlineKeyboardButton(
                text=f"{booking_time} - {staff_name}",
                callback_data=booking_cb.new(id=booking.id, action='view')
            )
        )
        
    # Add cancel button
    markup.add(
        InlineKeyboardButton(
            text=_('❌ Close'),
            callback_data='cancel'
        )
    )
    
    return markup

def booking_actions_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    """Create a keyboard with actions for a booking."""
    markup = InlineKeyboardMarkup(row_width=1)
    
    # Add reschedule button
    markup.add(
        InlineKeyboardButton(
            text=_('🔄 Reschedule'),
            callback_data=booking_cb.new(id=booking_id, action='reschedule')
        )
    )
    
    # Add cancel booking button
    markup.add(
        InlineKeyboardButton(
            text=_('❌ Cancel Booking'),
            callback_data=booking_cb.new(id=booking_id, action='cancel')
        )
    )
    
    # Add back button
    markup.add(
        InlineKeyboardButton(
            text=_('⬅️ Back'),
            callback_data=booking_cb.new(id=0, action='back')
        )
    )
    
    return markup

def cancel_booking_confirmation_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    """Create a confirmation keyboard for cancelling a booking."""
    markup = InlineKeyboardMarkup(row_width=2)
    
    markup.row(
        InlineKeyboardButton(
            text=_('✅ Yes, Cancel'),
            callback_data=booking_cb.new(id=booking_id, action='confirm_cancel')
        ),
        InlineKeyboardButton(
            text=_('🔙 No, Go Back'),
            callback_data=booking_cb.new(id=booking_id, action='view')
        )
    )
    
    return markup
