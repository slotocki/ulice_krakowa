#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pobiera bezbłędne, precyzyjne geometrie z OpenStreetMap dla wszystkich ulic demonstracyjnych:
- Aleja Juliusza Słowackiego (z wielkiej litery)
- Stanisława Lema
- Floriańska
- Grodzka
- Józefa Dietla
- Szeroka
- Mogilska
- Szewska
- Kanonicza
- Promenada/Park im. Wisławy Szymborskiej
"""

import json
import urllib.request
import urllib.parse

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

QUERIES = [
    ('slowackiego', 'way["highway"]["name"="Aleja Juliusza Słowackiego"]'),
    ('lema', 'way["highway"]["name"="Stanisława Lema"]'),
    ('florianska', 'way["highway"]["name"="Floriańska"]'),
    ('grodzka', 'way["highway"]["name"="Grodzka"]'),
    ('dietla', 'way["highway"]["name"="Józefa Dietla"]'),
    ('szeroka', 'way["highway"]["name"="Szeroka"]'),
    ('mogilska', 'way["highway"]["name"="Mogilska"]'),
    ('szymborskiej', 'way[id=39393926]'), # Park im. Wisławy Szymborskiej
]

def fetch_geom(selector):
    q = f"""[out:json][timeout:25];( {selector}(50.00,19.88,50.10,20.06); );out body geom;"""
    data = urllib.parse.urlencode({"data": q}).encode("utf-8")
    req = urllib.request.Request(OVERPASS_URL, data=data, headers={"User-Agent": "KrakowStreetsBatch/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    
    elements = res.get("elements", [])
    lines = []
    for el in elements:
        geom = el.get("geometry", [])
        if len(geom) >= 2:
            pts = [[pt["lon"], pt["lat"]] for pt in geom]
            lines.append(pts)
    return lines

def main():
    with open("data/streets_sample.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for sid, selector in QUERIES:
        print(f"[*] Pobieranie OSM dla '{sid}'...")
        try:
            lines = fetch_geom(selector)
            if lines:
                feature = next((f for f in data["features"] if f["properties"]["id"] == sid), None)
                if feature:
                    if len(lines) == 1:
                        feature["geometry"] = {"type": "LineString", "coordinates": lines[0]}
                    else:
                        feature["geometry"] = {"type": "MultiLineString", "coordinates": lines}
                    print(f"  [SUKCES] '{sid}': pobrano {len(lines)} segmentów.")
            else:
                print(f"  [!] Brak geometrii dla '{sid}'")
        except Exception as e:
            print(f"  [!] Błąd dla '{sid}': {e}")

    with open("data/streets_sample.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n[GOTOWE] Zaktualizowano wszystkie ulice w data/streets_sample.json!")

if __name__ == "__main__":
    main()
