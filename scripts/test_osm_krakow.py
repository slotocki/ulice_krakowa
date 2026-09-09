# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import json
import time

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
]

# Zapytanie o wszystkie nazwane drogi w Krakowie (admin_level=8, Kraków)
# Używamy formatu [out:json][timeout:90][maxsize:536870912];
query = """[out:json][timeout:90];
area["name"="Kraków"]["admin_level"="8"]->.krk;
(
  way["highway"~"^(residential|tertiary|secondary|primary|unclassified|living_street|pedestrian)$"]["name"](area.krk);
);
out tags qt;
"""

print("Testowanie Overpass API dla Krakowa (pobieranie unikalnych nazw ulic)...")
data = urllib.parse.urlencode({'data': query}).encode('utf-8')

for server in OVERPASS_SERVERS:
    print(f"Próba serwera: {server}...")
    t0 = time.time()
    try:
        req = urllib.request.Request(
            server, 
            data=data, 
            headers={'User-Agent': 'KrakowStreetsResearch/1.0 (academic/open-data portal)'}
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode('utf-8')
            res = json.loads(raw)
            dt = time.time() - t0
            elements = res.get('elements', [])
            print(f"Sukces na serwerze {server}! Czas: {dt:.2f} s. Pobranych segmentów: {len(elements)}")
            
            # Analiza unikalnych nazw
            names = set()
            for el in elements:
                n = el.get('tags', {}).get('name')
                if n:
                    names.add(n)
            print(f"Liczba unikalnych nazw ulic w Krakowie: {len(names)}")
            
            # Zapisz listę nazw
            with open('data/krakow_street_names.json', 'w', encoding='utf-8') as f:
                json.dump(sorted(list(names)), f, ensure_ascii=False, indent=2)
            print("Zapisano listę do data/krakow_street_names.json")
            break
    except Exception as e:
        print(f"Błąd serwera {server}: {e}")
