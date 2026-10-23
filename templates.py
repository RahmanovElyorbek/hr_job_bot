"""
templates.py — nomzodga avtomatik yuboriladigan xabar shablonlari.

Hardcode qilinmagan — bu faylni o'zgartirsangiz keyingi deploy'dan
boshlab yangi matn ishlatiladi, kod ichida qidirish shart emas.

"invited" (Taklif) uchun shablon YO'Q — bu status uchun avtomatik xabar
yuborilmaydi, admin nomzodga to'g'ridan-to'g'ri (tg://user havolasi
orqali) o'zi yozadi.
"""

TEMPLATES = {
    "rejected": (
        "Assalomu alaykum, {name}. Suhbat uchun rahmat 🤝\n\n"
        "Afsuski, bu lavozimga boshqa nomzod tanlandi. Sizga ishingizda omad "
        "tilaymiz.\n\n"
        "<b>Sharq Supermarket</b>"
    ),
    "reserve": (
        "Assalomu alaykum, {name}. Suhbat uchun rahmat 🤝\n\n"
        "Nomzodingizni <b>zahira ro'yxatimizga</b> kiritdik. Mos o'rin bo'shashi "
        "bilan birinchi bo'lib siz bilan bog'lanamiz.\n\n"
        "<b>Sharq Supermarket</b>"
    ),
}
