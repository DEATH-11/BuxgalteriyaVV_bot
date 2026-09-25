from aiogram.fsm.state import State, StatesGroup


class ShartnomaForm(StatesGroup):
    shartnoma_raqami = State()
    sana = State()
    firma_nomi = State()
    stir_raqami = State()
    confirm = State()
