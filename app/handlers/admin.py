import logging
from datetime import timedelta, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)

from app.bot_instance import bot
from app.config import COMPANIES, settings
from app.database.base import async_session
from app.database.repo import (
    add_drug,
    count_users_by_status,
    delete_drug,
    delete_user,
    get_all_speks,
    get_all_users,
    get_contract,
    get_contract_prefix,
    get_contracts_by_inn,
    get_drug,
    get_drugs_by_company,
    get_spek_counter,
    get_user_by_id,
    get_users_by_company,
    set_contract_prefix,
    set_spek_counter,
    set_user_company,
    set_user_status,
    update_drug,
)
from app.keyboards.admin import (
    get_admin_menu,
    get_cancel_keyboard,
    get_contract_view_keyboard,
    get_contracts_list_keyboard,
    get_contracts_menu,
    get_drug_edit_keyboard,
    get_drugs_company_keyboard,
    get_drugs_list_keyboard,
    get_drugs_menu,
    get_settings_menu,
    get_user_company_keyboard,
    get_user_view_keyboard,
    get_users_company_keyboard,
    get_users_menu,
)
from app.keyboards.main_menu import get_main_menu
from app.states.admin import AdminContractForm, AdminDrugForm, AdminSettingsForm, AdminUserForm

logger = logging.getLogger(__name__)
router = Router()

TASHKENT_TZ = timezone(timedelta(hours=5))

STATUS_LABELS = {
    "pending": "⏳ Kutilmoqda",
    "approved": "✅ Tasdiqlangan",
    "rejected": "❌ Rad etilgan",
}


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_list


def _tashkent(dt):
    if dt is None:
        return "—"
    return (dt.astimezone(TASHKENT_TZ)).strftime("%d.%m.%Y %H:%M")


def _company_name(key: str) -> str:
    return COMPANIES.get(key, key or "—")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("👨‍💼 <b>Admin panel</b>", reply_markup=get_admin_menu())


@router.callback_query(F.data == "admin:back")
async def admin_back(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo‘q", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text("👨‍💼 <b>Admin panel</b>", reply_markup=get_admin_menu())
    await call.answer()


# ========== USERS ==========

async def _users_menu_text(call: CallbackQuery):
    async with async_session() as session:
        counts = await count_users_by_status(session)
    total = sum(counts.values())
    pending = counts.get("pending", 0)
    approved = counts.get("approved", 0)
    rejected = counts.get("rejected", 0)
    text = (
        "👥 <b>Foydalanuvchilar</b>\n\n"
        f"Jami: <b>{total}</b>\n"
        f"⏳ Kutilmoqda: <b>{pending}</b>\n"
        f"✅ Tasdiqlangan: <b>{approved}</b>\n"
        f"❌ Rad etilgan: <b>{rejected}</b>"
    )
    try:
        await call.message.edit_text(text, reply_markup=get_users_menu())
    except Exception:
        await call.message.answer(text, reply_markup=get_users_menu())


@router.callback_query(F.data == "admin:users")
async def admin_users(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo‘q", show_alert=True)
        return
    await state.clear()
    await _users_menu_text(call)
    await call.answer()


@router.callback_query(F.data.startswith("admin:users:"))
async def admin_users_status(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    status = call.data.split(":")[2]
    text = "🏢 Kompaniyani tanlang:"
    try:
        await call.message.edit_text(text, reply_markup=get_users_company_keyboard(status))
    except Exception:
        await call.message.answer(text, reply_markup=get_users_company_keyboard(status))
    await call.answer()


@router.callback_query(F.data.startswith("admin:uc:"))
async def admin_users_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split(":")
    company = parts[2]
    status = parts[3]

    async with async_session() as session:
        if company == "ALL":
            users = await get_all_users(
                session,
                status=None if status == "ALL" else status,
            )
        else:
            users = await get_users_by_company(
                session,
                company=company,
                status=None if status == "ALL" else status,
            )

    if not users:
        await call.answer("Bo‘sh", show_alert=True)
        return

    buttons = []
    for u in users:
        status_icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(u.status, "?")
        co_icon = "🏢"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status_icon} {co_icon}{u.first_name} {u.last_name}",
                callback_data=f"admin:user:view:{u.id}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:users")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    label = COMPANIES.get(company, "Hammasi") if company != "ALL" else "Hammasi"
    text = f"👥 <b>{label} ({len(users)}):</b>"
    try:
        await call.message.edit_text(text, reply_markup=kb)
    except Exception:
        await call.message.answer(text, reply_markup=kb)
    await call.answer()


@router.callback_query(F.data.startswith("admin:user:view:"))
async def admin_user_view(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    user_id = int(call.data.split(":")[3])
    async with async_session() as session:
        u = await get_user_by_id(session, user_id)
    if not u:
        await call.answer("Topilmadi", show_alert=True)
        return

    status_label = STATUS_LABELS.get(u.status, u.status)
    company_label = _company_name(u.company)
    text = (
        f"👤 <b>{u.first_name} {u.last_name}</b>\n\n"
        f"🔗 Username: @{u.username or '—'}\n"
        f"📞 Telefon: {u.phone}\n"
        f"📍 Viloyat: {u.region}\n"
        f"🏢 Kompaniya: {company_label}\n"
        f"🌐 Til: {u.language}\n"
        f"📊 Holat: {status_label}\n"
        f"📅 Ro‘yxatdan: {_tashkent(u.created_at)}"
    )
    await call.message.edit_text(text, reply_markup=get_user_view_keyboard(u.id))
    await call.answer()


@router.callback_query(F.data.startswith("admin:user:co:"))
async def admin_user_company(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    user_id = int(call.data.split(":")[3])
    await call.message.edit_text(
        "🏢 Yangi kompaniyani tanlang:",
        reply_markup=get_user_company_keyboard(user_id),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:user:setco:"))
async def admin_user_setco(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split(":")
    user_id = int(parts[3])
    company = parts[4]
    if company not in COMPANIES:
        await call.answer("Noto‘g‘ri kompaniya", show_alert=True)
        return
    async with async_session() as session:
        u = await get_user_by_id(session, user_id)
        if not u:
            await call.answer("Topilmadi", show_alert=True)
            return
        await set_user_company(session, u.telegram_id, company)
    await call.answer(f"✅ {COMPANIES[company]}", show_alert=False)
    try:
        await call.message.edit_text(
            f"✅ Kompaniya o‘zgartirildi: <b>{COMPANIES[company]}</b>",
            reply_markup=get_user_view_keyboard(user_id),
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("admin:user:del:"))
async def admin_user_del(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    user_id = int(call.data.split(":")[3])

    async with async_session() as session:
        u = await get_user_by_id(session, user_id)
        if not u:
            await call.answer("Topilmadi", show_alert=True)
            return
        tg_id = u.telegram_id
        await delete_user(session, tg_id)

    try:
        await bot.send_message(
            tg_id,
            "🚫 <b>Hisobingiz o‘chirildi</b>\n\n"
            "Hurmatli foydalanuvchi,\n\n"
            "Sizning hisobingiz administrator tomonidan "
            "<b>botdan foydalanish huquqidan chetlatildi</b>.\n\n"
            "Savollar bo‘lsa, administrator bilan bog‘laning.",
            reply_markup=ReplyKeyboardRemove(),
        )
    except Exception as e:
        logger.error(f"Notify deleted user failed: {e}")

    await call.answer("🗑 O‘chirildi", show_alert=False)
    await state.clear()
    await _users_menu_text(call)


# ========== APPROVE / REJECT ==========

@router.callback_query(F.data.startswith("approve:"))
async def approve_user(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    user_id = int(call.data.split(":")[1])
    async with async_session() as session:
        u = await get_user_by_id(session, user_id)
        if not u:
            await call.answer("Topilmadi", show_alert=True)
            return
        await set_user_status(session, u.telegram_id, "approved")
        lang = u.language
        tg_id = u.telegram_id

    try:
        await bot.send_message(
            tg_id,
            "✅ <b>Arizangiz tasdiqlandi!</b>\n\nBotdan foydalanishingiz mumkin.",
            reply_markup=get_main_menu(lang),
        )
    except Exception as e:
        logger.error(f"Notify user failed: {e}")

    try:
        await call.message.edit_text(call.message.html_text + "\n\n✅ <b>TASDIQLANDI</b>")
    except Exception:
        pass
    await call.answer("Tasdiqlandi")


@router.callback_query(F.data.startswith("reject:"))
async def reject_user(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    user_id = int(call.data.split(":")[1])
    async with async_session() as session:
        u = await get_user_by_id(session, user_id)
        if not u:
            await call.answer("Topilmadi", show_alert=True)
            return
        await set_user_status(session, u.telegram_id, "rejected")
        tg_id = u.telegram_id

    try:
        await bot.send_message(
            tg_id,
            "❌ <b>Afsus, arizangiz rad etildi.</b>",
            reply_markup=ReplyKeyboardRemove(),
        )
    except Exception as e:
        logger.error(f"Notify user failed: {e}")

    try:
        await call.message.edit_text(call.message.html_text + "\n\n❌ <b>RAD ETILDI</b>")
    except Exception:
        pass
    await call.answer("Rad etildi")


# ========== DRUGS ==========

@router.callback_query(F.data == "admin:drugs")
async def admin_drugs(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo‘q", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text(
        "💊 <b>Kompaniyani tanlang:</b>",
        reply_markup=get_drugs_company_keyboard(),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:drugs:co:"))
async def admin_drugs_company(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    company = call.data.split(":")[3]
    if company not in COMPANIES:
        await call.answer("Noto‘g‘ri kompaniya", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text(
        f"💊 <b>{COMPANIES[company]}</b>",
        reply_markup=get_drugs_menu(company),
    )
    await call.answer()


@router.callback_query(F.data.startswith("admin:drug:add:"))
async def admin_drug_add(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    company = call.data.split(":")[3]
    if company not in COMPANIES:
        await call.answer("Noto‘g‘ri kompaniya", show_alert=True)
        return
    await state.update_data(company=company)
    await state.set_state(AdminDrugForm.add_name)
    await call.message.edit_text(
        f"➕ <b>Yangi dori</b> ({COMPANIES[company]})\n\nNomi:",
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
    company = data.get("company", "")
    async with async_session() as session:
        await add_drug(session, company, data["name"], data["unit"], price)
    await state.clear()
    await m.answer(
        f"✅ Dori qo‘shildi: {data['name']}",
        reply_markup=get_drugs_menu(company),
    )


@router.callback_query(F.data.startswith("admin:drug:list:"))
async def admin_drug_list(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    company = call.data.split(":")[3]
    await state.clear()
    async with async_session() as session:
        drugs = await get_drugs_by_company(session, company)
    if not drugs:
        await call.message.edit_text(
            "📋 Ro‘yxat bo‘sh.",
            reply_markup=get_drugs_menu(company),
        )
        await call.answer()
        return
    await call.message.edit_text(
        f"📋 <b>{COMPANIES.get(company, company)} dorilari:</b>",
        reply_markup=get_drugs_list_keyboard(drugs, company),
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
    price = f"{int(drug.price):,}".replace(",", " ")
    await call.message.edit_text(
        f"✏️ <b>{drug.name}</b>\n\n"
        f"🏢 {COMPANIES.get(drug.company, drug.company)}\n"
        f"📏 Birligi: {drug.unit}\n"
        f"💰 Narxi: {price}",
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
            await m.answer("✅ Nom o‘zgartirildi.", reply_markup=get_drugs_menu(drug.company))
            return
    await state.clear()
    await m.answer("❌ Dori topilmadi.")


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
            await m.answer("✅ Birlik o‘zgartirildi.", reply_markup=get_drugs_menu(drug.company))
            return
    await state.clear()
    await m.answer("❌ Dori topilmadi.")


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
            await m.answer("✅ Narx o‘zgartirildi.", reply_markup=get_drugs_menu(drug.company))
            return
    await state.clear()
    await m.answer("❌ Dori topilmadi.")


@router.callback_query(F.data.startswith("admin:drug:del:"))
async def del_drug(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split(":")
    drug_id = int(parts[3])
    company = parts[4] if len(parts) > 4 else ""
    async with async_session() as session:
        await delete_drug(session, drug_id)
    await call.answer("🗑 O‘chirildi")
    if company:
        async with async_session() as session:
            drugs = await get_drugs_by_company(session, company)
        if not drugs:
            await call.message.edit_text(
                "📋 Ro‘yxat bo‘sh.",
                reply_markup=get_drugs_menu(company),
            )
        else:
            await call.message.edit_text(
                f"📋 <b>{COMPANIES.get(company, company)} dorilari:</b>",
                reply_markup=get_drugs_list_keyboard(drugs, company),
            )


@router.callback_query(F.data.startswith("admin:drug:del2:"))
async def del_drug_2(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    drug_id = int(call.data.split(":")[3])
    async with async_session() as session:
        drug = await get_drug(session, drug_id)
        company = drug.company if drug else ""
        await delete_drug(session, drug_id)
    await call.answer("🗑 O‘chirildi")
    if company:
        async with async_session() as session:
            drugs = await get_drugs_by_company(session, company)
        if not drugs:
            await call.message.edit_text(
                "📋 Ro‘yxat bo‘sh.",
                reply_markup=get_drugs_menu(company),
            )
        else:
            await call.message.edit_text(
                f"📋 <b>{COMPANIES.get(company, company)} dorilari:</b>",
                reply_markup=get_drugs_list_keyboard(drugs, company),
            )


# ========== CONTRACTS ==========

@router.callback_query(F.data == "admin:contracts")
async def admin_contracts(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo‘q", show_alert=True)
        return
    await state.clear()
    await call.message.edit_text("📄 <b>Shartnomalar</b>", reply_markup=get_contracts_menu())
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
    async with async
