# GeoTradeV2/detector/ontology.py

from storage.db import get_ontology


def get_country_exports(country):
    return get_ontology("exports", country) or []


def get_waterway_countries(waterway):
    return get_ontology("waterways", waterway) or []


def is_opec_member(country):
    members = get_ontology("organizations", "opec") or []
    return country.lower() in members


def get_alliance_members(alliance):
    return get_ontology("alliances", alliance) or []


def get_concept_relations(concept):
    return get_ontology("conceptnet", concept) or {}


def get_country_info(country):
    return get_ontology("geonames", country) or {}


def enrich_article(countries, locations, events):
    enrichment = {
        "exports_at_risk":   [],
        "waterways_at_risk": [],
        "is_opec_involved":  False,
        "alliance_context":  [],
        "related_concepts":  [],
        "risk_multiplier":   1.0,
        "reason":            []
    }

    for country in countries:
        country_lower = country.lower()

        exports = get_country_exports(country_lower)
        if exports:
            enrichment["exports_at_risk"].extend(exports[:3])
            enrichment["reason"].append(
                f"{country} exports at risk: {', '.join(exports[:3])}"
            )

        if is_opec_member(country_lower):
            enrichment["is_opec_involved"] = True
            enrichment["risk_multiplier"] *= 1.3
            enrichment["reason"].append(
                f"{country} is OPEC member → oil supply risk"
            )

        info = get_country_info(country_lower)
        if info:
            enrichment["alliance_context"].append({
                "country":   country,
                "continent": info.get("continent"),
                "currency":  info.get("currency"),
                "neighbors": info.get("neighbors", [])
            })

    for location in locations:
        location_lower      = location.lower()
        waterway_countries  = get_waterway_countries(location_lower)
        if waterway_countries:
            enrichment["waterways_at_risk"].append(location)
            enrichment["risk_multiplier"] *= 1.5
            enrichment["reason"].append(
                f"{location} is a strategic waterway — "
                f"borders: {', '.join(waterway_countries)}"
            )

    for event in events:
        relations = get_concept_relations(event.lower())
        if relations:
            related = relations.get("RelatedTo", [])[:5]
            enrichment["related_concepts"].extend(related)

    return enrichment


if __name__ == "__main__":
    result = enrich_article(
        countries=["Iran", "UAE"],
        locations=["Persian Gulf", "Strait of Hormuz"],
        events=["war", "oil"]
    )
    print("Exports at risk:", result["exports_at_risk"])
    print("Waterways at risk:", result["waterways_at_risk"])
    print("OPEC involved:", result["is_opec_involved"])
    print("Risk multiplier:", result["risk_multiplier"])
    print("Reasons:")
    for r in result["reason"]:
        print(" →", r)