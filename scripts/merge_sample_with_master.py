# -*- coding: utf-8 -*-
"""
Upewnienie się, że wszystkie 10 wzorcowych ulic (w tym Park Szymborskiej, Lema, Dietla itd.)
są idealnie zintegrowane w master GeoJSON z ich kanonicznymi ID.
"""

import json

with open('data/streets_sample.json', 'r', encoding='utf-8') as f:
    sample_data = json.load(f)

with open('data/krakow_streets.geojson', 'r', encoding='utf-8') as f:
    master_data = json.load(f)

# Mapa ulic wzorcowych po ID
sample_by_id = {feat['properties']['id']: feat for feat in sample_data['features']}

# Usuwamy z mastera duplikaty o nazwach odpowiadających próbce
clean_master = []
for feat in master_data['features']:
    pid = feat['properties']['id']
    # Jeśli to wariant jednej z naszych próbkowych ulic, pomijamy surowy z OSM na rzecz dopracowanego
    if pid in ['stanislawa_lema', 'juliusza_slowackiego', 'jozefa_dietla', 'florianska', 'kwiatowa', 'szewska']:
        continue
    clean_master.append(feat)

# Dodajemy wszystkie 10 wzorcowych ulic z zachowaniem ich kanonicznych ID
merged_features = list(sample_data['features']) + clean_master

# Sortowanie alfabetyczne po nazwie
def get_sort_key(f):
    name = f['properties'].get('name')
    if isinstance(name, dict):
        return name.get('pl', '')
    return str(name or '')

merged_features.sort(key=get_sort_key)

output = {
    "type": "FeatureCollection",
    "features": merged_features
}

with open('data/krakow_streets.geojson', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False)

print(f"Połączono pomyślnie! Łącznie ulic w master GeoJSON: {len(merged_features)}")
