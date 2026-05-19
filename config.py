# GeoTradeV2/config.py

# --- API Keys ---
import os
from dotenv import load_dotenv
load_dotenv()

NEWS_API_KEY      = os.getenv("NEWS_API_KEY", "")
GEONAMES_USERNAME = os.getenv("GEONAMES_USERNAME", "")
HF_API_KEY        = os.getenv("HF_API_KEY", "")

# --- Database ---
DB_PATH = "data/news.db"

# --- Scraper ---
FETCH_INTERVAL_MINUTES = 15
NEWSAPI_PAGE_SIZE = 20
NEWSAPI_QUERIES = [
    "war", "military attack", "sanctions",
    "oil supply", "geopolitical conflict",
    "missile strike", "coup", "civil unrest"
]

# --- Detector ---
RELEVANCE_THRESHOLD = 0.35
MIN_RISK_SCORE = 30

# --- Pre-filter Keywords ---
GEO_KEYWORDS = [
    "iran", "russia", "ukraine", "israel", "china", "nato",
    "military", "sanction", "missile", "troops", "attack",
    "oil", "gas", "opec", "conflict", "ceasefire", "coup",
    "war", "strike", "embargo", "pipeline", "protest", "riot"
]

# --- Zero-shot Labels ---
CANDIDATE_LABELS = [
    "geopolitical conflict",
    "energy and oil markets",
    "economic sanctions",
    "military attack",
    "civil unrest",
    "entertainment and culture",
    "sports",
    "technology",
    "crime",
    "weather"
]

RELEVANT_LABELS = {
    "geopolitical conflict",
    "energy and oil markets",
    "economic sanctions",
    "military attack",
    "civil unrest"
}

# --- NER ---
NER_MODEL = "dslim/bert-base-NER"
NER_LABELS = {
    "LOC": "location",
    "GPE": "country",
    "ORG": "organization",
    "PER": "person",
    "MISC": "miscellaneous"
}

# --- Asset Map ---
ASSET_MAP = {
    "geopolitical conflict":  {"asset": "Gold",        "signal": "BUY"},
    "military attack":        {"asset": "Gold",        "signal": "BUY"},
    "energy and oil markets": {"asset": "Oil",         "signal": "BUY"},
    "economic sanctions":     {"asset": "Commodities", "signal": "WATCH"},
    "civil unrest":           {"asset": "Currency",    "signal": "SELL"},
}