import asyncio
import json
import logging

import anthropic
from anthropic import AsyncAnthropic

from config import ANTHROPIC_API_KEY
from questions import BLOCK1_QUESTIONS, BLOCK4_QUESTIONS, POSITIONS, SITUATIONS
from services.sheets import get_candidate_row, update_ai_result

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-5"
MAX_RETRIES = 2
RETRYABLE_EXCEPTIONS = (anthropic.APIError, json.JSONDecodeError, StopIteration)

SYSTEM_PROMPT = """Sen 20 yillik supermarket tajribasiga ega HR ekspertsan. Quyida {position}
lavozimiga nomzodning suhbat javoblari berilgan. Har bir savol yonida
"nimani o'lchaydi" izohi bor — shu mezonga qarab 0/1/2 ball qo'y.

Ballash: 0 = qizil bayroq (halollikka shubha, mas'uliyatsizlik, agressiya,
shablon/ma'nosiz javob), 1 = qoniqarli, 2 = kuchli (aniq, samimiy, tashabbusli).

Har javob uchun javob berish vaqti (soniyalarda) berilgan. Vaziyatli savolga
10 soniyadan tez berilgan uzun javob — nusxa ko'chirilgan bo'lishi mumkin,
buni izohda belgila.

Har bir "comment" — bitta qisqa jumla (10 so'zdan oshmasin).

Butun javobing bitta qatorda, valid JSON bo'lsin: matn maydonlari ichida
haqiqiy yangi qator belgisi ishlatma, va agar matn ichida qo'shtirnoq (")
belgisi kerak bo'lsa, uni \" deb escape qil.

Faqat quyidagi JSON formatda javob ber, boshqa hech narsa yozma:
{{
  "scores": [{{"question_id": "K1", "score": 2, "comment": "..."}}],
  "total_percent": 85,
  "auto_reject": false,
  "auto_reject_reason": null,
  "strengths": ["...", "...", "..."],
  "red_flags": ["..."],
  "verdict": "invite" | "reserve" | "reject",
  "summary": "2-3 gapdan iborat umumiy xulosa o'zbek tilida"
}}"""

_client = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    return _client


def _build_user_content(position_label: str, answers: list[dict]) -> str:
    lines = [f"Lavozim: {position_label}", ""]
    for a in answers:
        lines.append(f"[{a['id']}] Savol: {a['text']}")
        if a.get("measures"):
            lines.append(f"Nimani o'lchaydi: {a['measures']}")
        if a.get("weight"):
            lines.append(f"Koeffitsient: x{a['weight']}")
        lines.append(f"Javob: {a['answer']}")
        lines.append(f"Javob berish vaqti: {a.get('elapsed', '?')} soniya")
        lines.append("")
    return "\n".join(lines)


def _sanitize_json_text(raw: str) -> str:
    """JSON qator ichidagi qochirilmagan boshqaruv belgilarini (\\n, \\r, \\t) escape qiladi."""
    result = []
    in_string = False
    escape = False
    for ch in raw:
        if in_string:
            if escape:
                result.append(ch)
                escape = False
            elif ch == "\\":
                result.append(ch)
                escape = True
            elif ch == '"':
                result.append(ch)
                in_string = False
            elif ch == "\n":
                result.append("\\n")
            elif ch == "\r":
                result.append("\\r")
            elif ch == "\t":
                result.append("\\t")
            else:
                result.append(ch)
        else:
            if ch == '"':
                in_string = True
            result.append(ch)
    return "".join(result)


def _parse_ai_response(raw_text: str) -> dict:
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        try:
            return json.loads(_sanitize_json_text(raw_text))
        except json.JSONDecodeError:
            logger.warning(f"Claude javobi JSON emas, birinchi 500 belgi: {raw_text[:500]!r}")
            raise


def build_scoring_input(position: str, answers: dict, answer_times: dict) -> list[dict]:
    items = []
    for q in BLOCK1_QUESTIONS:
        if q["id"] in answers:
            items.append({
                "id": q["id"], "text": q["text"], "measures": q.get("measures", ""),
                "answer": answers[q["id"]], "elapsed": answer_times.get(q["id"]),
            })
    for q in SITUATIONS[position]:
        if q["id"] in answers:
            items.append({
                "id": q["id"], "text": q["text"], "measures": q.get("measures", ""),
                "answer": answers[q["id"]], "elapsed": answer_times.get(q["id"]),
                "weight": 2,
            })
    for q in BLOCK4_QUESTIONS:
        if q["id"] in answers:
            items.append({
                "id": q["id"], "text": q["text"], "measures": q.get("measures", ""),
                "answer": answers[q["id"]], "elapsed": answer_times.get(q["id"]),
            })
    return items


async def score_candidate(position_label: str, answers: list[dict]) -> tuple[dict | None, str | None]:
    system_prompt = SYSTEM_PROMPT.format(position=position_label)
    user_content = _build_user_content(position_label, answers)
    last_error = "Noma'lum xato"

    for attempt in range(MAX_RETRIES + 1):
        try:
            client = _get_client()
            response = await client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_content}],
            )
            raw_text = next(
                block.text for block in response.content if block.type == "text"
            )
            return _parse_ai_response(raw_text), None
        except RETRYABLE_EXCEPTIONS as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning(
                f"Ballash urinishi {attempt + 1}/{MAX_RETRIES + 1} muvaffaqiyatsiz: {last_error}"
            )
            if attempt < MAX_RETRIES:
                await asyncio.sleep(1.5 * (attempt + 1))
        except Exception as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.exception("Claude ballash kutilmagan xato berdi")
            break

    return None, last_error


async def rescore_from_sheet(row_number: int) -> tuple[dict | None, str | None]:
    row = await get_candidate_row(row_number)
    position = row.get("position")
    if position not in SITUATIONS:
        return None, f"Noma'lum lavozim: {position!r}"

    try:
        answer_times = json.loads(row.get("answer_times") or "{}")
    except json.JSONDecodeError:
        answer_times = {}

    answers = {
        q["id"]: row[q["id"]]
        for q in BLOCK1_QUESTIONS + SITUATIONS[position] + BLOCK4_QUESTIONS
        if row.get(q["id"])
    }

    scoring_input = build_scoring_input(position, answers, answer_times)
    if not scoring_input:
        return None, "Sheets da javoblar topilmadi"

    ai_result, error = await score_candidate(POSITIONS.get(position, position), scoring_input)
    if ai_result:
        await update_ai_result(row_number, ai_result)
    return ai_result, error
