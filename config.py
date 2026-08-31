import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
TORTKOL_MANAGER_ID = int(os.getenv("TORTKOL_MANAGER_ID")) if os.getenv("TORTKOL_MANAGER_ID", "").strip() else None
SHEET_ID = os.getenv("SHEET_ID")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_CREDENTIALS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
PORT = int(os.getenv("PORT", 10000))
