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
        "deleted": "🚫 Sizning hisobingiz o‘chirilgan.\n\nBotdan foydalana olmaysiz.",
    },
    "ru": {
        "welcome": "Здравствуйте, {name}!\n\nВыберите язык:",
        "menu_prompt": "Главное меню:",
        "pending": "⏳ Ваша заявка ожидает подтверждения администратора.",
        "rejected": "❌ Вам отказано в доступе.",
        "deleted": "🚫 Ваш аккаунт удалён.\n\nВы не можете пользоваться ботом.",
    },
}


@router.message(Command("start"))
async def cmd_start(message: Message):
    # Avval menyuni olib tashlaymiz
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
        await message.answer(
            TEXTS[lang]["pending"],
            reply_markup=ReplyKeyboardRemove(),
        )
    elif status == "rejected":
        await message.answer(
            TEXTS[lang]["rejected"],
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await message.answer(
            TEXTS[lang]["deleted"],
            reply_markup=ReplyKeyboardRemove(),
        )


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    async with async_session() as session:
        user = await get_user(session, message.from_user.id)

    if user and user.status == "approved":
        await message.answer(
            "Asosiy menyu:",
            reply_markup=get_main_menu(user.language),
        )
        return

    # Tasdiqlanmagan, rad etilgan, o‘chirilgan — menu yo‘q
    await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    if user is None:
        await message.answer(
            TEXTS["uz"]["welcome"].format(name=message.from_user.full_name),
            reply_markup=get_language_keyboard(),
        )
    elif user.status == "pending":
        await message.answer(TEXTS[user.language]["pending"])
    elif user.status == "rejected":
        await message.answer(TEXTS[user.language]["rejected"])
    else:
        await message.answer(TEXTS[user.language]["deleted"])
