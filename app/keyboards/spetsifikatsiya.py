from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_drugs_keyboard(drugs: list, selected: dict) -> InlineKeyboardMarkup:
    buttons = []
    for d in drugs:
        if d.id in selected:
            label = f"✅ {d.name} ({selected[d.id]['qty']})"
        else:
            label = f"{d.name} — {int(d.price):,}".replace(",", " ")
        buttons.append(
            [InlineKeyboardButton(text=label, callback_data=f"spec:pick:{d.id}")]
        )
    buttons.append(
        [InlineKeyboardButton(text="✅ Tayyor", callback_data="spec:done")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_qty_keyboard(drug_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="spec:cancel")],
        ]
    )


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yaratish", callback_data="spec:submit")],
            [InlineKeyboardButton(text="✏️ Boshidan", callback_data="spec:restart")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="spec:cancel")],
        ]
    )
