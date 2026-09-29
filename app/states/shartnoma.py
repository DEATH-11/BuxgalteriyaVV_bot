from aiogram.fsm.state import State, StatesGroup


class ShartnomaForm(StatesGroup):
    company = State()
    firma_nomi = State()
    stir_raqami = State()
    confirm = State()
