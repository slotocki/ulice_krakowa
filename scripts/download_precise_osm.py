#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pobiera precyzyjne linie z OpenStreetMap dla zestawu ulic w JEDNYM szybkim zapytaniu z Bounding Boxem.
"""

import json
import urllib.request
import urllib.parse

# Bounding box Krakowa: (min_lat, min_lon, max_lat, max_lon)
BBOX = "50.00,19.88,50.10,20.06"

STREETS_REGEX = "Stanisława Lema|Wisławy Szymborskiej|Floriańska|Grodzka|Józefa Dietla|Szeroka|Juliusza Słowackiego|aleja Juliusza Słowackiego|Mogilska"

QUERY = f"""[out:json][timeout:35];
(
  way["highway"]["name"~"^({STREETS_REGEX})$"]({BBOX});
);
out body geom;
"""

def main():
    print("[*] Pobieranie precyzyjnych linii ulic z Overpass API (Kraków BBOX)...")
    data = urllib.parse.urlencode({"data": QUERY}).encode("utf-8")
    req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=data, headers={"User-Agent": "KrakowStreetsBatch/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            osm_res = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[!] Błąd Overpass primary: {e}, próba mirrora...")
        req = urllib.request.Request("https://maps.mail.ru/osm/tools/overpass/api/interpreter", data=data, headers={"User-Agent": "KrakowStreetsBatch/1.0"})
        with urllib.request.urlopen(req, timeout=35) as resp:
            osm_res = json.loads(resp.read().decode("utf-8"))

    elements = [el for el in osm_res.get("elements", []) if el.get("type") == "way" and "geometry" in el]
    print(f"[+] Otrzymano {len(elements)} segmentów dróg.")

    # Grupowanie linii według nazwy ulicy
    grouped = {}
    for el in elements:
        name = el.get("tags", {}).get("name")
        if not name:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in el["geometry"]]
        if len(coords) >= 2:
            grouped.setdefault(name, []).append(coords)

    # Wczytanie pliku data/streets_sample.json i podmiana geometrii
    with open("data/streets_sample.json", "r", encoding="utf-8") as f:
        sample_data = json.load(f)

    updated_count = 0
    for feature in sample_data["features"]:
        sname = feature["properties"]["name"]
        fname = feature["properties"]["full_name"]
        
        matched_lines = None
        for osm_name, lines in grouped.items():
            if osm_name == sname or osm_name == fname or sname in osm_name:
                matched_lines = lines
                break

        if matched_lines:
            if len(matched_lines) == 1:
                feature["geometry"] = {
                    "type": "LineString",
                    "coordinates": matched_lines[0]
                }
            else:
                feature["geometry"] = {
                    "type": "MultiLineString",
                    "coordinates": matched_lines
                }
            updated_count += 1
            print(f"  [OK] Zaktualizowano precyzyjną geometrię: {sname} ({len(matched_lines)} segmentów)")

    with open("data/streets_sample.json", "w", encoding="utf-8") as f:
        json.dump(sample_data, f, ensure_ascii=False, indent=2)

    print(f"\n[SUKCES] Zaktualizowano {updated_count} ulic w data/streets_sample.json!")

if __name__ == "__main__":
    main()
