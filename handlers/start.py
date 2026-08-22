import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from questions import (
    BLOCK0_AGE_OPTIONS,
    BLOCK0_AGE_REJECT,
    BLOCK0_BRANCH_OPTIONS,
    BLOCK0_SHIFT_OPTIONS,
    BLOCK0_SHIFT_REJECT,
    BLOCK0_START_DATE_OPTIONS,
    MINOR_AGE_RANGE,
    MINOR_SHIFT_LABEL,
    POSITIONS,
)
from services.sheets import has_recent_application
from states import Interview

logger = logging.getLogger(__name__)
router = Router(name="start")


def _options_keyboard(prefix: str, options: list[str]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=opt, callback_data=f"{prefix}:{opt}")]
            for opt in options
        ]
    )


def _position_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=label, callback_data=f"pos:{key}")]
            for key, label in POSITIONS.items()
        ]
    )


async def reject_candidate(user_first_name: str, message: Message, state: FSMContext):
    name = user_first_name or "do'stim"
    await message.answer(
        f"Rahmat, {name}! Afsuski, hozircha talablarimizga mos kelmadingiz. "
        "Kelajakda yana urinib ko'rishingiz mumkin."
    )
    await state.clear()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()

    if await has_recent_application(message.from_user.id):
        await message.answer(
            "Siz yaqinda ariza topshirgansiz. Javobimizni kuting yoki "
            "30 kundan keyin qayta urinib ko'ring."
        )
        return

    name = message.from_user.first_name or "do'stim"
    await message.answer(
        f"👋 Assalomu alaykum, {name}!\n\n"
        "Men Sharq Supermarket'ning HR botiman. Ishga qabul bo'yicha bir nechta "
        "savol beraman (davomiyligi ~10 daqiqa). Ba'zi savollarga ovozli va "
        "dumaloq video javob berishingiz so'raladi.\n\nBoshlaymizmi?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Boshlash ✅", callback_data="consent:start")]
            ]
        ),
    )
    await state.set_state(Interview.consent)


@router.callback_query(Interview.consent, F.data == "consent:start")
async def consent_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Yoshingiz nechada?",
        reply_markup=_options_keyboard("b0age", BLOCK0_AGE_OPTIONS),
    )
    await state.set_state(Interview.filter_age)


@router.callback_query(Interview.filter_age, F.data.startswith("b0age:"))
async def filter_age(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    if value in BLOCK0_AGE_REJECT:
        await reject_candidate(callback.from_user.first_name, callback.message, state)
        return

    await state.update_data(age_range=value)
    await callback.message.answer(
        "Qaysi filialda ishlay olasiz?",
        reply_markup=_options_keyboard("b0branch", BLOCK0_BRANCH_OPTIONS),
    )
    await state.set_state(Interview.filter_branch)


@router.callback_query(Interview.filter_branch, F.data.startswith("b0branch:"))
async def filter_branch(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.update_data(branch=value)

    data = await state.get_data()
    if data.get("age_range") == MINOR_AGE_RANGE:
        await state.update_data(shift_ok=MINOR_SHIFT_LABEL)
        await callback.message.answer(
            f"⚠️ Siz 16-17 yoshdasiz. Qonunchilikka ko'ra, siz faqat {MINOR_SHIFT_LABEL} "
            "smenasida ishlashingiz mumkin. Arizangiz shu smena uchun qabul qilinadi."
        )
        await callback.message.answer(
            "Qachondan ishni boshlay olasiz?",
            reply_markup=_options_keyboard("b0start", BLOCK0_START_DATE_OPTIONS),
        )
        await state.set_state(Interview.filter_start_date)
        return

    await callback.message.answer(
        "Smenali jadvalda (ertalabki/kechki) ishlay olasizmi?",
        reply_markup=_options_keyboard("b0shift", BLOCK0_SHIFT_OPTIONS),
    )
    await state.set_state(Interview.filter_shift)


@router.callback_query(Interview.filter_shift, F.data.startswith("b0shift:"))
async def filter_shift(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    if value in BLOCK0_SHIFT_REJECT:
        await reject_candidate(callback.from_user.first_name, callback.message, state)
        return

    await state.update_data(shift_ok=value)
    await callback.message.answer(
        "Qachondan ishni boshlay olasiz?",
        reply_markup=_options_keyboard("b0start", BLOCK0_START_DATE_OPTIONS),
    )
    await state.set_state(Interview.filter_start_date)


@router.callback_query(Interview.filter_start_date, F.data.startswith("b0start:"))
async def filter_start_date(callback: CallbackQuery, state: FSMContext):
    value = callback.data.split(":", 1)[1]
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.update_data(start_date=value)
    await callback.message.answer(
        "Qaysi lavozimga nomzod bo'lmoqchisiz?",
        reply_markup=_position_keyboard(),
    )
    await state.set_state(Interview.position)
