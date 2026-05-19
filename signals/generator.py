# GeoTradeV2/signals/generator.py

from config import ASSET_MAP, MIN_RISK_SCORE
from detector.ontology import enrich_article

HIGH_PRIORITY_COUNTRIES = ["Iran", "Russia", "China", "Israel", "Ukraine"]


def generate_signal(label, sentiment, sentiment_score, entities, enrichment):

    # base signal from classifier label
    asset_info = ASSET_MAP.get(label, {"asset": "None", "signal": "HOLD"})
    asset      = asset_info["asset"]
    signal     = asset_info["signal"]

    # base confidence from sentiment
    if sentiment == "negative":
        base_confidence = sentiment_score
    elif sentiment == "positive":
        base_confidence = sentiment_score * 0.5
    else:
        # neutral — use label strength
        if label in ["military attack", "economic sanctions"]:
            base_confidence = 0.5
        elif label in ["geopolitical conflict", "energy and oil markets"]:
            base_confidence = 0.45
        else:
            base_confidence = 0.3

    # boost from ontology
    risk_multiplier = enrichment.get("risk_multiplier", 1.0)
    confidence      = min(base_confidence * risk_multiplier, 1.0)

    # override asset if waterway detected → always Oil
    waterways = enrichment.get("waterways_at_risk", [])
    exports   = enrichment.get("exports_at_risk",   [])

    if waterways:
        asset  = "Oil"
        signal = "BUY"

    if "wheat" in exports or "grain" in exports:
        asset  = "Wheat"
        signal = "BUY"

    # ── GOLD FILTER ──
    if asset == "Gold" and signal == "BUY":

        is_high_priority = any(
            c in entities.get("countries", [])
            for c in HIGH_PRIORITY_COUNTRIES
        )
        has_war_keyword  = is_high_priority
        has_waterway     = len(waterways) > 0
        high_sentiment   = sentiment_score >= 0.75
        opec_involved    = enrichment.get("is_opec_involved", False)

        strong_signals = sum([
            has_war_keyword,
            has_waterway,
            high_sentiment,
            opec_involved
        ])

        # high priority countries need only 1 strong signal
        # others need 2
        required = 1 if is_high_priority else 2

        if strong_signals < required:
            asset      = "None"
            signal     = "HOLD"
            confidence = confidence * 0.5

    # de-escalation → sell safe havens
    if sentiment == "positive" and signal == "BUY" and asset == "Gold":
        signal = "SELL"

    # ── MINIMUM CONFIDENCE ──
    if confidence < 0.40 and not waterways:
        asset  = "None"
        signal = "HOLD"

    # build reason string
    reasons = enrichment.get("reason", [])
    reason  = " | ".join(reasons) if reasons else label

    return {
        "asset":           asset,
        "signal":          signal,
        "confidence":      round(confidence, 3),
        "label":           label,
        "sentiment":       sentiment,
        "sentiment_score": sentiment_score,
        "countries":       entities.get("countries", []),
        "locations":       entities.get("locations", []),
        "waterways":       waterways,
        "exports_at_risk": exports,
        "reason":          reason
    }


if __name__ == "__main__":
    test_cases = [
        {
            "title":      "Iran strikes UAE oil port in Fujairah",
            "label":      "military attack",
            "sentiment":  "negative",
            "sent_score": 0.918,
            "entities": {
                "countries":     ["Iran", "UAE"],
                "locations":     ["Fujairah", "Persian Gulf"],
                "organizations": [],
                "persons":       []
            }
        },
        {
            "title":      "Clock is ticking for Iran - Trump",
            "label":      "geopolitical conflict",
            "sentiment":  "neutral",
            "sent_score": 0.494,
            "entities": {
                "countries":     ["Iran", "US"],
                "locations":     [],
                "organizations": [],
                "persons":       ["Trump"]
            }
        },
        {
            "title":      "Cuba vows to annihilate US invaders",
            "label":      "military attack",
            "sentiment":  "neutral",
            "sent_score": 0.557,
            "entities": {
                "countries":     ["Cuba", "US"],
                "locations":     [],
                "organizations": [],
                "persons":       []
            }
        },
        {
            "title":      "Another strike on alleged drug boat kills 3",
            "label":      "military attack",
            "sentiment":  "negative",
            "sent_score": 0.945,
            "entities": {
                "countries":     [],
                "locations":     ["Pacific"],
                "organizations": [],
                "persons":       []
            }
        },
        {
            "title":      "Ceasefire reached between Israel and Hamas",
            "label":      "geopolitical conflict",
            "sentiment":  "positive",
            "sent_score": 0.872,
            "entities": {
                "countries":     ["Israel"],
                "locations":     ["Gaza"],
                "organizations": ["Hamas"],
                "persons":       []
            }
        },
        {
            "title":      "Russia cuts gas supply through Nord Stream",
            "label":      "energy and oil markets",
            "sentiment":  "negative",
            "sent_score": 0.936,
            "entities": {
                "countries":     ["Russia", "Germany"],
                "locations":     ["Nord Stream", "Black Sea"],
                "organizations": [],
                "persons":       []
            }
        }
    ]

    for t in test_cases:
        enrichment = enrich_article(
            t["entities"]["countries"],
            t["entities"]["locations"],
            [t["label"]]
        )
        signal = generate_signal(
            t["label"],
            t["sentiment"],
            t["sent_score"],
            t["entities"],
            enrichment
        )
        print(f"Title:      {t['title'][:60]}")
        print(f"Asset:      {signal['asset']}")
        print(f"Signal:     {signal['signal']}")
        print(f"Confidence: {signal['confidence']}")
        print()