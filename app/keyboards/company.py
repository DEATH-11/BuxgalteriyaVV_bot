from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import COMPANIES


def get_company_keyboard(prefix: str = "co") -> InlineKeyboardMarkup:
    buttons = []
    for key, name in COMPANIES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"🏢 {name}",
                callback_data=f"{prefix}:{key}",
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"{prefix}:cancel")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
