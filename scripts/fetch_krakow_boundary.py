import urllib.request
import urllib.parse
import json
import time

query = """[out:json][timeout:25];
relation["name"="Kraków"]["admin_level"="8"]["boundary"="administrative"];
out geom;
"""

data = urllib.parse.urlencode({'data': query}).encode('utf-8')
req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=data, headers={'User-Agent': 'KrakowBoundary/1.0'})

t0 = time.time()
with urllib.request.urlopen(req, timeout=25) as r:
    d = json.loads(r.read().decode('utf-8'))

print(f"Time: {time.time()-t0:.2f}s, Elements: {len(d.get('elements', []))}")
with open('data/krakow_boundary.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False)
print("Saved to data/krakow_boundary.json")
