import logging
import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiogram.utils.executor import start_webhook

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)

# ================= ENV =================
TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_CREDS = os.getenv("GOOGLE_CREDS")

if not TOKEN:
    raise ValueError("BOT_TOKEN topilmadi!")

if not GOOGLE_CREDS:
    raise ValueError("GOOGLE_CREDS topilmadi!")

ADMIN_ID = 8008645253

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


# ================= GOOGLE SHEETS =================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds_dict = json.loads(GOOGLE_CREDS)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("Ishchilar_bazasi").sheet1

    logging.info("Google Sheets ulandi ✅")

except Exception as e:
    logging.error(f"Google Sheets ulanmadi ❌ {e}")
    sheet = None


# ================= STATES =================
class JobForm(StatesGroup):
    name = State()
    phone = State()
    age = State()
    position = State()


# ================= START =================
@dp.message_handler(commands="start")
async def start(message: types.Message):
    await message.answer(
        "👋 Assalomu alaykum!\n\nIshga topshirish uchun ismingizni yozing:"
    )
    await JobForm.name.set()


# ================= NAME =================
@dp.message_handler(state=JobForm.name)
async def get_name(message: types.Message, state: FSMContext):

    if len(message.text) < 2:
        await message.answer("Ism noto‘g‘ri. Qayta kiriting:")
        return

    await state.update_data(name=message.text)

    contact_btn = types.ReplyKeyboardMarkup(resize_keyboard=True)
    contact_btn.add(
        types.KeyboardButton("📞 Telefon raqam yuborish", request_contact=True)
    )

    await message.answer(
        "Telefon raqamingizni yuboring:",
        reply_markup=contact_btn
    )

    await JobForm.phone.set()


# ================= PHONE =================
@dp.message_handler(content_types=types.ContentType.CONTACT, state=JobForm.phone)
async def get_phone(message: types.Message, state: FSMContext):

    phone = message.contact.phone_number

    await state.update_data(phone=phone)

    await message.answer(
        "Yoshingiz nechida?",
        reply_markup=types.ReplyKeyboardRemove()
    )

    await JobForm.age.set()


# ================= AGE =================
@dp.message_handler(state=JobForm.age)
async def get_age(message: types.Message, state: FSMContext):

    if not message.text.isdigit():
        await message.answer("Iltimos faqat son kiriting (masalan: 25)")
        return

    await state.update_data(age=message.text)

    await message.answer("Qaysi lavozimga ishga kirmoqchisiz?")
    await JobForm.position.set()


# ================= POSITION =================
@dp.message_handler(state=JobForm.position)
async def get_position(message: types.Message, state: FSMContext):

    await state.update_data(position=message.text)
    data = await state.get_data()

    text = f"""
📌 <b>Yangi ishchi arizasi!</b>

👤 <b>Ismi:</b> {data.get('name')}
📞 <b>Telefon:</b> {data.get('phone')}
🎂 <b>Yoshi:</b> {data.get('age')}
💼 <b>Lavozim:</b> {data.get('position')}
🕒 <b>Vaqt:</b> {datetime.now().strftime("%Y-%m-%d %H:%M")}
"""

    # ===== Google Sheet =====
    if sheet:
        try:
            sheet.append_row([
                data.get('name'),
                data.get('phone'),
                data.get('age'),
                data.get('position'),
                datetime.now().strftime("%Y-%m-%d %H:%M")
            ])
        except Exception as e:
            logging.error(f"Sheetga yozilmadi ❌ {e}")

    # ===== Admin =====
    try:
        await bot.send_message(
            ADMIN_ID,
            text,
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"Adminga yuborilmadi ❌ {e}")

    await message.answer(
        "✅ Rahmat! Tez orada siz bilan bog'lanamiz."
    )

    await state.finish()


# ================= ERROR HANDLER =================
@dp.errors_handler()
async def global_error_handler(update, exception):
    logging.error(f"Xato chiqdi: {exception}")
    return True


# ================= RUN =================
if __name__ == "__main__":

WEBHOOK_HOST = "https://hr-job-bot.onrender.com"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.environ.get("PORT", 10000))


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp):
    await bot.delete_webhook()


if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
