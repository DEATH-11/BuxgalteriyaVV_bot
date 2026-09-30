import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.bot_instance import bot
from app.config import COMPANIES, settings
from app.database.base import async_session
from app.database.repo import (
    get_contract_date_mode,
    get_user,
    next_contract_number,
    save_contract,
)
from app.keyboards.main_menu import get_main_menu, get_menu_button
from app.keyboards.shartnoma import (
    get_company_keyboard,
    get_confirm_keyboard,
    get_nav_keyboard,
)
from app.services.docx_service import render_shartnoma
from app.services.pdf_service import convert_to_pdf
from app.states.shartnoma import ShartnomaForm

logger = logging.getLogger(__name__)
router = Router()


STEPS = {
    "uz": [
        ("firma_nomi", "2/3 — 🏢 Firma nomini kiriting."),
        ("stir_raqami", "3/3 — 🔢 STIR (INN) raqamini kiriting."),
    ],
    "ru": [
        ("firma_nomi", "2/3 — 🏢 Введите название фирмы."),
        ("stir_raqami", "3/3 — 🔢 Введите ИНН."),
    ],
}

STATES = {
    "firma_nomi": ShartnomaForm.firma_nomi,
    "stir_raqami": ShartnomaForm.stir_raqami,
}

TEXTS = {
    "uz": {
        "title": "📄 <b>Shartnoma yaratish</b>",
        "ask_company": "1/3 — 🏢 Qaysi kompaniya uchun shartnoma?",
        "confirm": "📋 <b>Tekshiring:</b>",
        "creating": "⏳ Hujjat tayyorlanmoqda...",
        "menu": "Asosiy menyu:",
        "number": "🔢 Raqam",
        "date": "📅 Sana",
        "firm": "🏢 Firma",
        "inn": "🔢 INN",
        "company": "🏢 Kompaniya",
        "denied": "⛔ Siz tasdiqlanmagansiz.",
    },
    "ru": {
        "title": "📄 <b>Создание договора</b>",
        "ask_company": "1/3 — 🏢 Для какой компании договор?",
        "confirm": "📋 <b>Проверьте:</b>",
        "creating": "⏳ Документ готовится...",
        "menu": "Главное меню:",
        "number": "🔢 Номер",
        "date": "📅 Дата",
        "firm": "🏢 Фирма",
        "inn": "🔢 ИНН",
        "company": "🏢 Компания",
        "denied": "⛔ Вы не подтверждены.",
    },
}


async def _check_approved(user_id: int) -> bool:
    async with async_session() as session:
        u = await get_user(session, user_id)
    return bool(u and u.status == "approved")


def _company_name(key: str) -> str:
    return COMPANIES.get(key, key)


async def _notify_admins(text: str):
    for admin_id in settings.admin_list:
        try:
            await bot.send_message(admin_id, text)
        except Exception as e:
            logger.error(f"Admin notify failed ({admin_id}): {e}")


async def _ask(message: Message, state: FSMContext, index: int, lang: str):
    steps = STEPS.get(lang, STEPS["uz"])
    if index >= len(steps):
        await _show_confirm(message, state, lang)
        return
    key, text = steps[index]
    await state.update_data(step=index)
    await state.set_state(STATES[key])
    await message.answer(
        text,
        reply_markup=get_nav_keyboard(show_back=index > 0, prefix="sh"),
    )


async def _handle(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    step = data.get("step", 0)
    steps = STEPS.get(lang, STEPS["uz"])
    key = steps[step][0]
    answers = data.get("answers", {})
    answers[key] = message.text or ""
    await state.update_data(answers=answers)
    await _ask(message, state, step + 1, lang)


async def _show_confirm(message: Message, state: FSMContext, lang: str):
    data = await state.get_data()
    a = data.get("answers", {})
    number = data.get("contract_number", "")
    date = data.get("contract_date", "")
    company = data.get("company", "")
    t = TEXTS.get(lang, TEXTS["uz"])
    text = (
        f"{t['confirm']}\n\n"
        f"{t['company']}: {_company_name(company)}\n"
        f"{t['number']}: {number}\n"
        f"{t['date']}: {date}\n"
        f"{t['firm']}: {a.get('firma_nomi', '—')}\n"
        f"{t['inn']}: {a.get('stir_raqami', '—')}"
    )
    await state.set_state(ShartnomaForm.confirm)
    await message.answer(text, reply_markup=get_confirm_keyboard("sh"))


async def _prepare_and_ask(message: Message, state: FSMContext, lang: str):
    data = await state.get_data()
    company = data.get("company", "")
    async with async_session() as session:
        number = await next_contract_number(session, company)
        date_mode = await get_contract_date_mode(session, company)

    if date_mode == "auto":
        date = datetime.now().strftime("%d.%m.%Y")
    else:
        date = date_mode

    await state.update_data(contract_number=number, contract_date=date)
    if lang == "uz":
        await message.answer(
            f"🏢 Kompaniya: <b>{_company_name(company)}</b>\n"
            f"🔢 Raqam: <b>{number}</b>\n"
            f"📅 Sana: <b>{date}</b>"
        )
    else:
        await message.answer(
            f"🏢 Компания: <b>{_company_name(company)}</b>\n"
            f"🔢 Номер: <b>{number}</b>\n"
            f"📅 Дата: <b>{date}</b>"
        )
    await _ask(message, state, 0, lang)


@router.message(F.text == "📄 Shartnoma yaratish")
async def start_shartnoma_uz(message: Message, state: FSMContext):
    if not await _check_approved(message.from_user.id):
        await message.answer(TEXTS["uz"]["denied"])
        return
    await state.clear()
    await state.update_data(answers={}, step=0, lang="uz")
    await message.answer(TEXTS["uz"]["title"], reply_markup=get_menu_button("uz"))
    await message.answer(
        TEXTS["uz"]["ask_company"],
        reply_markup=get_company_keyboard("sh"),
    )
    await state.set_state(ShartnomaForm.company)


@router.message(F.text == "📄 Создать договор")
async def start_shartnoma_ru(message: Message, state: FSMContext):
    if not await _check_approved(message.from_user.id):
        await message.answer(TEXTS["ru"]["denied"])
        return
    await state.clear()
    await state.update_data(answers={}, step=0, lang="ru")
    await message.answer(TEXTS["ru"]["title"], reply_markup=get_menu_button("ru"))
    await message.answer(
        TEXTS["ru"]["ask_company"],
        reply_markup=get_company_keyboard("sh"),
    )
    await state.set_state(ShartnomaForm.company)


@router.callback_query(F.data.startswith("sh:company:"))
async def sh_company(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        return
    key = call.data.split(":", 2)[2]
    if key not in COMPANIES:
        await call.answer("Noto‘g‘ri kompaniya.", show_alert=True)
        return
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.update_data(company=key)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await _prepare_and_ask(call.message, state, lang)
    await call.answer()


@router.message(F.text == "🏠 Menu")
async def back_to_menu_uz(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu("uz"))


@router.message(F.text == "🏠 Меню")
async def back_to_menu_ru(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=get_main_menu("ru"))


@router.message(ShartnomaForm.firma_nomi)
async def h_firma(m: Message, state: FSMContext):
    await _handle(m, state)


@router.message(ShartnomaForm.stir_raqami)
async def h_stir(m: Message, state: FSMContext):
    await _handle(m, state)


@router.callback_query(F.data == "sh:back")
async def sh_back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    step = data.get("step", 0)
    if step == 0:
        await call.answer(
            "Bu birinchi qadam." if lang == "uz" else "Это первый шаг.",
            show_alert=True,
        )
        return
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await _ask(call.message, state, step - 1, lang)
    await call.answer()


@router.callback_query(F.data == "sh:cancel")
async def sh_cancel(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    try:
        await call.message.edit_text("❌ Bekor qilindi." if lang == "uz" else "❌ Отменено.")
    except Exception:
        pass
    await call.message.answer(
        "Asosiy menyu:" if lang == "uz" else "Главное меню:",
        reply_markup=get_main_menu(lang),
    )
    await call.answer()


@router.callback_query(F.data == "sh:restart")
async def sh_restart(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        return
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    await state.update_data(answers={}, step=0, lang=lang)
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer(
        TEXTS[lang]["ask_company"],
        reply_markup=get_company_keyboard("sh"),
    )
    await state.set_state(ShartnomaForm.company)
    await call.answer()


@router.callback_query(F.data == "sh:submit")
async def sh_submit(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        await state.clear()
        return

    data = await state.get_data()
    lang = data.get("lang", "uz")
    a = data.get("answers", {})
    number = data.get("contract_number", "")
    date = data.get("contract_date", "")
    company = data.get("company", "")
    t = TEXTS.get(lang, TEXTS["uz"])

    try:
        await call.message.edit_text(t["creating"])
    except Exception:
        pass
    await call.answer()

    payload = {
        "shartnoma_raqami": number,
        "sana": date,
        "firma_nomi": a.get("firma_nomi", ""),
        "stir_raqami": a.get("stir_raqami", ""),
    }

    try:
        docx_path = render_shartnoma(company, payload)
    except Exception as e:
        logger.error(f"DOCX error: {e}")
        await call.message.answer(f"❌ Xato: {e}")
        await state.clear()
        return

    pdf_path = convert_to_pdf(docx_path)
    file_to_send = pdf_path if pdf_path else docx_path

    pdf_bytes = None
    pdf_name = ""
    if pdf_path and pdf_path.exists():
        pdf_bytes = pdf_path.read_bytes()
        pdf_name = pdf_path.name

    try:
        async with async_session() as session:
            await save_contract(
                session,
                company=company,
                inn=payload["stir_raqami"],
                firma=payload["firma_nomi"],
                number=payload["shartnoma_raqami"],
                date=payload["sana"],
                user_id=call.from_user.id,
                user_name=call.from_user.full_name,
                pdf_data=pdf_bytes,
                pdf_name=pdf_name,
            )
    except Exception as e:
        logger.error(f"DB error: {e}")

    file = FSInputFile(str(file_to_send))
    await bot.send_document(call.from_user.id, file)

    user = call.from_user
    username = f"@{user.username}" if user.username else "—"
    notify_text = (
        "📄 <b>YANGI SHARTNOMA</b>\n\n"
        f"🏢 Kompaniya: {_company_name(company)}\n"
        f"👤 User: {user.full_name}\n"
        f"🔗 Username: {username}\n"
        f"🏢 Firma: {payload['firma_nomi']}\n"
        f"🔢 INN: {payload['stir_raqami']}\n"
        f"🔢 Raqam: {payload['shartnoma_raqami']}\n"
        f"📅 Sana: {payload['sana']}"
    )
    await _notify_admins(notify_text)

    await state.clear()
    await call.message.answer(t["menu"], reply_markup=get_main_menu(lang))
