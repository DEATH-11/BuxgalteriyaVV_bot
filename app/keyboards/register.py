from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import COMPANIES


REGIONS = {
    "uz": [
        "Toshkent shahar",
        "Toshkent viloyati",
        "Andijon",
        "Buxoro",
        "Farg‘ona",
        "Jizzax",
        "Xorazm",
        "Namangan",
        "Navoiy",
        "Qashqadaryo",
        "Qoraqalpog‘iston",
        "Samarqand",
        "Sirdaryo",
        "Surxondaryo",
    ],
    "ru": [
        "город Ташкент",
        "Ташкентская область",
        "Андижан",
        "Бухара",
        "Фергана",
        "Джизак",
        "Хорезм",
        "Наманган",
        "Навои",
        "Кашкадарья",
        "Каракалпакстан",
        "Самарканд",
        "Сырдарья",
        "Сурхандарья",
    ],
}


def get_company_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    buttons = []
    for key, name in COMPANIES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"🏢 {name}",
                callback_data=f"company:{key}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_region_keyboard(lang: str = "uz") -> InlineKeyboardMarkup:
    regions = REGIONS.get(lang, REGIONS["uz"])
    buttons = []
    for r in regions:
        buttons.append(
            [InlineKeyboardButton(text=r, callback_data=f"reg:{r}")]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_register_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Yuborish", callback_data="reg:submit")],
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="reg:cancel")],
        ]
    )


def get_admin_approve_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{user_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{user_id}"),
            ],
        ]
    )
