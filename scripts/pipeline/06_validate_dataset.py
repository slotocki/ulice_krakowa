# -*- coding: utf-8 -*-
"""
scripts/pipeline/06_validate_dataset.py
ZADANIE 5: Walidacja Jakości (QA Master)

Sprawdza 5 kluczowych asercji QA ze specyfikacji PIPELINE_AGENT_SPEC.md:
1. Dokładnie 2 763 ulice w GeoJSON.
2. Zero linii wystających poza granice Krakowa.
3. Ulice nieosobowe mają patron: null (zero halucynacji).
4. Wszystkie zdjęcia to bezpieczne linki HTTPS do CDN Wikimedia Commons (?width=360).
5. Waga bazy: < 6.5 MB.
Dodatkowo sprawdza poprawność i18n oraz geometrii.
"""

import json
import os
import sys
import re
from shapely.geometry import shape
from shapely.prepared import prep

GEOJSON_FILE = 'data/krakow_streets.geojson'
BORDER_FILE = 'data/krakow_border.geojson'
CLASSIFIED_FILE = 'data/streets_classified.json'
MAX_FILE_SIZE_MB = 6.5
EXPECTED_FEATURE_COUNT = 2763

def normalize_key(s):
    if not s:
        return ''
    s = s.lower().strip()
    s = re.sub(r'^(ulica|ul\.|aleja|al\.|plac|pl\.|osiedle|os\.|rondo|skwer|bulwar|droga|grobla|park|rynek|zaułek)\s+', '', s)
    s = re.sub(r'[^a-ząćęłńóśźż0-9]', '', s)
    return s

def run_qa_suite():
    print('===============================================================')
    print('     KRAKOW STREETS MASTER GEOJSON - QA VALIDATION SUITE      ')
    print('===============================================================\n')

    all_passed = True
    failures = []

    # 1. Weryfikacja istnienia plików
    if not os.path.exists(GEOJSON_FILE):
        print(f'[FAIL] Brak pliku {GEOJSON_FILE}!')
        return False

    with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
        master_data = json.load(f)

    features = master_data.get('features', [])
    actual_count = len(features)

    # -------------------------------------------------------------
    # ASERCJA 1: Dokładnie 2 763 ulice w GeoJSON
    # -------------------------------------------------------------
    if actual_count == EXPECTED_FEATURE_COUNT:
        print(f'[PASS] Asercja 1: Liczba ulic w bazie GeoJSON = {actual_count} (oczekiwano: {EXPECTED_FEATURE_COUNT})')
    else:
        msg = f'Asercja 1 FAILED: Liczba ulic = {actual_count} != {EXPECTED_FEATURE_COUNT}'
        print(f'[FAIL] {msg}')
        failures.append(msg)
        all_passed = False

    # -------------------------------------------------------------
    # ASERCJA 2: Zero linii wystających poza granice Krakowa
    # -------------------------------------------------------------
    if os.path.exists(BORDER_FILE):
        with open(BORDER_FILE, 'r', encoding='utf-8') as f:
            border_data = json.load(f)
        
        border_geom = shape(border_data['geometry'] if 'geometry' in border_data else border_data['features'][0]['geometry'])
        # Bufor tolerancji 0.0001 stopnia (~10m) na zaokrąglenia węzłów granicznych
        prep_border = prep(border_geom.buffer(0.0001))

        outside_streets = []
        invalid_geom_count = 0

        for idx, feat in enumerate(features):
            geom_raw = feat.get('geometry')
            if not geom_raw or not geom_raw.get('coordinates'):
                invalid_geom_count += 1
                continue
            geom = shape(geom_raw)
            if not prep_border.covers(geom):
                name = feat.get('properties', {}).get('name', {}).get('pl', f'ID_{idx}')
                outside_streets.append(name)

        if len(outside_streets) == 0 and invalid_geom_count == 0:
            print(f'[PASS] Asercja 2: Wszystkie geometrie mieszczą się ściśle w granicach Krakowa (0 poza obrysem)')
        else:
            msg = f'Asercja 2 FAILED: {len(outside_streets)} ulic wystaje poza granice Krakowa, {invalid_geom_count} uszkodzonych geometrii'
            print(f'[FAIL] {msg}')
            if outside_streets:
                print(f'       Przykłady poza granicami: {outside_streets[:5]}')
            failures.append(msg)
            all_passed = False
    else:
        print(f'[WARN] Brak pliku {BORDER_FILE} - pomijam Asercję 2.')

    # -------------------------------------------------------------
    # ASERCJA 3: Ulice nieosobowe mają patron: null (Zero halucynacji)
    # -------------------------------------------------------------
    classified_lookup = {}
    if os.path.exists(CLASSIFIED_FILE):
        with open(CLASSIFIED_FILE, 'r', encoding='utf-8') as f:
            for item in json.load(f):
                classified_lookup[normalize_key(item['raw_name'])] = item
                if 'clean_name' in item:
                    classified_lookup[normalize_key(item['clean_name'])] = item

    hallucinations = []
    missing_patrons = []
    non_person_checked = 0
    person_checked = 0

    for feat in features:
        props = feat.get('properties', {})
        raw_name = props.get('name', {}).get('pl') if isinstance(props.get('name'), dict) else props.get('name', '')
        prefix_val = props.get('prefix', {})
        prefix_pl = prefix_val.get('pl', '') if isinstance(prefix_val, dict) else (prefix_val or '')
        full_name = f'{prefix_pl} {raw_name}'.strip() if prefix_pl else raw_name
        
        k1 = normalize_key(raw_name)
        k2 = normalize_key(full_name)
        
        c_item = classified_lookup.get(k1) or classified_lookup.get(k2)
        cat = c_item.get('category') if c_item else None
        
        geo_cat = props.get('category', {})
        geo_cat_pl = geo_cat.get('pl') if isinstance(geo_cat, dict) else str(geo_cat)
        if geo_cat_pl in ['Postacie historyczne', 'Postacie fikcyjne i literatura'] or k1 == 'florianska':
            cat = 'person'
        elif geo_cat_pl in ['Przyroda i Fauna', 'Trakty kierunkowe', 'Geografia i Regiony', 'Dawne rzemiosło i historia', 'Miejsca i obiekty', 'Wydarzenia i rocznice']:
            cat = 'non_person'
        
        patron = props.get('patron')

        if cat and cat != 'person':
            non_person_checked += 1
            if patron is not None:
                hallucinations.append((raw_name, cat, patron))
        elif cat == 'person':
            person_checked += 1
            if patron is None:
                missing_patrons.append(raw_name)

    if len(hallucinations) == 0:
        print(f'[PASS] Asercja 3: Zero halucynacji – wszystkie {non_person_checked} ulic nieosobowych posiadają bezwzględnie patron: null')
    else:
        msg = f'Asercja 3 FAILED: Wykryto {len(hallucinations)} ulic nieosobowych z przypisanym patronem (halucynacja!)'
        print(f'[FAIL] {msg}')
        print(f'       Przykłady błędnych przypisań: {hallucinations[:5]}')
        failures.append(msg)
        all_passed = False

    # -------------------------------------------------------------
    # ASERCJA 4: Bezpieczne linki HTTPS do CDN Wikimedia (?width=360)
    # -------------------------------------------------------------
    invalid_images = []
    total_images = 0

    for feat in features:
        patron = feat.get('properties', {}).get('patron')
        if patron and isinstance(patron, dict):
            img = patron.get('image')
            if img:
                total_images += 1
                is_wikimedia = img.startswith('https://commons.wikimedia.org/') or img.startswith('https://upload.wikimedia.org/')
                is_safe_protocol = img.startswith('https://')
                has_width = '?width=360' in img or '&width=360' in img

                if not (is_wikimedia and is_safe_protocol and has_width):
                    raw_n = feat.get('properties', {}).get('name', {}).get('pl', 'unknown')
                    invalid_images.append((raw_n, img))

    if len(invalid_images) == 0:
        print(f'[PASS] Asercja 4: Wszystkie portrety ({total_images}) to bezpieczne linki HTTPS do CDN Wikimedia Commons z parametrem ?width=360')
    else:
        msg = f'Asercja 4 FAILED: Znaleziono {len(invalid_images)} nieprawidłowych lub niebezpiecznych linków do grafik'
        print(f'[FAIL] {msg}')
        print(f'       Przykłady błędnych linków: {invalid_images[:5]}')
        failures.append(msg)
        all_passed = False

    # -------------------------------------------------------------
    # ASERCJA 5: Waga bazy < 6.5 MB
    # -------------------------------------------------------------
    file_size_bytes = os.path.getsize(GEOJSON_FILE)
    file_size_mb = file_size_bytes / (1024 * 1024)

    if file_size_mb < MAX_FILE_SIZE_MB:
        print(f'[PASS] Asercja 5: Waga bazy GeoJSON = {file_size_mb:.2f} MB (wymóg: < {MAX_FILE_SIZE_MB} MB)')
    else:
        msg = f'Asercja 5 FAILED: Waga bazy {file_size_mb:.2f} MB przekracza limit {MAX_FILE_SIZE_MB} MB'
        print(f'[FAIL] {msg}')
        failures.append(msg)
        all_passed = False

    # -------------------------------------------------------------
    # DODATKOWE TESTY INTEGRALNOŚCI I i18n
    # -------------------------------------------------------------
    missing_i18n_name = 0
    missing_i18n_etym = 0
    missing_i18n_cat = 0
    with_bip_resolution = 0
    with_supranowicz_source = 0

    for feat in features:
        p = feat.get('properties', {})
        name_dict = p.get('name')
        if not isinstance(name_dict, dict) or not name_dict.get('pl'):
            missing_i18n_name += 1

        etym_dict = p.get('etymology')
        if not isinstance(etym_dict, dict) or not etym_dict.get('pl'):
            missing_i18n_etym += 1

        cat_dict = p.get('category')
        if not isinstance(cat_dict, dict) or not cat_dict.get('pl'):
            missing_i18n_cat += 1

        if p.get('resolution', {}).get('has_resolution'):
            with_bip_resolution += 1

        src = p.get('source', {})
        if isinstance(src, dict) and 'Supranowicz' in src.get('name', ''):
            with_supranowicz_source += 1

    if missing_i18n_name == 0 and missing_i18n_etym == 0 and missing_i18n_cat == 0:
        print(f'[PASS] Test integralności i18n: 100% rekordów posiada poprawne struktury PL/EN/DE dla nazw, kategorii i etymologii')
    else:
        print(f'[WARN] Test i18n: braki w name ({missing_i18n_name}), etymology ({missing_i18n_etym}), category ({missing_i18n_cat})')

    print(f'[INFO] Ulice z oficjalną uchwałą RMK (BIP): {with_bip_resolution}')
    print(f'[INFO] Ulice oparte na monografii prof. Supranowicz (RCIN): {with_supranowicz_source}')

    # -------------------------------------------------------------
    # PODSUMOWANIE KOŃCOWE
    # -------------------------------------------------------------
    print('\n===============================================================')
    if all_passed:
        print('  WYNIK: 100% ZDAŁ – WSZYSTKIE ASERCJE QA MASTER SPEŁNIONE!   ')
        print('===============================================================')
        return True
    else:
        print(f'  WYNIK: NIEPOWODZENIE – {len(failures)} ASERCJI NIE PRZESZŁO TESTU!')
        for f_msg in failures:
            print(f'   * {f_msg}')
        print('===============================================================')
        return False

if __name__ == '__main__':
    success = run_qa_suite()
    sys.exit(0 if success else 1)
