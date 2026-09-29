from aiogram.fsm.state import State, StatesGroup


class SpetsifikatsiyaForm(StatesGroup):
    company = State()
    pick_drug = State()
    enter_qty = State()
    confirm = State()
