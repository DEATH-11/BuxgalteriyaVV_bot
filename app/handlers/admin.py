import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from app.bot_instance import bot
from app.config import settings
from app.database.base import async_session
from app.database.repo import (
    add_drug,
    count_users_by_status,
    delete_drug,
    delete_user,
    get_all_drugs,
    get_all_speks,
    get_all_users,
    get_contract,
    get_contract_prefix,
    get_contracts_by_inn,
    get_drug,
    get_user_by_id,
    set_contract_prefix,
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
    get_drugs_list_keyboard,
    get_drugs_menu,
    get_settings_menu,
    get_user_view_keyboard,
    get_users_menu,
    get_users_status_keyboard,
)
from app.keyboards.main_menu import get_main_menu
from app.states.admin import AdminContractForm, AdminDrugForm, AdminSettingsForm

logger = logging.getLogger(__name__)
router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in settings.admin_list


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

@router.callback_query(F.data == "admin:users")
async def admin_users(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("Ruxsat yo‘q", show_alert=True)
        return
    await state.clear()
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
    await call.message.edit_text(text, reply_markup=get_users_menu())
    await call.answer()


@router.callback_query(F.data.startswith("admin:users:"))
async def admin_users_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    status = call.data.split(":")[2]
    async with async_session() as session:
        if status == "ALL":
            users = await get_all_users(session)
        else:
            users = await get_all_users(session, status=status)

    if not users:
        await call.answer("Bo‘sh", show_alert=True)
        return

    lines = [f"👥 <b>Foydalanuvchilar ({len(users)}):</b>\n"]
    buttons = []
    for u in users:
        uname = f"@{u.username}" if u.username else "—"
        status_icon = {"pending": "⏳", "approved": "✅", "rejected": "❌"}.get(u.status, "?")
        lines.append(f"{status_icon} {u.first_name} {u.last_name} — {uname}")
        buttons.append([
            __import__("aiogram").types.InlineKeyboardButton(
                text=f"{status_icon} {u.first_name} {u.last_name}",
                callback_data=f"admin:user:view:{u.id}",
            )
        ])
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:users")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await call.message.edit_text("\n".join(lines), reply_markup=kb)
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
    created = u.created_at.strftime("%d.%m.%Y %H:%M") if u.created_at else "—"
    text = (
        f"👤 <b>{u.first_name} {u.last_name}</b>\n\n"
        f"🔗 Username: @{u.username or '—'}\n"
        f"🆔 ID: <code>{u.telegram_id}</code>\n"
        f"📞 Telefon: {u.phone}\n"
        f"📍 Viloyat: {u.region}\n"
        f"🌐 Til: {u.language}\n"
        f"📊 Holat: {u.status}\n"
        f"📅 Ro‘yxatdan: {created}"
    )
    await call.message.edit_text(text, reply_markup=get_user_view_keyboard(u.id))
    await call.answer()


@router.callback_query(F.data.startswith("admin:user:del:"))
async def admin_user_del(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    user_id = int(call.data.split(":")[3])
    async with async_session() as session:
        u = await get_user_by_id(session, user_id)
        if u:
            await delete_user(session, u.telegram_id)
    await call.answer("🗑 O‘chirildi")
    await admin_users(call, None)


# ========== APPROVE / REJECT (callback from notification) ==========

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
            "✅ <b>Zayavkangiz tasdiqlandi!</b>\n\nBotdan foydalanishingiz mumkin.",
            reply_markup=get_main_menu(lang),
        )
    except Exception as e:
        logger.error(f"Notify user failed: {e}")

    await call.message.edit_text(
        call.message.html_text + "\n\n✅ <b>TASDIQLANDI</b>"
    )
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
        lang = u.language
        tg_id = u.telegram_id

    try:
        await bot.send_message(
            tg_id,
            "❌ <b>Afsus, sizga ruxsat berilmadi.</b>",
        )
    except Exception as e:
        logger.error(f"Notify user failed: {e}")

    await call.message.edit_text(
        call.message.html_text + "\n\n❌ <b>RAD ETILDI</b>"
    )
    await call.answer("Rad etildi")


# ========== DRUGS ==========

@router.callback_query(F.data == "admin:drugs")
async def admin_drugs(call: CallbackQuery, state: FSMContext):
    if not
