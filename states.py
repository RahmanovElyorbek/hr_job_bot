from aiogram.fsm.state import State, StatesGroup


class Interview(StatesGroup):
    consent = State()

    # Blok 0 — avtofiltr
    filter_age = State()
    filter_branch = State()
    filter_shift = State()
    filter_start_date = State()

    # Lavozim va aloqa
    position = State()
    phone = State()

    # Blok 1 — umumiy faktlar
    facts_last_job = State()
    facts_leave_reason = State()
    facts_job_count = State()
    facts_reference = State()

    # Blok 2 — lavozimga xos vaziyatli savollar (data["sit_index"] orqali yuriladi)
    situations = State()
    omborchi_health = State()

    # Blok 3 — media
    media_voice = State()
    media_video = State()

    # Blok 4 — motivatsiya
    motivation_why = State()
    motivation_future = State()
    motivation_weakness = State()
    motivation_questions = State()
