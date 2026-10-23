"""
services/notify.py — HR status o'zgarishi va nomzodga avtomatik xabar
yuborish mantig'i. handlers/admin.py bu yerdagi funksiyalarni chaqiradi,
o'zi faqat callback qabul qiladi (yupqa handler).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDS, LOG_CHANNEL_ID, NOTIFY_MODE, TIMEZONE
from db.models import Candidate, CandidateStatus, NotifyStatus
from db.session import async_session
from services.sheets import update_status as sheets_update_status
from templates import TEMPLATES

logger = logging.getLogger(__name__)

TZ = ZoneInfo(TIMEZONE)
NIGHT_START_HOUR = 21   # 21:00 dan
NIGHT_END_HOUR = 8      # 08:00 gacha — shu oraliqda xabar yuborilmaydi
RESERVE_DAYS = 90

STATUS_LABELS = {
    CandidateStatus.invited: "✅ Taklif",
    CandidateStatus.reserve: "📋 Zahira",
    CandidateStatus.rejected: "❌ Rad",
    CandidateStatus.new: "Yangi",
}


def is_night_time(moment: datetime | None = None) -> bool:
    moment = moment or datetime.now(TZ)
    return moment.hour >= NIGHT_START_HOUR or moment.hour < NIGHT_END_HOUR


def _now_naive() -> datetime:
    """Bazaga yozish uchun — TIMESTAMP ustuni tz-siz, shuning uchun
    Toshkent vaqtini tzinfo'siz saqlaymiz (loyihaning boshqa joylarida
    ham shu konvensiya: services/sheets.py'dagi now_tashkent_str())."""
    return datetime.now(TZ).replace(tzinfo=None)


async def _send_with_retry(bot: Bot, telegram_id: int, text: str) -> "tuple[str, str | None]":
    """Xabar yuboradi. TelegramRetryAfter (flood control) bo'lsa kutib bir
    marta qayta uradi. Qaytaradi: ('sent'|'failed', xato_matni_yoki_None)."""
    try:
        await bot.send_message(telegram_id, text, parse_mode="HTML")
        return "sent", None
    except TelegramRetryAfter as e:
        logger.warning(f"Flood control: {e.retry_after}s kutamiz (telegram_id={telegram_id})")
        await asyncio.sleep(e.retry_after + 1)
        try:
            await bot.send_message(telegram_id, text, parse_mode="HTML")
            return "sent", None
        except (TelegramForbiddenError, TelegramBadRequest) as e2:
            return "failed", str(e2)
        except Exception as e2:
            logger.exception("Qayta urinishda ham xato")
            return "failed", str(e2)
    except (TelegramForbiddenError, TelegramBadRequest) as e:
        return "failed", str(e)
    except Exception as e:
        logger.exception("Xabar yuborishda kutilmagan xato")
        return "failed", str(e)


async def _deliver_notification(bot: Bot, candidate: Candidate) -> str:
    """Nomzodga shablon xabarini yuboradi (yoki NOTIFY_MODE=mock bo'lsa
    faqat log qiladi). candidate obyektini JOYIDA (in-place) yangilaydi —
    commit chaqiruvchida. Qaytaradi: 'sent' | 'failed' | 'no_template'."""
    template = TEMPLATES.get(candidate.status.value)
    if not template:
        # "invited" uchun shablon yo'q — avtomatik xabar yuborilmaydi
        return "no_template"

    text = template.format(name=candidate.full_name)

    if NOTIFY_MODE == "mock":
        logger.info(f"[MOCK NOTIFY] telegram_id={candidate.telegram_id} -> {text!r}")
        candidate.notify_status = NotifyStatus.sent
        candidate.notified_at = _now_naive()
        return "sent"

    result, error = await _send_with_retry(bot, candidate.telegram_id, text)
    if result == "sent":
        candidate.notify_status = NotifyStatus.sent
        candidate.notified_at = _now_naive()
        return "sent"

    candidate.notify_status = NotifyStatus.failed
    candidate.notify_error = error
    return "failed"


async def _notify_admins_of_failure(bot: Bot, candidate: Candidate):
    text = (
        f"⚠️ {candidate.full_name} ga Telegram orqali xabar ketmadi "
        f"(botni bloklagan yoki boshqa xato).\n"
        f"Qo'lda bog'laning: <code>{candidate.phone or '—'}</code>"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
        except Exception:
            logger.exception(f"Xato haqida adminga ({admin_id}) xabar berib bo'lmadi")


async def log_decision(bot: Bot, candidate: Candidate, notify_result: str):
    """Har bir status o'zgarishini log kanaliga yozadi."""
    if not LOG_CHANNEL_ID:
        return
    icon = {
        "sent": "✅", "queued": "🕒", "failed": "⚠️",
        "already_sent": "↺", "no_template": "—",
    }.get(notify_result, "—")
    admin_label = candidate.status_changed_by or "?"
    status_label = STATUS_LABELS.get(candidate.status, candidate.status.value)
    text = f"{candidate.full_name} → {status_label} (admin: {admin_label}) | Xabar: {icon}"
    try:
        await bot.send_message(LOG_CHANNEL_ID, text)
    except Exception:
        logger.exception("Log kanaliga yozishda xato")


async def process_decision(
    bot: Bot, session: AsyncSession, candidate: Candidate,
    new_status: CandidateStatus, admin_label: str,
) -> str:
    """Bitta nomzod uchun qaror qabul qilingandan keyingi TO'LIQ jarayon:
    status yangilanadi, (agar shablon bo'lsa) xabar yuboriladi yoki
    tungi bo'lsa navbatga qo'yiladi, Sheets'ga dual-write qilinadi,
    log kanaliga yoziladi. Qaytaradi: notify_result
    ('sent'|'queued'|'failed'|'no_template'|'already_sent')."""

    if candidate.notified_at is not None:
        # Notifikatsiya nuqtai nazaridan idempotentlik — lekin status
        # allaqachon o'zgargan bo'lishi kerak, shuning uchun bu holat
        # amalda decide_candidate() dagi status tekshiruvi bilan qamrab
        # olinadi. Himoya sifatida qoldirilgan.
        return "already_sent"

    candidate.status = new_status
    candidate.status_changed_at = _now_naive()
    candidate.status_changed_by = admin_label
    if new_status == CandidateStatus.reserve:
        candidate.reserve_until = _now_naive() + timedelta(days=RESERVE_DAYS)

    if is_night_time():
        candidate.notify_status = NotifyStatus.queued
        notify_result = "queued"
    else:
        notify_result = await _deliver_notification(bot, candidate)

    await session.commit()

    if candidate.sheet_row:
        try:
            await sheets_update_status(
                candidate.sheet_row, new_status.value, admin_label,
                candidate.status_changed_at.strftime("%Y-%m-%d %H:%M:%S"),
            )
        except Exception:
            logger.exception("Sheets'ga status yozishda xato (dual-write)")

    if notify_result == "failed":
        await _notify_admins_of_failure(bot, candidate)

    await log_decision(bot, candidate, notify_result)
    return notify_result


async def flush_queued_notifications(bot: Bot):
    """APScheduler orqali har kuni ertalab 09:00 (Asia/Tashkent) da
    ishga tushadi — tunda navbatga qo'shilgan xabarlarni yuboradi."""
    async with async_session() as session:
        result = await session.execute(
            select(Candidate).where(Candidate.notify_status == NotifyStatus.queued)
        )
        queued = result.scalars().all()
        if not queued:
            return

        sent, failed = 0, 0
        for candidate in queued:
            notify_result = await _deliver_notification(bot, candidate)
            await session.commit()
            if notify_result == "sent":
                sent += 1
            elif notify_result == "failed":
                failed += 1
                await _notify_admins_of_failure(bot, candidate)
            await log_decision(bot, candidate, notify_result)

        logger.info(f"Tungi navbat yuborildi: {sent} ta muvaffaqiyatli, {failed} ta xato")
