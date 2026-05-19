# GeoTradeV2/detector/sentiment.py

import requests
import time
from config import HF_API_KEY

API_URL = "https://router.huggingface.co/hf-inference/models/ProsusAI/finbert"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}


def get_sentiment(title, description):
    text = (title + ". " + description)[:512]

    for attempt in range(3):
        try:
            response = requests.post(
                API_URL,
                headers=HEADERS,
                json={"inputs": text},
                timeout=60
            )
            result = response.json()
            scores = result[0]
            top    = max(scores, key=lambda x: x["score"])
            label  = top["label"].lower()
            score  = round(top["score"], 3)
            return label, score

        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2)

    return "neutral", 0.0


if __name__ == "__main__":
    test_articles = [
        {
            "title": "Iran strikes UAE oil port in Fujairah",
            "description": "Major attack disrupts global oil supply chain"
        },
        {
            "title": "Russia sanctions spark energy crisis in Europe",
            "description": "Gas prices surge as embargo hits Nord Stream pipeline"
        },
        {
            "title": "Ceasefire reached between Israel and Hamas",
            "description": "Peace deal signed, markets rally on positive news"
        },
        {
            "title": "OPEC cuts oil production by 2 million barrels",
            "description": "Oil prices expected to rise sharply after decision"
        }
    ]

    for a in test_articles:
        label, score = get_sentiment(a["title"], a["description"])
        print(f"Title:     {a['title'][:60]}")
        print(f"Sentiment: {label} (confidence: {score})")
        print()