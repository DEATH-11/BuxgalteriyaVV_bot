from aiogram.fsm.state import State, StatesGroup


class SpetsifikatsiyaForm(StatesGroup):
    pick_drug = State()
    enter_qty = State()
    confirm = State()
