"""
db/session.py — async SQLAlchemy engine, session factory va sxemani
avtomatik (idempotent) tayyorlash.

Alembic ISHLATILMAYDI (vazifa talabiga ko'ra) — sxema oddiy
"CREATE TABLE IF NOT EXISTS" / "ADD COLUMN IF NOT EXISTS" orqali
main.py ishga tushganda avtomatik tayyorlanadi. Xuddi shu SQL
migrations/001_create_candidates.sql faylida ham bor — agar production
bazani deploy'dan OLDIN qo'lda tekshirib ko'rmoqchi bo'lsangiz, o'sha
faylni to'g'ridan-to'g'ri ham ishlatishingiz mumkin, natija bir xil.
"""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import DATABASE_URL

logger = logging.getLogger(__name__)


def _normalize_database_url(url: str) -> str:
    """Render/Heroku uslubidagi 'postgres://' yoki oddiy 'postgresql://'
    manzillarni SQLAlchemy async drayveri talab qiladigan
    'postgresql+asyncpg://' shakliga o'giradi."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


engine = create_async_engine(_normalize_database_url(DATABASE_URL), pool_size=5, max_overflow=2)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Sxemani idempotent tarzda tayyorlaydi — bir necha marta ishga
    tushirilsa ham xato bermaydi. Mavjud qatorlarga tegilmaydi."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS candidates (
                id                  SERIAL PRIMARY KEY,
                telegram_id         BIGINT NOT NULL,
                username            VARCHAR(64),
                full_name           VARCHAR(255) NOT NULL,
                phone               VARCHAR(32),
                position            VARCHAR(64),
                sheet_row           INTEGER,
                applied_at          TIMESTAMP NOT NULL DEFAULT NOW(),
                status              VARCHAR(16) NOT NULL DEFAULT 'new',
                status_changed_at   TIMESTAMP,
                status_changed_by   VARCHAR(64),
                notify_status       VARCHAR(16) NOT NULL DEFAULT 'none',
                notified_at         TIMESTAMP,
                notify_error        TEXT,
                reserve_until       TIMESTAMP
            )
        """))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_candidates_telegram_id ON candidates(telegram_id)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status)"
        ))
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_candidates_reserve_until ON candidates(reserve_until) "
            "WHERE status = 'reserve'"
        ))
    logger.info("✅ candidates jadvali tayyor")
