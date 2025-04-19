"""
State machine for the booking process.
"""
from aiogram.dispatcher.filters.state import State, StatesGroup


class BookingStates(StatesGroup):
    """
    States for the booking process.
    """
    selecting_staff = State()
    selecting_date = State()
    selecting_time = State()
    confirming_booking = State()
    awaiting_payment = State()