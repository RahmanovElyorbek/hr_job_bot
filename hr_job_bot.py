import logging
import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiohttp import web
from aiogram.dispatcher.webhook import get_new_configured_app

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
GOOGLE_CREDS = os.getenv("GOOGLE_CREDS")

ADMIN_ID = 8008645253

bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


# ================= GOOGLE SHEETS =================
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(GOOGLE_CREDS)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Ishchilar_bazasi").sheet1

logging.info("✅ Google Sheets ulandi")


# ================= STATES =================
class JobForm(StatesGroup):
    name = State()
    phone = State()
    age = State()
    position = State()

def position_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 Sotuvchi", "💳 Kassir")
    kb.add("📦 Yuk tashuvchi", "🧹 Farrosh")
    return kb


# ================= START =================
@dp.message_handler(commands="start")
async def start(message: types.Message):
    await message.answer("👋 Assalomu alaykum!\n\nIsmingizni yozing:")
    await JobForm.name.set()


# ================= NAME =================
@dp.message_handler(state=JobForm.name)
async def get_name(message: types.Message, state: FSMContext):

    if len(message.text) < 2:
        await message.answer("Ism noto‘g‘ri. Qayta yozing:")
        return

    await state.update_data(name=message.text)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton("📞 Telefon yuborish", request_contact=True))

    await message.answer("Telefon raqamingizni yuboring:", reply_markup=kb)
    await JobForm.phone.set()


# ================= PHONE =================
@dp.message_handler(content_types=types.ContentType.CONTACT, state=JobForm.phone)
async def get_phone(message: types.Message, state: FSMContext):

    await state.update_data(phone=message.contact.phone_number)

    await message.answer(
        "Yoshingiz nechida?",
        reply_markup=types.ReplyKeyboardRemove()
    )

    await JobForm.age.set()


# ================= AGE =================
@dp.message_handler(state=JobForm.age)
async def get_age(message: types.Message, state: FSMContext):

    if not message.text.isdigit():
        await message.answer("Faqat son kiriting! (masalan 25)")
        return

    await state.update_data(age=message.text)

    await message.answer(
    "Qaysi lavozimga ishga kirmoqchisiz?",
    reply_markup=position_keyboard()
    )
    await JobForm.position.set()


# ================= POSITION =================
# ================= POSITION =================
@dp.message_handler(state=JobForm.position)
async def get_position(message: types.Message, state: FSMContext):

    VALID_POSITIONS = [
        "🛒 Sotuvchi",
        "💳 Kassir",
        "📦 Yuk tashuvchi",
        "🧹 Farrosh"
    ]

    # Tugmadan tanlashni majbur qilamiz
    if message.text not in VALID_POSITIONS:
        await message.answer("Iltimos tugmalardan birini tanlang 👇")
        return

    await state.update_data(position=message.text)
    data = await state.get_data()

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # USERGA DARROV JAVOB
    await message.answer(
        "✅ Rahmat! Arizangiz qabul qilindi.",
        reply_markup=types.ReplyKeyboardRemove()
    )

    # SHEETGA YOZISH
    try:
        sheet.append_row([
            data.get('name'),
            data.get('phone'),
            data.get('age'),
            data.get('position'),
            now
        ])
    except Exception as e:
        logging.error(f"Sheetga yozilmadi: {e}")

    # ADMINGA YUBORISH
    text = f"""
📌 Yangi ishchi!

👤 {data.get('name')}
📞 {data.get('phone')}
🎂 {data.get('age')}
💼 {data.get('position')}
🕒 {now}
"""

    await bot.send_message(ADMIN_ID, text)

    await state.finish()


# ================= RUN =================

WEBHOOK_HOST = "https://hr-job-bot.onrender.com"
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    logging.warning("✅ Webhook ishga tushdi!")

async def on_shutdown(dp):
    await bot.delete_webhook()
    logging.warning("⛔ Webhook o‘chirildi!")

if __name__ == "__main__":

    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_PATH)

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
