# GeoTradeV2/scraper/newsapi.py

import requests
from storage.db import save_articles, init_db
from config import NEWS_API_KEY, NEWSAPI_QUERIES, NEWSAPI_PAGE_SIZE

NEWSAPI_URL = "https://newsapi.org/v2/everything"


def fetch_articles(query):
    try:
        response = requests.get(
            NEWSAPI_URL,
            params={
                "q":        query,
                "language": "en",
                "sortBy":   "publishedAt",
                "pageSize": NEWSAPI_PAGE_SIZE,
                "apiKey":   NEWS_API_KEY
            },
            timeout=10
        )
        response.raise_for_status()
        return response.json().get("articles", [])
    except Exception as e:
        print(f"  Error fetching '{query}': {e}")
        return []


def normalize(raw):
    return {
        "title":       raw.get("title", "")       or "",
        "description": raw.get("description", "") or "",
        "content":     raw.get("content", "")     or "",
        "published":   raw.get("publishedAt", "")  or "",
        "source":      raw.get("source", {}).get("name", "") or "",
        "link":        raw.get("url", "")          or ""
    }


def run_scraper():
    print("\nFetching news...")
    init_db()

    all_articles = []

    for query in NEWSAPI_QUERIES:
        print(f"  Querying: '{query}'")
        raw_articles = fetch_articles(query)
        normalized   = [normalize(a) for a in raw_articles]
        all_articles.extend(normalized)

    # deduplicate within batch
    seen   = set()
    unique = []
    for a in all_articles:
        if a["link"] not in seen and a["link"]:
            seen.add(a["link"])
            unique.append(a)

    print(f"  Fetched {len(unique)} unique articles")
    save_articles(unique)


if __name__ == "__main__":
    run_scraper()