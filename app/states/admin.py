from aiogram.fsm.state import State, StatesGroup


class AdminDrugForm(StatesGroup):
    add_name = State()
    add_unit = State()
    add_price = State()
    edit_name = State()
    edit_unit = State()
    edit_price = State()


class AdminContractForm(StatesGroup):
    search_inn = State()
