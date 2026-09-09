# -*- coding: utf-8 -*-
"""
Rygorystyczne filtrowanie i docinanie ulic do dokładnych granic administracyjnych m. Krakowa
z wykorzystaniem silnika geometrycznego GEOS (Shapely) oraz urzędowego rejestru ulic.
"""

import json
import glob
import re
import math
import os
from shapely.geometry import shape, LineString, MultiLineString, mapping
from shapely.prepared import prep

BORDER_FILE = "data/krakow_border.geojson"
CHUNK_DIR = "data/osm_chunks"
OFFICIAL_NAMES_FILE = "data/krakow_street_names.json"
SAMPLE_DATA_FILE = "data/streets_sample.json"
OUTPUT_GEOJSON = "data/krakow_streets.geojson"

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

def normalize_key(s):
    if not s:
        return ''
    s = s.lower().strip()
    s = re.sub(r'^(ulica|ul\.|aleja|al\.|plac|pl\.|osiedle|os\.|rondo|skwer|bulwar|droga|grobla|park)\s+', '', s)
    s = re.sub(r'[^a-ząćęłńóśźż0-9]', '', s)
    return s

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

def main():
    print("1. Wczytuję wielokąt granic administracyjnych Krakowa...", flush=True)
    with open(BORDER_FILE, 'r', encoding='utf-8') as f:
        border_feat = json.load(f)
    krakow_polygon = shape(border_feat['geometry'])
    prepared_border = prep(krakow_polygon)

    print("2. Wczytuję urzędowy wykaz ulic w granicach Krakowa...", flush=True)
    with open(OFFICIAL_NAMES_FILE, 'r', encoding='utf-8') as f:
        official_names = json.load(f)
    print(f"Liczba oficjalnych nazw: {len(official_names)}")

    official_map = {}
    for oname in official_names:
        key = normalize_key(oname)
        if key not in official_map or oname.startswith(('Aleja', 'Plac', 'Rondo', 'Osiedle', 'Rynek', 'Park')):
            official_map[key] = oname

    print("3. Wczytuję segmenty z kafelków OSM i testuję geometrycznie...", flush=True)
    chunk_files = sorted(glob.glob(os.path.join(CHUNK_DIR, "chunk_*.json")))
    all_ways = {}
    for cf in chunk_files:
        with open(cf, 'r', encoding='utf-8') as f:
            d = json.load(f)
            for el in d.get('elements', []):
                all_ways[el['id']] = el

    print(f"Liczba wszystkich pobranych segmentów: {len(all_ways)}")

    streets_grouped = {}
    outside_geom_count = 0
    outside_name_count = 0
    clipped_count = 0

    for wid, el in all_ways.items():
        raw_name = el.get('tags', {}).get('name')
        if not raw_name:
            continue
        
        norm_k = normalize_key(raw_name)
        if norm_k not in official_map:
            outside_name_count += 1
            continue

        raw_geom = el.get('geometry', [])
        if len(raw_geom) < 2:
            continue

        coords = [[pt['lon'], pt['lat']] for pt in raw_geom]
        try:
            line_geom = LineString(coords)
        except Exception:
            continue

        # GEOMETRYCZNY TEST ZAWIERANIA W GRANICACH KRAKOWA
        if not prepared_border.intersects(line_geom):
            # Segment leży całkowicie poza Krakowem (np. Kościuszki w Wieliczce!)
            outside_geom_count += 1
            continue

        # Jeśli segment częściowo wystaje poza Kraków (np. droga wylotowa), docinamy go dokładnie do granicy
        if not krakow_polygon.contains(line_geom):
            clipped = line_geom.intersection(krakow_polygon)
            clipped_count += 1
            clipped_lines = []
            if clipped.geom_type == 'LineString':
                clipped_lines.append(list(clipped.coords))
            elif clipped.geom_type == 'MultiLineString':
                for part in clipped.geoms:
                    clipped_lines.append(list(part.coords))
            elif clipped.geom_type == 'GeometryCollection':
                for part in clipped.geoms:
                    if part.geom_type == 'LineString':
                        clipped_lines.append(list(part.coords))
        else:
            clipped_lines = [coords]

        canonical_name = official_map[norm_k]
        if canonical_name not in streets_grouped:
            streets_grouped[canonical_name] = []

        for cl in clipped_lines:
            if len(cl) >= 2:
                # Zaokrąglenie do 5 miejsc po przecinku
                rounded = [[round(pt[0], 5), round(pt[1], 5)] for pt in cl]
                streets_grouped[canonical_name].append(rounded)

    print(f"\n--- WYNIKI GEOMETRYCZNEJ WERYFIKACJI ---")
    print(f"Odrzucono dróg o nazwach spoza Krakowa: {outside_name_count}")
    print(f"Odrzucono segmentów leżących FIZYCZNIE poza granicami Krakowa (np. te same nazwy w Wieliczce/Skawinie): {outside_geom_count}")
    print(f"Przycięto do granicy miasta dróg wylotowych: {clipped_count}")
    print(f"Pozostało zweryfikowanych ulic ściśle w granicach Krakowa: {len(streets_grouped)}\n")

    # 4. Wczytanie wzorcowych ulic
    sample_features = {}
    if os.path.exists(SAMPLE_DATA_FILE):
        with open(SAMPLE_DATA_FILE, 'r', encoding='utf-8') as f:
            s_data = json.load(f)
            for feat in s_data.get('features', []):
                sample_features[feat['properties']['id']] = feat

    features = []
    used_ids = set()

    for pid, sfeat in sample_features.items():
        s_name = sfeat['properties'].get('name')
        if isinstance(s_name, dict):
            s_name = s_name.get('pl', '')
        norm_s = normalize_key(s_name)
        canon = official_map.get(norm_s)
        if canon and canon in streets_grouped:
            sfeat['geometry']['coordinates'] = streets_grouped[canon]
            del streets_grouped[canon]
        used_ids.add(pid)
        features.append(sfeat)

    # 5. Dodanie pozostałych ulic
    for canon_name, lines in streets_grouped.items():
        prefix, clean_name = parse_prefix_and_name(canon_name)
        street_id = slugify(clean_name)
        if not street_id or street_id in used_ids:
            street_id = slugify(canon_name)
        
        base_id = street_id
        c = 2
        while street_id in used_ids:
            street_id = f"{base_id}_{c}"
            c += 1
        used_ids.add(street_id)

        length = calculate_total_length(lines)
        full_name_pl = canon_name if (prefix in ["aleja", "plac", "rondo", "osiedle", "park", "rynek", "bulwar", "skwer"]) else f"ulica {clean_name}"

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
                    "en": "avenue" if prefix == "aleja" else ("street" if prefix == "ulica" else prefix),
                    "de": "Allee" if prefix == "aleja" else ("Straße" if prefix == "ulica" else prefix)
                },
                "full_name": {
                    "pl": full_name_pl,
                    "en": f"{clean_name} Avenue" if prefix == "aleja" else f"{clean_name} Street",
                    "de": f"{clean_name}-Allee" if prefix == "aleja" else f"{clean_name}-Straße"
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
                    "pl": f"{full_name_pl} w Krakowie.",
                    "en": f"{clean_name} in Kraków.",
                    "de": f"{clean_name} in Krakau."
                },
                "patron": None,
                "etymology": {
                    "pl": f"{full_name_pl} – oficjalna ulica m. Krakowa. Pełna etymologia historyczna zostanie uzupełniona na podstawie monografii prof. E. Supranowicz i uchwał Rady Miasta Krakowa.",
                    "en": f"{clean_name} – official street in Kraków.",
                    "de": f"{clean_name} – offizielle Straße in Krakau."
                },
                "resolution": {
                    "has_resolution": False
                },
                "source": {
                    "name": "Ewidencja Ulic Miasta Krakowa / OpenStreetMap",
                    "url": "https://www.bip.krakow.pl",
                    "label": "BIP / OSM"
                }
            },
            "geometry": {
                "type": "MultiLineString",
                "coordinates": lines
            }
        }
        features.append(feat)

    def sort_key(f):
        n = f['properties'].get('name')
        if isinstance(n, dict):
            return n.get('pl', '')
        return str(n or '')

    features.sort(key=sort_key)

    out_coll = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(OUTPUT_GEOJSON, 'w', encoding='utf-8') as f:
        json.dump(out_coll, f, ensure_ascii=False)

    size_mb = os.path.getsize(OUTPUT_GEOJSON) / (1024 * 1024)
    print(f"Zapisano {len(features)} ulic do {OUTPUT_GEOJSON} ({size_mb:.2f} MB)")

if __name__ == '__main__':
    main()
