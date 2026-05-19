# GeoTradeV2/main.py

import schedule
import time
from storage.db import init_db, get_unprocessed, update_article, save_signal
from scraper.newsapi import run_scraper
from detector.filter import is_geopolitically_relevant
from detector.classifier import classify_article
from detector.sentiment import get_sentiment
from detector.entities import extract_entities
from detector.ontology import enrich_article
from signals.generator import generate_signal


def process_articles():
    print("\nProcessing articles...")
    articles = get_unprocessed()
    print(f"Found {len(articles)} unprocessed articles")

    for article in articles:
        article_id, title, description, content, published, source = article
        text = title + " " + (description or "")

        # Stage 1 — keyword filter
        relevant, matched = is_geopolitically_relevant(title, description or "")
        if not relevant:
            update_article(article_id, {"processed": 1, "relevant": 0})
            continue

        # Stage 2 — AI classifier
        relevant, label, score = classify_article(title, description or "")
        if not relevant:
            update_article(article_id, {
                "processed": 1,
                "relevant":  0,
                "label":     label
            })
            continue

        # Stage 3 — sentiment
        sentiment, sentiment_score = get_sentiment(title, description or "")

        # Stage 4 — entities
        entities = extract_entities(title, description or "")

        # Stage 5 — ontology enrichment
        enrichment = enrich_article(
            entities["countries"],
            entities["locations"],
            [label]
        )

        # Stage 6 — signal generation
        signal = generate_signal(
            label,
            sentiment,
            sentiment_score,
            entities,
            enrichment
        )

        # save to db
        update_article(article_id, {
            "processed":       1,
            "relevant":        1,
            "label":           label,
            "sentiment":       sentiment,
            "sentiment_score": sentiment_score,
            "countries":       str(entities["countries"]),
            "locations":       str(entities["locations"]),
            "organizations":   str(entities["organizations"]),
            "risk_multiplier": enrichment["risk_multiplier"],
            "signal":          signal["signal"]
        })

        save_signal(article_id, signal)

        # print signal
        print(f"\n{'='*60}")
        print(f"Title:      {title[:60]}")
        print(f"Label:      {label}")
        print(f"Sentiment:  {sentiment} ({sentiment_score})")
        print(f"Countries:  {entities['countries']}")
        print(f"Waterways:  {enrichment['waterways_at_risk']}")
        print(f"Asset:      {signal['asset']}")
        print(f"Signal:     {signal['signal']}")
        print(f"Confidence: {signal['confidence']}")
        print(f"Reason:     {signal['reason'][:80]}")


def run():
    print("GeoTradeV2 Starting...")
    init_db()

    # fetch + process immediately on startup
    run_scraper()
    process_articles()

    # then schedule every 15 mins
    schedule.every(15).minutes.do(run_scraper)
    schedule.every(15).minutes.do(process_articles)

    print("\nScheduler running — fetching every 15 mins")
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    run()