import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message

from app.bot_instance import bot
from app.config import COMPANIES, settings
from app.database.base import async_session
from app.database.repo import (
    get_drug,
    get_drugs_by_company,
    get_user,
    save_spek,
)
from app.keyboards.main_menu import get_main_menu, get_menu_button
from app.keyboards.shartnoma import get_company_keyboard
from app.keyboards.spetsifikatsiya import (
    get_confirm_keyboard,
    get_drugs_keyboard,
    get_edit_keyboard,
    get_qty_keyboard,
)
from app.services.docx_service import render_spetsifikatsiya
from app.services.pdf_service import convert_to_pdf
from app.states.spetsifikatsiya import SpetsifikatsiyaForm

logger = logging.getLogger(__name__)
router = Router()


DENIED_UZ = "⛔ Siz tasdiqlanmagansiz."
DENIED_RU = "⛔ Вы не подтверждены."

TEXTS = {
    "uz": {
        "title": "📊 <b>Spetsifikatsiya yaratish</b>",
        "ask_company": "1/2 — 🏢 Qaysi kompaniya uchun?",
        "pick_drug": "💊 <b>Dori tanlang:</b>",
        "empty_drugs": "❌ Bu kompaniya uchun dorilar ro‘yxati bo‘sh.",
        "menu": "Asosiy menyu:",
    },
    "ru": {
        "title": "📊 <b>Создание спецификации</b>",
        "ask_company": "1/2 — 🏢 Для какой компании?",
        "pick_drug": "💊 <b>Выберите товар:</b>",
        "empty_drugs": "❌ Для этой компании список товаров пуст.",
        "menu": "Главное меню:",
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


def _fmt(num) -> str:
    try:
        return f"{int(round(float(num))):,}".replace(",", " ")
    except Exception:
        return str(num)


async def _show_drugs(message: Message, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", {})
    company = data.get("company", "")
    lang = data.get("lang", "uz")
    async with async_session() as session:
        drugs = await get_drugs_by_company(session, company)
    if not drugs:
        await message.answer(TEXTS[lang]["empty_drugs"])
        return
    await state.set_state(SpetsifikatsiyaForm.pick_drug)
    await message.answer(
        TEXTS[lang]["pick_drug"],
        reply_markup=get_drugs_keyboard(drugs, selected),
    )


async def _show_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    selected = data.get("selected", {})
    if not selected:
        await message.answer("ℹ️ Hozircha hech narsa tanlanmagan.")
        await _show_drugs(message, state)
        return
    await state.set_state(SpetsifikatsiyaForm.pick_drug)
    await message.answer(
        "✏️ <b>Tanlangan dorilar:</b>",
        reply_markup=get_edit_keyboard(selected),
    )


@router.message(F.text == "📊 Spetsifikatsiya yaratish")
async def start_spec_uz(message: Message, state: FSMContext):
    if not await _check_approved(message.from_user.id):
        await message.answer(DENIED_UZ)
        return
    await state.clear()
    await state.update_data(selected={}, items=[], lang="uz")
    await message.answer(TEXTS["uz"]["title"], reply_markup=get_menu_button("uz"))
    await message.answer(
        TEXTS["uz"]["ask_company"],
        reply_markup=get_company_keyboard("sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.company)


@router.message(F.text == "📊 Создать спецификацию")
async def start_spec_ru(message: Message, state: FSMContext):
    if not await _check_approved(message.from_user.id):
        await message.answer(DENIED_RU)
        return
    await state.clear()
    await state.update_data(selected={}, items=[], lang="ru")
    await message.answer(TEXTS["ru"]["title"], reply_markup=get_menu_button("ru"))
    await message.answer(
        TEXTS["ru"]["ask_company"],
        reply_markup=get_company_keyboard("sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.company)


@router.callback_query(F.data.startswith("sp:company:"))
async def sp_company(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        return
    key = call.data.split(":", 2)[2]
    if key not in COMPANIES:
        await call.answer("Noto‘g‘ri kompaniya.", show_alert=True)
        return
    await state.update_data(company=key, selected={}, items=[])
    await call.message.edit_reply_markup(reply_markup=None)
    await _show_drugs(call.message, state)
    await call.answer()


@router.message(F.text == "🏠 Menu")
async def back_to_menu_uz(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Asosiy menyu:", reply_markup=get_main_menu("uz"))


@router.message(F.text == "🏠 Меню")
async def back_to_menu_ru(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню:", reply_markup=get_main_menu("ru"))


@router.callback_query(F.data.startswith("spec:pick:"))
async def pick_drug(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        return
    drug_id = int(call.data.split(":")[2])
    data = await state.get_data()
    selected = data.get("selected", {})

    if drug_id in selected:
        await call.answer("Bu dori allaqachon tanlangan.", show_alert=True)
        return

    async with async_session() as session:
        drug = await get_drug(session, drug_id)
    if not drug:
        await call.answer("Dori topilmadi", show_alert=True)
        return

    await state.update_data(current_drug_id=drug_id)
    await state.set_state(SpetsifikatsiyaForm.enter_qty)
    price_str = _fmt(drug.price)
    await call.message.edit_text(
        f"💊 <b>{drug.name}</b>\n"
        f"💰 Narxi: {price_str}\n\n"
        "Nechta olasiz?",
        reply_markup=get_qty_keyboard(),
    )
    await call.answer()


@router.message(SpetsifikatsiyaForm.enter_qty)
async def enter_qty(m: Message, state: FSMContext):
    if not await _check_approved(m.from_user.id):
        await m.answer(DENIED_UZ)
        await state.clear()
        return
    data = await state.get_data()
    drug_id = data.get("current_drug_id")
    try:
        qty = float((m.text or "").replace(",", ".").strip())
        if qty <= 0:
            raise ValueError
    except ValueError:
        await m.answer("❌ Iltimos, musbat raqam kiriting.")
        return

    async with async_session() as session:
        drug = await get_drug(session, drug_id)
    if not drug:
        await m.answer("❌ Dori topilmadi.")
        return

    selected = data.get("selected", {})
    selected[drug_id] = {
        "name": drug.name,
        "unit": drug.unit,
        "price": drug.price,
        "qty": qty,
    }
    await state.update_data(selected=selected)

    await m.answer(f"✅ {drug.name} tanlandi.")
    await _show_drugs(m, state)


@router.callback_query(F.data == "spec:edit")
async def edit_selected(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        return
    await call.message.edit_reply_markup(reply_markup=None)
    await _show_edit(call.message, state)
    await call.answer()


@router.callback_query(F.data == "spec:add_more")
async def add_more(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        return
    await call.message.edit_reply_markup(reply_markup=None)
    await _show_drugs(call.message, state)
    await call.answer()


@router.callback_query(F.data.startswith("spec:del:"))
async def del_drug(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        return
    drug_id = int(call.data.split(":")[2])
    data = await state.get_data()
    selected = data.get("selected", {})
    if drug_id in selected:
        del selected[drug_id]
    await state.update_data(selected=selected)
    await call.message.edit_reply_markup(reply_markup=None)
    await _show_edit(call.message, state)
    await call.answer("🗑 O‘chirildi")


@router.callback_query(F.data.startswith("spec:edit_qty:"))
async def edit_qty_start(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        return
    drug_id = int(call.data.split(":")[2])
    data = await state.get_data()
    selected = data.get("selected", {})
    item = selected.get(drug_id)
    if not item:
        await call.answer("Topilmadi", show_alert=True)
        return
    await state.update_data(current_drug_id=drug_id)
    await state.set_state(SpetsifikatsiyaForm.enter_qty)
    await call.message.edit_text(
        f"✏️ <b>{item['name']}</b>\n"
        f"Hozirgi miqdor: {item['qty']}\n\n"
        "Yangi miqdorni kiriting:",
        reply_markup=get_qty_keyboard(),
    )
    await call.answer()


@router.callback_query(F.data == "spec:done")
async def spec_done(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        return
    data = await state.get_data()
    selected = data.get("selected", {})
    if not selected:
        await call.answer("Hech narsa tanlanmagan.", show_alert=True)
        return

    items = []
    for d in selected.values():
        items.append({
            "dori_nomi": d["name"],
            "unit": d["unit"],
            "miqdori": d["qty"],
            "narxi": d["price"],
            "umumiy_narxi": d["qty"] * d["price"],
        })

    total = sum(i["umumiy_narxi"] for i in items)
    await state.update_data(items=items, total=total)

    lines = ["📋 <b>Tekshiring:</b>\n"]
    for i, item in enumerate(items, 1):
        lines.append(
            f"{i}. {item['dori_nomi']} — {item['miqdori']} x {_fmt(item['narxi'])} = {_fmt(item['umumiy_narxi'])}"
        )
    lines.append(f"\n💰 <b>Jami:</b> {_fmt(total)}")

    await state.set_state(SpetsifikatsiyaForm.confirm)
    await call.message.edit_text("\n".join(lines), reply_markup=get_confirm_keyboard())
    await call.answer()


@router.callback_query(F.data == "spec:cancel")
async def spec_cancel(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    await call.message.edit_text("❌ Bekor qilindi.")
    await call.message.answer("Asosiy menyu:", reply_markup=get_main_menu(lang))
    await call.answer()


@router.callback_query(F.data == "spec:restart")
async def spec_restart(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        return
    data = await state.get_data()
    lang = data.get("lang", "uz")
    await state.clear()
    await state.update_data(selected={}, items=[], lang=lang)
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer(
        TEXTS[lang]["ask_company"],
        reply_markup=get_company_keyboard("sp"),
    )
    await state.set_state(SpetsifikatsiyaForm.company)
    await call.answer()


@router.callback_query(F.data == "spec:submit")
async def spec_submit(call: CallbackQuery, state: FSMContext):
    if not await _check_approved(call.from_user.id):
        await call.answer("Siz tasdiqlanmagansiz.", show_alert=True)
        await state.clear()
        return

    data = await state.get_data()
    items = data.get("items", [])
    total = data.get("total", 0)
    lang = data.get("lang", "uz")
    company = data.get("company", "")

    async with async_session() as session:
        spek = await save_spek(
            session,
            company=company,
            user_id=call.from_user.id,
            user_name=call.from_user.full_name,
            items=items,
            total=total,
        )

    payload = {
        "spek_raqami": spek.number,
        "items": items,
        "jami_summa": total,
    }

    await call.message.edit_text("⏳ Hujjat tayyorlanmoqda...")
    await call.answer()

    try:
        docx_path = render_spetsifikatsiya(company, payload)
    except Exception as e:
        logger.error(f"DOCX error: {e}")
        await call.message.answer(f"❌ Xato: {e}")
        await state.clear()
        return

    pdf_path = convert_to_pdf(docx_path)
    file_to_send = pdf_path if pdf_path else docx_path
    file = FSInputFile(str(file_to_send))
    await bot.send_document(call.from_user.id, file)

    user = call.from_user
    username = f"@{user.username}" if user.username else "—"
    lines = [
        "📊 <b>YANGI SPETSIFFIKATSIYA</b>\n",
        f"🏢 Kompaniya: {_company_name(company)}",
        f"👤 User: {user.full_name}",
        f"🔗 Username: {username}",
        f"🔢 Raqam: {spek.number}",
        f"💰 Jami: {_fmt(total)} so'm\n",
        "💊 <b>Dorilar:</b>",
    ]
    for i, item in enumerate(items, 1):
        lines.append(
            f"{i}. {item['dori_nomi']} — {item['miqdori']} x {_fmt(item['narxi'])} = {_fmt(item['umumiy_narxi'])}"
        )
    await _notify_admins("\n".join(lines))

    await state.clear()
    await call.message.answer("Asosiy menyu:", reply_markup=get_main_menu(lang))
