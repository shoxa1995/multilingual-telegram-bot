"""
States for the booking process FSM (Finite State Machine).
"""
from aiogram.dispatcher.filters.state import State, StatesGroup

class BookingStates(StatesGroup):
    """
    States for the booking process.
    """
    select_staff = State()
    select_date = State()
    select_time = State()
    enter_phone = State()
    confirm = State()
    payment = State()

class RescheduleStates(StatesGroup):
    """
    States for the reschedule process.
    """
    select_date = State()
    select_time = State()
