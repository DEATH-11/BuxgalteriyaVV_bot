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
async def show_drugs_ru(message: Message):
    await message.answer(
        "🏢 Товары какой компании?",
        reply_markup=get_company_keyboard("drugs"),
    )


@router.callback_query(F.data.startswith("drugs:"))
async def show_drugs_company(call: CallbackQuery):
    value = call.data.split(":", 1)[1]
    if value == "cancel":
        await call.message.edit_text("❌ Bekor qilindi.")
        await call.answer()
        return
    if value not in COMPANIES:
        await call.answer("Noto‘g‘ri kompaniya.", show_alert=True)
        return

    async with async_session() as session:
        drugs = await get_drugs_by_company(session, value)

    if not drugs:
        await call.message.edit_text(
            f"💊 {COMPANIES[value]} — dorilar ro‘yxati bo‘sh."
        )
        await call.answer()
        return

    lines = [f"💊 <b>{COMPANIES[value]} dorilar ro‘yxati:</b>\n"]
    for d in drugs:
        price = f"{int(d.price):,}".replace(",", " ")
        lines.append(f"• {d.name} — {price}")

    await call.message.edit_text("\n".join(lines))
    await call.answer()
