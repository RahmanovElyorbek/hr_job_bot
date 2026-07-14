import json
import logging

from anthropic import AsyncAnthropic

from config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-5"

SYSTEM_PROMPT = """Sen 20 yillik supermarket tajribasiga ega HR ekspertsan. Quyida {position}
lavozimiga nomzodning suhbat javoblari berilgan. Har bir savol yonida
"nimani o'lchaydi" izohi bor — shu mezonga qarab 0/1/2 ball qo'y.

Ballash: 0 = qizil bayroq (halollikka shubha, mas'uliyatsizlik, agressiya,
shablon/ma'nosiz javob), 1 = qoniqarli, 2 = kuchli (aniq, samimiy, tashabbusli).

Har javob uchun javob berish vaqti (soniyalarda) berilgan. Vaziyatli savolga
10 soniyadan tez berilgan uzun javob — nusxa ko'chirilgan bo'lishi mumkin,
buni izohda belgila.

Har bir "comment" — bitta qisqa jumla (10 so'zdan oshmasin).

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


async def score_candidate(position_label: str, answers: list[dict]) -> dict | None:
    system_prompt = SYSTEM_PROMPT.format(position=position_label)
    user_content = _build_user_content(position_label, answers)

    try:
        client = _get_client()
        response = await client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        raw_text = response.content[0].text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.strip("`")
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
        return json.loads(raw_text.strip())
    except Exception:
        logger.exception("Claude ballash xato berdi")
        return None
