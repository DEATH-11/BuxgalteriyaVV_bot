from aiogram.fsm.state import State, StatesGroup


class AdminDrugForm(StatesGroup):
    select_company = State()
    add_name = State()
    add_unit = State()
    add_price = State()
    edit_name = State()
    edit_unit = State()
    edit_price = State()


class AdminContractForm(StatesGroup):
    search_inn = State()


class AdminSettingsForm(StatesGroup):
    edit_contract_vivora = State()
    edit_contract_almas = State()
    edit_spek_vivora = State()
    edit_spek_almas = State()


class AdminUserForm(StatesGroup):
    edit_company = State()
