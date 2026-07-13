from aiogram import Router
from aiogram.types import Message

router = Router(name="fallback")


@router.message()
async def fallback(message: Message):
    await message.answer("Iltimos, /start dan qayta boshlang.")
