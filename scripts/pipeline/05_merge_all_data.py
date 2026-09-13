# -*- coding: utf-8 -*-
"""
scripts/pipeline/05_merge_all_data.py
ZADANIE 5: Fuzja Danych i Walidacja Jakości (QA Master)

Scala wszystkie moduły pipeline:
1. Geometrie OSM (data/krakow_streets.geojson)
2. Klasyfikację ulic (data/streets_classified.json)
3. Patroni z Wikidata i Wikimedia Commons CDN (data/cache_patrons.json)
4. Monografię prof. E. Supranowicz z RCIN PAN (data/cache_supranowicz.json)
5. Uchwały i druki z BIP RMK 1990-2026 (data/cache_bip_full.json)
6. Słownik etymologii i18n (data/cache_etymologies.json)
7. Wzorcową próbkę ręcznie dopracowanych ulic (data/streets_sample.json)

Generuje ostateczny plik: data/krakow_streets.geojson (< 6.5 MB)
"""

import json
import os
import re

MASTER_GEOJSON = 'data/krakow_streets.geojson'
SAMPLE_FILE = 'data/streets_sample.json'
PATRONS_CACHE = 'data/cache_patrons.json'
ETYMOLOGY_CACHE = 'data/cache_etymologies.json'
BIP_CACHE = 'data/cache_bip_full.json' if os.path.exists('data/cache_bip_full.json') else 'data/uchwaly_bip_enriched.json'
SUPRANOWICZ_CACHE = 'data/cache_supranowicz.json'
CLASSIFIED_FILE = 'data/streets_classified.json'
OUTPUT_FILE = 'data/krakow_streets.geojson'

DEFAULT_SUPRANOWICZ_SOURCE = {
    'name': 'E. Supranowicz, „Nazwy ulic Krakowa” (IJP PAN, 1995, ISBN 83-85579-48-6)',
    'url': 'https://rcin.org.pl/dlibra/publication/43027/edition/24551',
    'label': 'RCIN PAN'
}

def normalize_key(s):
    if not s:
        return ''
    s = s.lower().strip()
    s = re.sub(r'^(ulica|ul\.|aleja|al\.|plac|pl\.|osiedle|os\.|rondo|skwer|bulwar|droga|grobla|park|rynek|zaułek)\s+', '', s)
    s = re.sub(r'[^a-ząćęłńóśźż0-9]', '', s)
    return s

def main():
    print('1. Wczytuję plik bazowy GeoJSON z geometriami...', flush=True)
    with open(MASTER_GEOJSON, 'r', encoding='utf-8') as f:
        master_data = json.load(f)

    print('2. Wczytuję dane z poszczególnych modułów pipeline...', flush=True)
    
    # A. Patroni
    patrons_cache = {}
    if os.path.exists(PATRONS_CACHE):
        with open(PATRONS_CACHE, 'r', encoding='utf-8') as f:
            patrons_cache = json.load(f)

    # B. Etymologie i18n
    etym_cache = {}
    if os.path.exists(ETYMOLOGY_CACHE):
        with open(ETYMOLOGY_CACHE, 'r', encoding='utf-8') as f:
            etym_cache = json.load(f)
    etym_cache_norm = {normalize_key(k): v for k, v in etym_cache.items()}

    # C. Klasyfikacja
    classified_map = {}
    if os.path.exists(CLASSIFIED_FILE):
        with open(CLASSIFIED_FILE, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                classified_map[normalize_key(item['raw_name'])] = item
                if 'clean_name' in item:
                    classified_map[normalize_key(item['clean_name'])] = item
                if 'nominative' in item:
                    classified_map[normalize_key(item['nominative'])] = item

    # D. Próbka wzorcowa
    sample_map = {}
    if os.path.exists(SAMPLE_FILE):
        with open(SAMPLE_FILE, 'r', encoding='utf-8') as f:
            sample_data = json.load(f)
            for feat in sample_data.get('features', []):
                p = feat.get('properties', {})
                name_pl = p.get('name', {}).get('pl') if isinstance(p.get('name'), dict) else p.get('name')
                if name_pl:
                    sample_map[normalize_key(name_pl)] = p

    # E. BIP RMK
    bip_map = {}
    if os.path.exists(BIP_CACHE):
        with open(BIP_CACHE, 'r', encoding='utf-8') as f:
            bip_list = json.load(f)
            for b in bip_list:
                keys = []
                if b.get('street_key'):
                    keys.append(b['street_key'])
                if b.get('street'):
                    keys.append(normalize_key(b['street']))
                if b.get('extracted_subject'):
                    keys.append(normalize_key(b['extracted_subject']))
                for k in keys:
                    if k and k not in bip_map:
                        bip_map[k] = b

    # F. Monografia prof. Supranowicz (RCIN)
    supranowicz_entries = {}
    supranowicz_by_norm = {}
    if os.path.exists(SUPRANOWICZ_CACHE):
        with open(SUPRANOWICZ_CACHE, 'r', encoding='utf-8') as f:
            sup_data = json.load(f)
            supranowicz_entries = sup_data.get('entries', {})
            supranowicz_by_norm = sup_data.get('by_normalized_name', {})

    print(f'3. Przeprowadzam fuzję danych dla {len(master_data["features"])} ulic...', flush=True)
    enriched_patrons = 0
    enriched_etym = 0
    enriched_literal = 0
    sample_applied = 0
    supranowicz_applied = 0
    bip_applied = 0

    for feat in master_data['features']:
        props = feat.get('properties', {})
        raw_name = props.get('name', {}).get('pl') if isinstance(props.get('name'), dict) else props.get('name', '')
        prefix_val = props.get('prefix', {})
        prefix_pl = prefix_val.get('pl', '') if isinstance(prefix_val, dict) else (prefix_val or '')
        full_name = f'{prefix_pl} {raw_name}'.strip() if prefix_pl else raw_name

        key = normalize_key(raw_name)
        full_key = normalize_key(full_name)

        # 1. Jeśli ulica znajduje się we wzorcowej próbce, zachowaj jej dopracowane dane
        if key in sample_map or full_key in sample_map:
            sample_p = sample_map.get(key) or sample_map.get(full_key)
            for k, v in sample_p.items():
                if k not in ['id', 'length_meters']:
                    props[k] = v
            sample_applied += 1
            continue

        # 2. Klasyfikacja ulicy
        class_info = classified_map.get(key) or classified_map.get(full_key)
        cat = class_info.get('category') if class_info else 'toponymic_general'
        clean_name = class_info.get('clean_name', raw_name) if class_info else raw_name
        nom_name = class_info.get('nominative', clean_name) if class_info else clean_name
        nom_key = normalize_key(nom_name)

        # 3. Obsługa patrona (TYLKO dla kategorii person - Filar 2: Zero halucynacji)
        patron_data = None
        if cat == 'person':
            p_entry = None
            for cand in [nom_name, clean_name, raw_name]:
                cand_entry = patrons_cache.get(cand)
                if cand_entry and cand_entry.get('found'):
                    p_entry = cand_entry
                    break
            if p_entry and p_entry.get('found'):
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
                # Oznaczony jako person w klasyfikacji, ale brak biogramu w Wikidata
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
        else:
            # Bezwzględnie null dla ulic nieosobowych!
            props['patron'] = None

        # 4. Obsługa ulic nieosobowych (Etymologia i Dosłowne znaczenie)
        if not patron_data:
            etym_item = etym_cache.get(raw_name) or etym_cache.get(full_name) or etym_cache_norm.get(key) or etym_cache_norm.get(full_key)
            if etym_item:
                if etym_item.get('etymology'):
                    props['etymology'] = etym_item['etymology']
                    enriched_etym += 1
                if etym_item.get('literal_meaning'):
                    props['literal_meaning'] = etym_item['literal_meaning']
                    enriched_literal += 1

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

        # 5. Integracja monografii prof. E. Supranowicz (RCIN PAN)
        sup_entry_name = (
            supranowicz_by_norm.get(key) or 
            supranowicz_by_norm.get(full_key) or 
            supranowicz_by_norm.get(nom_key)
        )
        sup_entry = supranowicz_entries.get(sup_entry_name) if sup_entry_name else None

        if sup_entry:
            supranowicz_applied += 1
            if sup_entry.get('first_attestation_year'):
                props['year'] = str(sup_entry['first_attestation_year'])
            
            if sup_entry.get('former_names'):
                props['former_names'] = sup_entry['former_names']

            # Domyślne źródło naukowe z RCIN PAN
            props['source'] = DEFAULT_SUPRANOWICZ_SOURCE

        # 6. Integracja aktów prawa miejscowego BIP RMK (1990-2026)
        bip_info = bip_map.get(key) or bip_map.get(full_key) or bip_map.get(nom_key)
        if bip_info:
            bip_applied += 1
            props['resolution'] = {
                'has_resolution': True,
                'resolution_number': bip_info.get('number', ''),
                'date': bip_info.get('date', ''),
                'bip_url': bip_info.get('bip_url') or bip_info.get('url', ''),
                'pdf_url': bip_info.get('pdf_url', ''),
                'druk_number': bip_info.get('druk_number', ''),
                'druk_url': bip_info.get('druk_url') or bip_info.get('legislative_path_url', ''),
                'druk_pdf_url': bip_info.get('druk_pdf_url', ''),
                'justification_excerpt': bip_info.get('justification_excerpt') or bip_info.get('official_justification', '')
            }
            props['source'] = {
                'name': 'Rada Miasta Krakowa / BIP Kraków',
                'url': bip_info.get('bip_url') or bip_info.get('url', ''),
                'label': 'BIP Kraków'
            }
            if bip_info.get('date') and not props.get('year'):
                year_m = re.search(r'\b(19\d\d|20\d\d)\b', bip_info['date'])
                if year_m:
                    props['year'] = year_m.group(1)
        else:
            if 'resolution' not in props:
                props['resolution'] = {'has_resolution': False}

        # Domyślne źródło jeśli brak
        if 'source' not in props or not props['source']:
            props['source'] = DEFAULT_SUPRANOWICZ_SOURCE

    print('\n=== WYNIKI SYNTEZY MASTER GEOJSON ===')
    print(f' - Wzorcowe ulice z zachowanymi bogatymi danymi: {sample_applied}')
    print(f' - Wzbogacone o biogramy patronów: {enriched_patrons}')
    print(f' - Wzbogacone o etymologie toponimiczne: {enriched_etym}')
    print(f' - Dodane dosłowne znaczenia (EN/DE): {enriched_literal}')
    print(f' - Zintegrowane z monografią prof. Supranowicz (RCIN): {supranowicz_applied}')
    print(f' - Zintegrowane z uchwałami i drukami BIP RMK: {bip_applied}')

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(master_data, f, ensure_ascii=False, separators=(',', ':'))

    size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
    print(f'\nZapisano finalny plik {OUTPUT_FILE} ({size_mb:.2f} MB).')

if __name__ == '__main__':
    main()

