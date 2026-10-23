"""
db/models.py — HR status + avtomatik xabar moduli uchun SQLAlchemy modeli.

Faqat BITTA jadval: candidates. Bu Google Sheets'dagi to'liq anketa
ma'lumotlarini (savol-javoblar, AI ballash) ALMASHTIRMAYDI — ular hamon
services/sheets.py orqali Sheets'da saqlanadi. Bu jadval FAQAT status va
xabar yuborish holatini kuzatish uchun, tezkor va ishonchli qidiruv
(masalan /zahira) va idempotentlik uchun kerak.

status/notify_status Python enum bilan ifodalanadi, lekin bazada oddiy
VARCHAR + CHECK constraint sifatida saqlanadi (native_enum=False) — bu
kelajakda yangi status qo'shishni ALTER TYPE siz, oddiy CHECK
constraint yangilash bilan qiladi.
"""

import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class CandidateStatus(str, enum.Enum):
    new = "new"
    invited = "invited"
    reserve = "reserve"
    rejected = "rejected"


class NotifyStatus(str, enum.Enum):
    none = "none"
    queued = "queued"
    sent = "sent"
    failed = "failed"


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32))
    position: Mapped[str | None] = mapped_column(String(64))

    # services/sheets.py dagi qatorga bog'lanish — status Sheets'ga ham
    # yozilishi (dual-write) uchun kerak, mavjud /stats buyrug'i buzilmasin.
    sheet_row: Mapped[int | None] = mapped_column(Integer)

    applied_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    status: Mapped[CandidateStatus] = mapped_column(
        Enum(CandidateStatus, name="candidate_status", native_enum=False, length=16),
        nullable=False, default=CandidateStatus.new,
    )
    status_changed_at: Mapped[datetime | None] = mapped_column(DateTime)
    status_changed_by: Mapped[str | None] = mapped_column(String(64))

    notify_status: Mapped[NotifyStatus] = mapped_column(
        Enum(NotifyStatus, name="notify_status", native_enum=False, length=16),
        nullable=False, default=NotifyStatus.none,
    )
    notified_at: Mapped[datetime | None] = mapped_column(DateTime)
    notify_error: Mapped[str | None] = mapped_column(Text)

    # Zahira: status_changed_at + 90 kun. /zahira shu maydon bo'yicha filtrlaydi.
    reserve_until: Mapped[datetime | None] = mapped_column(DateTime)
