from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from app.config import settings
from app.database.base import async_session
from app.database.repo import get_user


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        user_id = event.from_user.id

        # Admin — har doim ruxsat
        if user_id in settings.admin_list:
            return await handler(event, data)

        # Foydalanuvchini bazadan tekshiramiz
        async with async_session() as session:
            user = await get_user(session, user_id)

        # Tasdiqlangan bo‘lsa — davom etamiz
        if user and user.status == "approved":
            return await handler(event, data)

        # Tasdiqlanmagan — hech narsa qilmaymiz
        # Faqat /start va til tanlash uchun ruxsat beramiz
        if isinstance(event, Message):
            text = event.text or ""
            if text.startswith("/start") or text == "/menu":
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            if event.data and event.data.startswith("lang:"):
                return await handler(event, data)

        # Qolgan hamma narsani bloklaymiz
        if isinstance(event, Message):
            try:
                await event.answer(
                    "🚫 Siz botdan foydalana olmaysiz.",
                    reply_markup=ReplyKeyboardRemove(),
                )
            except Exception:
                pass
        elif isinstance(event, CallbackQuery):
            try:
                await event.answer("🚫 Ruxsat yo‘q", show_alert=True)
            except Exception:
                pass

        return None
