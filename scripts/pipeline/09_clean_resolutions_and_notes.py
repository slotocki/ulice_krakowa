# -*- coding: utf-8 -*-
"""
scripts/pipeline/09_clean_resolutions_and_notes.py

1. Wyłącza fałszywie przypisane uchwały (has_resolution: False) dla 19 ulic,
   gdzie uchwały z BIP dotyczyły parków, rond, przedszkoli, mostów lub petycji.
2. Usuwa wewnętrzne notatki techniczne audytorów ([Uwaga: odrzucono...], [Uwaga: usunięto...])
   z pola etymology.pl, pozostawiając wyłącznie czysty, encyklopedyczny tekst.
3. Zapisuje zaktualizowany plik data/krakow_streets.geojson z zachowaniem limitu wagi (<6.5 MB).
"""

import json
import os
import re

GEOJSON_FILE = 'data/krakow_streets.geojson'

INVALID_RESOLUTION_STREETS = {
    'ulica Aleksandry',
    'ulica Dolina',
    'ulica Heleny',
    'ulica Insurekcji Kościuszkowskiej',
    'ulica Józefa',
    'Rynek Kleparski',
    'ulica Królewska',
    'ulica Nad Sudołem',
    'ulica Nowa',
    'ulica Piasta Kołodzieja',
    'ulica Reduta',
    'ulica Ruczaj',
    'ulica Skwerowa',
    'ulica Stanisława Wyspiańskiego',
    'ulica Stefana Jurczaka',
    'ulica Tadeusza Kościuszki',
    'ulica Wiśniowy Sad',
    'ulica Włodzimierza Tetmajera',
    'ulica do Zamku'
}

def clean_debug_notes(text):
    if not text:
        return text
    # Usuwa notatki zaczynające się od odrzucono/usunięto/skorygowano/poprawiono
    cleaned = re.sub(r'\s*\[Uwaga:\s*(odrzucono|usunięto|skorygowano|poprawiono).*?\]', '', text, flags=re.IGNORECASE)
    # Usuwa podwójne spacje i czyści końce zdań
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    cleaned = cleaned.strip()
    return cleaned

def run_cleaning():
    print(f"Wczytywanie {GEOJSON_FILE}...")
    with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
        geojson = json.load(f)

    features = geojson.get('features', [])
    print(f"Załadowano {len(features)} ulic.")

    disabled_resolutions_count = 0
    notes_cleaned_count = 0

    for feat in features:
        props = feat['properties']
        fn_dict = props.get('full_name')
        fn_pl = fn_dict.get('pl', '') if isinstance(fn_dict, dict) else str(fn_dict)

        # 1. Wyłączenie fałszywych uchwał
        if fn_pl in INVALID_RESOLUTION_STREETS:
            res = props.get('resolution')
            if res and res.get('has_resolution'):
                props['resolution'] = {'has_resolution': False}
                disabled_resolutions_count += 1
                # Jeśli źródło było ustawione na fałszywy BIP, przywróć Supranowicz / RCIN jeśli to ulica historyczna
                if props.get('source', {}).get('label') == 'BIP RMK':
                    props['source'] = {
                        'name': 'E. Supranowicz, „Nazwy ulic Krakowa” (IJP PAN, 1995, ISBN 83-85579-48-6)',
                        'url': 'https://rcin.org.pl/dlibra/publication/43027/edition/24551',
                        'label': 'RCIN PAN'
                    }

        # 2. Czyszczenie notatek debugowych z etymology.pl
        etym = props.get('etymology', {})
        if isinstance(etym, dict) and 'pl' in etym:
            orig_pl = etym['pl']
            cleaned_pl = clean_debug_notes(orig_pl)
            if cleaned_pl != orig_pl:
                etym['pl'] = cleaned_pl
                notes_cleaned_count += 1

    print(f"Wyłączono fałszywe uchwały dla: {disabled_resolutions_count} ulic.")
    print(f"Usunięto notatki techniczne z opisów dla: {notes_cleaned_count} ulic.")

    print("Zapisywanie zaktualizowanego GeoJSON...")
    with open(GEOJSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(',', ':'))

    size_mb = os.path.getsize(GEOJSON_FILE) / (1024 * 1024)
    print(f"Zapisano pomyślnie! Rozmiar pliku: {size_mb:.2f} MB")

if __name__ == '__main__':
    run_cleaning()
