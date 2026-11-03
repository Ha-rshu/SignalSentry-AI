from pathlib import Path
from dotenv import load_dotenv
import os

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

APP_NAME = "SignalSentry AI"
META_API_KEY = os.getenv("META_API_KEY", "")
META_API_BASE_URL = os.getenv("META_API_BASE_URL", "")
META_MODEL_NAME = os.getenv("META_MODEL_NAME", "")
