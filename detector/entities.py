# GeoTradeV2/detector/entities.py

import requests
import time
from config import HF_API_KEY

API_URL = "https://router.huggingface.co/hf-inference/models/dslim/bert-base-NER"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}


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

            # merge consecutive entities of same type
            merged = []
            for entity in result:
                label = entity.get("entity_group", "") or entity.get("entity", "")
                word  = entity.get("word", "")

                if merged and merged[-1]["label"] == label:
                    merged[-1]["word"] += " " + word.replace("##", "")
                else:
                    merged.append({"word": word.replace("##", ""), "label": label})

            for entity in merged:
                word  = entity["word"].strip()
                label = entity["label"]

                if "LOC" in label:
                    locations.append(word)
                    countries.append(word)
                elif "ORG" in label:
                    organizations.append(word)
                elif "PER" in label:
                    persons.append(word)

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