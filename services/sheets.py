import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_CREDENTIALS_JSON, SHEET_ID

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

WORKSHEET_NAME = "Nomzodlar"
TASHKENT_TZ = ZoneInfo("Asia/Tashkent")
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

HEADERS = [
    "timestamp", "telegram_id", "username", "full_name", "phone",
    "position", "branch", "age_range", "shift_ok", "start_date",
    "q1_1", "q1_2", "q1_3", "q1_4",
    "K1", "K2", "K3", "K4", "K5",
    "S1", "S2", "S3", "S4", "S5",
    "O1", "O2", "O3", "O4", "O5", "O_health",
    "F1", "F2", "F3", "F4", "F5",
    "q4_1", "q4_2", "q4_3", "q4_4",
    "answer_times", "voice_file_id", "video_file_id",
    "ai_percent", "ai_verdict", "ai_summary", "ai_red_flags",
    "status", "decided_by", "decided_at",
]

_worksheet = None
_dup_cache = {}  # telegram_id -> (checked_at, is_duplicate)
DUP_CACHE_TTL = 600  # 10 daqiqa — gspread kvotasini tejash uchun


def now_tashkent_str() -> str:
    return datetime.now(TASHKENT_TZ).strftime(TIMESTAMP_FORMAT)


def _get_worksheet():
    global _worksheet
    if _worksheet is not None:
        return _worksheet

    creds_dict = json.loads(GOOGLE_CREDENTIALS_JSON)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(SHEET_ID)
    try:
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(WORKSHEET_NAME, rows=1000, cols=len(HEADERS))

    if not worksheet.row_values(1):
        worksheet.append_row(HEADERS)

    _worksheet = worksheet
    logger.info("Google Sheets ulandi")
    return _worksheet


def _append_candidate_sync(row_dict: dict) -> int:
    worksheet = _get_worksheet()
    row = [row_dict.get(h, "") for h in HEADERS]
    worksheet.append_row(row, value_input_option="USER_ENTERED")
    return len(worksheet.get_all_values())


async def append_candidate(row_dict: dict) -> int:
    return await asyncio.to_thread(_append_candidate_sync, row_dict)


def _update_status_sync(row_number: int, status: str, decided_by: str, decided_at: str):
    worksheet = _get_worksheet()
    worksheet.update_cell(row_number, HEADERS.index("status") + 1, status)
    worksheet.update_cell(row_number, HEADERS.index("decided_by") + 1, decided_by)
    worksheet.update_cell(row_number, HEADERS.index("decided_at") + 1, decided_at)


async def update_status(row_number: int, status: str, decided_by: str, decided_at: str):
    await asyncio.to_thread(_update_status_sync, row_number, status, decided_by, decided_at)


def _has_recent_application_sync(telegram_id: int) -> bool:
    worksheet = _get_worksheet()
    records = worksheet.get_all_values()
    if len(records) <= 1:
        return False

    id_col = HEADERS.index("telegram_id")
    ts_col = HEADERS.index("timestamp")
    cutoff = datetime.now() - timedelta(days=30)

    for row in records[1:]:
        if len(row) <= max(id_col, ts_col) or row[id_col] != str(telegram_id):
            continue
        try:
            ts = datetime.strptime(row[ts_col], TIMESTAMP_FORMAT)
        except ValueError:
            continue
        if ts >= cutoff:
            return True
    return False


async def has_recent_application(telegram_id: int) -> bool:
    now = time.time()
    cached = _dup_cache.get(telegram_id)
    if cached and now - cached[0] < DUP_CACHE_TTL:
        return cached[1]

    result = await asyncio.to_thread(_has_recent_application_sync, telegram_id)
    _dup_cache[telegram_id] = (now, result)
    return result


def _get_all_rows_sync():
    return _get_worksheet().get_all_values()


async def get_all_rows():
    return await asyncio.to_thread(_get_all_rows_sync)
