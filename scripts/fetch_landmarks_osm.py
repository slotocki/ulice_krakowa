# -*- coding: utf-8 -*-
"""
scripts/fetch_landmarks_osm.py

Fetches geometries and coordinates from OpenStreetMap for:
- 77 housing estates (Osiedla)
- 25 bridges & footbridges (Mosty i Kładki)
- 52 parks, boulevards & greenery (Parki i Bulwary)
Total: 154 landmarks.
"""

import json
import os
import re
import urllib.request
import urllib.parse
import time

OVERPASS_SERVERS = [
    'https://overpass-api.de/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter'
]

def query_overpass(query_str):
    for server in OVERPASS_SERVERS:
        print(f"Próba zapytania do {server}...")
        try:
            data = urllib.parse.urlencode({'data': query_str}).encode('utf-8')
            req = urllib.request.Request(
                server,
                data=data,
                headers={'User-Agent': 'KrakowLandmarksMapper/1.0 (contact: admin@krakow.pl)'}
            )
            with urllib.request.urlopen(req, timeout=50) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                print(f"Pomyślnie pobrano {len(result.get('elements', []))} elementów z {server}")
                return result
        except Exception as e:
            print(f"Błąd serwera {server}: {e}")
            time.sleep(2)
    return None

def main():
    q = """[out:json][timeout:60];
area["name"="Kraków"]["admin_level"="8"]->.krakow;
(
  node["place"~"neighbourhood|suburb"](area.krakow);
  way["place"~"neighbourhood|suburb"](area.krakow);
  relation["place"~"neighbourhood|suburb"](area.krakow);
  
  node["name"~"Osiedle|os\\.|Park|Bulwar|Most|Kładka"](area.krakow);
  way["name"~"Osiedle|os\\.|Park|Bulwar|Most|Kładka"](area.krakow);
  relation["name"~"Osiedle|os\\.|Park|Bulwar|Most|Kładka"](area.krakow);
  
  way["leisure"="park"](area.krakow);
  relation["leisure"="park"](area.krakow);
);
out body center tags;
"""
    res = query_overpass(q)
    if not res:
        print("Nie udało się pobrać danych z Overpass!")
        return

    elements = res.get('elements', [])
    print(f"Łącznie pobrano {len(elements)} elementów z OSM.")

    os.makedirs('data/cache', exist_ok=True)
    with open('data/cache/osm_raw_landmarks.json', 'w', encoding='utf-8') as f:
        json.dump(elements, f, ensure_ascii=False, indent=2)
    print("Zapisano dane do data/cache/osm_raw_landmarks.json")

if __name__ == '__main__':
    main()
