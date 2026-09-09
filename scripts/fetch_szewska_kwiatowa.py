# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.parse

query = """[out:json][timeout:20];
(
  way["name"="Szewska"](50.05,19.92,50.07,19.95);
  way["name"="Kwiatowa"](49.98,19.85,50.12,20.05);
);
out geom;"""

data = urllib.parse.urlencode({'data': query}).encode('utf-8')
req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=data, headers={'User-Agent': 'KrakowStreets/1.0'})

with urllib.request.urlopen(req, timeout=20) as resp:
    res = json.loads(resp.read().decode('utf-8'))

szewska_lines = []
kwiatowa_lines = []

for el in res.get('elements', []):
    name = el.get('tags', {}).get('name')
    coords = [[pt['lon'], pt['lat']] for pt in el.get('geometry', [])]
    if not coords:
        continue
    if name == 'Szewska':
        szewska_lines.append(coords)
    elif name == 'Kwiatowa':
        kwiatowa_lines.append(coords)

print(f"Szewska lines: {len(szewska_lines)}")
print(f"Kwiatowa lines: {len(kwiatowa_lines)}")

with open('data/temp_streets.json', 'w', encoding='utf-8') as f:
    json.dump({'szewska': szewska_lines, 'kwiatowa': kwiatowa_lines}, f, ensure_ascii=False, indent=2)
print("Saved to data/temp_streets.json")
