# GeoTradeV2/detector/filter.py

from config import GEO_KEYWORDS


def is_geopolitically_relevant(title, description):
    text    = (title + " " + description).lower()
    matched = [kw for kw in GEO_KEYWORDS if kw in text]

    if matched:
        return True, matched
    return False, []


if __name__ == "__main__":
    from storage.db import get_connection

    con  = get_connection()
    rows = con.execute(
        "SELECT id, title, description FROM articles"
    ).fetchall()

    passed = 0
    failed = 0

    for row in rows:
        article_id, title, description = row
        relevant, matched = is_geopolitically_relevant(
            title, description or ""
        )

        if relevant:
            passed += 1
            print(f"✅ {title[:60]}")
            print(f"   matched: {matched}\n")
        else:
            failed += 1
            print(f"❌ {title[:60]}\n")

    print(f"\nTotal: {passed} passed, {failed} filtered out")