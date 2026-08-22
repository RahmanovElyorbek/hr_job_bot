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

from config import ADMIN_IDS, SHEET_ID
from questions import MINOR_AGE_RANGE, MINOR_SHIFT_LABEL, POSITIONS
from services.scoring import rescore_from_sheet
from services.sheets import (
    TIMESTAMP_FORMAT,
    get_all_rows,
    get_candidate_row,
    now_tashkent_str,
    update_status,
)

logger = logging.getLogger(__name__)
router = Router(name="admin")

# row_number -> {"messages": [(admin_id, message_id), ...], "candidate_id": int, "candidate_name": str}
_pending_decisions = {}

STATUS_LABELS = {
    "invited": "✅ Sinov kuniga taklif qilindi",
    "reserve": "🟡 Zaxira ro'yxatiga qo'shildi",
    "rejected": "❌ Rad etildi",
}

CANDIDATE_MESSAGES = {
    "invited": "🎉 Tabriklaymiz, {name}! Sizni sinov kuniga taklif qilamiz. Tez orada administratorimiz siz bilan bog'lanadi.",
    "reserve": "Rahmat, {name}! Arizangiz zaxira ro'yxatiga kiritildi. Bo'sh o'rin ochilsa birinchilardan bo'lib xabar beramiz.",
    "rejected": "Rahmat, {name}! Afsuski, hozircha boshqa nomzodni tanladik. Arizangiz bazamizda saqlanadi.",
}

ACTION_TO_STATUS = {"invite": "invited", "reserve": "reserve", "reject": "rejected"}


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


def _decision_keyboard(row_number) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Sinov kuniga taklif", callback_data=f"dec:{row_number}:invite"),
                InlineKeyboardButton(text="🟡 Zaxiraga", callback_data=f"dec:{row_number}:reserve"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"dec:{row_number}:reject"),
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
    summary_text = _build_summary_text(row_number, candidate, ai_result)
    if not row_number:
        summary_text += "\n\n⚠️ Sheets ga yozishda xato bo'ldi, qo'lda tekshiring."

    warning_keyboard = _rescore_keyboard(row_number) if row_number and not ai_result else None
    sent_button_messages = []

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, summary_text, reply_markup=warning_keyboard)

            if candidate.get("voice_file_id"):
                await bot.send_voice(admin_id, candidate["voice_file_id"])
            if candidate.get("video_file_id"):
                await bot.send_video_note(admin_id, candidate["video_file_id"])

            if row_number:
                msg = await bot.send_message(
                    admin_id,
                    "Qaror qabul qiling:",
                    reply_markup=_decision_keyboard(row_number),
                )
                sent_button_messages.append((admin_id, msg.message_id))
        except Exception:
            logger.exception(f"Adminga xabar yuborishda xato: {admin_id}")

    if row_number:
        _pending_decisions[row_number] = {
            "messages": sent_button_messages,
            "candidate_id": candidate["telegram_id"],
            "candidate_name": candidate["full_name"],
        }


@router.callback_query(F.data.startswith("dec:"))
async def decide_candidate(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Sizda ruxsat yo'q", show_alert=True)
        return

    _, row_str, action = callback.data.split(":")
    row_number = int(row_str)

    pending = _pending_decisions.get(row_number)
    if not pending:
        await callback.answer("Bu nomzod bo'yicha qaror allaqachon qabul qilingan", show_alert=True)
        return

    status = ACTION_TO_STATUS[action]
    decided_by = f"@{callback.from_user.username}" if callback.from_user.username else str(callback.from_user.id)
    decided_at = now_tashkent_str()

    del _pending_decisions[row_number]

    await update_status(row_number, status, decided_by, decided_at)

    decided_text = f"{STATUS_LABELS[status]} — {decided_by} tomonidan"
    for admin_id, message_id in pending["messages"]:
        try:
            await callback.bot.edit_message_text(decided_text, chat_id=admin_id, message_id=message_id)
        except Exception:
            logger.exception("Admin xabarini yangilashda xato")

    await callback.answer("Qaror saqlandi")

    try:
        text = CANDIDATE_MESSAGES[status].format(name=pending["candidate_name"])
        await callback.bot.send_message(pending["candidate_id"], text)
    except Exception:
        logger.exception("Nomzodga xabar yuborishda xato")


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
            text += f"\n\n📌 Holat: {STATUS_LABELS.get(status, status)}"
            keyboard = None
        else:
            keyboard = _decision_keyboard(row_number)
            telegram_id = row.get("telegram_id")
            pending = _pending_decisions.setdefault(row_number, {
                "messages": [],
                "candidate_id": int(telegram_id) if telegram_id else None,
                "candidate_name": row.get("full_name", ""),
            })
            if (chat_id, message_id) not in pending["messages"]:
                pending["messages"].append((chat_id, message_id))

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
    if callback.from_user.id not in ADMIN_IDS:
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
    if callback.from_user.id not in ADMIN_IDS:
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
        await message.answer(
            f"Nomzod #{row_number} ({row.get('full_name', '-')}) bo'yicha qaror allaqachon qabul qilingan: "
            f"{STATUS_LABELS.get(status, status)}.\nBaribir qayta ballansinmi?",
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
