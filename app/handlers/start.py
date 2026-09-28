from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove

from app.database.base import async_session
from app.database.repo import get_user
from app.keyboards.main_menu import get_language_keyboard, get_main_menu

router = Router()


TEXTS = {
    "uz": {
        "welcome": "Assalomu alaykum, {name}!\n\nTilni tanlang:",
        "menu_prompt": "Asosiy menyu:",
        "pending": "⏳ Arizangiz admin tasdiqlashini kutmoqda.",
        "rejected": "❌ Sizga ruxsat berilmagan.",
        "deleted": "🚫 Sizning hisobingiz o‘chirilgan. Botdan foydalana olmaysiz.",
    },
    "ru": {
        "welcome": "Здравствуйте, {name}!\n\nВыберите язык:",
        "menu_prompt": "Главное меню:",
        "pending": "⏳ Ваша заявка ожидает подтверждения администратора.",
        "rejected": "❌ Вам отказано в доступе.",
        "deleted": "🚫 Ваш аккаунт удалён. Вы не можете пользоваться ботом.",
    },
}


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("⏳", reply_markup=ReplyKeyboardRemove())

    async with async_session() as session:
        user = await get_user(session, message.from_user.id)

    if user is None:
        # Yangi user — til tanlash
        await message.answer(
            TEXTS["uz"]["welcome"].format(name=message.from_user.full_name),
            reply_markup=get_language_keyboard(),
        )
        return

    lang = user.language
    status = user.status

    if status == "approved":
        await message.answer(
            TEXTS[lang]["menu_prompt"],
            reply_markup=get_main_menu(lang),
        )
    elif status == "pending":
        await message.answer(TEXTS[lang]["pending"])
    elif status == "rejected":
        await message.answer(TEXTS[lang]["rejected"])
    else:
        # deleted yoki boshqa holat
        await message.answer(TEXTS[lang]["deleted"])


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    async with async_session() as session:
        user = await get_user(session, message.from_user.id)

    if user and user.status == "approved":
        await message.answer(
            "Asosiy menyu:",
            reply_markup=get_main_menu(user.language),
        )
    elif user and user.status == "pending":
        await message.answer(TEXTS[user.language]["pending"])
    elif user and user.status == "rejected":
        await message.answer(TEXTS[user.language]["rejected"])
