import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.config import settings
from app.database.base import async_session
from app.database.repo import (
    add_drug,
    delete_drug,
    get_all_drugs,
    get_all_speks,
    get_drug,
    update_drug,
)
from app.keyboards.admin import (
    get_admin_menu,
    get_cancel_keyboard,
    get_drug_edit_keyboard,
    get_drugs_list_keyboard,
    get_drugs_menu,
)
from app.keyboards.main_menu import get_main_menu
from app.states.admin import AdminDrugForm

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_list


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "👨‍💼 <b>Admin panel</b>",
        reply_markup=get_admin_menu(),
    )


@router.callback_query(F.data == "admin:back")
async def admin_back(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo‘q", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text("👨‍💼 <b>Admin panel</b>", reply_markup=get_admin_menu())
    await call.answer()


@router.callback_query(F.data == "admin:drugs")
async def admin_drugs(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo‘q", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text("💊 <b>Dorilar</b>", reply_markup=get_drugs_menu())
    await call.answer()


@router.callback_query(F.data == "admin:drug:add")
async def admin_drug_add(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminDrugForm.add_name)
    await call.message.edit_text(
        "➕ <b>Yangi dori</b>\n\nNomi:",
        reply_markup=get_cancel_keyboard(),
    )
    await call.answer()


@router.message(AdminDrugForm.add_name)
async def add_name(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    await state.update_data(name=m.text or "")
    await state.set_state(AdminDrugForm.add_unit)
    await m.answer("📏 O‘lchov birligi (masalan: упак):", reply_markup=get_cancel_keyboard())


@router.message(AdminDrugForm.add_unit)
async def add_unit(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    await state.update_data(unit=m.text or "упак")
    await state.set_state(AdminDrugForm.add_price)
    await m.answer("💰 Narxi (QQS bilan):", reply_markup=get_cancel_keyboard())


@router.message(AdminDrugForm.add_price)
async def add_price(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    try:
        price = float((m.text or "").replace(",", ".").replace(" ", "").strip())
    except ValueError:
        await m.answer("❌ Raqam kiriting.")
        return
    data = await state.get_data()
    async with async_session() as session:
        await add_drug(session, data["name"], data["unit"], price)
    await state.clear()
    await m.answer(
        f"✅ Dori qo‘shildi: {data['name']}",
        reply_markup=get_drugs_menu(),
    )


@router.callback_query(F.data == "admin:drug:list")
async def admin_drug_list(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.clear()
    async with async_session() as session:
        drugs = await get_all_drugs(session)
    if not drugs:
        await call.message.edit_text(
            "📋 Ro‘yxat bo‘sh.",
            reply_markup=get_drugs_menu(),
        )
        await call.answer()
        return
    await call.message.edit_text(
        "📋 <b>Dorilar ro‘yxati:</b>",
        reply_markup=get_drugs_list_keyboard(drugs),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:drug:edit:"))
async def admin_drug_edit(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    drug_id = int(call.data.split(":")[3])
    async with async_session() as session:
        drug = await get_drug(session, drug_id)
    if not drug:
        await call.answer("Topilmadi", show_alert=True)
        return
    await call.message.edit_text(
        f"✏️ <b>{drug.name}</b>\n\n"
        f"📏 Birligi: {drug.unit}\n"
        f"💰 Narxi: {int(drug.price):,}".replace(",", " "),
        reply_markup=get_drug_edit_keyboard(drug_id),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:drug:en:"))
async def edit_name_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    drug_id = int(call.data.split(":")[3])
    await state.update_data(drug_id=drug_id)
    await state.set_state(AdminDrugForm.edit_name)
    await call.message.edit_text("✏️ Yangi nomi:", reply_markup=get_cancel_keyboard())
    await call.answer()


@router.message(AdminDrugForm.edit_name)
async def edit_name(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    data = await state.get_data()
    async with async_session() as session:
        drug = await get_drug(session, data["drug_id"])
        if drug:
            await update_drug(session, drug.id, m.text or "", drug.unit, drug.price)
    await state.clear()
    await m.answer("✅ Nom o‘zgartirildi.", reply_markup=get_drugs_menu())


@router.callback_query(F.data.startswith("admin:drug:eu:"))
async def edit_unit_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    drug_id = int(call.data.split(":")[3])
    await state.update_data(drug_id=drug_id)
    await state.set_state(AdminDrugForm.edit_unit)
    await call.message.edit_text("📏 Yangi birlik:", reply_markup=get_cancel_keyboard())
    await call.answer()


@router.message(AdminDrugForm.edit_unit)
async def edit_unit(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    data = await state.get_data()
    async with async_session() as session:
        drug = await get_drug(session, data["drug_id"])
        if drug:
            await update_drug(session, drug.id, drug.name, m.text or "", drug.price)
    await state.clear()
    await m.answer("✅ Birlik o‘zgartirildi.", reply_markup=get_drugs_menu())


@router.callback_query(F.data.startswith("admin:drug:ep:"))
async def edit_price_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    drug_id = int(call.data.split(":")[3])
    await state.update_data(drug_id=drug_id)
    await state.set_state(AdminDrugForm.edit_price)
    await call.message.edit_text("💰 Yangi narx:", reply_markup=get_cancel_keyboard())
    await call.answer()


@router.message(AdminDrugForm.edit_price)
async def edit_price(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    try:
        price = float((m.text or "").replace(",", ".").replace(" ", "").strip())
    except ValueError:
        await m.answer("❌ Raqam kiriting.")
        return
    data = await state.get_data()
    async with async_session() as session:
        drug = await get_drug(session, data["drug_id"])
        if drug:
            await update_drug(session, drug.id, drug.name, drug.unit, price)
    await state.clear()
    await m.answer("✅ Narx o‘zgartirildi.", reply_markup=get_drugs_menu())


@router.callback_query(F.data.startswith("admin:drug:del:"))
async def del_drug(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    drug_id = int(call.data.split(":")[3])
    async with async_session() as session:
        await delete_drug(session, drug_id)
    await call.answer("🗑 O‘chirildi")
    await admin_drug_list(call, state)


@router.callback_query(F.data == "admin:speks")
async def admin_speks(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    async with async_session() as session:
        speks = await get_all_speks(session, limit=50)
    if not speks:
        await call.message.edit_text("📊 Spetsifikatsiyalar yo‘q.", reply_markup=get_admin_menu())
        await call.answer()
        return
    lines = ["📊 <b>Spetsifikatsiyalar:</b>\n"]
    for s in speks:
        lines.append(f"№ {s.number} — {s.user_name} — {s.total:,.0f} so'm".replace(",", " "))
    await call.message.edit_text("\n".join(lines), reply_markup=get_admin_menu())
    await call.answer()
