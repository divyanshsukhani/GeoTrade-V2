# GeoTradeV2/backtest/engine.py

import yfinance as yf
import sqlite3
import json
from datetime import datetime, timedelta, timezone
from config import DB_PATH

# ─────────────────────────────────────────
# ASSET → YAHOO FINANCE TICKER
# ─────────────────────────────────────────

ASSET_TICKERS = {
    "Oil":         "CL=F",
    "Gold":        "GC=F",
    "Wheat":       "ZW=F",
    "Commodities": "GSG",
    "Currency":    "DX-Y.NYB",
}

# ─────────────────────────────────────────
# FETCH PRICE AT A GIVEN TIME
# ─────────────────────────────────────────

def get_price(ticker_symbol, at_time, window_hours=2):
    try:
        start = at_time - timedelta(hours=window_hours)
        end   = at_time + timedelta(hours=window_hours)

        ticker = yf.Ticker(ticker_symbol)
        hist   = ticker.history(start=start, end=end, interval="1h")

        if hist.empty:
            return None

        hist.index = hist.index.tz_localize(None) if hist.index.tz is None else hist.index.tz_convert(None)
        target     = at_time.replace(tzinfo=None)
        closest    = min(hist.index, key=lambda t: abs(t - target))
        return float(hist.loc[closest, "Close"])

    except Exception as e:
        print(f"  Price fetch error for {ticker_symbol}: {e}")
        return None


def get_price_change(ticker_symbol, at_time, hours_later=24):
    price_then  = get_price(ticker_symbol, at_time)
    price_later = get_price(ticker_symbol, at_time + timedelta(hours=hours_later))

    if price_then is None or price_later is None:
        return None, None, None

    pct_change = ((price_later - price_then) / price_then) * 100
    return price_then, price_later, round(pct_change, 3)


# ─────────────────────────────────────────
# SCORE A SIGNAL
# ─────────────────────────────────────────

def score_signal(signal, price_then, price_later, pct_change):
    if pct_change is None:
        return None

    direction = signal["signal"]

    if direction == "BUY":
        correct = pct_change > 0
    elif direction == "SELL":
        correct = pct_change < 0
    elif direction == "WATCH":
        correct = abs(pct_change) > 1.0
    else:
        return None

    return {
        "correct":     correct,
        "pct_change":  pct_change,
        "price_then":  price_then,
        "price_later": price_later,
        "direction":   direction,
        "signal":      direction,
        "asset":       signal["asset"],
        "confidence":  signal["confidence"],
        "title":       signal.get("title", ""),
        "created_at":  signal["created_at"]
    }


# ─────────────────────────────────────────
# LOAD SIGNALS FROM DB
# ─────────────────────────────────────────

def load_signals(limit=100):
    con  = sqlite3.connect(DB_PATH)
    rows = con.execute("""
        SELECT s.asset, s.signal, s.confidence, s.reason,
               s.created_at, a.title
        FROM signals s
        JOIN articles a ON s.article_id = a.id
        ORDER BY s.created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    con.close()

    return [
        {
            "asset":      r[0],
            "signal":     r[1],
            "confidence": r[2],
            "reason":     r[3],
            "created_at": r[4],
            "title":      r[5]
        }
        for r in rows
    ]


# ─────────────────────────────────────────
# RUN BACKTEST
# ─────────────────────────────────────────

def run_backtest(hours_later=24, limit=50):
    print(f"\n{'='*60}")
    print(f"GEOTRADE BACKTEST ENGINE")
    print(f"Checking signal accuracy {hours_later}hrs after generation")
    print(f"{'='*60}\n")

    signals = load_signals(limit)
    print(f"Loaded {len(signals)} signals from database\n")

    results = []
    skipped = 0

    for i, signal in enumerate(signals):
        asset  = signal["asset"]
        ticker = ASSET_TICKERS.get(asset)

        if not ticker:
            skipped += 1
            continue

        try:
            at_time = datetime.fromisoformat(
                signal["created_at"].replace("Z", "+00:00")
            )
        except:
            at_time = datetime.now(timezone.utc) - timedelta(days=2)

        print(f"[{i+1}/{len(signals)}] {signal['signal']} {asset} @ {at_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Title: {signal['title'][:60]}")

        price_then, price_later, pct_change = get_price_change(
            ticker, at_time, hours_later
        )

        if pct_change is None:
            print(f"  ⚠️  No price data available\n")
            skipped += 1
            continue

        result = score_signal(signal, price_then, price_later, pct_change)

        if result:
            status = "✅ CORRECT" if result["correct"] else "❌ WRONG"
            print(f"  Price: ${price_then:.2f} → ${price_later:.2f} ({pct_change:+.2f}%)")
            print(f"  Signal: {signal['signal']} → {status}")
            print(f"  Confidence: {signal['confidence']}\n")
            results.append(result)

    # ── REPORT ──
    print(f"\n{'='*60}")
    print(f"BACKTEST RESULTS")
    print(f"{'='*60}")

    if not results:
        print("No results — signals may be too recent for price data")
        print("Tip: wait 24hrs after generating signals then rerun")
        return

    total    = len(results)
    correct  = sum(1 for r in results if r["correct"])
    accuracy = (correct / total) * 100

    print(f"\nOverall Accuracy: {correct}/{total} = {accuracy:.1f}%")
    print(f"Skipped:          {skipped} (no price data)")

    # by asset
    print(f"\n── By Asset ──")
    for asset in set(r["asset"] for r in results):
        ar  = [r for r in results if r["asset"] == asset]
        ac  = sum(1 for r in ar if r["correct"])
        pct = (ac / len(ar)) * 100
        print(f"  {asset:12} {ac}/{len(ar)} = {pct:.1f}%")

    # by confidence
    print(f"\n── By Confidence ──")
    tiers = [
        ("HIGH   (>0.8)",    lambda r: r["confidence"] > 0.8),
        ("MEDIUM (0.5-0.8)", lambda r: 0.5 <= r["confidence"] <= 0.8),
        ("LOW    (<0.5)",    lambda r: r["confidence"] < 0.5),
    ]
    for label, fn in tiers:
        tr = [r for r in results if fn(r)]
        if not tr:
            continue
        tc  = sum(1 for r in tr if r["correct"])
        pct = (tc / len(tr)) * 100
        print(f"  {label}  {tc}/{len(tr)} = {pct:.1f}%")

    # best signals
    print(f"\n── Top 3 Best Signals ──")
    best = sorted(
        [r for r in results if r["correct"]],
        key=lambda r: abs(r["pct_change"]),
        reverse=True
    )[:3]
    for r in best:
        print(f"  {r['signal']} {r['asset']:10} {r['pct_change']:+.2f}% ✅")
        print(f"  {r['title'][:55]}")

    # worst signals
    print(f"\n── Top 3 Worst Signals ──")
    worst = sorted(
        [r for r in results if not r["correct"]],
        key=lambda r: abs(r["pct_change"]),
        reverse=True
    )[:3]
    for r in worst:
        print(f"  {r['signal']} {r['asset']:10} {r['pct_change']:+.2f}% ❌")
        print(f"  {r['title'][:55]}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    run_backtest(hours_later=24, limit=50)