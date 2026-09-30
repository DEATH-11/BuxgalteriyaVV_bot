from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.config import COMPANIES


def get_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin:users")],
            [InlineKeyboardButton(text="💊 Dorilar", callback_data="admin:drugs")],
            [InlineKeyboardButton(text="📄 Shartnomalar", callback_data="admin:contracts")],
            [InlineKeyboardButton(text="📊 Spetsifikatsiyalar", callback_data="admin:speks")],
            [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin:settings")],
        ]
    )


# ========== USERS ==========

def get_users_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏳ Kutilmoqda", callback_data="admin:users:pending")],
            [InlineKeyboardButton(text="✅ Tasdiqlangan", callback_data="admin:users:approved")],
            [InlineKeyboardButton(text="❌ Rad etilgan", callback_data="admin:users:rejected")],
            [InlineKeyboardButton(text="📋 Barchasi", callback_data="admin:users:ALL")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")],
        ]
    )


def get_users_company_keyboard(status: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📋 Hammasi", callback_data=f"admin:uc:ALL:{status}")],
    ]
    for key, name in COMPANIES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"🏢 {name}",
                callback_data=f"admin:uc:{key}:{status}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:users")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_user_view_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 Kompaniyani o‘zgartirish", callback_data=f"admin:user:co:{user_id}")],
            [InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"admin:user:del:{user_id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:users")],
        ]
    )


def get_user_company_keyboard(user_id: int) -> InlineKeyboardMarkup:
    buttons = []
    for key, name in COMPANIES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"🏢 {name}",
                callback_data=f"admin:user:setco:{user_id}:{key}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin:user:view:{user_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ========== DRUGS ==========

def get_drugs_company_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for key, name in COMPANIES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"🏢 {name}",
                callback_data=f"admin:drugs:co:{key}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_drugs_menu(company: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Dori qo‘shish", callback_data=f"admin:drug:add:{company}")],
            [InlineKeyboardButton(text="📋 Ro‘yxat", callback_data=f"admin:drug:list:{company}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:drugs")],
        ]
    )


def get_drugs_list_keyboard(drugs: list, company: str) -> InlineKeyboardMarkup:
    buttons = []
    for d in drugs:
        price = f"{int(d.price):,}".replace(",", " ")
        buttons.append([
            InlineKeyboardButton(
                text=f"✏️ {d.name} — {price}",
                callback_data=f"admin:drug:edit:{d.id}",
            ),
            InlineKeyboardButton(text="🗑", callback_data=f"admin:drug:del:{d.id}:{company}"),
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin:drugs:co:{company}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_drug_edit_keyboard(drug_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Nomi", callback_data=f"admin:drug:en:{drug_id}")],
            [InlineKeyboardButton(text="📏 Birligi", callback_data=f"admin:drug:eu:{drug_id}")],
            [InlineKeyboardButton(text="💰 Narxi", callback_data=f"admin:drug:ep:{drug_id}")],
            [InlineKeyboardButton(text="🗑 O‘chirish", callback_data=f"admin:drug:del2:{drug_id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:drugs")],
        ]
    )


# ========== CONTRACTS ==========

def get_contracts_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 INN bo‘yicha qidirish", callback_data="admin:contract:search")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")],
        ]
    )


def get_contracts_list_keyboard(contracts: list) -> InlineKeyboardMarkup:
    buttons = []
    for c in contracts:
        buttons.append([
            InlineKeyboardButton(
                text=f"📄 {c.firma} — {c.number}",
                callback_data=f"admin:contract:view:{c.id}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:contracts")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_contract_view_keyboard(contract_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 PDF yuklab olish", callback_data=f"admin:contract:pdf:{contract_id}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:contracts")],
        ]
    )


# ========== SETTINGS ==========

def get_settings_company_keyboard() -> InlineKeyboardMarkup:
    """Sozlamalar — kompaniya tanlash."""
    buttons = []
    for key, name in COMPANIES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"🏢 {name}",
                callback_data=f"admin:settings:co:{key}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_company_settings_menu(
    company: str, prefix: str, spek_number: int, date_mode: str
) -> InlineKeyboardMarkup:
    """Bitta kompaniya sozlamalari."""
    date_label = "Avto (bugungi)" if date_mode == "auto" else date_mode
    name = COMPANIES.get(company, company)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"🔢 Shartnoma raqami: {prefix}",
                callback_data=f"admin:set:contract:{company}",
            )],
            [InlineKeyboardButton(
                text=f"📅 Shartnoma sanasi: {date_label}",
                callback_data=f"admin:set:date:{company}",
            )],
            [InlineKeyboardButton(
                text=f"📊 Spek raqami: {spek_number}",
                callback_data=f"admin:set:spek:{company}",
            )],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="admin:settings")],
        ]
    )


def get_date_mode_keyboard(company: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 Avto (bugungi sana)", callback_data=f"admin:date:auto:{company}")],
            [InlineKeyboardButton(text="✏️ Sanani kiritish", callback_data=f"admin:date:manual:{company}")],
            [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"admin:settings:co:{company}")],
        ]
    )


# ========== COMMON ==========

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="admin:back")],
        ]
    )


def get_settings_cancel_keyboard(company: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Bekor qilish", callback_data=f"admin:settings:co:{company}")],
        ]
    )
