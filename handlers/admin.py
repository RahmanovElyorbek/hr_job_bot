import logging
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import ADMIN_IDS, SHEET_ID, TORTKOL_MANAGER_ID
from db.models import Candidate, CandidateStatus
from db.session import async_session
from questions import MINOR_AGE_RANGE, MINOR_SHIFT_LABEL, POSITIONS
from services.notify import STATUS_LABELS, TZ, process_decision
from services.scoring import rescore_from_sheet
from services.sheets import (
    TIMESTAMP_FORMAT,
    get_all_rows,
    get_candidate_row,
)

logger = logging.getLogger(__name__)
router = Router(name="admin")

AUTHORIZED_IDS = set(ADMIN_IDS) | ({TORTKOL_MANAGER_ID} if TORTKOL_MANAGER_ID else set())

# candidate_id -> [(admin_id, message_id), ...] — "Qaror qabul qiling:"
# xabarlarini kim(lar)ga yuborilgani (bitta admin qaror qilsa, qolganlarnikini
# ham yangilash uchun). Xotirada — bot qayta ishga tushsa tozalanadi, lekin
# haqiqiy idempotentlik (qayta qaror qilib bo'lmasligi) Candidate.status
# ustunida saqlanadi, shuning uchun funksional xavfsizlik yo'qolmaydi.
_pending_messages: dict[int, list[tuple[int, int]]] = {}

ACTION_TO_STATUS = {
    "invite": CandidateStatus.invited,
    "reserve": CandidateStatus.reserve,
    "reject": CandidateStatus.rejected,
}


def _recipients_for(branch: str) -> list[int]:
    if branch == "To'rtko'l" and TORTKOL_MANAGER_ID:
        return [TORTKOL_MANAGER_ID]
    if branch == "Ikkalasi ham":
        recipients = list(ADMIN_IDS)
        if TORTKOL_MANAGER_ID:
            recipients.append(TORTKOL_MANAGER_ID)
        return recipients
    return list(ADMIN_IDS)


def _sheet_link() -> str:
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"


def _verdict_emoji(verdict: str) -> str:
    return {"invite": "🟢", "reserve": "🟡", "reject": "🔴"}.get(verdict, "⚪")


def _build_summary_text(row_number, candidate: dict, ai_result: dict | None) -> str:
    position_label = POSITIONS.get(candidate["position"], candidate["position"])
    contact = f"@{candidate['username']}" if candidate.get("username") else candidate.get("phone", "-")

    lines = [
        f"🆕 YANGI NOMZOD #{row_number if row_number else '?'}",
        "",
        f"👤 {candidate['full_name']} | 📱 {contact}",
        f"💼 Lavozim: {position_label} | 🏪 Filial: {candidate.get('branch', '-')}",
        f"📅 Boshlashi mumkin: {candidate.get('start_date', '-')}",
    ]

    if candidate.get("age_range") == MINOR_AGE_RANGE:
        lines.append(f"🔞 Yosh: {MINOR_AGE_RANGE} — faqat {MINOR_SHIFT_LABEL} ishlashi mumkin")

    lines.append("")

    if ai_result:
        percent = ai_result.get("total_percent", "?")
        verdict = ai_result.get("verdict", "")
        lines.append(f"📊 AI baho: {percent}% — {_verdict_emoji(verdict)} {verdict}")
        if ai_result.get("auto_reject"):
            lines.append(f"⛔ AVTOMATIK RAD: {ai_result.get('auto_reject_reason', '')}")
        lines.append("")
        lines.append("💪 Kuchli tomonlari:")
        for s in ai_result.get("strengths", []):
            lines.append(f"• {s}")
        lines.append("🚩 Qizil bayroqlar:")
        for r in ai_result.get("red_flags", []):
            lines.append(f"• {r}")
        lines.append("")
        lines.append(f"📝 Xulosa: {ai_result.get('summary', '')}")
    else:
        lines.append("⚠️ AI ballash ishlamadi, javoblarni Sheets dan qo'lda ko'ring")

    lines.append("")
    lines.append(f"📄 To'liq javoblar: {_sheet_link()}")

    return "\n".join(lines)


# ===================== QAROR TUGMALARI (HR status moduli) =====================

def _decision_keyboard(candidate_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Taklif", callback_data=f"cand:{candidate_id}:invite"),
                InlineKeyboardButton(text="📋 Zahira", callback_data=f"cand:{candidate_id}:reserve"),
                InlineKeyboardButton(text="❌ Rad", callback_data=f"cand:{candidate_id}:reject"),
            ]
        ]
    )


def _reject_confirm_keyboard(candidate_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ha, yubor", callback_data=f"cand_yes:{candidate_id}"),
                InlineKeyboardButton(text="Bekor qilish", callback_data=f"cand_no:{candidate_id}"),
            ]
        ]
    )


def _rescore_keyboard(row_number) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔁 Qayta ballash", callback_data=f"rescore:{row_number}")]]
    )


def _rescore_loading_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⏳ Ballanmoqda...", callback_data="noop")]]
    )


def _rescore_confirm_keyboard(row_number) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ha, qayta ballansin", callback_data=f"rescore_yes:{row_number}"),
                InlineKeyboardButton(text="Yo'q", callback_data=f"rescore_no:{row_number}"),
            ]
        ]
    )


async def notify_admins(bot: Bot, row_number, candidate: dict, ai_result: dict | None):
    """Yangi nomzod haqida adminlarga xabar yuboradi. Shu bilan birga
    Postgres'da candidates yozuvini yaratadi (HR status moduli uchun) —
    Sheets'dagi to'liq anketa (row_number orqali) o'zgarishsiz qoladi."""
    summary_text = _build_summary_text(row_number, candidate, ai_result)
    if not row_number:
        summary_text += "\n\n⚠️ Sheets ga yozishda xato bo'ldi, qo'lda tekshiring."

    candidate_db_id = None
    try:
        async with async_session() as session:
            db_candidate = Candidate(
                telegram_id=candidate["telegram_id"],
                username=candidate.get("username") or None,
                full_name=candidate["full_name"],
                phone=candidate.get("phone") or None,
                position=candidate.get("position") or None,
                sheet_row=row_number,
            )
            session.add(db_candidate)
            await session.commit()
            await session.refresh(db_candidate)
            candidate_db_id = db_candidate.id
    except Exception:
        logger.exception("Postgres'ga nomzod yozishda xato — qaror tugmalari ko'rsatilmaydi")

    warning_keyboard = _rescore_keyboard(row_number) if row_number and not ai_result else None
    sent_button_messages = []
    recipients = _recipients_for(candidate.get("branch", ""))

    for admin_id in recipients:
        try:
            await bot.send_message(admin_id, summary_text, reply_markup=warning_keyboard)

            if candidate.get("voice_file_id"):
                await bot.send_voice(admin_id, candidate["voice_file_id"])
            if candidate.get("video_file_id"):
                await bot.send_video_note(admin_id, candidate["video_file_id"])

            if candidate_db_id:
                msg = await bot.send_message(
                    admin_id,
                    "Qaror qabul qiling:",
                    reply_markup=_decision_keyboard(candidate_db_id),
                )
                sent_button_messages.append((admin_id, msg.message_id))
        except Exception:
            logger.exception(f"Adminga xabar yuborishda xato: {admin_id}")

    if candidate_db_id:
        _pending_messages[candidate_db_id] = sent_button_messages


def _decided_text(candidate: Candidate, admin_label: str, action: str, notify_result: str) -> str:
    status_label = STATUS_LABELS.get(candidate.status, candidate.status.value)
    header = f"{status_label} — {admin_label} tomonidan"

    if action == "invite":
        phone_line = f"📱 Telefon: <code>{candidate.phone}</code>" if candidate.phone else "📱 Telefon: —"
        return (
            f"{header}\n\n"
            f"👤 {candidate.full_name}\n"
            f"{phone_line}\n"
            f"💬 Yozish uchun: <a href='tg://user?id={candidate.telegram_id}'>havola</a>\n\n"
            f"<i>Xabar avtomatik yuborilmaydi — o'zingiz yozing.</i>"
        )

    if notify_result == "queued":
        return f"{header}\n\n🕒 Xabar tunda (21:00–08:00) navbatga qo'yildi, ertalab 09:00 da avtomatik yuboriladi."
    if notify_result == "sent":
        return f"{header}\n\n✅ Nomzodga avtomatik xabar yuborildi."
    if notify_result == "already_sent":
        sent_at = candidate.notified_at.strftime("%d.%m.%Y %H:%M") if candidate.notified_at else "-"
        return f"{header}\n\nℹ️ Bu nomzodga xabar allaqachon yuborilgan ({sent_at})."
    if notify_result == "failed":
        return (
            f"{header}\n\n"
            f"⚠️ Nomzodga xabar YUBORILMADI (botni bloklagan bo'lishi mumkin).\n"
            f"Qo'lda bog'laning: <code>{candidate.phone or '—'}</code>"
        )
    return header


async def _apply_decision(callback: CallbackQuery, session: AsyncSession, candidate: Candidate, action: str):
    new_status = ACTION_TO_STATUS[action]
    admin_label = f"@{callback.from_user.username}" if callback.from_user.username else str(callback.from_user.id)

    notify_result = await process_decision(callback.bot, session, candidate, new_status, admin_label)
    decided_text = _decided_text(candidate, admin_label, action, notify_result)

    try:
        await callback.message.edit_text(decided_text, parse_mode="HTML")
    except Exception:
        logger.exception("Admin xabarini yangilashda xato")

    await callback.answer("Qaror saqlandi")

    pending = _pending_messages.pop(candidate.id, [])
    for admin_id, message_id in pending:
        if (admin_id, message_id) == (callback.message.chat.id, callback.message.message_id):
            continue
        try:
            await callback.bot.edit_message_text(
                decided_text, chat_id=admin_id, message_id=message_id, parse_mode="HTML"
            )
        except Exception:
            logger.exception("Boshqa admin xabarini yangilashda xato")


@router.callback_query(F.data.startswith("cand:"))
async def decide_candidate(callback: CallbackQuery):
    if callback.from_user.id not in AUTHORIZED_IDS:
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return

    _, cand_id_str, action = callback.data.split(":")
    candidate_id = int(cand_id_str)

    async with async_session() as session:
        candidate = await session.get(Candidate, candidate_id)
        if not candidate:
            await callback.answer("Nomzod topilmadi", show_alert=True)
            return
        if candidate.status != CandidateStatus.new:
            await callback.answer(
                f"Bu nomzod bo'yicha qaror allaqachon qabul qilingan: "
                f"{STATUS_LABELS.get(candidate.status, candidate.status.value)}",
                show_alert=True,
            )
            return

        if action == "reject":
            await callback.answer()
            try:
                await callback.message.edit_text(
                    f"❗ Nomzod: {candidate.full_name}\nRad xabari yuborilsinmi?",
                    reply_markup=_reject_confirm_keyboard(candidate_id),
                )
            except Exception:
                logger.exception("Rad tasdiqlash xabarini ko'rsatishda xato")
            return

        await _apply_decision(callback, session, candidate, action)


@router.callback_query(F.data.startswith("cand_yes:"))
async def confirm_reject(callback: CallbackQuery):
    if callback.from_user.id not in AUTHORIZED_IDS:
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return

    candidate_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        candidate = await session.get(Candidate, candidate_id)
        if not candidate:
            await callback.answer("Nomzod topilmadi", show_alert=True)
            return
        if candidate.status != CandidateStatus.new:
            await callback.answer(
                f"Bu nomzod bo'yicha qaror allaqachon qabul qilingan: "
                f"{STATUS_LABELS.get(candidate.status, candidate.status.value)}",
                show_alert=True,
            )
            return
        await _apply_decision(callback, session, candidate, "reject")


@router.callback_query(F.data.startswith("cand_no:"))
async def cancel_reject(callback: CallbackQuery):
    candidate_id = int(callback.data.split(":")[1])
    await callback.answer("Bekor qilindi")
    try:
        await callback.message.edit_text(
            "Qaror qabul qiling:",
            reply_markup=_decision_keyboard(candidate_id),
        )
    except Exception:
        logger.exception("Bekor qilishda tugmani tiklashda xato")


@router.message(Command("zahira"))
async def zahira_list(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    now_naive = datetime.now(TZ).replace(tzinfo=None)
    async with async_session() as session:
        result = await session.execute(
            select(Candidate)
            .where(Candidate.status == CandidateStatus.reserve)
            .where(Candidate.reserve_until.isnot(None))
            .where(Candidate.reserve_until > now_naive)
            .order_by(Candidate.reserve_until)
        )
        candidates = result.scalars().all()

    if not candidates:
        await message.answer("📋 Zahira ro'yxati bo'sh.")
        return

    lines = ["📋 <b>Zahira nomzodlar</b> (muddati tugamagan):", ""]
    for c in candidates:
        position_label = POSITIONS.get(c.position, c.position or "-")
        decided = c.status_changed_at.strftime("%d.%m.%Y") if c.status_changed_at else "-"
        lines.append(
            f"👤 {c.full_name} | 💼 {position_label}\n"
            f"📅 {decided} | <a href='tg://user?id={c.telegram_id}'>Yozish</a>"
        )
    await message.answer("\n\n".join(lines), parse_mode="HTML")


# ===================== QAYTA BALLASH (AI, o'zgarishsiz) =====================

DECIDED_STATUSES = {"invited", "reserve", "rejected"}


def _row_to_candidate(row: dict) -> dict:
    return {
        "position": row.get("position", ""),
        "full_name": row.get("full_name", ""),
        "username": row.get("username", ""),
        "phone": row.get("phone", ""),
        "branch": row.get("branch", ""),
        "start_date": row.get("start_date", ""),
        "telegram_id": row.get("telegram_id", ""),
    }


async def _perform_rescore(bot: Bot, chat_id: int, message_id: int, row_number: int, fallback_text: str):
    try:
        await bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=message_id, reply_markup=_rescore_loading_keyboard()
        )
    except Exception:
        logger.exception("Ballanmoqda tugmasini o'rnatishda xato")

    row = await get_candidate_row(row_number)
    ai_result, error = await rescore_from_sheet(row_number)

    if ai_result:
        text = _build_summary_text(row_number, _row_to_candidate(row), ai_result)
        status = row.get("status") or "new"

        if status in DECIDED_STATUSES:
            labels = {"invited": "✅ Taklif", "reserve": "📋 Zahira", "rejected": "❌ Rad"}
            text += f"\n\n📌 Holat: {labels.get(status, status)}"
            keyboard = None
        else:
            keyboard = None  # eski row_number asosidagi tugmalar endi ishlatilmaydi

        try:
            await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, reply_markup=keyboard)
        except Exception:
            logger.exception("Qayta ballash natijasini yangilashda xato")
        return

    error_text = f"{fallback_text}\n\n❌ Qayta ballash ham muvaffaqiyatsiz: {error}"
    try:
        await bot.edit_message_text(
            error_text, chat_id=chat_id, message_id=message_id, reply_markup=_rescore_keyboard(row_number)
        )
    except Exception:
        logger.exception("Qayta ballash xato xabarini yangilashda xato")


@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("rescore_yes:"))
async def rescore_confirm_yes(callback: CallbackQuery):
    if callback.from_user.id not in AUTHORIZED_IDS:
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return

    row_number = int(callback.data.split(":")[1])
    await callback.answer()
    await _perform_rescore(
        callback.bot, callback.message.chat.id, callback.message.message_id,
        row_number, callback.message.text or "",
    )


@router.callback_query(F.data.startswith("rescore_no:"))
async def rescore_confirm_no(callback: CallbackQuery):
    row_number = int(callback.data.split(":")[1])
    await callback.answer("Bekor qilindi")
    try:
        await callback.message.edit_reply_markup(reply_markup=_rescore_keyboard(row_number))
    except Exception:
        logger.exception("Bekor qilishda tugmani tiklashda xato")


@router.callback_query(F.data.startswith("rescore:"))
async def rescore_button(callback: CallbackQuery):
    if callback.from_user.id not in AUTHORIZED_IDS:
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return

    row_number = int(callback.data.split(":")[1])
    row = await get_candidate_row(row_number)
    status = row.get("status") or "new"

    if status in DECIDED_STATUSES:
        await callback.answer()
        try:
            await callback.message.edit_reply_markup(reply_markup=_rescore_confirm_keyboard(row_number))
        except Exception:
            logger.exception("Tasdiq tugmasini ko'rsatishda xato")
        return

    await callback.answer()
    await _perform_rescore(
        callback.bot, callback.message.chat.id, callback.message.message_id,
        row_number, callback.message.text or "",
    )


@router.message(Command("rescore"))
async def rescore_command(message: Message, command: CommandObject):
    if message.from_user.id not in ADMIN_IDS:
        return

    if not command.args or not command.args.strip().isdigit():
        await message.answer("Foydalanish: /rescore <qator_raqami>")
        return

    row_number = int(command.args.strip())
    row = await get_candidate_row(row_number)
    if not row.get("full_name"):
        await message.answer(f"#{row_number} qatorida nomzod topilmadi.")
        return

    status = row.get("status") or "new"

    if status in DECIDED_STATUSES:
        labels = {"invited": "✅ Taklif", "reserve": "📋 Zahira", "rejected": "❌ Rad"}
        await message.answer(
            f"Nomzod #{row_number} ({row.get('full_name', '-')}) bo'yicha qaror allaqachon qabul qilingan: "
            f"{labels.get(status, status)}.\nBaribir qayta ballansinmi?",
            reply_markup=_rescore_confirm_keyboard(row_number),
        )
        return

    msg = await message.answer(f"⏳ Ballanmoqda... (#{row_number})")
    await _perform_rescore(message.bot, msg.chat.id, msg.message_id, row_number, f"Nomzod #{row_number}")


@router.message(Command("stats"))
async def stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    rows = await get_all_rows()
    if len(rows) <= 1:
        await message.answer("Hozircha nomzodlar yo'q.")
        return

    header, *records = rows
    ts_idx = header.index("timestamp")
    pos_idx = header.index("position")
    now = datetime.now()

    today_count = 0
    week_count = 0
    by_position = {}

    for row in records:
        if len(row) <= max(ts_idx, pos_idx):
            continue
        try:
            ts = datetime.strptime(row[ts_idx], TIMESTAMP_FORMAT)
        except ValueError:
            continue

        if ts.date() == now.date():
            today_count += 1
        if (now - ts).days <= 7:
            week_count += 1

        position = row[pos_idx]
        by_position[position] = by_position.get(position, 0) + 1

    lines = [
        "📊 Statistika",
        "",
        f"Bugun: {today_count}",
        f"Bu hafta: {week_count}",
        f"Jami: {len(records)}",
        "",
        "Lavozimlar kesimida:",
    ]
    for position, count in by_position.items():
        lines.append(f"{POSITIONS.get(position, position)}: {count}")

    await message.answer("\n".join(lines))
