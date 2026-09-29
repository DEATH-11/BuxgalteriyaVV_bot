from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.config import COMPANIES
from app.database.base import async_session
from app.database.repo import get_drugs_by_company
from app.keyboards.company import get_company_keyboard

router = Router()


@router.message(F.text == "💊 Dorilar")
async def show_drugs_uz(message: Message):
    await message.answer(
        "🏢 Qaysi kompaniya dorilarini ko‘rasiz?",
        reply_markup=get_company_keyboard("drugs"),
    )


@router.message(F.text == "💊 Товары")
async def show
