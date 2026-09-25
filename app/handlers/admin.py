from app.database.repo import (
    get_contract,
    get_contracts_by_inn,
    save_contract,
)
from app.keyboards.admin import (
    get_contract_view_keyboard,
    get_contracts_list_keyboard,
    get_contracts_menu,
)
from app.states.admin import AdminContractForm
from aiogram.types import BufferedInputFile


@router.callback_query(F.data == "admin:contracts")
async def admin_contracts(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo‘q", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text(
        "📄 <b>Shartnomalar</b>",
        reply_markup=get_contracts_menu(),
    )
    await call.answer()


@router.callback_query(F.data == "admin:contract:search")
async def contract_search_start(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminContractForm.search_inn)
    await call.message.edit_text(
        "🔍 <b>INN bo‘yicha qidirish</b>\n\nINN raqamini kiriting:",
        reply_markup=get_cancel_keyboard(),
    )
    await call.answer()


@router.message(AdminContractForm.search_inn)
async def contract_search(m: Message, state: FSMContext):
    if not is_admin(m.from_user.id):
        return
    inn = (m.text or "").strip()
    await state.clear()
    async with async_session() as session:
        contracts = await get_contracts_by_inn(session, inn)
    if not contracts:
        await m.answer(
            f"❌ INN <b>{inn}</b> bo‘yicha shartnoma topilmadi.",
            reply_markup=get_contracts_menu(),
        )
        return
    await m.answer(
        f"📄 <b>{inn}</b> — {len(contracts)} ta shartnoma:",
        reply_markup=get_contracts_list_keyboard(contracts),
    )


@router.callback_query(F.data.startswith("admin:contract:view:"))
async def contract_view(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    contract_id = int(call.data.split(":")[3])
    async with async_session() as session:
        c = await get_contract(session, contract_id)
    if not c:
        await call.answer("Topilmadi", show_alert=True)
        return
    text = (
        f"📄 <b>Shartnoma</b>\n\n"
        f"🏢 Firma: {c.firma}\n"
        f"🔢 INN: {c.inn}\n"
        f"🔢 Raqam: {c.number}\n"
        f"📅 Sana: {c.date}\n"
        f"👤 Yuboruvchi: {c.user_name}\n"
        f"📅 Yaratilgan: {c.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    await call.message.edit_text(text, reply_markup=get_contract_view_keyboard(contract_id))
    await call.answer()


@router.callback_query(F.data.startswith("admin:contract:pdf:"))
async def contract_pdf(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    contract_id = int(call.data.split(":")[3])
    async with async_session() as session:
        c = await get_contract(session, contract_id)
    if not c or not c.pdf_data:
        await call.answer("PDF topilmadi", show_alert=True)
        return
    file = BufferedInputFile(c.pdf_data, filename=c.pdf_name or f"shartnoma_{c.number}.pdf")
    await bot.send_document(call.from_user.id, file)
    await call.answer("PDF yuborildi")
