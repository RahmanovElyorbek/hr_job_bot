-- migrations/001_create_candidates.sql
-- HR status + avtomatik xabar moduli uchun candidates jadvali.
--
-- IDEMPOTENT: bir necha marta ishga tushirilsa ham xato bermaydi
-- (IF NOT EXISTS hamma joyda). Mavjud qatorlarga tegilmaydi.
--
-- Bu jadval Google Sheets'dagi to'liq anketa ma'lumotlarini ALMASHTIRMAYDI
-- (interview javoblari, AI ballash hamon Sheets'da) — faqat status va
-- xabar yuborish holatini kuzatish uchun.
--
-- ISHGA TUSHIRISH (ixtiyoriy — bot birinchi marta ishga tushganda
-- db/session.py orqali AVTOMATIK ham bajariladi, bu faylni qo'lda
-- ishga tushirish shart emas, lekin deploy'dan oldin tekshirib
-- ko'rmoqchi bo'lsangiz foydalanishingiz mumkin):
--
--   psql "$DATABASE_URL" -f migrations/001_create_candidates.sql

CREATE TABLE IF NOT EXISTS candidates (
    id                  SERIAL PRIMARY KEY,
    telegram_id         BIGINT NOT NULL,
    username            VARCHAR(64),
    full_name           VARCHAR(255) NOT NULL,
    phone               VARCHAR(32),
    position            VARCHAR(64),

    -- services/sheets.py dagi qatorga bog'lanish (dual-write uchun)
    sheet_row           INTEGER,

    applied_at          TIMESTAMP NOT NULL DEFAULT NOW(),

    -- new | invited | reserve | rejected
    status              VARCHAR(16) NOT NULL DEFAULT 'new',
    status_changed_at   TIMESTAMP,
    status_changed_by   VARCHAR(64),

    -- none | queued | sent | failed
    notify_status       VARCHAR(16) NOT NULL DEFAULT 'none',
    notified_at         TIMESTAMP,
    notify_error        TEXT,

    -- Zahira: status_changed_at + 90 kun
    reserve_until       TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_telegram_id ON candidates(telegram_id);
CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
CREATE INDEX IF NOT EXISTS idx_candidates_reserve_until ON candidates(reserve_until)
    WHERE status = 'reserve';

-- Rollback (qo'lda, ehtiyot bo'ling — barcha status/xabar tarixi yo'qoladi):
--   DROP TABLE IF EXISTS candidates;
