import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

SSC_API_KEY = os.getenv("API_KEY", "")
SSC_BASE_URL = "https://api.securityscorecard.io"

DATA_DIR = BACKEND_DIR / "data"
CUSTOMERS_FILE = DATA_DIR / "customers.json"
DECISION_MAKERS_DIR = DATA_DIR / "decision_makers"
