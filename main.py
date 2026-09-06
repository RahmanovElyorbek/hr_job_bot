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


async def _init_db_with_retry():
    """Supabase (va boshqa managed Postgres) ba'zan sovuq holatdan sekin
    tiklanadi — birinchi ulanish "Healthy" ko'rsatsa ham timeout berishi
    mumkin. Bitta muvaffaqiyatsiz urinishda to'xtab qolish o'rniga,
    ortib boruvchi kutish bilan (10s, 20s, ... 60s gacha) cheksiz qayta
    uriladi. Port allaqachon ochiq bo'lgani uchun Render health-check
    bunga xalaqit bermaydi (Oson Budget loyihasida sinovdan o'tgan yechim)."""
    attempt = 0
    while True:
        attempt += 1
        try:
            logger.info(f"🔄 DB ulanmoqda... (urinish {attempt})")
            await asyncio.wait_for(init_db(), timeout=45)
            logger.info("✅ Postgres (candidates) tayyor")
            return
        except asyncio.TimeoutError:
            wait_s = min(10 * attempt, 60)
            logger.error(f"❌ DB ulanishi 45 soniyada timeout! {wait_s}s dan keyin qayta urinaman...")
            await asyncio.sleep(wait_s)
        except Exception as e:
            wait_s = min(10 * attempt, 60)
            logger.error(f"❌ DB xatolik: {e}. {wait_s}s dan keyin qayta urinaman...")
            await asyncio.sleep(wait_s)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(interview.router)
    dp.include_router(admin.router)
    dp.include_router(fallback.router)

    # Portni BIRINCHI ochamiz — Render health-check darhol ko'radi,
    # DB ulanishi orqada (kerak bo'lsa qayta urinib) davom etadi.
    await run_keep_alive_server(PORT)

    await _init_db_with_retry()

    await bot.delete_webhook(drop_pending_updates=True)

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
