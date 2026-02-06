import logging
import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime


import os

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8008645253
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = json.loads(os.getenv("GOOGLE_CREDS"))
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Ishchilar_bazasi").sheet1

# ====== STATE ======
class JobForm(StatesGroup):
    name = State()
    phone = State()
    age = State()
    position = State()


# ====== START ======
@dp.message_handler(commands='start')
async def start(message: types.Message):
    await message.answer("Assalomu alaykum! Ishga topshirish uchun ismingizni yozing:")
    await JobForm.name.set()


# ====== NAME ======
@dp.message_handler(state=JobForm.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    
    contact_btn = types.ReplyKeyboardMarkup(resize_keyboard=True)
    contact_btn.add(types.KeyboardButton("📞 Telefon raqam yuborish", request_contact=True))

    await message.answer("Telefon raqamingizni yuboring:", reply_markup=contact_btn)
    await JobForm.phone.set()


# ====== PHONE ======
@dp.message_handler(content_types=types.ContentType.CONTACT, state=JobForm.phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)

    await message.answer("Yoshingiz nechida?", reply_markup=types.ReplyKeyboardRemove())
    await JobForm.age.set()


# ====== AGE ======
@dp.message_handler(state=JobForm.age)
async def get_age(message: types.Message, state: FSMContext):
    await state.update_data(age=message.text)

    await message.answer("Qaysi lavozimga ishga kirmoqchisiz?")
    await JobForm.position.set()


# ====== POSITION ======
@dp.message_handler(state=JobForm.position)
async def get_position(message: types.Message, state: FSMContext):

    await state.update_data(position=message.text)
    data = await state.get_data()

    text = f"""
📌 Yangi ishchi arizasi!

👤 Ismi: {data['name']}
📞 Telefon: {data['phone']}
🎂 Yoshi: {data['age']}
💼 Lavozim: {data['position']}
"""

    sheet.append_row([
        data['name'],
        data['phone'],
        data['age'],
        data['position'],
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ])

    await bot.send_message(ADMIN_ID, text)

    await message.answer("Rahmat! Tez orada siz bilan bog'lanamiz ✅")

    await state.finish()

    await state.update_data(position=message.text)
    data = await state.get_data()

    text = f"""
📌 Yangi ishchi arizasi!
👤 Ismi: {data['name']}
📞 Telefon: {data['phone']}
🎂 Yoshi: {data['age']}
💼 Lavozim: {data['position']}
"""

    sheet.append_row([
        data['name'],
        data['phone'],
        data['age'],
        data['position'],
        datetime.now().strftime("%Y-%m-%d %H:%M")
    ])

    await bot.send_message(ADMIN_ID, text)

    await message.answer("Rahmat! Tez orada siz bilan bog'lanamiz ✅")

    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
