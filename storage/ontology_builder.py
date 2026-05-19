# GeoTradeV2/storage/ontology_builder.py

import requests
import time
from GeoTradeV2.storage.db import save_ontology, init_db
from GeoTradeV2.config import GEONAMES_USERNAME

# ─────────────────────────────────────────
# WIKIDATA
# ─────────────────────────────────────────

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "GeoTradeV2/1.0",
    "Accept": "application/json"
}

VALID_COMMODITIES = {
    "oil", "gas", "wheat", "steel", "copper", "gold", "silver",
    "coal", "iron", "aluminum", "cotton", "coffee", "sugar",
    "timber", "rubber", "petroleum", "fertilizer", "uranium",
    "lithium", "corn", "rice", "soybeans", "natural gas",
    "crude oil", "phosphate", "nickel", "zinc", "tin"
}

def query_wikidata(sparql):
    try:
        response = requests.get(
            WIKIDATA_ENDPOINT,
            params={"query": sparql, "format": "json"},
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["results"]["bindings"]
    except Exception as e:
        print(f"Wikidata error: {e}")
        return []

def fetch_country_exports():
    print("  Fetching country exports...")
    sparql = """
    SELECT ?countryLabel ?exportLabel WHERE {
      ?country wdt:P31 wd:Q3624078;
               wdt:P1304 ?export.
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en".
      }
    }
    LIMIT 500
    """
    results = query_wikidata(sparql)
    exports = {}
    for r in results:
        country = r.get("countryLabel", {}).get("value", "").lower()
        export  = r.get("exportLabel",  {}).get("value", "").lower()

        # only keep real commodities
        if country and export and any(c in export for c in VALID_COMMODITIES):
            exports.setdefault(country, []).append(export)
    return exports

def fetch_strategic_waterways():
    print("  Fetching strategic waterways...")
    sparql = """
    SELECT ?waterwayLabel ?countryLabel WHERE {
      VALUES ?waterway {
        wd:Q40921
        wd:Q1003232
        wd:Q37250
        wd:Q5482
        wd:Q1247
        wd:Q186081
        wd:Q3100
      }
      ?waterway wdt:P17 ?country.
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en".
      }
    }
    """
    results = query_wikidata(sparql)
    waterways = {}
    for r in results:
        way     = r.get("waterwayLabel", {}).get("value", "").lower()
        country = r.get("countryLabel",  {}).get("value", "").lower()
        if way and country:
            waterways.setdefault(way, []).append(country)
    return waterways

def fetch_opec_members():
    print("  Fetching OPEC members...")
    sparql = """
    SELECT ?countryLabel WHERE {
      wd:Q7795 wdt:P527 ?country.
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en".
      }
    }
    """
    results = query_wikidata(sparql)
    return [r.get("countryLabel", {}).get("value", "").lower() for r in results]

def fetch_military_alliances():
    print("  Fetching military alliances...")
    sparql = """
    SELECT ?allianceLabel ?memberLabel WHERE {
      VALUES ?alliance {
        wd:Q7184
        wd:Q842490
        wd:Q188822
      }
      ?alliance wdt:P527 ?member.
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language "en".
      }
    }
    """
    results = query_wikidata(sparql)
    alliances = {}
    for r in results:
        alliance = r.get("allianceLabel", {}).get("value", "").lower()
        member   = r.get("memberLabel",   {}).get("value", "").lower()
        if alliance and member:
            alliances.setdefault(alliance, []).append(member)
    return alliances


# ─────────────────────────────────────────
# CONCEPTNET
# ─────────────────────────────────────────

CONCEPTNET_API = "https://api.conceptnet.io"

FINANCIAL_CONCEPTS = [
    "oil", "gas", "gold", "sanctions", "embargo",
    "war", "conflict", "pipeline", "port", "wheat",
    "inflation", "commodity", "currency", "missile"
]

def fetch_conceptnet_relations(concept):
    try:
        url = f"{CONCEPTNET_API}/c/en/{concept}"
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {}
        data = response.json()
        relations = {}
        for edge in data.get("edges", []):
            if "/en/" not in edge.get("end", {}).get("@id", ""):
                continue
            rel   = edge.get("rel",   {}).get("label", "")
            end   = edge.get("end",   {}).get("label", "").lower()
            start = edge.get("start", {}).get("label", "").lower()
            relations.setdefault(rel, []).append(
                end if start == concept else start
            )
        return relations
    except Exception as e:
        print(f"  ConceptNet error for '{concept}': {e}")
        return {}

def fetch_all_conceptnet():
    print("  Fetching ConceptNet relations...")
    all_relations = {}
    for concept in FINANCIAL_CONCEPTS:
        print(f"    → {concept}")
        all_relations[concept] = fetch_conceptnet_relations(concept)
        time.sleep(0.5)
    return all_relations


# ─────────────────────────────────────────
# GEONAMES
# ─────────────────────────────────────────

def fetch_geonames_countries():
    print("  Fetching GeoNames country data...")
    if not GEONAMES_USERNAME:
        print("  Skipping GeoNames — no username set in config.py")
        return {}
    try:
        url = "http://api.geonames.org/countryInfoJSON"
        response = requests.get(
            url,
            params={"username": GEONAMES_USERNAME},
            timeout=10
        )
        countries = {}
        for c in response.json().get("geonames", []):
            name = c.get("countryName", "").lower()
            countries[name] = {
                "continent": c.get("continentName", ""),
                "capital":   c.get("capital", ""),
                "currency":  c.get("currencyCode", ""),
                "neighbors": c.get("neighbours", "").split(",")
            }
        return countries
    except Exception as e:
        print(f"  GeoNames error: {e}")
        return {}


# ─────────────────────────────────────────
# BUILD EVERYTHING
# ─────────────────────────────────────────

def build_ontology():
    print("\nBuilding ontology...")
    init_db()

    # 1. Country exports
    exports = fetch_country_exports()
    for country, items in exports.items():
        save_ontology("exports", country, items)
    print(f"  Saved exports for {len(exports)} countries")

    # 2. Waterways — merge fallback FIRST, then save
    waterways = fetch_strategic_waterways()
    WATERWAY_FALLBACK = {
        "strait of hormuz":  ["iran", "uae", "oman"],
        "strait of malacca": ["malaysia", "singapore", "indonesia"],
        "suez canal":        ["egypt"],
        "bab-el-mandeb":     ["yemen", "djibouti", "eritrea"],
        "black sea":         ["russia", "ukraine", "turkey", "romania"],
        "south china sea":   ["china", "vietnam", "philippines", "malaysia"],
        "persian gulf":      ["iran", "iraq", "kuwait", "saudi arabia", "uae"]
    }
    for way, countries in WATERWAY_FALLBACK.items():
        if way not in waterways:
            waterways[way] = countries
    for way, countries in waterways.items():
        save_ontology("waterways", way, countries)
    print(f"  Saved {len(waterways)} waterways")

    # 3. OPEC
    opec = fetch_opec_members()
    save_ontology("organizations", "opec", opec)
    print(f"  Saved {len(opec)} OPEC members")

    # 4. Alliances — merge fallback FIRST, then save
    alliances = fetch_military_alliances()
    ALLIANCE_FALLBACK = {
        "nato": ["usa", "uk", "france", "germany", "italy", "spain",
                 "poland", "turkey", "canada", "norway", "denmark"],
        "csto": ["russia", "belarus", "kazakhstan", "armenia",
                 "kyrgyzstan", "tajikistan"],
        "sco":  ["china", "russia", "india", "pakistan",
                 "kazakhstan", "uzbekistan", "iran"]
    }
    for alliance, members in ALLIANCE_FALLBACK.items():
        if alliance not in alliances:
            alliances[alliance] = members
    for alliance, members in alliances.items():
        save_ontology("alliances", alliance, members)
    print(f"  Saved {len(alliances)} alliances")

    # 5. ConceptNet
    conceptnet = fetch_all_conceptnet()
    for concept, relations in conceptnet.items():
        save_ontology("conceptnet", concept, relations)
    print(f"  Saved {len(conceptnet)} concepts")

    # 6. GeoNames
    geonames = fetch_geonames_countries()
    for country, info in geonames.items():
        save_ontology("geonames", country, info)
    print(f"  Saved {len(geonames)} countries from GeoNames")

    print("\nOntology build complete!")


if __name__ == "__main__":
    build_ontology()