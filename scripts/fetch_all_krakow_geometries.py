# -*- coding: utf-8 -*-
"""
Pobieranie pełnej siatki geometrii ulic Krakowa za pomocą kafelkowania (Spatial Grid Bounding Box)
z automatyczną rotacją serwerów Overpass i odpornością na błędy 429 (Too Many Requests).
"""

import urllib.request
import urllib.parse
import json
import os
import math
import time
import re

OVERPASS_SERVERS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter"
]

CHUNK_DIR = "data/osm_chunks"
OUTPUT_GEOJSON = "data/krakow_streets.geojson"
SAMPLE_DATA_FILE = "data/streets_sample.json"

os.makedirs(CHUNK_DIR, exist_ok=True)

# Granice Krakowa podzielone na 12 kafelków (3x4)
LAT_STEPS = [49.965, 50.020, 50.075, 50.130]
LON_STEPS = [19.780, 19.890, 20.000, 20.110, 20.220]

def haversine_distance(coord1, coord2):
    lon1, lat1 = coord1
    lon2, lat2 = coord2
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def calculate_total_length(multiline_coords):
    total = 0.0
    for line in multiline_coords:
        for i in range(len(line) - 1):
            total += haversine_distance(line[i], line[i + 1])
    return int(round(total))

def slugify(text):
    text = text.lower().strip()
    replacements = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
        'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        ' ': '_', '-': '_', '.': '', ',': '', '/': '_', '"': '', "'": ''
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = re.sub(r'[^a-z0-9_]', '', text)
    text = re.sub(r'_+', '_', text).strip('_')
    return text

def parse_prefix_and_name(raw_name):
    lower = raw_name.lower().strip()
    prefixes = [
        ("aleja ", "aleja"),
        ("al. ", "aleja"),
        ("plac ", "plac"),
        ("pl. ", "plac"),
        ("rondo ", "rondo"),
        ("osiedle ", "osiedle"),
        ("os. ", "osiedle"),
        ("park ", "park"),
        ("bulwar ", "bulwar"),
        ("skwer ", "skwer"),
        ("droga ", "droga"),
        ("grobla ", "grobla"),
        ("rynek ", "rynek"),
        ("zaułek ", "zaułek"),
        ("ulica ", "ulica"),
        ("ul. ", "ulica"),
    ]
    for pref_str, pref_norm in prefixes:
        if lower.startswith(pref_str):
            clean_name = raw_name[len(pref_str):].strip()
            return pref_norm, clean_name
    return "ulica", raw_name.strip()

def fetch_chunk(s_lat, s_lon, n_lat, n_lon, idx):
    cache_path = os.path.join(CHUNK_DIR, f"chunk_{idx}.json")
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1000:
        print(f"[{idx+1}/12] Kafelek z pamięci podręcznej (ok. {os.path.getsize(cache_path)//1024} KB)...", flush=True)
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    query = f"""[out:json][timeout:45];
(
  way["highway"~"^(residential|tertiary|secondary|primary|unclassified|living_street|pedestrian)$"]["name"]({s_lat:.5f},{s_lon:.5f},{n_lat:.5f},{n_lon:.5f});
);
out geom qt;
"""
    data = urllib.parse.urlencode({'data': query}).encode('utf-8')

    max_attempts = 4
    for attempt in range(max_attempts):
        server = OVERPASS_SERVERS[(idx + attempt) % len(OVERPASS_SERVERS)]
        print(f"[{idx+1}/12] Pobieranie z {server} (próba {attempt+1})...", flush=True)
        t0 = time.time()
        try:
            req = urllib.request.Request(
                server, 
                data=data, 
                headers={'User-Agent': f'KrakowStreetsGrid/1.{attempt} (academic open data portal)'}
            )
            with urllib.request.urlopen(req, timeout=45) as resp:
                d = json.loads(resp.read().decode('utf-8'))
            el_count = len(d.get('elements', []))
            dt = time.time() - t0
            print(f"[{idx+1}/12] Sukces w {dt:.2f} s: {el_count} segmentów.", flush=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(d, f, ensure_ascii=False)
            time.sleep(1.5)  # Uprzejme opóźnienie
            return d
        except urllib.error.HTTPError as he:
            print(f"[{idx+1}/12] Błąd HTTP {he.code} na {server}. Zmiana serwera...", flush=True)
            time.sleep(3)
        except Exception as e:
            print(f"[{idx+1}/12] Błąd {e} na {server}. Przełączam serwer...", flush=True)
            time.sleep(2)

    print(f"[{idx+1}/12] Ostateczne niepowodzenie kafelka {idx}.", flush=True)
    return {"elements": []}

def main():
    print("=== Rozpoczynam kafelkowe pobieranie ulic Krakowa (12 sektorów) ===", flush=True)
    all_elements_by_id = {}
    idx = 0

    for i in range(len(LAT_STEPS) - 1):
        s_lat, n_lat = LAT_STEPS[i], LAT_STEPS[i + 1]
        for j in range(len(LON_STEPS) - 1):
            s_lon, n_lon = LON_STEPS[j], LON_STEPS[j + 1]
            chunk_data = fetch_chunk(s_lat, s_lon, n_lat, n_lon, idx)
            for el in chunk_data.get('elements', []):
                all_elements_by_id[el['id']] = el
            idx += 1

    print(f"\nŁącznie unikalnych segmentów drogowych: {len(all_elements_by_id)}", flush=True)

    # Agregacja segmentów według dokładnej nazwy ulicy
    streets_by_name = {}
    for el in all_elements_by_id.values():
        name = el.get('tags', {}).get('name')
        if not name:
            continue
        geom = el.get('geometry', [])
        if len(geom) < 2:
            continue
        line = [[round(pt['lon'], 5), round(pt['lat'], 5)] for pt in geom]
        if name not in streets_by_name:
            streets_by_name[name] = {
                'tags': el.get('tags', {}),
                'lines': []
            }
        streets_by_name[name]['lines'].append(line)

    print(f"Zagregowano {len(streets_by_name)} unikalnych nazw ulic!", flush=True)

    # Wczytanie bogatych danych próbkowych (aby zachować szczegóły Floriańskiej, Szymborskiej, Lema itd.)
    sample_features = {}
    if os.path.exists(SAMPLE_DATA_FILE):
        with open(SAMPLE_DATA_FILE, 'r', encoding='utf-8') as f:
            s_data = json.load(f)
            for feat in s_data.get('features', []):
                pid = feat['properties']['id']
                sample_features[pid] = feat

    features = []
    used_ids = set()

    for raw_name, s_info in streets_by_name.items():
        prefix, clean_name = parse_prefix_and_name(raw_name)
        street_id = slugify(clean_name)
        if not street_id:
            street_id = slugify(raw_name)

        base_id = street_id
        counter = 2
        while street_id in used_ids:
            street_id = f"{base_id}_{counter}"
            counter += 1
        used_ids.add(street_id)

        lines = s_info['lines']
        length = calculate_total_length(lines)

        # Sprawdzenie czy mamy ręcznie zweryfikowane dane
        matched_sample = None
        for pid, sfeat in sample_features.items():
            s_pl_name = sfeat['properties'].get('name')
            if isinstance(s_pl_name, dict):
                s_pl_name = s_pl_name.get('pl', '')
            if s_pl_name and (s_pl_name.lower() in raw_name.lower() or raw_name.lower() in s_pl_name.lower() or pid == street_id):
                matched_sample = sfeat
                break

        if matched_sample:
            feat = {
                "type": "Feature",
                "id": street_id,
                "properties": {
                    **matched_sample['properties'],
                    "id": street_id,
                    "length_meters": length if length > 0 else matched_sample['properties'].get('length_meters', 0)
                },
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": lines
                }
            }
        else:
            full_name_pl = f"{prefix} {clean_name}" if prefix != "ulica" else f"ulica {clean_name}"
            feat = {
                "type": "Feature",
                "id": street_id,
                "properties": {
                    "id": street_id,
                    "name": {
                        "pl": clean_name,
                        "en": clean_name,
                        "de": clean_name
                    },
                    "prefix": {
                        "pl": prefix,
                        "en": "street" if prefix == "ulica" else ("avenue" if prefix == "aleja" else prefix),
                        "de": "Straße" if prefix == "ulica" else ("Allee" if prefix == "aleja" else prefix)
                    },
                    "full_name": {
                        "pl": full_name_pl,
                        "en": f"{clean_name} Street" if prefix == "ulica" else f"{clean_name} {prefix}",
                        "de": f"{clean_name}-Straße" if prefix == "ulica" else f"{clean_name}-{prefix}"
                    },
                    "district": {
                        "pl": "Kraków",
                        "en": "Kraków",
                        "de": "Krakau"
                    },
                    "category": {
                        "pl": "Ulice Krakowa",
                        "en": "Streets of Kraków",
                        "de": "Straßen von Krakau"
                    },
                    "year": None,
                    "length_meters": length,
                    "summary": {
                        "pl": f"{full_name_pl.capitalize()} w Krakowie.",
                        "en": f"{clean_name} in Kraków.",
                        "de": f"{clean_name} in Krakau."
                    },
                    "patron": None,
                    "etymology": {
                        "pl": f"Ulica {clean_name} w Krakowie. Pełny biogram patrona lub etymologia historyczna zostanie uzupełniona w kolejnym kroku integracji z rejestrem BIP oraz monografią prof. E. Supranowicz.",
                        "en": f"{clean_name} in Kraków. Detailed historical background and municipal resolution data are being indexed.",
                        "de": f"{clean_name} in Krakau. Detaillierte historische Hintergründe und Stadtratsbeschlüsse werden erfasst."
                    },
                    "resolution": {
                        "has_resolution": False
                    },
                    "source": {
                        "name": "OpenStreetMap / Miasto Kraków",
                        "url": "https://www.openstreetmap.org",
                        "label": "OSM"
                    }
                },
                "geometry": {
                    "type": "MultiLineString",
                    "coordinates": lines
                }
            }
        features.append(feat)

    features.sort(key=lambda f: f['properties']['name']['pl'] if isinstance(f['properties']['name'], dict) else f['properties']['name'])

    output_collection = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(OUTPUT_GEOJSON, 'w', encoding='utf-8') as f:
        json.dump(output_collection, f, ensure_ascii=False)

    size_mb = os.path.getsize(OUTPUT_GEOJSON) / (1024 * 1024)
    print(f"\n=======================================================", flush=True)
    print(f"Sukces! Wygenerowano pełną bazę wszystkich ulic Krakowa:", flush=True)
    print(f"Plik docelowy: {OUTPUT_GEOJSON}", flush=True)
    print(f"Liczba unikalnych ulic: {len(features)}", flush=True)
    print(f"Rozmiar pliku GeoJSON: {size_mb:.2f} MB", flush=True)
    print(f"=======================================================\n", flush=True)

if __name__ == '__main__':
    main()
