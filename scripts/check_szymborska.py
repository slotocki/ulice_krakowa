import urllib.request
import urllib.parse
import json

q = """[out:json][timeout:25];
area["name"="Kraków"]["admin_level"="8"]->.krakow;
(
  nwr["name"~"Szymborsk"](area.krakow);
);
out body geom;"""

data = urllib.parse.urlencode({"data": q}).encode("utf-8")
req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=data, headers={"User-Agent": "KrakowStreetsDebug/1.0"})

with urllib.request.urlopen(req, timeout=30) as resp:
    res = json.loads(resp.read().decode("utf-8"))

for el in res.get("elements", []):
    print(el.get("type"), el.get("id"), el.get("tags"))
