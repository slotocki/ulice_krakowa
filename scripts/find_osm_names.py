import urllib.request
import urllib.parse
import json

q = """[out:json][timeout:25];
area["name"="Kraków"]["admin_level"="8"]->.krakow;
(
  way["name"~"Słowackiego|Szymborsk"](area.krakow);
);
out body geom;"""

data = urllib.parse.urlencode({'data': q}).encode('utf-8')
req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=data, headers={'User-Agent': 'KrakowStreetsDebug/1.0'})

with urllib.request.urlopen(req, timeout=30) as resp:
    res = json.loads(resp.read().decode('utf-8'))

names = set()
for el in res.get('elements', []):
    tags = el.get('tags', {})
    if 'name' in tags:
        names.add((tags.get('name') or '', tags.get('highway') or '', el.get('id')))

for n in sorted(names):
    print(n)
