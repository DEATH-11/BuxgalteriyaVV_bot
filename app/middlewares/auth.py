from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.config import settings
from app.database.base import async_session
from app.database.repo import get_user
from app.states.register import RegisterForm


REGISTER_STATES = {
    RegisterForm.first_name.state,
    RegisterForm.last_name.state,
    RegisterForm.phone.state,
    RegisterForm.region.state,
    RegisterForm.confirm.state,
}


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

        # Ro‘yxatdan o‘tish state’ida — ruxsat beramiz
        state: FSMContext | None = data.get("state")
        if state is not None:
            current = await state.get_state()
            if current in REGISTER_STATES:
                return await handler(event, data)

        # /start, /menu va lang: — ruxsat
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
