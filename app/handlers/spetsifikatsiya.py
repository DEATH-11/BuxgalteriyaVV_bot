import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, ReplyKeyboardRemove

from app.bot_instance import bot
from app.database.base import async_session
from app.database.repo import get_all_drugs, get_drug, save_spek
from app.keyboards.main_menu import get_main_menu
from app.keyboards.spetsifikatsiya import (
    get_confirm_keyboard,
    get_drugs_keyboard,
    get_qty_keyboard,
)
from app.services.docx_service import render_spetsifikatsiya
from app.services.pdf_service import convert_to_pdf
from app.states.spetsifikatsiya import SpetsifikatsiyaForm

logger = logging.getLogger(__name__)
router = Router()


async def _show_drugs(message: Message, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", {})
    async with async_session() as session:
        drugs = await get_all_drugs(session)
    if not drugs:
        await message.answer("❌ Dorilar ro‘yxati bo‘sh. Admin bilan bog‘laning.")
        return
    await state.set_state(SpetsifikatsiyaForm.pick_drug)
    await message.answer(
        "💊 <b>Dori tanlang:</b>",
        reply_markup=get_drugs_keyboard(drugs, selected),
    )


@router.message(F.text == "📊 Spetsifikatsiya yaratish")
async def start_spec_uz(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(selected={}, items=[], lang="uz")
    await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await message.answer("📊 <b>Spetsifikatsiya yaratish</b>")
    await _show_drugs(message, state)


@router.message(F.text == "📊 Создать спецификацию")
async def start_spec_ru(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(selected={}, items=[], lang="ru")
    await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await message.answer("📊 <b>Создание спецификации</b>")
    await _show_drugs(message, state)


@router.callback_query(F.data.startswith("spec:pick:"))
async def pick_drug(call: CallbackQuery, state: FSMContext):
    drug_id = int(call.data.split(":")[2])
    data = await state.get_data()
    selected = data.get("selected", {})

    if drug_id in selected:
        await call.answer("Bu dori allaqachon tanlangan.", show_alert=True)
        return

    async with async_session() as session:
        drug = await get_drug(session, drug_id)
    if not drug:
        await call.answer("Dori topilmadi", show_alert=True)
        return

    await state.update_data(current_drug_id=drug_id)
    await state.set_state(SpetsifikatsiyaForm.enter_qty)
    await call.message.edit_text(
        f"💊 <b>{drug.name}</b>\n"
        f"💰 Narxi: {int(drug.price):,}".replace(",", " ") + "\n\n"
        "Nechta olasiz?",
        reply_markup=get_qty_keyboard(drug_id),
    )
    await call.answer()


@router.message(SpetsifikatsiyaForm.enter_qty)
async def enter_qty(m: Message, state: FSMContext):
    data = await state.get_data()
    drug_id = data.get("current_drug_id")
    try:
        qty = float((m.text or "").replace(",", ".").strip())
        if qty <= 0:
            raise ValueError
    except ValueError:
        await m.answer("❌ Iltimos, musbat raqam kiriting.")
        return

    async with async_session() as session:
        drug = await get_drug(session, drug_id)
    if not drug:
        await m.answer("❌ Dori topilmadi.")
        return

    selected = data.get("selected", {})
    selected[drug_id] = {
        "name": drug.name,
        "unit": drug.unit,
        "price": drug.price,
        "qty": qty,
    }
    await state.update_data(selected=selected)

    await m.answer(f"✅ {drug.name} tanlandi.")
    await _show_drugs(m, state)


@router.callback_query(F.data == "spec:done")
async def spec_done(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", {})
    if not selected:
        await call.answer("Hech narsa tanlanmagan.", show_alert=True)
        return

    items = []
    for d in selected.values():
        items.append({
            "dori_nomi": d["name"],
            "unit": d["unit"],
            "miqdori": d["qty"],
            "narxi": d["price"],
            "umumiy_narxi": d["qty"] * d["price"],
        })

    total = sum(i["umumiy_narxi"] for i in items)
    await state.update_data(items=items, total=total)

    lines = ["📋 <b>Tekshiring:</b>\n"]
    for i, item in enumerate(items, 1):
        lines.append(
            f"{i}. {item['dori_nomi']} — {item['miqdori']} x {item['narxi']} = {item['umumiy_narxi']}"
        )
    lines.append(f"\n💰 <b>Jami:</b> {total:,.0f}".replace(",", " "))

    await state.set_state(SpetsifikatsiyaForm.confirm)
    await call.message.edit_text("\n".join(lines), reply_markup=get_confirm_keyboard())
    await call.answer()


@router.callback_query(F.data == "spec:cancel")
async def spec_cancel(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    await call.message.edit_text("❌ Bekor qilindi.")
    await call.message.answer("Asosiy menyu:", reply_markup=get_main_menu(lang))
    await call.answer()


@router.callback_query(F.data == "spec:restart")
async def spec_restart(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.update_data(selected={}, items=[], lang="uz")
    await call.message.edit_reply_markup(reply_markup=None)
    await _show_drugs(call.message, state)
    await call.answer()


@router.callback_query(F.data == "spec:submit")
async def spec_submit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])
    total = data.get("total", 0)
    lang = data.get("lang", "uz")

    async with async_session() as session:
        spek = await save_spek(
            session,
            user_id=call.from_user.id,
            user_name=call.from_user.full_name,
            items=items,
            total=total,
        )

    payload = {
        "spek_raqami": spek.number,
        "items": items,
        "jami_summa": total,
    }

    await call.message.edit_text("⏳ Hujjat tayyorlanmoqda...")
    await call.answer()

    try:
        docx_path = render_spetsifikatsiya(payload)
    except Exception as e:
        logger.error(f"DOCX error: {e}")
        await call.message.answer(f"❌ Xato: {e}")
        await state.clear()
        return

    pdf_path = convert_to_pdf(docx_path)
    file_to_send = pdf_path if pdf_path else docx_path
    file = FSInputFile(str(file_to_send))
    await bot.send_document(call.from_user.id, file)

    await state.clear()
    await call.message.answer("Asosiy menyu:", reply_markup=get_main_menu(lang))
