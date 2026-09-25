from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def get_language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O‘zbek tili", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            ]
        ]
    )


def get_main_menu(lang: str = "uz") -> ReplyKeyboardMarkup:
    if lang == "ru":
        buttons = [
            [KeyboardButton(text="📄 Создать договор")],
            [KeyboardButton(text="📊 Создать спецификацию")],
            [KeyboardButton(text="💊 Товары")],
        ]
    else:
        buttons = [
            [KeyboardButton(text="📄 Shartnoma yaratish")],
            [KeyboardButton(text="📊 Spetsifikatsiya yaratish")],
            [KeyboardButton(text="💊 Dorilar")],
        ]

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Menyudan tanlang...",
    )
