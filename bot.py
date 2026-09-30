import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.bot_instance import bot
from app.database.base import init_db
from app.handlers import admin as admin_handlers
from app.handlers import drugs as drugs_handlers
from app.handlers import register as register_handlers
from app.handlers import shartnoma as shartnoma_handlers
from app.handlers import spetsifikatsiya as spets_handlers
from app.handlers import start as start_handlers
from app.middlewares.auth import AuthMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

dp = Dispatcher()

dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())

dp.include_router(start_handlers.router)
dp.include_router(register_handlers.router)
dp.include_router(admin_handlers.router)
dp.include_router(shartnoma_handlers.router)
dp.include_router(spets_handlers.router)
dp.include_router(drugs_handlers.router)


async def main():
    await init_db()

    # Webhook'ni o'chirish (agar o'rnatilgan bo'lsa)
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook o'chirildi, eski xabarlar tozalandi")
    except Exception as e:
        logger.warning(f"Webhook o'chirishda xato: {e}")

    # Polling boshlash
    while True:
        try:
            await dp.start_polling(
                bot,
                drop_pending_updates=True,
                allowed_updates=dp.resolve_used_update_types(),
            )
        except Exception as e:
            logger.error(f"Polling xatosi: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
