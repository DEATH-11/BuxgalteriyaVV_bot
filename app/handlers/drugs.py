from aiogram import F, Router
from aiogram.types import Message, ReplyKeyboardRemove

from app.database.base import async_session
from app.database.repo import get_all_drugs

router = Router()


@router.message(F.text == "💊 Dorilar")
async def show_drugs(message: Message):
    async with async_session() as session:
        drugs = await get_all_drugs(session)

    if not drugs:
        await message.answer("💊 Dorilar ro‘yxati bo‘sh.")
        return

    lines = ["💊 <b>Dorilar ro‘yxati:</b>\n"]
    for d in drugs:
        price = f"{int(d.price):,}".replace(",", " ")
        lines.append(f"• {d.name} — {price}")

    await message.answer("\n".join(lines))


@router.message(F.text == "💊 Товары")
async def show_drugs_ru(message: Message):
    async with async_session() as session:
        drugs = await get_all_drugs(session)

    if not drugs:
        await message.answer("💊 Список товаров пуст.")
        return

    lines = ["💊 <b>Список товаров:</b>\n"]
    for d in drugs:
        price = f"{int(d.price):,}".replace(",", " ")
        lines.append(f"• {d.name} — {price}")

    await message.answer("\n".join(lines))
