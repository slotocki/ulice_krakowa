import urllib.request
import json

def fetch_street(name):
    url = f"https://nominatim.openstreetmap.org/search?street={urllib.parse.quote(name)}&city=Krakow&format=geojson&polygon_geojson=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'KrakowStreetsApp/1.0 (contact: admin@krakowstreets.pl)'})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            d = json.loads(r.read().decode('utf-8'))
        lines = []
        for feat in d.get('features', []):
            geom = feat.get('geometry', {})
            if geom.get('type') == 'LineString':
                lines.append(geom['coordinates'])
            elif geom.get('type') == 'MultiLineString':
                lines.extend(geom['coordinates'])
        return lines
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return []

szewska = fetch_street("Szewska")
kwiatowa = fetch_street("Kwiatowa")
print(f"Szewska lines: {len(szewska)}")
print(f"Kwiatowa lines: {len(kwiatowa)}")

with open('data/temp_streets.json', 'w', encoding='utf-8') as f:
    json.dump({'szewska': szewska, 'kwiatowa': kwiatowa}, f, ensure_ascii=False, indent=2)
print("Saved to data/temp_streets.json")
