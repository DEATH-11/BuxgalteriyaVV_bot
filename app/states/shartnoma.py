from aiogram.fsm.state import State, StatesGroup


class ShartnomaForm(StatesGroup):
    sana = State()
    raqam = State()
    firma = State()
    stir = State()
    confirm = State()
