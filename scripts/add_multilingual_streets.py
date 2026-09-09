# -*- coding: utf-8 -*-
import json
import urllib.request
import urllib.parse

# 1. Pobranie geometrii Szewska i Kwiatowa z Overpass API
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def fetch_osm_way(name):
    query = f"""
    [out:json][timeout:25];
    area["name"="Kraków"]["admin_level"="8"]->.a;
    way["name"="{name}"](area.a);
    out geom;
    """
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')
    req = urllib.request.Request(OVERPASS_URL, data=data, headers={'User-Agent': 'KrakowStreetsBuilder/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            d = json.loads(resp.read().decode('utf-8'))
        coords = []
        for el in d.get('elements', []):
            line = [[pt['lon'], pt['lat']] for pt in el.get('geometry', [])]
            if line:
                coords.append(line)
        return coords
    except Exception as e:
        print(f"Error fetching {name}: {e}")
        return None

szewska_coords = fetch_osm_way("Szewska")
kwiatowa_coords = fetch_osm_way("Kwiatowa")

print(f"Szewska segments: {len(szewska_coords) if szewska_coords else 0}")
print(f"Kwiatowa segments: {len(kwiatowa_coords) if kwiatowa_coords else 0}")
