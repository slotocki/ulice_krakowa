import urllib.request
import urllib.parse
import json
import time

query = """[out:json][timeout:30];
(
  way["highway"~"^(residential|tertiary|secondary|primary|unclassified|living_street|pedestrian)$"]["name"](50.05, 19.90, 50.08, 19.98);
);
out geom qt;
"""

t0 = time.time()
data = urllib.parse.urlencode({'data': query}).encode('utf-8')
req = urllib.request.Request('https://overpass-api.de/api/interpreter', data=data, headers={'User-Agent': 'KrakowTest/1.0'})
with urllib.request.urlopen(req, timeout=30) as r:
    d = json.loads(r.read().decode('utf-8'))
print(f"Time: {time.time()-t0:.2f}s, Elements: {len(d.get('elements', []))}")
