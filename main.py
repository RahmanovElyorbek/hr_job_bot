import asyncio
import logging
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import BOT_TOKEN, PORT, TIMEZONE
from db.session import init_db
from handlers import admin, fallback, interview, start
from services.keep_alive import run_keep_alive_server
from services.notify import flush_queued_notifications

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(interview.router)
    dp.include_router(admin.router)
    dp.include_router(fallback.router)

    await init_db()
    logger.info("✅ Postgres (candidates) tayyor")

    await bot.delete_webhook(drop_pending_updates=True)
    await run_keep_alive_server(PORT)

    scheduler = AsyncIOScheduler(timezone=ZoneInfo(TIMEZONE))
    scheduler.add_job(
        flush_queued_notifications,
        trigger="cron",
        hour=9,
        minute=0,
        args=[bot],
        id="flush_queued_notifications",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("🔔 Scheduler: tunda (21:00-08:00) navbatga qo'shilgan xabarlar har kuni 09:00 da yuboriladi")

    logger.info("Bot polling boshlandi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
