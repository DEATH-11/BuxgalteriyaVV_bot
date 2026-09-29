from aiogram.fsm.state import State, StatesGroup


class RegisterForm(StatesGroup):
    company = State()
    first_name = State()
    last_name = State()
    phone = State()
    region = State()
    confirm = State()
