import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")

SSC_API_KEY = os.getenv("API_KEY", "")

# Who is using the app. Stands in for the signed-in user until there are real accounts:
# it greets them on the board and signs any drafted email that the customer record
# doesn't already name a CSM for.
CSM_NAME = os.getenv("CSM_NAME", "Alex")
SSC_BASE_URL = "https://api.securityscorecard.io"

DATA_DIR = BACKEND_DIR / "data"
CUSTOMERS_FILE = DATA_DIR / "customers.json"
DECISION_MAKERS_DIR = DATA_DIR / "decision_makers"
USAGE_INDIVIDUALS_DIR = DATA_DIR / "usage_individuals"
NEWS_EVENTS_DIR = DATA_DIR / "news_events"
