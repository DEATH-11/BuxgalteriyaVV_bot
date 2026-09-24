from aiogram.fsm.state import State, StatesGroup


class SpetsifikatsiyaForm(StatesGroup):
    raqam = State()
    sana = State()
    firma = State()
    stir = State()
    count = State()
    item_name = State()
    item_qty = State()
    item_price = State()
    confirm = State()
