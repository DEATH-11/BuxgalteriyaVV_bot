import asyncio
import logging

from aiogram import Dispatcher

from app.bot_instance import bot
from app.handlers import shartnoma as shartnoma_handlers
from app.handlers import spetsifikatsiya as spets_handlers
from app.handlers import start as start_handlers

logging.basicConfig(level=logging.INFO)

dp = Dispatcher()
dp.include_router(start_handlers.router)
dp.include_router(shartnoma_handlers.router)
dp.include_router(spets_handlers.router)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
