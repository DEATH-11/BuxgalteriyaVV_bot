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


TEXTS = {
    "uz": {
        "title": "📊 <b>Spetsifikatsiya yaratish</b>",
        "ask_number": "1/2 — 🔢 Spetsifikatsiya raqamini kiriting.",
        "ask_count": "2/2 — 💊 Nechta dori kiritasiz? (raqam)\nMasalan: 3",
        "ask_dori": "💊 {n}/{total} — Dori nomini kiriting.",
        "ask_miqdor": "🔢 Miqdorini kiriting (soni):",
        "ask_narx": "💰 Narxini kiriting (1 dona uchun):",
        "error_num": "❌ Iltimos, butun musbat raqam kiriting.",
        "error_digit": "❌ Raqam kiriting.",
        "confirm": "📋 <b>Tekshiring:</b>",
        "drugs": "<b>Dorilar:</b>",
        "creating": "⏳ Hujjat tayyorlanmoqda...",
        "menu": "Asosiy menyu:",
        "cancel": "❌ Bekor qilindi.",
        "back": "Bu qadamda orqaga qaytish yo‘q.",
    },
    "ru": {
        "title": "📊 <b>Создание спецификации</b>",
        "ask_number": "1/2 — 🔢 Введите номер спецификации.",
        "ask_count": "2/2 — 💊 Сколько товаров будете вводить? (число)\nНапример: 3",
        "ask_dori": "💊 {n}/{total} — Введите название товара.",
        "ask_miqdor": "🔢 Введите количество:",
        "ask_narx": "💰 Введите цену (за 1 единицу):",
        "error_num": "❌ Введите целое положительное число.",
        "error_digit": "❌ Введите число.",
        "confirm": "📋 <b>Проверьте:</b>",
        "drugs": "<b>Товары:</b>",
        "creating": "⏳ Документ готовится...",
        "menu": "Главное меню:",
        "cancel": "❌ Отменено.",
        "back": "На этом шаге возврат невозможен.",
    },
}


@router.message(F.text == "📊 Spetsifikatsiya yaratish")
async def start_spec_uz(message: Message, state: FSMContext):
    await _start(message, state, "uz")


@router.message(F.text == "📊 Создать спецификацию")
async def start_spec_ru(message: Message, state: FSMContext):
    await _start(message, state, "ru")


async def _start(message: Message, state: FSMContext, lang: str):
    t = TEXTS[lang]
    await state.clear()
    await state.update_data(items=[], idx=0, count=0, lang=lang)
    await message.answer("⏳", reply_markup=ReplyKeyboardRemove())
    await message.answer(t["title"])
    await message.answer(
        t["ask_number"],
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.spek_raqami)


@router.message(SpetsifikatsiyaForm.spek_raqami)
async def sp_raqam(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    t = TEXTS[lang]
    await state.update_data(spek_raqami=m.text or "")
    await m.answer(
        t["ask_count"],
        reply_markup=get_nav_keyboard(show_back=True, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.count)


@router.message(SpetsifikatsiyaForm.count)
async def sp_count(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    t = TEXTS[lang]
    try:
        count = int((m.text or "").strip())
        if count <= 0:
            raise ValueError
    except ValueError:
        await m.answer(t["error_num"])
        return

    await state.update_data(count=count, idx=0, items=[])
    await m.answer(
        t["ask_dori"].format(n=1, total=count),
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.item_dori)


@router.message(SpetsifikatsiyaForm.item_dori)
async def sp_item_dori(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    t = TEXTS[lang]
    await state.update_data(current_dori=m.text or "")
    await m.answer(
        t["ask_miqdor"],
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.item_miqdor)


@router.message(SpetsifikatsiyaForm.item_miqdor)
async def sp_item_miqdor(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    t = TEXTS[lang]
    try:
        qty = float((m.text or "").replace(",", ".").strip())
    except ValueError:
        await m.answer(t["error_digit"])
        return
    await state.update_data(current_miqdor=qty)
    await m.answer(
        t["ask_narx"],
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.item_narx)


@router.message(SpetsifikatsiyaForm.item_narx)
async def sp_item_narx(m: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    t = TEXTS[lang]
    try:
        price = float((m.text or "").replace(",", ".").replace(" ", "").strip())
    except ValueError:
        await m.answer(t["error_digit"])
        return

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
        await _show_confirm(m, state, lang)
        return

    await m.answer(
        t["ask_dori"].format(n=idx + 1, total=count),
        reply_markup=get_nav_keyboard(show_back=False, prefix="sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.item_dori)


async def _show_confirm(message: Message, state: FSMContext, lang: str):
    data = await state.get_data()
    t = TEXTS[lang]
    items = data.get("items", [])
    lines = [t["confirm"], ""]
    lines.append(f"🔢 {data.get('spek_raqami', '—')}\n")
    lines.append(t["drugs"])
    for i, item in enumerate(items, 1):
        lines.append(
            f"{i}. {item['dori_nomi']} — {item['miqdori']} x {item['narxi']} = {item['umumiy_narxi']}"
        )
    await state.set_state(SpetsifikatsiyaForm.confirm)
    await message.answer("\n".join(lines), reply_markup=get_confirm_keyboard("sp"))


@router.callback_query(F.data == "sp:cancel")
async def sp_cancel(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    t = TEXTS[lang]
    await state.clear()
    await call.message.edit_text(t["cancel"])
    await call.message.answer(t["menu"], reply_markup=get_main_menu(lang))
    await call.answer()


@router.callback_query(F.data == "sp:restart")
async def sp_restart(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    await call.message.edit_reply_markup(reply_markup=None)
    await _start(call.message, state, lang)
    await call.answer()


@router.callback_query(F.data == "sp:back")
async def sp_back(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await call.answer(TEXTS[lang]["back"], show_alert=True)


@router.callback_query(F.data == "sp:submit")
async def sp_submit(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    t = TEXTS[lang]
    items = data.get("items", [])

    payload = {
        "spek_raqami": data.get("spek_raqami", ""),
        "items": items,
        "jami_summa": sum(i["umumiy_narxi"] for i in items),
    }

    await call.message.edit_text(t["creating"])
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
    await call.message.answer(t["menu"], reply_markup=get_main_menu(lang))
