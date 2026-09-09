#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do pobierania geometrii ulic Krakowa z OpenStreetMap za pomocą Overpass API
i eksportu do formatu GeoJSON (LineString / MultiLineString).
"""

import sys
import json
import argparse
from urllib.request import Request, urlopen
from urllib.parse import urlencode

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

OVERPASS_QUERY_TEMPLATE = """
[out:json][timeout:120];
area["name"="Kraków"]["admin_level"="8"]->.krakow;
(
  way["highway"~"^(primary|secondary|tertiary|residential|living_street|pedestrian)$"]["name"{name_filter}](area.krakow);
);
out body geom;
"""

def fetch_osm_streets(street_name=None):
    """Pobiera geometrie ulic z Overpass API."""
    name_filter = f'="{street_name}"' if street_name else ""
    query = OVERPASS_QUERY_TEMPLATE.format(name_filter=name_filter)
    
    print("[*] Wysyłanie zapytania do Overpass API (Kraków streets)...")
    data = urlencode({"data": query}).encode("utf-8")
    req = Request(OVERPASS_URL, data=data, headers={"User-Agent": "KrakowStreetsExtractor/1.0"})

    with urlopen(req, timeout=140) as response:
        content = response.read().decode("utf-8")
        return json.loads(content)


def osm_to_geojson(osm_data):
    """Konwertuje odpowiedź Overpass API na GeoJSON FeatureCollection pogrupowaną według nazw ulic."""
    streets_grouped = {}

    elements = osm_data.get("elements", [])
    print(f"[+] Otrzymano {len(elements)} segmentów dróg (ways). Grupowanie według nazw...")

    for el in elements:
        if el.get("type") != "way":
            continue

        name = el.get("tags", {}).get("name")
        if not name:
            continue

        geometry = el.get("geometry", [])
        if len(geometry) < 2:
            continue

        coords = [[pt["lon"], pt["lat"]] for pt in geometry]

        if name not in streets_grouped:
            streets_grouped[name] = {
                "name": name,
                "highway_type": el.get("tags", {}).get("highway"),
                "lines": []
            }
        streets_grouped[name]["lines"].append(coords)

    features = []
    for name, data in streets_grouped.items():
        lines = data["lines"]
        
        # Pojedynczy odcinek to LineString, wiele odcinków to MultiLineString
        if len(lines) == 1:
            geom_type = "LineString"
            geom_coords = lines[0]
        else:
            geom_type = "MultiLineString"
            geom_coords = lines

        feature = {
            "type": "Feature",
            "properties": {
                "id": name.lower().replace(" ", "_").replace("ulica_", ""),
                "name": name,
                "full_name": f"ulica {name}" if not name.lower().startswith(("al.", "aleja", "plac", "pl.", "os.", "rondo")) else name,
                "highway": data["highway_type"],
                "segments_count": len(lines)
            },
            "geometry": {
                "type": geom_type,
                "coordinates": geom_coords
            }
        }
        features.append(feature)

    print(f"[+] Utworzono {len(features)} unikalnych ulic w GeoJSON.")
    return {
        "type": "FeatureCollection",
        "features": features
    }


def main():
    parser = argparse.ArgumentParser(description="Pobieranie ulic Krakowa z OpenStreetMap Overpass API")
    parser.add_argument("--street", help="Nazwa konkretnej ulicy (opcjonalnie, np. 'Floriańska')")
    parser.add_argument("--output", default="data/krakow_streets.geojson", help="Ścieżka do pliku wyjściowego GeoJSON")
    
    args = parser.parse_args()

    try:
        osm_raw = fetch_osm_streets(street_name=args.street)
        geojson = osm_to_geojson(osm_raw)

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(geojson, f, ensure_ascii=False)
        print(f"\n[SUKCES] Zapisano plik GeoJSON: {args.output}")

    except Exception as e:
        print(f"[!] Błąd: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
