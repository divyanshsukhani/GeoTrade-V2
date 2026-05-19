# GeoTradeV2/detector/classifier.py

import requests
import time
from config import RELEVANT_LABELS, HF_API_KEY

API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-mnli"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

LABELS = list(RELEVANT_LABELS) + [
    "entertainment and culture",
    "sports", "technology",
    "crime", "weather"
]

def classify_article(title, description):
    text = (title + ". " + description)[:512]

    for attempt in range(3):
        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json={
                    "inputs": text,
                    "parameters": {"candidate_labels": LABELS}
                },
                timeout=60
            )
            result    = response.json()
            top_label = result[0]["label"]
            top_score = result[0]["score"]
            relevant  = top_label in RELEVANT_LABELS
            return relevant, top_label, round(top_score, 3)
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2)

    return False, "unknown", 0.0


if __name__ == "__main__":
    test_articles = [
        {
            "title": "Iran strikes UAE oil port in Fujairah",
            "description": "Attack on key oil port disrupts global supply"
        },
        {
            "title": "Massive Attack return with first new music in six years",
            "description": "The band announced a new album dropping next month"
        },
        {
            "title": "Russia sanctions spark energy crisis in Europe",
            "description": "Gas prices surge as embargo hits Nord Stream pipeline"
        },
        {
            "title": "Apple unveils new iPhone with AI features",
            "description": "Tech giant announces latest smartphone lineup"
        }
    ]

    for a in test_articles:
        relevant, label, score = classify_article(a["title"], a["description"])
        status = "✅" if relevant else "❌"
        print(f"{status} {a['title'][:60]}")
        print(f"   label: {label}, score: {score}\n")