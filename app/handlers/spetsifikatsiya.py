import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message, ReplyKeyboardRemove

from app.bot_instance import bot
from app.keyboards.main_menu import get_main_menu
from app.keyboards.shartnoma import get_confirm_keyboard, get_nav_keyboard
from app.services.docx_service import render_spetsifikatsiya
from app.services.pdf_service import convert_to_pdf
from app.states.spetsifikatsiya import SpetsifikatsiyaForm

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text == "📊 Spetsifikatsiya yaratish")
async def start_spec(message: Message, state: FSMContext):
    await state.clear()
    await state.update_data(items=[], idx=0, count=0)
    await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await message.answer("📊 <b>Spetsifikatsiya yaratish</b>")
    await message.answer(
        "1/2 — 🔢 Spetsifikatsiya raqamini kiriting.",
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.spek_raqami)


@router.message(SpetsifikatsiyaForm.spek_raqami)
async def sp_raqam(m: Message, state: FSMContext):
    await state.update_data(spek_raqami=m.text or "")
    await m.answer(
        "2/2 — 💊 Nechta dori kiritasiz? (raqam)\nMasalan: 3",
        reply_markup=get_nav_keyboard(show_back=True, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.count)


@router.message(SpetsifikatsiyaForm.count)
async def sp_count(m: Message, state: FSMContext):
    try:
        count = int((m.text or "").strip())
        if count <= 0:
            raise ValueError
    except ValueError:
        await m.answer("❌ Iltimos, butun musbat raqam kiriting.")
        return

    await state.update_data(count=count, idx=0, items=[])
    await m.answer(
        f"💊 1/{count} — Dori nomini kiriting.",
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.item_dori)


@router.message(SpetsifikatsiyaForm.item_dori)
async def sp_item_dori(m: Message, state: FSMContext):
    await state.update_data(current_dori=m.text or "")
    await m.answer(
        "🔢 Miqdorini kiriting (soni):",
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.item_miqdor)


@router.message(SpetsifikatsiyaForm.item_miqdor)
async def sp_item_miqdor(m: Message, state: FSMContext):
    try:
        qty = float((m.text or "").replace(",", ".").strip())
    except ValueError:
        await m.answer("❌ Raqam kiriting.")
        return
    await state.update_data(current_miqdor=qty)
    await m.answer(
        "💰 Narxini kiriting (1 dona uchun):",
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.item_narx)


@router.message(SpetsifikatsiyaForm.item_narx)
async def sp_item_narx(m: Message, state: FSMContext):
    try:
        price = float((m.text or "").replace(",", ".").replace(" ", "").strip())
    except ValueError:
        await m.answer("❌ Raqam kiriting.")
        return

    data = await state.get_data()
    name = data.get("current_dori", "")
    qty = data.get("current_miqdor", 0)
    total = qty * price

    items = data.get("items", [])
    items.append({
        "dori_nomi": name,
        "miqdori": qty,
        "narxi": price,
        "umumiy_narxi": total,
    })
    idx = data.get("idx", 0) + 1
    count = data.get("count", 0)
    await state.update_data(items=items, idx=idx)

    if idx >= count:
        await _show_confirm(m, state)
        return

    await m.answer(
        f"💊 {idx + 1}/{count} — Dori nomini kiriting.",
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.item_dori)


async def _show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])
    lines = ["📋 <b>Tekshiring:</b>\n"]
    lines.append(f"🔢 Raqam: {data.get('spek_raqami', '—')}\n")
    lines.append("<b>Dorilar:</b>")
    for i, item in enumerate(items, 1):
        lines.append(
            f"{i}. {item['dori_nomi']} — {item['miqdori']} x {item['narxi']} = {item['umumiy_narxi']}"
        )
    await state.set_state(SpetsifikatsiyaForm.confirm)
    await message.answer("\n".join(lines), reply_markup=get_confirm_keyboard("sp"))


@router.callback_query(F.data == "sp:cancel")
async def sp_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("❌ Bekor qilindi.")
    await call.message.answer("Asosiy menyu:", reply_markup=get_main_menu("uz"))
    await call.answer()


@router.callback_query(F.data == "sp:restart")
async def sp_restart(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_reply_markup(reply_markup=None)
    await start_spec(call.message, state)
    await call.answer()


@router.callback_query(F.data == "sp:back")
async def sp_back(call: CallbackQuery, state: FSMContext):
    await call.answer("Bu qadamda orqaga qaytish yo‘q.", show_alert=True)


@router.callback_query(F.data == "sp:submit")
async def sp_submit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])

    payload = {
        "spek_raqami": data.get("spek_raqami", ""),
        "items": items,
        "jami_summa": sum(i["umumiy_narxi"] for i in items),
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
    await call.message.answer("Asosiy menyu:", reply_markup=get_main_menu("uz"))
