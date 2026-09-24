from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_nav_keyboard(show_back: bool = False, prefix: str = "sh") -> InlineKeyboardMarkup:
    row = []
    if show_back:
        row.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"{prefix}:back"))
    row.append(InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"{prefix}:cancel"))
    return InlineKeyboardMarkup(inline_keyboard=[row])


def get_confirm_keyboard(prefix: str = "sh") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yaratish", callback_data=f"{prefix}:submit")],
            [InlineKeyboardButton(text="✏️ Boshidan", callback_data=f"{prefix}:restart")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"{prefix}:cancel")],
        ]
    )
