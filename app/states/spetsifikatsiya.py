from aiogram.fsm.state import State, StatesGroup


class SpetsifikatsiyaForm(StatesGroup):
    spek_raqami = State()
    count = State()
    item_dori = State()
    item_miqdor = State()
    item_narx = State()
    confirm = State()
