# GeoTradeV2/storage/db.py

import sqlite3
import json
from datetime import datetime, timezone
from config import DB_PATH


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    con = get_connection()

    # --- Articles table ---
    con.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            link            TEXT UNIQUE,
            title           TEXT,
            description     TEXT,
            content         TEXT,
            published       TEXT,
            source          TEXT,
            fetched_at      TEXT,
            processed       INTEGER DEFAULT 0,
            relevant        INTEGER DEFAULT 0,
            label           TEXT,
            label_score     REAL,
            sentiment       TEXT,
            sentiment_score REAL,
            countries       TEXT,
            locations       TEXT,
            organizations   TEXT,
            exports_at_risk TEXT,
            waterways       TEXT,
            risk_multiplier REAL,
            signal          TEXT
        )
    """)

    # --- Ontology table ---
    con.execute("""
        CREATE TABLE IF NOT EXISTS ontology (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            category   TEXT,
            key        TEXT,
            data       TEXT,
            updated_at TEXT,
            UNIQUE(category, key)
        )
    """)

    # --- Signals history table ---
    con.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id      INTEGER,
            asset           TEXT,
            signal          TEXT,
            confidence      REAL,
            reason          TEXT,
            countries       TEXT,
            waterways       TEXT,
            exports_at_risk TEXT,
            created_at      TEXT,
            FOREIGN KEY (article_id) REFERENCES articles(id)
        )
    """)

    con.commit()
    con.close()
    print("Database initialized.")


# ─────────────────────────────────────────
# ARTICLES
# ─────────────────────────────────────────

def save_articles(articles):
    con = get_connection()
    added = 0
    for a in articles:
        try:
            con.execute("""
                INSERT OR IGNORE INTO articles 
                (link, title, description, content, published, source, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                a.get("link", ""),
                a.get("title", ""),
                a.get("description", ""),
                a.get("content", ""),
                a.get("published", ""),
                a.get("source", ""),
                datetime.now(timezone.utc).isoformat()
            ))
            if con.execute("SELECT changes()").fetchone()[0]:
                added += 1
        except Exception as e:
            print(f"Error saving article: {e}")
    con.commit()
    con.close()
    print(f"Saved {added} new articles.")


def get_unprocessed():
    con = get_connection()
    rows = con.execute("""
        SELECT id, title, description, content, published, source
        FROM articles 
        WHERE processed = 0
    """).fetchall()
    con.close()
    return rows


def update_article(article_id, data: dict):
    con = get_connection()
    fields = ", ".join([f"{k} = ?" for k in data.keys()])
    values = list(data.values()) + [article_id]
    con.execute(f"UPDATE articles SET {fields} WHERE id = ?", values)
    con.commit()
    con.close()


# ─────────────────────────────────────────
# SIGNALS
# ─────────────────────────────────────────

def save_signal(article_id, signal_data: dict):
    con = get_connection()
    con.execute("""
        INSERT INTO signals 
        (article_id, asset, signal, confidence, reason, countries, waterways, exports_at_risk, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        article_id,
        signal_data.get("asset", ""),
        signal_data.get("signal", ""),
        signal_data.get("confidence", 0.0),
        signal_data.get("reason", ""),
        json.dumps(signal_data.get("countries", [])),
        json.dumps(signal_data.get("waterways", [])),
        json.dumps(signal_data.get("exports_at_risk", [])),
        datetime.now(timezone.utc).isoformat()
    ))
    con.commit()
    con.close()


def get_recent_signals(limit=20):
    con = get_connection()
    rows = con.execute("""
        SELECT s.asset, s.signal, s.confidence, s.reason, s.created_at, a.title
        FROM signals s
        JOIN articles a ON s.article_id = a.id
        ORDER BY s.created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    con.close()
    return rows


# ─────────────────────────────────────────
# ONTOLOGY
# ─────────────────────────────────────────

def save_ontology(category, key, data):
    con = get_connection()
    con.execute("""
        INSERT INTO ontology (category, key, data, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(category, key) DO UPDATE SET
            data = excluded.data,
            updated_at = excluded.updated_at
    """, (category, key.lower(), json.dumps(data), datetime.now(timezone.utc).isoformat()))
    con.commit()
    con.close()


def get_ontology(category, key):
    con = get_connection()
    row = con.execute(
        "SELECT data FROM ontology WHERE category = ? AND key = ?",
        (category, key.lower())
    ).fetchone()
    con.close()
    return json.loads(row[0]) if row else None


# ─────────────────────────────────────────
# TEST
# ─────────────────────────────────────────

if __name__ == "__main__":
    init_db()

    # Test save and read
    test_article = [{
        "link": "https://test.com/article1",
        "title": "Iran strikes UAE oil port",
        "description": "Major attack on Fujairah port disrupts oil supply",
        "content": "",
        "published": "2026-04-19",
        "source": "Test"
    }]

    save_articles(test_article)
    unprocessed = get_unprocessed()
    print(f"Unprocessed articles: {len(unprocessed)}")
    print("First article title:", unprocessed[0][1])