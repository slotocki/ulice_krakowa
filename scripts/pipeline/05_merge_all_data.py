# -*- coding: utf-8 -*-
import json
import os
import re

MASTER_GEOJSON = 'data/krakow_streets.geojson'
SAMPLE_FILE = 'data/streets_sample.json'
PATRONS_CACHE = 'data/cache_patrons.json'
ETYMOLOGY_CACHE = 'data/cache_etymologies.json'
BIP_CACHE = 'data/uchwaly_bip_enriched.json'
CLASSIFIED_FILE = 'data/streets_classified.json'
OUTPUT_FILE = 'data/krakow_streets.geojson'

def normalize_key(s):
    if not s:
        return ''
    s = s.lower().strip()
    s = re.sub(r'^(ulica|ul\.|aleja|al\.|plac|pl\.|osiedle|os\.|rondo|skwer|bulwar|droga|grobla|park)\s+', '', s)
    s = re.sub(r'[^a-ząćęłńóśźż0-9]', '', s)
    return s

def main():
    print('1. Wczytuję plik bazowy GeoJSON z geometriami...', flush=True)
    with open(MASTER_GEOJSON, 'r', encoding='utf-8') as f:
        master_data = json.load(f)

    print('2. Wczytuję dane z poszczególnych modułów pipeline...', flush=True)
    patrons_cache = {}
    if os.path.exists(PATRONS_CACHE):
        with open(PATRONS_CACHE, 'r', encoding='utf-8') as f:
            patrons_cache = json.load(f)

    etym_cache = {}
    if os.path.exists(ETYMOLOGY_CACHE):
        with open(ETYMOLOGY_CACHE, 'r', encoding='utf-8') as f:
            etym_cache = json.load(f)

    classified_map = {}
    if os.path.exists(CLASSIFIED_FILE):
        with open(CLASSIFIED_FILE, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                classified_map[normalize_key(item['raw_name'])] = item

    sample_map = {}
    if os.path.exists(SAMPLE_FILE):
        with open(SAMPLE_FILE, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
            for feat in sample_data.get('features', []):
                p = feat.get('properties', {})
                name_pl = p.get('name', {}).get('pl') if isinstance(p.get('name'), dict) else p.get('name')
                if name_pl:
                    sample_map[normalize_key(name_pl)] = p

    bip_map = {}
    if os.path.exists(BIP_CACHE):
        with open(BIP_CACHE, 'r', encoding='utf-8') as f:
            bip_list = json.load(f)
            for b in bip_list:
                street_k = normalize_key(b.get('street', ''))
                if street_k:
                    bip_map[street_k] = b

    print(f'3. Przeprowadzam fuzję danych dla {len(master_data["features"])} ulic...', flush=True)
    enriched_patrons = 0
    enriched_etym = 0
    enriched_literal = 0
    sample_applied = 0

    for feat in master_data['features']:
        props = feat.get('properties', {})
        raw_name = props.get('name', {}).get('pl') if isinstance(props.get('name'), dict) else props.get('name', '')
        key = normalize_key(raw_name)

        # A. Jeśli ulica znajduje się we wzorcowej próbce, zachowaj jej bogate dane
        if key in sample_map:
            sample_p = sample_map[key]
            # Kopiujemy wzorcowe właściwości, zachowując metrykę długości i ID
            for k, v in sample_p.items():
                if k not in ['id', 'length_meters']:
                    props[k] = v
            sample_applied += 1
            continue

        # B. Pobranie klasyfikacji
        class_info = classified_map.get(key)
        cat = class_info.get('category') if class_info else 'toponymic_general'
        clean_name = class_info.get('clean_name', raw_name) if class_info else raw_name
        nom_name = class_info.get('nominative', clean_name) if class_info else clean_name

        # C. Obsługa patrona (jeśli postać osobowa)
        patron_data = None
        if cat == 'person' and nom_name in patrons_cache:
            p_entry = patrons_cache[nom_name]
            if p_entry.get('found'):
                role_pl = p_entry.get('role', {}).get('pl', '')
                role_en = p_entry.get('role', {}).get('en', '') or role_pl
                role_de = p_entry.get('role', {}).get('de', '') or role_pl

                patron_data = {
                    'name': p_entry.get('name', nom_name),
                    'role': {
                        'pl': role_pl or 'Patron ulicy',
                        'en': role_en or 'Street patron',
                        'de': role_de or 'Namenspatron'
                    },
                    'image': p_entry.get('image', ''),
                    'wiki_url': p_entry.get('wiki_url', f'https://pl.wikipedia.org/wiki/{clean_name}')
                }
                enriched_patrons += 1

                # Uzupełnienie kategorii i roku
                props['category'] = {
                    'pl': 'Postacie historyczne',
                    'en': 'Historical Figures',
                    'de': 'Historische Persönlichkeiten'
                }
                if p_entry.get('birth_year'):
                    props['year'] = p_entry['birth_year']

                p_name = p_entry.get('name', nom_name)
                props['etymology'] = {
                    'pl': f'{raw_name} – patronem ulicy jest {p_name} ({role_pl}).',
                    'en': f'{clean_name} – named in honor of {p_name} ({role_en}).',
                    'de': f'{clean_name} – benannt nach {p_name} ({role_de}).'
                }
            else:
                # Nie znaleziony w wikidata, ale oznaczony jako person
                patron_data = {
                    'name': nom_name,
                    'role': {
                        'pl': 'Postać historyczna / patron',
                        'en': 'Historical figure / patron',
                        'de': 'Historische Persönlichkeit / Patron'
                    },
                    'image': '',
                    'wiki_url': f'https://pl.wikipedia.org/wiki/{clean_name}'
                }
                props['category'] = {
                    'pl': 'Postacie historyczne',
                    'en': 'Historical Figures',
                    'de': 'Historische Persönlichkeiten'
                }
                props['etymology'] = {
                    'pl': f'{raw_name} – ulica upamiętnia postać: {nom_name}.',
                    'en': f'{clean_name} – commemorative street named after {nom_name}.',
                    'de': f'{clean_name} – Gedenkstraße, benannt nach {nom_name}.'
                }

        props['patron'] = patron_data

        # D. Obsługa ulic nieosobowych (Etymologia i Dosłowne znaczenie)
        if not patron_data:
            # Sprawdzenie w cache etymologii
            if raw_name in etym_cache:
                etym_item = etym_cache[raw_name]
                if etym_item.get('etymology'):
                    props['etymology'] = etym_item['etymology']
                    enriched_etym += 1
                if etym_item.get('literal_meaning'):
                    props['literal_meaning'] = etym_item['literal_meaning']
                    enriched_literal += 1

                # Dopasowanie kategorii
                if cat in ['nature_flora', 'nature_fauna']:
                    props['category'] = {
                        'pl': 'Przyroda i Fauna',
                        'en': 'Nature & Wildlife',
                        'de': 'Natur & Tierwelt'
                    }
                elif cat in ['directional', 'directional_regional']:
                    props['category'] = {
                        'pl': 'Trakty kierunkowe',
                        'en': 'Directional Routes',
                        'de': 'Richtungstrassen'
                    }
                elif cat == 'historical_craft':
                    props['category'] = {
                        'pl': 'Dawne rzemiosło i historia',
                        'en': 'Historic Crafts',
                        'de': 'Historisches Handwerk'
                    }
                elif cat == 'event_date':
                    props['category'] = {
                        'pl': 'Wydarzenia i rocznice',
                        'en': 'Historical Events',
                        'de': 'Historische Ereignisse'
                    }

        # E. Dołączenie uchwały BIP jeśli dostępna
        if key in bip_map:
            bip_info = bip_map[key]
            props['resolution'] = {
                'has_resolution': True,
                'resolution_number': bip_info.get('number', ''),
                'date': bip_info.get('date', ''),
                'bip_url': bip_info.get('bip_url', ''),
                'pdf_url': bip_info.get('pdf_url', ''),
                'druk_number': bip_info.get('druk_number', ''),
                'druk_url': bip_info.get('druk_url', ''),
                'justification_excerpt': bip_info.get('justification_excerpt', '')
            }

    print('\n=== WYNIKI SYNTEZY MASTER GEOJSON ===')
    print(f' - Wzorcowe ulice z zachowanymi bogatymi danymi: {sample_applied}')
    print(f' - Wzbogacone o biogramy patronów: {enriched_patrons}')
    print(f' - Wzbogacone o etymologie toponimiczne: {enriched_etym}')
    print(f' - Dodane dosłowne znaczenia (EN/DE): {enriched_literal}')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, ensure_ascii=False)

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f'Zapisano finalny plik {OUTPUT_FILE} ({size_mb:.2f} MB).')

if __name__ == '__main__':
    main()
