import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.bot_instance import bot
from app.database.base import async_session
from app.database.repo import save_contract
from app.keyboards.main_menu import get_main_menu, get_menu_button
from app.keyboards.shartnoma import get_confirm_keyboard, get_nav_keyboard
from app.services.docx_service import render_shartnoma
from app.services.pdf_service import convert_to_pdf
from app.states.shartnoma import ShartnomaForm

logger = logging.getLogger(__name__)
router = Router()


STEPS = {
    "uz": [
        ("shartnoma_raqami", "1/4 — 🔢 Shartnoma raqamini kiriting.\nMasalan: 197/25"),
        ("sana", "2/4 — 📅 Sanani kiriting.\nMasalan: 24.09.2026"),
        ("firma_nomi", "3/4 — 🏢 Firma nomini kiriting."),
        ("stir_raqami", "4/4 — 🔢 STIR (INN) raqamini kiriting."),
    ],
    "ru": [
        ("shartnoma_raqami", "1/4 — 🔢 Введите номер договора.\nНапример: 197/25"),
        ("sana", "2/4 — 📅 Введите дату.\nНапример: 24.09.2026"),
        ("firma_nomi", "3/4 — 🏢 Введите название фирмы."),
        ("stir_raqami", "4/4 — 🔢 Введите ИНН."),
    ],
}

STATES = {
    "shartnoma_raqami": ShartnomaForm.shartnoma_raqami,
    "sana": ShartnomaForm.sana,
    "firma_nomi": ShartnomaForm.firma_nomi,
    "stir_raqami": ShartnomaForm.stir_raqami,
}

TEXTS = {
    "uz": {
        "title": "📄 <b>Shartnoma yaratish</b>",
        "confirm": "📋 <b>Tekshiring:</b>",
        "creating": "⏳ Hujjat tayyorlanmoqda...",
        "menu": "Asosiy menyu:",
    },
    "ru": {
        "title": "📄 <b>Создание договора</b>",
        "confirm": "📋 <b>Проверьте:</b>",
        "creating": "⏳ Документ готовится...",
        "menu": "Главное меню:",
    },
}


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
    t = TEXTS.get(lang, TEXTS["uz"])
    text = (
        f"{t['confirm']}\n\n"
        f"🔢 Raqam: {a.get('shartnoma_raqami', '—')}\n"
        f"📅 Sana: {a.get('sana', '—')}\n"
        f"🏢 Firma: {a.get('firma_nomi', '—')}\n"
        f"🔢 INN: {a.get('stir_raqami', '—')}"
    )
    await state.set_state(ShartnomaForm.confirm)
    await message.answer(text, reply_markup=get_confirm_keyboard("sh"))


@router.message(F.text == "📄 Shartnoma yaratish")
async def start_shartnoma_uz(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(answers={}, step=0, lang="uz")
    await message.answer(
        TEXTS["uz"]["title"],
        reply_markup=get_menu_button("uz"),
    )
    await _ask(message, state, 0, "uz")


@router.message(F.text == "📄 Создать договор")
async def start_shartnoma_ru(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(answers={}, step=0, lang="ru")
    await message.answer(
        TEXTS["ru"]["title"],
        reply_markup=get_menu_button("ru"),
    )
    await _ask(message, state, 0, "ru")


@router.message(F.text == "🏠 Menu")
async def back_to_menu_uz(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu("uz"))


@router.message(F.text == "🏠 Меню")
async def back_to_menu_ru(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=get_main_menu("ru"))


@router.message(ShartnomaForm.shartnoma_raqami)
async def h_raqam(m: Message, state: FSMContext):
    await _handle(m, state)


@router.message(ShartnomaForm.sana)
async def h_sana(m: Message, state: FSMContext):
    await _handle(m, state)


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
    await call.message.edit_reply_markup(reply_markup=None)
    await _ask(call.message, state, step - 1, lang)
    await call.answer()


@router.callback_query(F.data == "sh:cancel")
async def sh_cancel(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    await call.message.edit_text("❌ Bekor qilindi." if lang == "uz" else "❌ Отменено.")
    await call.message.answer(
        "Asosiy menyu:" if lang == "uz" else "Главное меню:",
        reply_markup=get_main_menu(lang),
    )
    await call.answer()


@router.callback_query(F.data == "sh:restart")
async def sh_restart(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    await state.update_data(answers={}, step=0, lang=lang)
    await call.message.edit_reply_markup(reply_markup=None)
    await _ask(call.message, state, 0, lang)
    await call.answer()


@router.callback_query(F.data == "sh:submit")
async def sh_submit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    a = data.get("answers", {})
    t = TEXTS.get(lang, TEXTS["uz"])

    await call.message.edit_text(t["creating"])
    await call.answer()

    try:
        docx_path = render_shartnoma(a)
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
                inn=a.get("stir_raqami", ""),
                firma=a.get("firma_nomi", ""),
                number=a.get("shartnoma_raqami", ""),
                date=a.get("sana", ""),
                user_id=call.from_user.id,
                user_name=call.from_user.full_name,
                pdf_data=pdf_bytes,
                pdf_name=pdf_name,
            )
    except Exception as e:
        logger.error(f"DB error: {e}")

    file = FSInputFile(str(file_to_send))
    await bot.send_document(call.from_user.id, file)

    await state.clear()
    await call.message.answer(t["menu"], reply_markup=get_main_menu(lang))
