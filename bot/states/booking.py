"""
State machine for the booking process.
"""
from aiogram.fsm.state import State, StatesGroup


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