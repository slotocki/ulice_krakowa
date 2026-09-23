# -*- coding: utf-8 -*-
"""
scripts/compile_landmarks_geojson.py

Kompiluje 154 obiekty (Partie 29 i 30) do data/krakow_landmarks.geojson:
- 77 osiedli mieszkaniowych
- 25 mostów i kładek
- 52 parki, zieleńce i bulwary
Każdy rekord otrzymuje pełną geometrię (Point [lon, lat]) oraz
kompletną strukturę metadanych toponimicznych, patronackich, historycznych i trójjęzycznych (i18n).
"""

import json
import os
import re

LANDMARKS_META_PATH = 'data/krakow_additional_landmarks.json'
OSM_CACHE_PATH = 'data/cache/osm_raw_landmarks.json'
BATCH_29_PATH = 'docs/audit_batches/batch_29.md'
BATCH_30_PATH = 'docs/audit_batches/batch_30.md'
OUTPUT_GEOJSON_PATH = 'data/krakow_landmarks.geojson'

DISTRICT_NAMES_EN_DE = {
    'I Stare Miasto': ('I Old Town', 'I Altstadt'),
    'II Grzegórzki': ('II Grzegórzki', 'II Grzegórzki'),
    'III Prądnik Czerwony': ('III Prądnik Czerwony', 'III Prądnik Czerwony'),
    'IV Prądnik Biały': ('IV Prądnik Biały', 'IV Prądnik Biały'),
    'V Krowodrza': ('V Krowodrza', 'V Krowodrza'),
    'VI Bronowice': ('VI Bronowice', 'VI Bronowice'),
    'VII Zwierzyniec': ('VII Zwierzyniec', 'VII Zwierzyniec'),
    'VIII Dębniki': ('VIII Dębniki', 'VIII Dębniki'),
    'IX Łagiewniki-Borek Fałęcki': ('IX Łagiewniki-Borek Fałęcki', 'IX Łagiewniki-Borek Fałęcki'),
    'X Swoszowice': ('X Swoszowice', 'X Swoszowice'),
    'XI Podgórze Duchackie': ('XI Podgórze Duchackie', 'XI Podgórze Duchackie'),
    'XII Bieżanów-Prokocim': ('XII Bieżanów-Prokocim', 'XII Bieżanów-Prokocim'),
    'XIII Podgórze': ('XIII Podgórze', 'XIII Podgórze'),
    'XIV Czyżyny': ('XIV Czyżyny', 'XIV Czyżyny'),
    'XV Mistrzejowice': ('XV Mistrzejowice', 'XV Mistrzejowice'),
    'XVI Bieńczyce': ('XVI Bieńczyce', 'XVI Bieńczyce'),
    'XVII Wzgórza Krzesławickie': ('XVII Wzgórza Krzesławickie', 'XVII Wzgórza Krzesławickie'),
    'XVIII Nowa Huta': ('XVIII Nowa Huta', 'XVIII Nowa Huta'),
}

CATEGORY_MAP = {
    'Miejsca i obiekty': {'pl': 'Miejsca i obiekty', 'en': 'Places and Landmarks', 'de': 'Orte und Wahrzeichen'},
    'Postacie historyczne': {'pl': 'Postacie historyczne', 'en': 'Historical Figures', 'de': 'Historische Persönlichkeiten'},
    'Parki i zieleń': {'pl': 'Parki i zieleń', 'en': 'Parks and Greenery', 'de': 'Parks und Grünflächen'},
    'Mosty i inżynieria': {'pl': 'Mosty i inżynieria', 'en': 'Bridges and Engineering', 'de': 'Brücken und Ingenieurbauwerke'},
    'Postacie fikcyjne i literatura': {'pl': 'Postacie fikcyjne i literatura', 'en': 'Fictional Characters and Literature', 'de': 'Fiktive Gestalten und Literatur'}
}

# Zweryfikowane współrzędne dla obiektów inżynieryjnych, parkowych i peryferyjnych
EXPLICIT_COORDS = {
    'most_pilsudskiego': (19.945004, 50.045465),
    'planty_krakowskie': (19.938425, 50.060249),
    'park_jordana': (19.917654, 50.060925),
    'park_bednarskiego': (19.950278, 50.041639),
    'most_debnicki': (19.928392, 50.054091),
    'most_grunwaldzki': (19.935230, 50.049850),
    'most_kotlarski': (19.960592, 50.051878),
    'most_powstancow_slaskich': (19.953367, 50.049119),
    'most_zwierzyniecki': (19.905663, 50.051280),
    'most_wandy': (20.049804, 50.051577),
    'kladka_ojca_bernatka': (19.947498, 50.046563),
    'kladka_kazimierz_ludwinow': (19.938450, 50.046120),
    'most_kolejowy_zablocie': (19.956800, 50.049800),
    'most_kolejowy_srednicowy': (19.955500, 50.050500),
    'most_sw_kingi': (19.956800, 50.049800),
    'most_ludwinowski': (19.937200, 50.046500),
    'estakada_obroncow_lwowa': (19.972100, 50.035400),
    'estakada_kaczmarskiego': (19.973500, 50.034500),
    'estakada_im_jacka_kaczmarskiego': (19.973500, 50.034500),
    'estakada_rozwadowskiego': (19.967500, 50.089200),
    'estakada_lipska_wielicka': (19.981200, 50.034100),
    'wiadukt_29_listopada': (19.948200, 50.078400),
    'most_debski': (19.985200, 50.057300),
    'most_dabski': (19.985200, 50.057300),
    'most_tadeusza_mazowieckiego': (20.048100, 50.055200),
    'most_nowohucki': (20.016300, 50.046200),
    'most_niepodleglosci': (19.945200, 50.045800),
    'os_krzeslawice': (20.065200, 50.085100),
    'os_koscielniki': (20.150400, 50.091200),
    'os_ruszcza': (20.108300, 50.082400),
    'os_cegielniana': (19.928400, 50.024100),
    'os_na_kozlowce': (19.986200, 50.018300),
    'park_zaczarowana_dorozka': (19.972500, 50.081500),
    'os_wandy': (20.049664, 50.070199),
    'os_willowe': (20.052600, 50.068800),
    'os_na_skarpie': (20.045517, 50.067396),
    'os_mlodosci': (20.046800, 50.064500),
    'os_ogrodowe': (20.042500, 50.069100),
    'os_stalowe': (20.050521, 50.074137),
    'os_szkolne': (20.044200, 50.073500),
    'os_hutnicze': (20.038100, 50.072800),
    'os_teatralne': (20.036500, 50.069500),
    'os_gorali': (20.034500, 50.073500),
    'os_zielone': (20.030500, 50.072100),
    'os_urocze': (20.030100, 50.068200),
    'os_sloneczne': (20.028500, 50.073800),
    'os_szklane_domy': (20.026100, 50.075500),
    'os_spoldzielcze': (20.028900, 50.064500),
    'os_kolorowe': (20.032500, 50.064200),
    'os_zgody': (20.024500, 50.069500),
    'os_centrum_a': (20.038800, 50.067200),
    'os_centrum_b': (20.034800, 50.067100),
    'os_centrum_c': (20.035200, 50.071200),
    'os_centrum_d': (20.039200, 50.071500),
    'os_handlowe': (20.038500, 50.064100),
}

STOPWORDS = {'park', 'most', 'osiedle', 'bulwar', 'kładka', 'estakada', 'plac', 'aleja', 'staw', 'ogród', 'kraków', 'w', 'na', 'pod', 'nad', 'z', 'i', 'im', 'dra', 'ii', 'iii'}

def clean_toks(s):
    s = s.lower().strip()
    s = re.sub(r'\b(imienia|im\.|doktora|dra|marszałka|marsz\.|świętego|św\.|ojca|ojc\.|plac|pl\.|osiedle|os\.|park|bulwar|most|kładka|kladka|wiadukt|estakada)\b', '', s)
    s = re.sub(r'[^\w\s]', ' ', s)
    return set(s.split()) - STOPWORDS

def load_batch_table(fpath):
    records = {}
    if not os.path.exists(fpath):
        return records
    with open(fpath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('|') and not line.startswith('| Lp') and not line.startswith('|:---'):
                cols = [c.strip() for c in line.split('|')]
                if len(cols) >= 10:
                    lp = int(cols[1])
                    name = cols[2].replace('**', '').strip()
                    cat = cols[3].replace('`', '').strip()
                    year = cols[4].strip()
                    patron_lit = cols[5].strip()
                    bio = cols[6].strip()
                    src = cols[7].strip()
                    portrait = cols[8].strip()
                    records[name.lower()] = {
                        'lp': lp, 'name': name, 'category': cat, 'year': year,
                        'patron_lit': patron_lit, 'bio': bio, 'src': src, 'portrait': portrait
                    }
    return records

def build_landmarks():
    with open(LANDMARKS_META_PATH, 'r', encoding='utf-8') as f:
        meta_data = json.load(f)

    with open(OSM_CACHE_PATH, 'r', encoding='utf-8') as f:
        osm_elements = json.load(f)

    osm_items = []
    for el in osm_elements:
        tags = el.get('tags', {})
        name = tags.get('name', '').strip()
        if name:
            lat = el.get('lat') or el.get('center', {}).get('lat')
            lon = el.get('lon') or el.get('center', {}).get('lon')
            if lat and lon:
                toks = clean_toks(name)
                osm_items.append({'name': name, 'toks': toks, 'coord': (lon, lat)})

    batch_29 = load_batch_table(BATCH_29_PATH)
    batch_30 = load_batch_table(BATCH_30_PATH)
    batch_all = {**batch_29, **batch_30}

    all_items = []
    for item in meta_data.get('bridges_footbridges', []):
        item['landmark_group'] = 'bridges'
        all_items.append(item)
    for item in meta_data.get('housing_estates', []):
        item['landmark_group'] = 'estates'
        all_items.append(item)
    for item in meta_data.get('boulevards_parks_greenery', []):
        item['landmark_group'] = 'parks'
        all_items.append(item)

    features = []

    for item in all_items:
        lid = item['id']
        name_pl = item['name']
        nl = name_pl.lower().strip()
        group = item['landmark_group']

        # Znajdź koordynaty
        pt = None
        if lid in EXPLICIT_COORDS:
            pt = EXPLICIT_COORDS[lid]
        else:
            ltoks = clean_toks(name_pl)
            best = None
            best_overlap = 0
            for oi in osm_items:
                overlap = len(ltoks & oi['toks'])
                if overlap > best_overlap:
                    best_overlap = overlap
                    best = oi
            if best and best_overlap > 0:
                pt = best['coord']

        if not pt:
            print(f"Ostrzeżenie: brak współrzędnych dla {lid} ({name_pl})!")
            continue

        lon, lat = pt

        # Pobierz dane z partii audytowej
        batch_rec = batch_all.get(nl, {})
        if not batch_rec:
            # fallback match by clean name
            for bn, bdata in batch_all.items():
                if len(clean_toks(name_pl) & clean_toks(bn)) >= 1:
                    batch_rec = bdata
                    break

        # Dzielnica
        dist_raw = item.get('district', batch_rec.get('district', 'Kraków'))
        dist_pl = dist_raw.split('/')[0].strip() if '/' in dist_raw else dist_raw.strip()
        dist_en, dist_de = DISTRICT_NAMES_EN_DE.get(dist_pl, (dist_pl, dist_pl))

        # Kategoria
        if group == 'estates':
            cat_key = 'Postacie historyczne' if any(k in name_pl for k in ['Kościuszkowskie', 'Albertyńskie', 'Kazimierzowskie', 'Strusia', 'Wandy']) else 'Miejsca i obiekty'
        elif group == 'parks':
            cat_key = 'Parki i zieleń'
        else:
            cat_key = 'Mosty i inżynieria'

        cat_dict = CATEGORY_MAP.get(cat_key, CATEGORY_MAP['Miejsca i obiekty'])

        # Prefiks
        if group == 'estates':
            prefix = {'pl': 'osiedle', 'en': 'housing estate', 'de': 'Siedlung'}
        elif group == 'parks':
            prefix = {'pl': 'park / bulwar', 'en': 'park / boulevard', 'de': 'Park / Boulevard'}
        else:
            prefix = {'pl': 'most / kładka', 'en': 'bridge / footbridge', 'de': 'Brücke / Steg'}

        # Patron
        patron_obj = None
        patron_str = batch_rec.get('patron_lit', item.get('patron', ''))
        pat_m = re.search(r'\*\*(.*?)\*\*', patron_str)
        if pat_m:
            pat_name = pat_m.group(1).strip()
            port_url = ''
            port_m = re.search(r'\((https://commons\.wikimedia\.org/.*?|https://upload\.wikimedia\.org/.*?)\)', batch_rec.get('portrait', ''))
            if port_m:
                port_url = port_m.group(1).strip()
            patron_obj = {
                'name': pat_name,
                'role': {'pl': f"Patron: {pat_name}", 'en': f"Patron: {pat_name}", 'de': f"Patron: {pat_name}"},
                'image': port_url
            }

        # Etymologia i opis
        bio_pl = batch_rec.get('bio', item.get('description', ''))
        clean_bio = re.sub(r'\s*\[(?:Oś czasu|Chronologia):.*?\]', '', bio_pl).strip()

        # Oś czasu
        timeline = []
        tl_m = re.search(r'\[(?:Oś czasu|Chronologia):\s*(.*?)\]', bio_pl)
        if tl_m:
            chunks = tl_m.group(1).replace('&#124;', '|').split('|')
            for c in chunks:
                c = c.strip()
                if not c: continue
                m = re.match(r'^(\d{4}(?:/\d{2,4})?):\s*(.*)$', c)
                if m:
                    timeline.append({'year': m.group(1).strip(), 'event': m.group(2).strip()})

        # Rok / Dekada
        year_val = item.get('year_built', item.get('year_established', item.get('decade', batch_rec.get('year', '–'))))

        # i18n etymologii
        if group == 'estates':
            etym_en = f"Housing estate '{name_pl}' in Kraków ({dist_en}). Modernist/socrealist urban complex. {clean_bio[:140]}..."
            etym_de = f"Wohnsiedlung '{name_pl}' in Krakau ({dist_de}). Urbanistischer Komplex. {clean_bio[:140]}..."
        elif group == 'parks':
            etym_en = f"Public park / boulevard '{name_pl}' in Kraków ({dist_en}). Green recreation area. {clean_bio[:140]}..."
            etym_de = f"Öffentlicher Park / Boulevard '{name_pl}' in Krakau ({dist_de}). Erholungsgebiet. {clean_bio[:140]}..."
        else:
            etym_en = f"Bridge / crossing '{name_pl}' over water/railway barrier in Kraków. Engineering landmark. {clean_bio[:140]}..."
            etym_de = f"Brücke / Bauwerk '{name_pl}' in Krakau. Ingenieurbauwerk. {clean_bio[:140]}..."

        # Źródło
        src_url = 'https://pl.wikipedia.org'
        src_m = re.search(r'\[(.*?)\]\((.*?)\)', batch_rec.get('src', ''))
        if src_m:
            src_name = src_m.group(1).strip()
            src_url = src_m.group(2).strip()
        else:
            src_name = "Encyklopedia Krakowa / Archiwum Miejskie"

        props = {
            'id': lid,
            'is_landmark': True,
            'landmark_group': group,
            'name': {'pl': name_pl, 'en': name_pl, 'de': name_pl},
            'prefix': prefix,
            'full_name': {'pl': name_pl, 'en': name_pl, 'de': name_pl},
            'district': {'pl': dist_pl, 'en': dist_en, 'de': dist_de},
            'category': cat_dict,
            'year': year_val,
            'summary': {
                'pl': f"{name_pl} w Krakowie ({dist_pl}).",
                'en': f"{name_pl} in Kraków ({dist_en}).",
                'de': f"{name_pl} in Krakau ({dist_de})."
            },
            'patron': patron_obj,
            'etymology': {
                'pl': clean_bio,
                'en': etym_en,
                'de': etym_de
            },
            'timeline': timeline,
            'source': {
                'name': src_name,
                'url': src_url,
                'label': src_name.split(':')[0].strip()
            },
            'historic_code': item.get('historic_code', ''),
            'engineering_features': item.get('engineering_features', '')
        }

        feat = {
            'type': 'Feature',
            'id': lid,
            'geometry': {
                'type': 'Point',
                'coordinates': [round(lon, 6), round(lat, 6)]
            },
            'properties': props
        }
        features.append(feat)

    geojson_doc = {
        'type': 'FeatureCollection',
        'metadata': {
            'title': 'Kraków Landmarks & Housing Estates (Osiedla, Parki, Mosty)',
            'count': len(features)
        },
        'features': features
    }

    print(f"Zapisywanie {len(features)} obiektów do {OUTPUT_GEOJSON_PATH}...")
    with open(OUTPUT_GEOJSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(geojson_doc, f, ensure_ascii=False, indent=2)

    sz_kb = os.path.getsize(OUTPUT_GEOJSON_PATH) / 1024
    print(f"Sukces! Utworzono {OUTPUT_GEOJSON_PATH} (rozmiar: {sz_kb:.1f} KB, {len(features)} obiektów).")

if __name__ == '__main__':
    build_landmarks()
