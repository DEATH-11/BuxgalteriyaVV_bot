from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from app.config import settings
from app.database.base import async_session
from app.database.repo import get_user
from app.states.register import RegisterForm


REGISTER_STATES = {
    RegisterForm.company.state,
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

        if user_id in settings.admin_list:
            return await handler(event, data)

        async with async_session() as session:
            user = await get_user(session, user_id)

        if user and user.status == "approved":
            return await handler(event, data)

        state: FSMContext | None = data.get("state")
        if state is not None:
            current = await state.get_state()
            if current in REGISTER_STATES:
                return await handler(event, data)

        if isinstance(event, Message):
            text = event.text or ""
            if text.startswith("/start") or text == "/menu":
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            if event.data and (
                event.data.startswith("lang:")
                or event.data.startswith("company:")
            ):
                return await handler(event, data)

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
