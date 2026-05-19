# GeoTradeV2/backtest/historical.py

import gdelt
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import re

# ─────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────

DAYS_BACK = 30

# GDELT event codes we care about
RELEVANT_EVENT_CODES = {
    "14":  "military attack",
    "19":  "military attack",
    "18":  "sanctions",
    "172": "sanctions",
    "173": "sanctions",
    "135": "civil unrest",
    "136": "civil unrest",
    "10":  "energy",
    "11":  "energy",
}

# countries we track
KEY_COUNTRIES = {
    "IRN": "iran",
    "RUS": "russia",
    "UKR": "ukraine",
    "ISR": "israel",
    "CHN": "china",
    "SAU": "saudi arabia",
    "USA": "usa",
    "IRQ": "iraq",
    "YEM": "yemen",
}

ASSET_TICKERS = {
    "Oil":   "CL=F",
    "Gold":  "GC=F",
    "Wheat": "ZW=F",
}

# ─────────────────────────────────────────
# STEP 1 — FETCH GDELT EVENTS
# ─────────────────────────────────────────

def fetch_gdelt_events(days_back=30):
    print(f"\nFetching {days_back} days of GDELT events...")
    gd      = gdelt.gdelt(version=2)
    all_events = []

    for i in range(days_back):
        date = datetime.now() - timedelta(days=days_back - i)
        date_str = date.strftime("%Y %b %d")

        try:
            df = gd.Search([date_str], table="events", coverage=False)

            if df is None or df.empty:
                continue

            # filter relevant event codes
            df["EventRootCode"] = df["EventRootCode"].astype(str)
            relevant = df[df["EventRootCode"].isin(RELEVANT_EVENT_CODES.keys())]

            # filter key countries
            relevant = relevant[
                relevant["Actor1CountryCode"].isin(KEY_COUNTRIES.keys()) |
                relevant["Actor2CountryCode"].isin(KEY_COUNTRIES.keys())
            ]

            if not relevant.empty:
                all_events.append(relevant)
                print(f"  {date_str}: {len(relevant)} relevant events")

            time.sleep(0.5)

        except Exception as e:
            print(f"  Error fetching {date_str}: {e}")
            continue

    if not all_events:
        print("No events found!")
        return pd.DataFrame()

    combined = pd.concat(all_events, ignore_index=True)
    print(f"\nTotal relevant events: {len(combined)}")
    return combined


# ─────────────────────────────────────────
# STEP 2 — CONVERT EVENTS TO SIGNALS
# ─────────────────────────────────────────

def events_to_signals(df):
    print("\nConverting events to signals...")
    signals = []

    for _, row in df.iterrows():
        event_code = str(row.get("EventRootCode", ""))
        label      = RELEVANT_EVENT_CODES.get(event_code, "other")

        # get countries involved
        c1 = KEY_COUNTRIES.get(str(row.get("Actor1CountryCode", "")), "")
        c2 = KEY_COUNTRIES.get(str(row.get("Actor2CountryCode", "")), "")
        countries = [c for c in [c1, c2] if c]

        # get date
        try:
            date_val = str(row.get("SQLDATE", ""))
            date     = datetime.strptime(date_val, "%Y%m%d")
        except:
            continue

        # goldstein scale — measures event impact (-10 to +10)
        goldstein = float(row.get("GoldsteinScale", 0) or 0)

        # determine asset and signal
        if label == "military attack":
            if any(c in ["iran", "iraq", "saudi arabia", "yemen"] for c in countries):
                asset  = "Oil"
                signal = "BUY"
            elif any(c in ["china"] for c in countries):
                asset  = "Gold"
                signal = "BUY"
            else:
                continue
        elif label == "sanctions":
            asset  = "Oil"
            signal = "BUY"
        elif label == "energy":
            asset  = "Oil"
            signal = "BUY"
        elif label == "civil unrest":
            asset  = "Gold"
            signal = "BUY"
        else:
            continue

        # confidence based on goldstein scale
        # more negative = more destabilizing = higher confidence
        confidence = min(abs(goldstein) / 10, 1.0)
        if confidence < 0.3:
            continue

        signals.append({
            "date":       date,
            "asset":      asset,
            "signal":     signal,
            "confidence": round(confidence, 3),
            "label":      label,
            "countries":  countries,
            "title":      str(row.get("SOURCEURL", ""))[:80]
        })

    print(f"Generated {len(signals)} signals")
    return signals


# ─────────────────────────────────────────
# STEP 3 — FETCH PRICES
# ─────────────────────────────────────────

def get_price_on_date(ticker_symbol, date):
    try:
        start = date - timedelta(days=1)
        end   = date + timedelta(days=2)
        hist  = yf.Ticker(ticker_symbol).history(start=start, end=end)
        if hist.empty:
            return None
        return float(hist["Close"].iloc[0])
    except:
        return None


# ─────────────────────────────────────────
# STEP 4 — BACKTEST
# ─────────────────────────────────────────

def run_historical_backtest(days_back=30):
    # fetch events
    df = fetch_gdelt_events(days_back)
    if df.empty:
        return

    # convert to signals
    signals = events_to_signals(df)
    if not signals:
        print("No signals generated!")
        return

    print("\nFetching prices and scoring signals...")
    results = []

    for s in signals:
        ticker      = ASSET_TICKERS.get(s["asset"])
        if not ticker:
            continue

        price_then  = get_price_on_date(ticker, s["date"])
        price_later = get_price_on_date(ticker, s["date"] + timedelta(days=1))

        if price_then is None or price_later is None:
            continue

        pct_change = ((price_later - price_then) / price_then) * 100

        if s["signal"] == "BUY":
            correct = pct_change > 0
        elif s["signal"] == "SELL":
            correct = pct_change < 0
        else:
            continue

        results.append({
            "date":       s["date"].strftime("%Y-%m-%d"),
            "asset":      s["asset"],
            "signal":     s["signal"],
            "confidence": s["confidence"],
            "correct":    correct,
            "pct_change": round(pct_change, 3),
            "countries":  s["countries"],
            "label":      s["label"]
        })

    # ── REPORT ──
    print(f"\n{'='*60}")
    print(f"HISTORICAL BACKTEST RESULTS — Last {days_back} days")
    print(f"{'='*60}")

    if not results:
        print("No results with price data")
        return

    total    = len(results)
    correct  = sum(1 for r in results if r["correct"])
    accuracy = (correct / total) * 100

    print(f"\nTotal signals scored: {total}")
    print(f"Overall Accuracy:     {correct}/{total} = {accuracy:.1f}%")

    # by asset
    print(f"\n── By Asset ──")
    for asset in set(r["asset"] for r in results):
        ar  = [r for r in results if r["asset"] == asset]
        ac  = sum(1 for r in ar if r["correct"])
        pct = (ac / len(ar)) * 100
        print(f"  {asset:12} {ac}/{len(ar)} = {pct:.1f}%")

    # by event type
    print(f"\n── By Event Type ──")
    for label in set(r["label"] for r in results):
        lr  = [r for r in results if r["label"] == label]
        lc  = sum(1 for r in lr if r["correct"])
        pct = (lc / len(lr)) * 100
        print(f"  {label:20} {lc}/{len(lr)} = {pct:.1f}%")

    # by confidence
    print(f"\n── By Confidence ──")
    tiers = [
        ("HIGH   (>0.7)", lambda r: r["confidence"] > 0.7),
        ("MEDIUM (0.4-0.7)", lambda r: 0.4 <= r["confidence"] <= 0.7),
        ("LOW    (<0.4)", lambda r: r["confidence"] < 0.4),
    ]
    for label, fn in tiers:
        tr  = [r for r in results if fn(r)]
        if not tr:
            continue
        tc  = sum(1 for r in tr if r["correct"])
        pct = (tc / len(tr)) * 100
        print(f"  {label}  {tc}/{len(tr)} = {pct:.1f}%")

    # best performing countries
    print(f"\n── By Country ──")
    country_results = {}
    for r in results:
        for c in r["countries"]:
            if c not in country_results:
                country_results[c] = []
            country_results[c].append(r["correct"])

    for country, outcomes in sorted(
        country_results.items(),
        key=lambda x: sum(x[1])/len(x[1]),
        reverse=True
    ):
        acc = (sum(outcomes) / len(outcomes)) * 100
        print(f"  {country:15} {sum(outcomes)}/{len(outcomes)} = {acc:.1f}%")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    run_historical_backtest(days_back=30)