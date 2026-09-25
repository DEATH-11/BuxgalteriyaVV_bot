from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💊 Dorilar", callback_data="admin:drugs")],
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
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"✏️ {d.name} — {int(d.price):,}".replace(",", " "),
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


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:drugs")],
        ]
    )


def get_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")],
        ]
    )
