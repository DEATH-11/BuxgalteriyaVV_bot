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
    await state.update_data(answers={}, items=[], idx=0, step=0)
    await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await message.answer("📊 <b>Spetsifikatsiya yaratish</b>")
    await message.answer(
        "1/5 — 🔢 Spetsifikatsiya raqamini kiriting.",
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.raqam)


@router.message(SpetsifikatsiyaForm.raqam)
async def sp_raqam(m: Message, state: FSMContext):
    await state.update_data(raqam=m.text or "")
    await m.answer(
        "2/5 — 📅 Sanani kiriting.\nMasalan: 24.09.2026",
        reply_markup=get_nav_keyboard(show_back=True, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.sana)


@router.message(SpetsifikatsiyaForm.sana)
async def sp_sana(m: Message, state: FSMContext):
    await state.update_data(sana=m.text or "")
    await m.answer(
        "3/5 — 🏢 Firma nomini kiriting.",
        reply_markup=get_nav_keyboard(show_back=True, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.firma)


@router.message(SpetsifikatsiyaForm.firma)
async def sp_firma(m: Message, state: FSMContext):
    await state.update_data(firma=m.text or "")
    await m.answer(
        "4/5 — 🔢 STIR raqamini kiriting.",
        reply_markup=get_nav_keyboard(show_back=True, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.stir)


@router.message(SpetsifikatsiyaForm.stir)
async def sp_stir(m: Message, state: FSMContext):
    await state.update_data(stir=m.text or "")
    await m.answer(
        "5/5 — 💊 Nechta dori kiritasiz? (raqam)\nMasalan: 3",
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
    await state.set_state(SpetsifikatsiyaForm.item_name)


@router.message(SpetsifikatsiyaForm.item_name)
async def sp_item_name(m: Message, state: FSMContext):
    await state.update_data(current_name=m.text or "")
    await m.answer(
        "🔢 Soni (miqdori):",
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.item_qty)


@router.message(SpetsifikatsiyaForm.item_qty)
async def sp_item_qty(m: Message, state: FSMContext):
    try:
        qty = float((m.text or "").replace(",", ".").strip())
    except ValueError:
        await m.answer("❌ Raqam kiriting.")
        return
    await state.update_data(current_qty=qty)
    await m.answer(
        "💰 Narxi (1 dona uchun):",
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.item_price)


@router.message(SpetsifikatsiyaForm.item_price)
async def sp_item_price(m: Message, state: FSMContext):
    try:
        price = float((m.text or "").replace(",", ".").strip())
    except ValueError:
        await m.answer("❌ Raqam kiriting.")
        return

    data = await state.get_data()
    name = data.get("current_name", "")
    qty = data.get("current_qty", 0)
    total = qty * price

    items = data.get("items", [])
    items.append({
        "name": name,
        "qty": qty,
        "price": price,
        "total": total,
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
    await state.set_state(SpetsifikatsiyaForm.item_name)


async def _show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    items = data.get("items", [])
    lines = ["📋 <b>Tekshiring:</b>\n"]
    lines.append(f"🔢 Raqam: {data.get('raqam', '—')}")
    lines.append(f"📅 Sana: {data.get('sana', '—')}")
    lines.append(f"🏢 Firma: {data.get('firma', '—')}")
    lines.append(f"🔢 STIR: {data.get('stir', '—')}\n")
    lines.append("<b>Dorilar:</b>")
    for i, item in enumerate(items, 1):
        lines.append(
            f"{i}. {item['name']} — {item['qty']} x {item['price']} = {item['total']}"
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
    await call.answer("Orqaga qaytish bu qadamda mavjud emas.", show_alert=True)


@router.callback_query(F.data == "sp:submit")
async def sp_submit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payload = {
        "raqam": data.get("raqam", ""),
        "sana": data.get("sana", ""),
        "firma": data.get("firma", ""),
        "stir": data.get("stir", ""),
        "items": data.get("items", []),
        "total_sum": sum(i["total"] for i in data.get("items", [])),
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
