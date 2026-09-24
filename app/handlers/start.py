from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.keyboards.main_menu import get_language_keyboard, get_main_menu

router = Router()


TEXTS = {
    "uz": {
        "welcome": "Assalomu alaykum!\n\nTilni tanlang:",
        "menu_ready": "Til tanlandi: 🇺🇿 O‘zbek tili",
        "menu_prompt": "Asosiy menyu:",
    },
    "ru": {
        "welcome": "Здравствуйте!\n\nВыберите язык:",
        "menu_ready": "Язык выбран: 🇷🇺 Русский",
        "menu_prompt": "Главное меню:",
    },
}


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await message.answer(
        TEXTS["uz"]["welcome"],
        reply_markup=get_language_keyboard(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def set_lang(call: CallbackQuery):
    lang = call.data.split(":")[1]
    await call.message.edit_text(TEXTS[lang]["menu_ready"])
    await call.message.answer(
        TEXTS[lang]["menu_prompt"],
        reply_markup=get_main_menu(lang),
    )
    await call.answer()


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu("uz"))
