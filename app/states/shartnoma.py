from aiogram.fsm.state import State, StatesGroup


class ShartnomaForm(StatesGroup):
    firma_nomi = State()
    stir_raqami = State()
    confirm = State()
