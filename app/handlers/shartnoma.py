import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, ReplyKeyboardRemove

from app.bot_instance import bot
from app.keyboards.main_menu import get_main_menu
from app.keyboards.shartnoma import get_confirm_keyboard, get_nav_keyboard
from app.services.docx_service import render_shartnoma
from app.states.shartnoma import ShartnomaForm

logger = logging.getLogger(__name__)
router = Router()


STEPS = [
    ("shartnoma_raqami", "1/4 — 🔢 Shartnoma raqamini kiriting.\nMasalan: 197/25"),
    ("sana", "2/4 — 📅 Sanani kiriting.\nMasalan: 24.09.2026"),
    ("firma_nomi", "3/4 — 🏢 Firma nomini kiriting."),
    ("stir_raqami", "4/4 — 🔢 STIR raqamini kiriting."),
]

STATES = {
    "shartnoma_raqami": ShartnomaForm.shartnoma_raqami,
    "sana": ShartnomaForm.sana,
    "firma_nomi": ShartnomaForm.firma_nomi,
    "stir_raqami": ShartnomaForm.stir_raqami,
}


async def _ask(message: Message, state: FSMContext, index: int):
    if index >= len(STEPS):
        await _show_confirm(message, state)
        return
    key, text = STEPS[index]
    await state.update_data(step=index)
    await state.set_state(STATES[key])
    await message.answer(text, reply_markup=get_nav_keyboard(show_back=index > 0, prefix="sh"))


async def _handle(message: Message, state: FSMContext):
    data = await state.get_data()
    step = data.get("step", 0)
    key = STEPS[step][0]
    answers = data.get("answers", {})
    answers[key] = message.text or ""
    await state.update_data(answers=answers)
    await _ask(message, state, step + 1)


async def _show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    a = data.get("answers", {})
    text = (
        "📋 <b>Tekshiring:</b>\n\n"
        f"🔢 Raqam: {a.get('shartnoma_raqami', '—')}\n"
        f"📅 Sana: {a.get('sana', '—')}\n"
        f"🏢 Firma: {a.get('firma_nomi', '—')}\n"
        f"🔢 STIR: {a.get('stir_raqami', '—')}"
    )
    await state.set_state(ShartnomaForm.confirm)
    await message.answer(text, reply_markup=get_confirm_keyboard("sh"))


@router.message(F.text == "📄 Shartnoma yaratish")
async def start_shartnoma(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(answers={}, step=0)
    await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await message.answer("📄 <b>Shartnoma yaratish</b>")
    await _ask(message, state, 0)


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
    step = data.get("step", 0)
    if step == 0:
        await call.answer("Bu birinchi qadam.", show_alert=True)
        return
    await call.message.edit_reply_markup(reply_markup=None)
    await _ask(call.message, state, step - 1)
    await call.answer()


@router.callback_query(F.data == "sh:cancel")
async def sh_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Bekor qilindi.")
    await call.message.answer("Asosiy menyu:", reply_markup=get_main_menu("uz"))
    await call.answer()


@router.callback_query(F.data == "sh:restart")
async def sh_restart(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.update_data(answers={}, step=0)
    await call.message.edit_reply_markup(reply_markup=None)
    await _ask(call.message, state, 0)
    await call.answer()


@router.callback_query(F.data == "sh:submit")
async def sh_submit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    a = data.get("answers", {})

    await call.message.edit_text("⏳ Hujjat tayyorlanmoqda...")
    await call.answer()

    try:
        docx_path = render_shartnoma(a)
    except Exception as e:
        logger.error(f"DOCX error: {e}")
        await call.message.answer(f"❌ Xato: {e}")
        await state.clear()
        return

    file = FSInputFile(str(docx_path))
    await bot.send_document(call.from_user.id, file)

    await state.clear()
    await call.message.answer("Asosiy menyu:", reply_markup=get_main_menu("uz"))
