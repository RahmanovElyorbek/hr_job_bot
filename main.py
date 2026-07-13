import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN, PORT
from handlers import admin, fallback, interview, start
from services.keep_alive import run_keep_alive_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(interview.router)
    dp.include_router(admin.router)
    dp.include_router(fallback.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await run_keep_alive_server(PORT)

    logger.info("Bot polling boshlandi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
