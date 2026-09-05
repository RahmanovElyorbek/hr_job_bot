# HR status + avtomatik xabar moduli

Bu hujjat @sharq_job_bot ga qo'shilgan yangi modulni tushuntiradi: admin
nomzod anketasi ostidagi 3 ta tugma orqali qaror qabul qiladi, nomzodga
kerak bo'lsa avtomatik xabar ketadi.

## Nima o'zgardi, nima o'zgarmadi

**O'zgarmadi** (Google Sheets, oldingidek ishlaydi):
- `handlers/interview.py` — anketa to'ldirish jarayoni
- `services/sheets.py` — savol-javoblar, AI ballash Sheets'da saqlanadi
- `/rescore`, `/stats` buyruqlari

**Yangi qo'shildi** (PostgreSQL, `candidates` jadvali):
- `db/models.py`, `db/session.py` — SQLAlchemy async model va sxema
- `templates.py` — nomzodga yuboriladigan xabar matnlari
- `services/notify.py` — qaror qabul qilish, xabar yuborish, tungi
  navbat, flood-control, log kanal
- `handlers/admin.py` ichidagi qaror tugmalari (`_decision_keyboard`,
  `decide_candidate` va h.k.) — Sheets'dagi `status`/`decided_by`/
  `decided_at` ustunlariga ham yozadi (dual-write), shuning uchun
  `/stats` va Sheets hisoboti buzilmaydi.
- `/zahira` buyrug'i

## Tugmalar va xatti-harakat

| Tugma | Status | Avtomatik xabar |
|---|---|---|
| ✅ Taklif | `invited` | **YO'Q** — admin nomzodga `tg://user?id=...` havolasi orqali o'zi yozadi. Admin xabarida telefon raqami `<code>` formatda (nusxalash uchun) ko'rsatiladi. |
| 📋 Zahira | `reserve` | Ha, darhol (yoki tunda bo'lsa — navbatga) |
| ❌ Rad | `rejected` | Tasdiqlashdan keyin ("Ha, yubor" bosilsa) |

**"❌ Rad" tugmasi bosilganda darhol yubormaydi** — avval "Nomzod: {ism}\nRad
xabari yuborilsinmi?" ko'rsatiladi, "Ha, yubor" / "Bekor qilish" bilan.

## Xatolikdan himoya

- **Idempotentlik**: `candidates.status` ustuni `new` bo'lmasa, tugma
  bosilganda "Bu nomzod bo'yicha qaror allaqachon qabul qilingan: ..."
  ko'rsatiladi — qayta qaror qabul qilib bo'lmaydi.
- **Bloklangan foydalanuvchi**: `TelegramForbiddenError`/`TelegramBadRequest`
  ushlanadi, `notify_status=failed` bo'ladi, barcha `ADMIN_IDS`ga
  "⚠️ {ism} ga xabar ketmadi... Qo'lda bog'laning: {telefon}" xabari
  ketadi.
- **Tungi soat (21:00–08:00, Asia/Tashkent)**: xabar `notify_status=queued`
  bilan navbatga qo'yiladi, APScheduler har kuni ertalab 09:00 da
  yuboradi (`services/notify.py:flush_queued_notifications`).
- **Flood control**: `TelegramRetryAfter` ushlanadi, ko'rsatilgan vaqt
  kutilib, BIR marta qayta uriniladi.
- **Ruxsat**: faqat `ADMIN_IDS` (+ mavjud `TORTKOL_MANAGER_ID`, filial
  bo'yicha) tugmalarni bosa oladi.

## NOTIFY_MODE=mock (test uchun)

`.env`da `NOTIFY_MODE=mock` qo'ysangiz, botga hech kimga (nomzodga ham,
xato xabarlariga ham emas — faqat haqiqiy Telegram yuborishlariga)
xabar ketmaydi, faqat log'da ko'rinadi:
```
[MOCK NOTIFY] telegram_id=123456789 -> 'Assalomu alaykum, Ali...'
```
Bu bilan butun tugma → status → xabar oqimini haqiqiy nomzodlarga
xalaqit bermasdan sinab ko'rishingiz mumkin.

## Windows'da lokal test

```powershell
cd hr_job_bot
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# .env faylini yarating (.env.example dan nusxa oling)
copy .env.example .env
notepad .env
```

`.env` faylida kamida shularni to'ldiring:
```
BOT_TOKEN=...
ADMIN_IDS=123456789
SHEET_ID=...
GOOGLE_CREDENTIALS_JSON={"type": "service_account", ...}
DATABASE_URL=postgresql://user:pass@host:5432/dbname
NOTIFY_MODE=mock
TIMEZONE=Asia/Tashkent
```

`DATABASE_URL` uchun lokal PostgreSQL yo'q bo'lsa, Render'da bepul
Postgres yaratib (Dashboard → New → PostgreSQL), "External Database URL"
ni shu yerga qo'yishingiz mumkin — lokal kompyuteringizdan ham unga
ulanadi.

Ishga tushirish:
```powershell
python main.py
```

Muvaffaqiyatli bo'lsa konsolda ko'rinadi:
```
✅ candidates jadvali tayyor
✅ Postgres (candidates) tayyor
🔔 Scheduler: tunda (21:00-08:00) navbatga qo'shilgan xabarlar har kuni 09:00 da yuboriladi
Bot polling boshlandi
```

## Render'da deploy

1. `render.yaml` allaqachon yangilangan — `DATABASE_URL`, `LOG_CHANNEL_ID`,
   `NOTIFY_MODE`, `TIMEZONE` qo'shilgan.
2. Render Dashboard → New → PostgreSQL — bepul reja bilan baza yarating,
   "Internal Database URL"ni nusxalang.
3. Bot xizmatining Environment bo'limida:
   - `DATABASE_URL` = yuqoridagi Internal Database URL
   - `LOG_CHANNEL_ID` = log kanalingiz ID'si (kanalga botni admin qilib
     qo'shing, keyin ID'ni oling — masalan `@userinfobot` yordamida)
   - `NOTIFY_MODE=real` (production uchun; test paytida `mock`)
   - `TIMEZONE=Asia/Tashkent`
4. Deploy — `candidates` jadvali birinchi ishga tushishda avtomatik
   yaratiladi (`db/session.py:init_db()`), qo'lda migratsiya ishga
   tushirish shart emas.

## Migratsiya fayli

`migrations/001_create_candidates.sql` — agar deploy'dan oldin bazani
qo'lda tekshirmoqchi bo'lsangiz:
```powershell
psql "$env:DATABASE_URL" -f migrations/001_create_candidates.sql
```
Bu ixtiyoriy — bot baribir shu SQL'ni avtomatik (idempotent) bajaradi.

## `/zahira` buyrug'i

Faqat `ADMIN_IDS` uchun. Muddati tugamagan (status_changed_at + 90 kun)
zahiradagi nomzodlarni ism, lavozim, sana va yozish havolasi bilan
ro'yxatlaydi.

## Log kanali

`LOG_CHANNEL_ID` o'rnatilgan bo'lsa, har bir qaror shu formatda yoziladi:
```
Ali Valiyev → ❌ Rad (admin: @elyorbek) | Xabar: ✅
```
`LOG_CHANNEL_ID` bo'sh qoldirilsa, log kanaliga yozish oddiy o'tkazib
yuboriladi (xato bermaydi).
