# GeoTradeV2/detector/entities.py

import requests
import time
from config import HF_API_KEY

API_URL = "https://router.huggingface.co/hf-inference/models/dslim/bert-base-NER"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

KNOWN_PLACES = [
    "Strait of Hormuz", "Strait of Malacca",
    "Persian Gulf", "Black Sea", "South China Sea",
    "Nord Stream", "Suez Canal", "Red Sea",
    "Bab-el-Mandeb", "Arabian Sea", "Caspian Sea"
]

KNOWN_COUNTRIES = [
    "iran", "russia", "ukraine", "israel", "china",
    "usa", "us", "uk", "germany", "france", "india",
    "pakistan", "turkey", "egypt", "uae", "saudi arabia",
    "cuba", "estonia", "belarus", "syria", "iraq", "yemen"
]


def fix_split_places(locations, text):
    fixed = list(locations)
    for place in KNOWN_PLACES:
        if place.lower() in text.lower():
            # remove ALL partial word matches
            parts = place.split()
            fixed = [l for l in fixed 
                     if l not in parts 
                     and not any(l == p for p in parts)]
            if place not in fixed:
                fixed.append(place)
    return list(dict.fromkeys(fixed))


def extract_entities(title, description):
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

            countries     = []
            locations     = []
            organizations = []
            persons       = []

            # merge subword tokens only
            merged = []
            for entity in result:
                label = entity.get("entity_group", "") or entity.get("entity", "")
                word  = entity.get("word", "")

                if word.startswith("##") and merged:
                    merged[-1]["word"] += word.replace("##", "")
                elif (merged and
                      merged[-1]["label"] == label and
                      entity.get("start", 0) == merged[-1].get("end", -1)):
                    merged[-1]["word"] += " " + word
                    merged[-1]["end"]   = entity.get("end", 0)
                else:
                    merged.append({
                        "word":  word,
                        "label": label,
                        "start": entity.get("start", 0),
                        "end":   entity.get("end",   0)
                    })

            for entity in merged:
                word       = entity["word"].strip()
                label      = entity["label"]
                word_lower = word.lower()

                # split merged country names like "Iran US"
                found = [c for c in KNOWN_COUNTRIES if c in word_lower]
                if len(found) > 1:
                    for c in found:
                        countries.append(c.title())
                        locations.append(c.title())
                    continue

                if "LOC" in label:
                    locations.append(word)
                    countries.append(word)
                elif "ORG" in label:
                    organizations.append(word)
                elif "PER" in label:
                    persons.append(word)

            # fix known multi-word places
            locations = fix_split_places(locations, text)
            countries = fix_split_places(countries, text)

            return {
                "countries":     list(dict.fromkeys(countries)),
                "locations":     list(dict.fromkeys(locations)),
                "organizations": list(dict.fromkeys(organizations)),
                "persons":       list(dict.fromkeys(persons))
            }

        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(2)

    return {
        "countries":     [],
        "locations":     [],
        "organizations": [],
        "persons":       []
    }


if __name__ == "__main__":
    test_articles = [
        {
            "title": "Iran strikes UAE oil port in Fujairah",
            "description": "The port of Fujairah plays a crucial role in keeping global supplies moving when the Strait of Hormuz is blocked."
        },
        {
            "title": "Russia sanctions spark energy crisis in Europe",
            "description": "Gas prices surge as embargo hits Nord Stream pipeline affecting Germany and Poland."
        },
        {
            "title": "Ukraine receives weapons from NATO allies",
            "description": "US and UK send missiles to Kyiv as conflict with Russia intensifies near Crimea."
        },
        {
            "title": "Congress is a huge target for spies",
            "description": "China Russia Iran are targeting US officials according to intelligence reports."
        }
    ]

    for a in test_articles:
        entities = extract_entities(a["title"], a["description"])
        print(f"Title:         {a['title'][:60]}")
        print(f"Countries:     {entities['countries']}")
        print(f"Locations:     {entities['locations']}")
        print(f"Organizations: {entities['organizations']}")
        print(f"Persons:       {entities['persons']}")
        print()