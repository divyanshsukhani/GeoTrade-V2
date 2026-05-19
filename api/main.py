# GeoTradeV2/api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from storage.db import get_connection
import json

app = FastAPI()

# allow React to talk to FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/signals")
def get_signals():
    con = get_connection()
    rows = con.execute("""
        SELECT s.asset, s.signal, s.confidence, s.reason,
               s.created_at, a.title, a.source,
               s.countries, s.waterways
        FROM signals s
        JOIN articles a ON s.article_id = a.id
        ORDER BY s.created_at DESC
        LIMIT 50
    """).fetchall()
    con.close()

    return [
        {
            "asset":      r[0],
            "signal":     r[1],
            "confidence": r[2],
            "reason":     r[3],
            "created_at": r[4],
            "title":      r[5],
            "source":     r[6],
            "countries":  json.loads(r[7]) if r[7] else [],
            "waterways":  json.loads(r[8]) if r[8] else []
        }
        for r in rows
    ]


@app.get("/risk")
def get_risk():
    con = get_connection()
    row = con.execute("""
        SELECT COUNT(*), AVG(confidence)
        FROM signals
        WHERE created_at > datetime('now', '-7 days')
    """).fetchone()
    con.close()

    count    = row[0] or 0
    avg_conf = row[1] or 0
    gti      = min(int(count * avg_conf * 10), 100)

    if gti >= 80:
        level = "CRITICAL"
    elif gti >= 60:
        level = "HIGH"
    elif gti >= 35:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {"gti": gti, "level": level, "signal_count": count}


@app.get("/countries")
def get_countries():
    con = get_connection()
    rows = con.execute("""
        SELECT s.countries, s.confidence
        FROM signals s
        WHERE s.created_at > datetime('now', '-7 days')
    """).fetchall()
    con.close()

    country_risk = {}
    for row in rows:
        countries  = json.loads(row[0]) if row[0] else []
        confidence = row[1] or 0
        for country in countries:
            c = country.lower()
            if c not in country_risk:
                country_risk[c] = 0
            country_risk[c] = max(country_risk[c], confidence)

    return country_risk


@app.get("/ticker")
def get_ticker():
    con = get_connection()
    rows = con.execute("""
        SELECT a.title, s.asset, s.signal
        FROM signals s
        JOIN articles a ON s.article_id = a.id
        ORDER BY s.created_at DESC
        LIMIT 10
    """).fetchall()
    con.close()

    return [
        {"title": r[0], "asset": r[1], "signal": r[2]}
        for r in rows
    ]