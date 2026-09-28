import logging
import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot_instance import bot
from app.config import settings
from app.database.base import async_session
from app.database.repo import create_user, get_user
from app.keyboards.main_menu import get_main_menu
from app.keyboards.register import (
    get_admin_approve_keyboard,
    get_register_confirm_keyboard,
    get_region_keyboard,
)
from app.states.register import RegisterForm

logger = logging.getLogger(__name__)
router = Router()


TEXTS = {
    "uz": {
        "ask_first": "1/4 — 👤 Ismingizni kiriting:",
        "ask_last": "2/4 — 👤 Familiyangizni kiriting:",
        "ask_phone": "3/4 — 📞 Telefon raqamingizni kiriting.\nMasalan: +998 90 123 45 67",
        "ask_region": "4/4 — 📍 Viloyatingizni tanlang:",
        "confirm": "📋 <b>Tekshiring:</b>\n\n👤 Ism: {f}\n👤 Familiya: {l}\n📞 Telefon: {p}\n📍 Viloyat: {r}\n\nYuborilsinmi?",
        "sent": "✅ Arizangiz yuborildi.\n\nAdmin tasdiqlashini kuting.",
        "menu": "Asosiy menyu:",
        "denied": "❌ Sizga ruxsat berilmagan.",
        "pending": "⏳ Arizangiz admin tasdiqlashini kutmoqda.",
        "deleted": "🚫 Sizning hisobingiz o‘chirilgan.",
        "err_name": "❌ Faqat harflar kiriting (raqam va belgilar bo‘lmasin).",
        "err_phone": "❌ Faqat raqamlar kiriting.\nMasalan: +998 90 123 45 67",
    },
    "ru": {
        "ask_first": "1/4 — 👤 Введите имя:",
        "ask_last": "2/4 — 👤 Введите фамилию:",
        "ask_phone": "3/4 — 📞 Введите номер телефона.\nНапример: +998 90 123 45 67",
        "ask_region": "4/4 — 📍 Выберите область:",
        "confirm": "📋 <b>Проверьте:</b>\n\n👤 Имя: {f}\n👤 Фамилия: {l}\n📞 Телефон: {p}\n📍 Область: {r}\n\nОтправить?",
        "sent": "✅ Ваша заявка отправлена.\n\nОжидайте подтверждения администратора.",
        "menu": "Главное меню:",
        "denied": "❌ Вам отказано в доступе.",
        "pending": "⏳ Ваша заявка ожидает подтверждения администратора.",
        "deleted": "🚫 Ваш аккаунт удалён.",
        "err_name": "❌ Только буквы (без цифр и символов).",
        "err_phone": "❌ Только цифры.\nНапример: +998 90 123 45 67",
    },
}


NAME_RE = re.compile(r"^[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳʼ'`\- ]{2,50}$")
PHONE_RE = re.compile(r"^\+?[0-9 \-()]{7,20}$")


def _valid_name(text: str) -> bool:
    return bool(NAME_RE.match(text.strip()))


def _valid_phone(text: str) -> bool:
    return bool(PHONE_RE.match(text.strip()))


async def _notify_admins_new_user(user, username):
    if username:
        username_line = f"🔗 Username: <a href=\"https://t.me/{username}\">@{username}</a>"
    else:
        username_line = "🔗 Username: —"

    text = (
        "🆕 <b>YANGI ARIZA</b>\n\n"
        f"👤 Ism: {user.first_name}\n"
        f"👤 Familiya: {user.last_name}\n"
        f"📞 Telefon: {user.phone}\n"
        f"📍 Viloyat: {user.region}\n"
        f"{username_line}"
    )
    for admin_id in settings.admin_list:
        try:
            await bot.send_message(
                admin_id,
                text,
                parse_mode="HTML",
                reply_markup=get_admin_approve_keyboard(user.id),
            )
        except Exception as e:
            logger.error(f"Admin notify failed ({admin_id}): {e}")


@router.callback_query(F.data.startswith("lang:"))
async def set_lang_register(call: CallbackQuery, state: FSMContext):
    lang = call.data.split(":")[1]

    async with async_session() as session:
        user = await get_user(session, call.from_user.id)

    if user is None:
        await state.clear()
        await state.update_data(lang=lang)
        await state.set_state(RegisterForm.first_name)
        try:
            await call.message.edit_text(TEXTS[lang]["ask_first"])
        except Exception:
            await call.message.answer(TEXTS[lang]["ask_first"])
        await call.answer()
        return

    if user.status == "approved":
        try:
            await call.message.edit_text(TEXTS[lang]["menu"])
        except Exception:
            pass
        await call.message.answer("Asosiy menyu:", reply_markup=get_main_menu(lang))
    elif user.status == "pending":
        try:
            await call.message.edit_text(TEXTS[lang]["pending"])
        except Exception:
            pass
    elif user.status == "rejected":
        try:
            await call.message.edit_text(TEXTS[lang]["denied"])
        except Exception:
            pass
    else:
        try:
            await call.message.edit_text(TEXTS[lang]["deleted"])
        except Exception:
            pass
    await call.answer()


@router.message(RegisterForm.first_name)
async def reg_first(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = (m.text or "").strip()
    if not _valid_name(text):
        await m.answer(TEXTS[lang]["err_name"])
        return
    await state.update_data(first_name=text)
    await state.set_state(RegisterForm.last_name)
    await m.answer(TEXTS[lang]["ask_last"])


@router.message(RegisterForm.last_name)
async def reg_last(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = (m.text or "").strip()
    if not _valid_name(text):
        await m.answer(TEXTS[lang]["err_name"])
        return
    await state.update_data(last_name=text)
    await state.set_state(RegisterForm.phone)
    await m.answer(TEXTS[lang]["ask_phone"])


@router.message(RegisterForm.phone)
async def reg_phone(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    text = (m.text or "").strip()
    if not _valid_phone(text):
        await m.answer(TEXTS[lang]["err_phone"])
        return
    await state.update_data(phone=text)
    await state.set_state(RegisterForm.region)
    await m.answer(TEXTS[lang]["ask_region"], reply_markup=get_region_keyboard(lang))


@router.callback_query(F.data == "reg:submit")
async def reg_submit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    f = data.get("first_name", "")
    l = data.get("last_name", "")
    p = data.get("phone", "")
    r = data.get("region", "")

    if not r:
        await call.answer("Avval viloyatni tanlang.", show_alert=True)
        return

    async with async_session() as session:
        existing = await get_user(session, call.from_user.id)
        if existing is None:
            user = await create_user(
                session,
                telegram_id=call.from_user.id,
                username=call.from_user.username,
                first_name=f,
                last_name=l,
                phone=p,
                region=r,
                language=lang,
            )
        else:
            user = existing

    await state.clear()
    try:
        await call.message.edit_text(TEXTS[lang]["sent"])
    except Exception:
        await call.message.answer(TEXTS[lang]["sent"])
    await call.answer("Yuborildi!")

    await _notify_admins_new_user(user, call.from_user.username)


@router.callback_query(F.data == "reg:cancel")
async def reg_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await call.message.edit_text("❌ Bekor qilindi.")
    except Exception:
        await call.message.answer("❌ Bekor qilindi.")
    await call.answer()


@router.callback_query(F.data.startswith("reg:"))
async def reg_region(call: CallbackQuery, state: FSMContext):
    value = call.data.split(":", 1)[1]

    if value in ("submit", "cancel"):
        return

    await state.update_data(region=value)
    data = await state.get_data()
    lang = data.get("lang", "uz")
    f = data.get("first_name", "")
    l = data.get("last_name", "")
    p = data.get("phone", "")

    text = TEXTS[lang]["confirm"].format(f=f, l=l, p=p, r=value)
    try:
        await call.message.edit_text(
            text,
            reply_markup=get_register_confirm_keyboard(),
        )
    except Exception:
        await call.message.answer(
            text,
            reply_markup=get_register_confirm_keyboard(),
        )
    await call.answer()
