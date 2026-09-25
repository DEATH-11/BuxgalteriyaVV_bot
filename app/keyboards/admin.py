from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💊 Dorilar", callback_data="admin:drugs")],
            [InlineKeyboardButton(text="📄 Shartnomalar", callback_data="admin:contracts")],
            [InlineKeyboardButton(text="📊 Spetsifikatsiyalar", callback_data="admin:speks")],
        ]
    )


def get_drugs_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Dori qo‘shish", callback_data="admin:drug:add")],
            [InlineKeyboardButton(text="📋 Ro‘yxat", callback_data="admin:drug:list")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")],
        ]
    )


def get_drugs_list_keyboard(drugs: list) -> InlineKeyboardMarkup:
    buttons = []
    for d in drugs:
        price = f"{int(d.price):,}".replace(",", " ")
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"✏️ {d.name} — {price}",
                    callback_data=f"admin:drug:edit:{d.id}",
                ),
                InlineKeyboardButton(
                    text="🗑",
                    callback_data=f"admin:drug:del:{d.id}",
                ),
            ]
        )
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:drugs")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_drug_edit_keyboard(drug_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Nomi", callback_data=f"admin:drug:en:{drug_id}")],
            [InlineKeyboardButton(text="📏 Birligi", callback_data=f"admin:drug:eu:{drug_id}")],
            [InlineKeyboardButton(text="💰 Narxi", callback_data=f"admin:drug:ep:{drug_id}")],
            [InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"admin:drug:del:{drug_id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:drug:list")],
        ]
    )


def get_contracts_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 INN bo‘yicha qidirish", callback_data="admin:contract:search")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")],
        ]
    )


def get_contracts_list_keyboard(contracts: list) -> InlineKeyboardMarkup:
    buttons = []
    for c in contracts:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"📄 {c.firma} — {c.number}",
                    callback_data=f"admin:contract:view:{c.id}",
                )
            ]
        )
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:contracts")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_contract_view_keyboard(contract_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 PDF yuklab olish", callback_data=f"admin:contract:pdf:{contract_id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:contracts")],
        ]
    )


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:back")],
        ]
    )
