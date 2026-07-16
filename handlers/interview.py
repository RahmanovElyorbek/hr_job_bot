import asyncio
import json
import logging
import time

from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from handlers.admin import notify_admins
from questions import (
    BLOCK1_QUESTIONS,
    BLOCK4_QUESTIONS,
    MEDIA_CONFIG,
    OMBORCHI_HEALTH_QUESTION,
    POSITIONS,
    SITUATIONS,
    VIDEO_QUESTION_TEXT,
    VOICE_QUESTION_TEXT,
)
from services.scoring import build_scoring_input, score_candidate
from services.sheets import append_candidate, now_tashkent_str
from states import Interview

logger = logging.getLogger(__name__)
router = Router(name="interview")

MIN_MEDIA_DURATION = 15
MAX_MEDIA_RETRIES = 2

FACTS_STATE_ORDER = [
    Interview.facts_last_job,
    Interview.facts_leave_reason,
    Interview.facts_job_count,
    Interview.facts_reference,
]

MOTIVATION_STATE_ORDER = [
    Interview.motivation_why,
    Interview.motivation_future,
    Interview.motivation_weakness,
    Interview.motivation_questions,
]


def _phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Telefon yuborish", request_contact=True)]],
        resize_keyboard=True,
    )


async def _ask_timed(message: Message, state: FSMContext, text: str):
    await state.update_data(asked_at=time.time())
    await message.answer(text)


async def _record_answer(state: FSMContext, question_id: str, text: str):
    data = await state.get_data()
    elapsed = round(time.time() - data.get("asked_at", time.time()), 1)

    answers = data.get("answers", {})
    answers[question_id] = text
    answer_times = data.get("answer_times", {})
    answer_times[question_id] = elapsed

    await state.update_data(answers=answers, answer_times=answer_times)


# ---- Lavozim va telefon ----

@router.callback_query(Interview.position, F.data.startswith("pos:"))
async def choose_position(callback: CallbackQuery, state: FSMContext):
    position_key = callback.data.split(":", 1)[1]
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.update_data(position=position_key)
    await callback.message.answer("Telefon raqamingizni yuboring:", reply_markup=_phone_keyboard())
    await state.set_state(Interview.phone)


@router.message(Interview.phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await message.answer("Rahmat! Endi bir nechta umumiy savol beraman.", reply_markup=ReplyKeyboardRemove())
    await _ask_timed(message, state, BLOCK1_QUESTIONS[0]["text"])
    await state.set_state(FACTS_STATE_ORDER[0])


@router.message(Interview.phone)
async def phone_invalid(message: Message):
    await message.answer("Iltimos, \"📞 Telefon yuborish\" tugmasini bosing.")


# ---- Blok 1: Faktlar ----

@router.message(StateFilter(*FACTS_STATE_ORDER), F.text)
async def facts_answer(message: Message, state: FSMContext):
    current = await state.get_state()
    idx = [s.state for s in FACTS_STATE_ORDER].index(current)
    question = BLOCK1_QUESTIONS[idx]
    await _record_answer(state, question["id"], message.text)

    if idx + 1 < len(FACTS_STATE_ORDER):
        await _ask_timed(message, state, BLOCK1_QUESTIONS[idx + 1]["text"])
        await state.set_state(FACTS_STATE_ORDER[idx + 1])
        return

    await _start_situations(message, state)


async def _start_situations(message: Message, state: FSMContext):
    data = await state.get_data()
    position = data["position"]
    await state.update_data(sit_index=0)
    await _ask_timed(message, state, SITUATIONS[position][0]["text"])
    await state.set_state(Interview.situations)


# ---- Blok 2: Vaziyatli savollar ----

@router.message(Interview.situations, F.text)
async def situations_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    position = data["position"]
    sit_index = data.get("sit_index", 0)
    situations = SITUATIONS[position]

    await _record_answer(state, situations[sit_index]["id"], message.text)

    sit_index += 1
    if sit_index < len(situations):
        await state.update_data(sit_index=sit_index)
        await _ask_timed(message, state, situations[sit_index]["text"])
        return

    if position == "omborchi":
        await message.answer(
            OMBORCHI_HEALTH_QUESTION,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Ha", callback_data="health:Ha"),
                        InlineKeyboardButton(text="Yo'q", callback_data="health:Yo'q"),
                    ]
                ]
            ),
        )
        await state.set_state(Interview.omborchi_health)
        return

    await _start_media(message, state)


@router.callback_query(Interview.omborchi_health, F.data.startswith("health:"))
async def omborchi_health(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.update_data(o_health=value)
    await _start_media(callback.message, state)


# ---- Blok 3: Media ----

async def _start_media(message: Message, state: FSMContext):
    data = await state.get_data()
    config = MEDIA_CONFIG[data["position"]]

    if config["voice"]:
        await message.answer(VOICE_QUESTION_TEXT)
        await state.set_state(Interview.media_voice)
        return

    if config["video"]:
        await message.answer(VIDEO_QUESTION_TEXT)
        await state.set_state(Interview.media_video)
        return

    await _start_motivation(message, state)


@router.message(Interview.media_voice, F.voice)
async def media_voice(message: Message, state: FSMContext):
    voice = message.voice
    data = await state.get_data()
    retries = data.get("voice_retry", 0)

    if voice.duration < MIN_MEDIA_DURATION and retries < MAX_MEDIA_RETRIES:
        await state.update_data(voice_retry=retries + 1)
        await message.answer("Juda qisqa bo'ldi, iltimos kamida 30 soniya gapiring")
        return

    await state.update_data(voice_file_id=voice.file_id, voice_short=voice.duration < MIN_MEDIA_DURATION)

    if MEDIA_CONFIG[data["position"]]["video"]:
        await message.answer(VIDEO_QUESTION_TEXT)
        await state.set_state(Interview.media_video)
    else:
        await _start_motivation(message, state)


@router.message(Interview.media_voice)
async def media_voice_invalid(message: Message):
    await message.answer("Iltimos, mikrofon tugmasini bosib ovozli xabar yuboring 🎤")


@router.message(Interview.media_video, F.video_note)
async def media_video(message: Message, state: FSMContext):
    video_note = message.video_note
    data = await state.get_data()
    retries = data.get("video_retry", 0)

    if video_note.duration < MIN_MEDIA_DURATION and retries < MAX_MEDIA_RETRIES:
        await state.update_data(video_retry=retries + 1)
        await message.answer("Juda qisqa bo'ldi, iltimos kamida 30 soniya gapiring")
        return

    await state.update_data(video_file_id=video_note.file_id, video_short=video_note.duration < MIN_MEDIA_DURATION)
    await _start_motivation(message, state)


@router.message(Interview.media_video)
async def media_video_invalid(message: Message):
    await message.answer(
        "Iltimos, oddiy video emas, dumaloq video yuboring — kamera belgisini bosib turing 🔴"
    )


# ---- Blok 4: Motivatsiya ----

async def _start_motivation(message: Message, state: FSMContext):
    await _ask_timed(message, state, BLOCK4_QUESTIONS[0]["text"])
    await state.set_state(MOTIVATION_STATE_ORDER[0])


@router.message(StateFilter(*MOTIVATION_STATE_ORDER), F.text)
async def motivation_answer(message: Message, state: FSMContext):
    current = await state.get_state()
    idx = [s.state for s in MOTIVATION_STATE_ORDER].index(current)
    question = BLOCK4_QUESTIONS[idx]
    await _record_answer(state, question["id"], message.text)

    if idx + 1 < len(MOTIVATION_STATE_ORDER):
        await _ask_timed(message, state, BLOCK4_QUESTIONS[idx + 1]["text"])
        await state.set_state(MOTIVATION_STATE_ORDER[idx + 1])
        return

    await _finish_interview(message, state)


# ---- Yakun va fon jarayoni ----

async def _finish_interview(message: Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user

    await message.answer(
        f"✅ Rahmat, {user.first_name}! Arizangiz qabul qilindi. Javoblaringizni "
        "ko'rib chiqamiz va 3 ish kuni ichida shu yerda javob yozamiz. "
        "Sharq Supermarket jamoasi."
    )

    candidate = {
        "telegram_id": user.id,
        "username": user.username or "",
        "full_name": user.full_name,
        **data,
    }
    await state.clear()

    asyncio.create_task(_process_application(message.bot, candidate))


async def _process_application(bot, candidate: dict):
    position = candidate["position"]
    answers = candidate.get("answers", {})
    answer_times = candidate.get("answer_times", {})

    ai_result, _ = await score_candidate(
        POSITIONS[position], build_scoring_input(position, answers, answer_times)
    )

    row = {
        "timestamp": now_tashkent_str(),
        "telegram_id": candidate["telegram_id"],
        "username": candidate["username"],
        "full_name": candidate["full_name"],
        "phone": candidate.get("phone", ""),
        "position": position,
        "branch": candidate.get("branch", ""),
        "age_range": candidate.get("age_range", ""),
        "shift_ok": candidate.get("shift_ok", ""),
        "start_date": candidate.get("start_date", ""),
        **{q["id"]: answers.get(q["id"], "") for q in BLOCK1_QUESTIONS},
        **{q["id"]: answers.get(q["id"], "") for pos_qs in SITUATIONS.values() for q in pos_qs},
        "O_health": candidate.get("o_health", ""),
        **{q["id"]: answers.get(q["id"], "") for q in BLOCK4_QUESTIONS},
        "answer_times": json.dumps(answer_times, ensure_ascii=False),
        "voice_file_id": candidate.get("voice_file_id", ""),
        "video_file_id": candidate.get("video_file_id", ""),
        "ai_percent": ai_result.get("total_percent", "") if ai_result else "",
        "ai_verdict": ai_result.get("verdict", "") if ai_result else "",
        "ai_summary": ai_result.get("summary", "") if ai_result else "",
        "ai_red_flags": "; ".join(ai_result.get("red_flags", [])) if ai_result else "",
        "status": "new",
        "decided_by": "",
        "decided_at": "",
    }

    try:
        row_number = await append_candidate(row)
    except Exception:
        logger.exception("Sheets ga yozishda xato")
        row_number = None

    await notify_admins(bot, row_number, candidate, ai_result)
