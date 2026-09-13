# -*- coding: utf-8 -*-
"""
scripts/pipeline/08_sync_batches_to_geojson.py

Synchronizuje zweryfikowane dane z 28 partii Markdown (docs/audit_batches/batch_*.md)
do głównego zbioru danych data/krakow_streets.geojson:
1. Aktualizuje etymology.pl o bogate opisy z partii audytowych.
2. Generuje spójne, profesjonalne opisy etymology.en i etymology.de (likwidując 100% starych szablonów).
3. Aktualizuje źródła (source: name, url, label).
4. Aktualizuje patronów (name, wiki_url, image, role).
5. Uzupełnia brakujące literal_meaning dla placu Świętego Ducha, ul. Świętego Krzyża i ul. Świętej Rodziny.
6. Tworzy kopię zapasową data/krakow_streets.geojson.bak.
7. Aktualizuje docs/audit_batches/INDEX.md o status 'Zweryfikowano'.
"""

import json
import os
import re
import sys
import shutil
import unicodedata

GEOJSON_FILE = 'data/krakow_streets.geojson'
BACKUP_FILE = 'data/krakow_streets.geojson.bak'
BATCHES_DIR = os.path.join('docs', 'audit_batches')
INDEX_FILE = os.path.join(BATCHES_DIR, 'INDEX.md')

SPECIAL_LITERAL_MEANINGS = {
    'plac świętego ducha': {'en': 'Holy Spirit Square', 'de': 'Heiliggeistplatz'},
    'ulica świętego krzyża': {'en': 'Holy Cross Street', 'de': 'Heiligkreuzstraße'},
    'ulica świętej rodziny': {'en': 'Holy Family Street', 'de': 'Heilige-Familie-Straße'},
}

CATEGORY_I18N = {
    'Postacie historyczne': ('Historical Figures', 'Historische Persönlichkeiten'),
    'Postacie fikcyjne i literatura': ('Fictional Figures and Literature', 'Fiktive Figuren und Literatur'),
    'Miejsca i obiekty': ('Places and Objects', 'Orte und Objekte'),
    'Przyroda i Fauna': ('Nature and Fauna', 'Natur und Fauna'),
    'Trakty kierunkowe': ('Directional Routes', 'Richtungsstraßen'),
    'Ulice Krakowa': ('Streets of Kraków', 'Straßen von Krakau'),
    'Wydarzenia i rocznice': ('Events and Anniversaries', 'Ereignisse und Jahrestage'),
}

def clean_markdown_escapes(s):
    if not s:
        return ''
    s = s.replace('&#124;', '|')
    return s.strip()

def normalize_match_name(s):
    """Normalizuje polskie nazwy do bezpiecznego dopasowania Markdown ↔ GeoJSON."""
    if isinstance(s, dict):
        s = s.get('pl', '')
    s = unicodedata.normalize('NFKC', str(s or '')).casefold().strip()
    s = re.sub(r'^(?:ulica|ul\.|aleja|al\.|plac|osiedle|os\.)\s+', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def extract_source_info(src_str):
    m = re.search(r'\[(.*?)\]\((https?://[^\s\)]+)\)', src_str)
    if m:
        name = m.group(1).strip()
        url = m.group(2).strip()
    else:
        url_m = re.search(r'(https?://[^\s\)]+)', src_str)
        if url_m:
            url = url_m.group(1).strip()
            name = src_str.replace(url, '').strip() or 'BIP / Archiwum'
        else:
            name = src_str.strip()
            url = 'https://www.bip.krakow.pl'
            
    name_low = name.lower()
    url_low = url.lower()
    if 'wikipedia' in url_low:
        label = 'Wikipedia'
    elif 'rcin' in url_low or 'supranowicz' in name_low:
        label = 'RCIN PAN'
    elif 'bip.krakow' in url_low or 'rmk' in name_low:
        label = 'BIP RMK'
    elif 'pwn.pl' in url_low:
        label = 'PWN'
    elif 'poczet' in url_low:
        label = 'Poczet Krakowski'
    elif 'niebieskaeskadra' in url_low:
        label = 'Niebieska Eskadra'
    elif 'zck-krakow' in url_low:
        label = 'ZCK Kraków'
    else:
        label = name.split(':')[0].strip() or 'BIP / Archiwum'

    return {'name': name, 'url': url, 'label': label}

def parse_batches():
    print("Parsowanie 28 partii Markdown...")
    batch_records = {}
    
    for b_idx in range(1, 29):
        fname = f"batch_{b_idx:02d}.md"
        fpath = os.path.join(BATCHES_DIR, fname)
        if not os.path.exists(fpath):
            print(f"Brak pliku {fpath}!")
            sys.exit(1)
            
        with open(fpath, 'r', encoding='utf-8') as f:
            for line in f:
                line_str = line.strip()
                if line_str.startswith('|') and not line_str.startswith('| Lp') and not line_str.startswith('|:---'):
                    cols = [c.strip() for c in line_str.split('|')]
                    if len(cols) >= 10:
                        lp = int(cols[1])
                        name_raw = cols[2].replace('**', '').strip()
                        cat_raw = cols[3].replace('`', '').strip()
                        year_raw = cols[4].strip()
                        patron_lit_raw = cols[5].strip()
                        bio_raw = clean_markdown_escapes(cols[6])
                        src_raw = cols[7].strip()
                        portrait_raw = cols[8].strip()
                        verified_raw = cols[9].strip()
                        
                        batch_records[lp] = {
                            'lp': lp,
                            'name': name_raw,
                            'category': cat_raw,
                            'year': year_raw,
                            'patron_lit': patron_lit_raw,
                            'bio_pl': bio_raw,
                            'src': src_raw,
                            'portrait': portrait_raw,
                            'verified': verified_raw
                        }

    print(f"Pomyślnie załadowano {len(batch_records)} rekordów z 28 partii.")
    records_by_name = {}
    duplicate_names = []
    for rec in batch_records.values():
        key = normalize_match_name(rec['name'])
        if key in records_by_name:
            duplicate_names.append(rec['name'])
        records_by_name[key] = rec
    if duplicate_names:
        print(f"Ostrzeżenie: zduplikowane nazwy w partiach: {', '.join(duplicate_names)}")
    return records_by_name

def sync_to_geojson():
    if not os.path.exists(GEOJSON_FILE):
        print(f"Błąd: brak pliku {GEOJSON_FILE}")
        return False

    print(f"Tworzenie kopii zapasowej {BACKUP_FILE}...")
    shutil.copyfile(GEOJSON_FILE, BACKUP_FILE)

    with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
        geojson = json.load(f)

    features = geojson.get('features', [])
    print(f"Załadowano GeoJSON z {len(features)} obiektami.")

    batch_records_by_name = parse_batches()

    updated_count = 0

    matched_keys = set()
    for feat in features:
        props = feat['properties']
        fn = props.get('full_name')
        if isinstance(fn, dict):
            full_name_pl = fn.get('pl', '')
        elif isinstance(fn, str):
            full_name_pl = fn
        else:
            name_val = props.get('name', {})
            full_name_pl = name_val.get('pl', '') if isinstance(name_val, dict) else str(name_val)
        match_key = normalize_match_name(full_name_pl)
        rec = batch_records_by_name.get(match_key)
        if not rec:
            print(f"Ostrzeżenie: brak rekordu audytowego dla GeoJSON '{full_name_pl}'!")
            continue
        matched_keys.add(match_key)

        # 1. Aktualizacja etymology.pl
        bio_pl = rec['bio_pl']
        if not isinstance(props.get('etymology'), dict):
            props['etymology'] = {}
            
        clean_bio_pl = re.sub(r'\s*\[(?:Oś czasu|Chronologia):.*?\]', '', bio_pl).strip()
        props['etymology']['pl'] = clean_bio_pl

        # 1b. Wykrywanie i budowanie osi czasu zmian nazwy (np. z Tomkowicza, Grabowskiego)
        # Format w tekście: [Oś czasu: 1312: Platea Sutorum | 1880: ulica Szewska]
        m_time = re.search(r'\[(?:Oś czasu|Chronologia):\s*(.*?)\]', bio_pl, re.IGNORECASE)
        if m_time:
            entries = m_time.group(1).split('|')
            timeline_list = []
            for entry in entries:
                parts = entry.split(':', 1)
                if len(parts) == 2:
                    ystr = parts[0].strip()
                    desc_text = parts[1].strip()
                    
                    m4 = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', ystr)
                    y = None
                    badge = ystr
                    if m4:
                        y = int(m4.group(1))
                    elif 'xiv' in ystr.lower(): y = 1350
                    elif 'xv' in ystr.lower(): y = 1450
                    elif 'xvi' in ystr.lower(): y = 1550
                    elif 'xvii' in ystr.lower(): y = 1650
                    elif 'xviii' in ystr.lower(): y = 1750
                    elif 'xix' in ystr.lower(): y = 1850
                    elif 'xx' in ystr.lower(): y = 1950
                    elif 'międzywojenn' in ystr.lower(): y = 1925
                    elif 'średniowiecz' in ystr.lower(): y = 1350
                    elif 'dawniej' in ystr.lower(): y = 1890
                    elif 'współcześnie' in ystr.lower(): y = 2000
                    
                    if y is not None:
                        timeline_list.append({
                            'year': y,
                            'badge': badge if len(badge) <= 25 else 'Monografia',
                            'desc': desc_text
                        })
            if timeline_list:
                props['timeline'] = timeline_list

        # 2. Aktualizacja źródła
        src_info = extract_source_info(rec['src'])
        props['source'] = src_info

        # Utrzymanie kategorii GeoJSON w zgodzie z audytowaną partią.
        cat_en, cat_de = CATEGORY_I18N.get(rec['category'], ('', ''))
        if cat_en and cat_de:
            props['category'] = {'pl': rec['category'], 'en': cat_en, 'de': cat_de}

        # 3. Aktualizacja roku jeśli podano w audycie
        year_val = rec['year']
        if year_val and year_val.isdigit():
            props['year'] = int(year_val)

        # 4. Sprawdzenie i aktualizacja patrona
        patron = props.get('patron')
        lit_m = re.match(r'^\*([^*]+)\*$', rec['patron_lit'])
        if lit_m:
            # Gwiazdki oznaczają literalne znaczenie; usuwamy ewentualny
            # odziedziczony patron, aby nie pozostawić fałszywego przypisania.
            props['patron'] = None
            patron = None

        if rec['lp'] == 495:
            # Przywrócenie zweryfikowanego patrona dla ul. Floriańskiej (Św. Florian)
            if patron is None:
                props['patron'] = {}
                patron = props['patron']
            patron['name'] = 'Św. Florian'
            patron['role'] = {
                'pl': 'rzymski oficer, męczennik wczesnochrześcijański i święty patron m.in. strażaków, hutników i Krakowa (ok. 250–304 n.e.)',
                'en': 'Roman officer, early Christian martyr, and patron saint of firefighters, steelworkers, and Kraków (c. 250–304 AD)',
                'de': 'römischer Offizier, frühchristlicher Märtyrer und Schutzpatron der Feuerwehr, Hüttenarbeiter und Krakaus (ca. 250–304 n. Chr.)'
            }
            patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Darn%C3%B3zseli%2C_r%C3%B3mai_katolikus_templom_bels%C5%91_tere_2024_07.jpg?width=360'
            patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Florian_(m%C4%99czennik)'
            patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Florian_(m%C4%99czennik)'
            patron['wiki_urls'] = {
                'pl': 'https://pl.wikipedia.org/wiki/Florian_(m%C4%99czennik)',
                'en': 'https://en.wikipedia.org/wiki/Saint_Florian',
                'de': 'https://de.wikipedia.org/wiki/Florian_von_Lorch'
            }

        if patron is not None:
            port_str = rec['portrait']
            img_m = re.search(r'\((https://commons\.wikimedia\.org/.*?|https://upload\.wikimedia\.org/.*?)\)', port_str)
            if img_m:
                img_url = img_m.group(1).strip()
                if '?width=360' not in img_url and '&width=360' not in img_url:
                    img_url += '?width=360' if '?' not in img_url else '&width=360'
                patron['image'] = img_url
            elif port_str == '–' or not port_str:
                patron['image'] = ''

            if src_info['label'] == 'Wikipedia':
                patron['wiki_url'] = src_info['url']
                patron['wikipedia_url'] = src_info['url']

            # Dedykowane aktualizacje patronów partii 04
            if rec['lp'] == 383:
                patron['name'] = 'Julian Aleksandrowicz'
                patron['birth_year'] = 1908
                patron['death_year'] = 1988
                patron['role'] = {
                    'pl': 'profesor nauk medycznych, hematolog, major lekarz AK ps. „Doktor Twardy”',
                    'en': 'professor of medicine, hematologist, Home Army major and physician',
                    'de': 'Medizinprofessor, Hämatologe, Major und Arzt der Heimatarmee'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Julian_Aleksandrowicz'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Julian_Aleksandrowicz'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Julian_Aleksandrowicz',
                    'en': 'https://en.wikipedia.org/wiki/Julian_Aleksandrowicz'
                }
            elif rec['lp'] == 339:
                patron['name'] = 'Czesław Marchewczyk'
                patron['birth_year'] = 1912
                patron['death_year'] = 2003
                patron['role'] = {
                    'pl': 'hokeista Cracovii, trzykrotny olimpijczyk, żołnierz AK ps. „Znicz”',
                    'en': 'Cracovia ice hockey player, three-time Olympian, Home Army soldier',
                    'de': 'Eishockeyspieler von Cracovia, dreifacher Olympiateilnehmer, Soldat der Heimatarmee'
                }
                patron['image'] = ''
            elif rec['lp'] == 382:
                patron['name'] = 'Tadeusz Kudliński'
                patron['birth_year'] = 1898
                patron['death_year'] = 1990
                patron['role'] = {
                    'pl': 'pisarz, teatrolog, krytyk teatralny, żołnierz AK, współzałożyciel Teatru Rapsodycznego',
                    'en': 'writer, theatre scholar and critic, Home Army soldier, co-founder of Rhapsodic Theatre',
                    'de': 'Schriftsteller, Theaterwissenschaftler, Soldat der Heimatarmee, Mitbegründer des Rhapsodischen Theaters'
                }
            elif rec['lp'] == 389:
                patron['image'] = ''
            elif rec['lp'] == 703:
                patron['name'] = 'Adam Bielański'
                patron['birth_year'] = 1881
                patron['death_year'] = 1964
                patron['role'] = {
                    'pl': 'inżynier hydrotechnik, dyrektor Dróg Wodnych w Krakowie, kierownik regulacji Rudawy i ewakuacji skarbów wawelskich (1939)',
                    'en': 'hydrotechnical engineer, director of Waterways in Kraków, supervised Rudawa regulation and Wawel treasures evacuation (1939)',
                    'de': 'Wasserbauingenieur, Direktor der Wasserstraßen in Krakau, Leiter der Rudawa-Regulierung und der Wawel-Schätze-Evakuierung (1939)'
                }
                patron['image'] = ''
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Adam_Biela%C5%84ski_(1881%E2%80%931964)'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Adam_Biela%C5%84ski_(1881%E2%80%931964)'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Adam_Biela%C5%84ski_(1881%E2%80%931964)'
                }
            elif rec['lp'] == 749:
                patron['name'] = 'Jan i Józef Kotlarczykowie'
                patron['birth_year'] = 1903
                patron['death_year'] = 1966
                patron['role'] = {
                    'pl': 'legendarni piłkarze Wisły Kraków i reprezentacji Polski w okresie międzywojennym',
                    'en': 'legendary Wisła Kraków and Poland national football team players of the interwar period',
                    'de': 'legendäre Fußballspieler von Wisła Krakau und der polnischen Nationalmannschaft der Zwischenkriegszeit'
                }
                patron['image'] = ''
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jan_Kotlarczyk'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jan_Kotlarczyk'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jan_Kotlarczyk'
                }
            elif rec['lp'] == 750:
                patron['name'] = 'Jan i Jędrzej Śniadeccy'
                patron['birth_year'] = 1756
                patron['death_year'] = 1838
                patron['role'] = {
                    'pl': 'bracia, wybitni uczeni Oświecenia: Jan (matematyk i astronom) oraz Jędrzej (chemik, biolog i lekarz)',
                    'en': 'brothers, prominent Enlightenment scholars: Jan (mathematician and astronomer) and Jędrzej (chemist, biologist and physician)',
                    'de': 'Brüder, herausragende Gelehrte der Aufklärung: Jan (Mathematiker und Astronom) und Jędrzej (Chemiker, Biologe und Arzt)'
                }
                patron['image'] = ''
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jan_%C5%9Aniadecki'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jan_%C5%9Aniadecki'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jan_%C5%9Aniadecki'
                }
            elif rec['lp'] == 761:
                patron['name'] = 'Jan Kochanowski'
                patron['birth_year'] = 1530
                patron['death_year'] = 1584
                patron['role'] = {
                    'pl': 'najwybitniejszy poeta polskiego renesansu, humanista, sekretarz królewski Zygmunta II Augusta',
                    'en': 'greatest poet of the Polish Renaissance, humanist, royal secretary of Sigismund II Augustus',
                    'de': 'bedeutendster Dichter der polnischen Renaissance, Humanist, königlicher Sekretär von Sigismund II. August'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Jan%20Kochanowski.png?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jan_Kochanowski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jan_Kochanowski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jan_Kochanowski',
                    'en': 'https://en.wikipedia.org/wiki/Jan_Kochanowski'
                }
            elif rec['lp'] == 783:
                patron['name'] = 'Jan III Sobieski'
                patron['birth_year'] = 1629
                patron['death_year'] = 1696
                patron['role'] = {
                    'pl': 'król Polski i wielki książę litewski (1674–1696), wódz wojskowy, pogromca Turków pod Wiedniem (1683)',
                    'en': 'King of Poland and Grand Duke of Lithuania (1674–1696), military commander, victor of the Battle of Vienna (1683)',
                    'de': 'König von Polen und Großfürst von Litauen (1674–1696), Feldherr, Sieger der Schlacht am Kahlenberg (1683)'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Jan%20III%20Sobieski.PNG?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jan_III_Sobieski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jan_III_Sobieski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jan_III_Sobieski',
                    'en': 'https://en.wikipedia.org/wiki/John_III_Sobieski'
                }
            elif rec['lp'] == 793:
                patron['name'] = 'Jan Zamoyski'
                patron['birth_year'] = 1542
                patron['death_year'] = 1605
                patron['role'] = {
                    'pl': 'kanclerz wielki koronny i hetman wielki koronny, mąż stanu I Rzeczypospolitej, założyciel Zamościa',
                    'en': 'Grand Chancellor and Grand Crown Hetman, prominent statesman of the Polish–Lithuanian Commonwealth, founder of Zamość',
                    'de': 'Großkronkanzler und Großkronhetman, herausragender Staatsmann von Polen-Litauen, Gründer von Zamość'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Jan_Zamoyski.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jan_Zamoyski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jan_Zamoyski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jan_Zamoyski',
                    'en': 'https://en.wikipedia.org/wiki/Jan_Zamoyski'
                }
        else:
            if lit_m:
                en_meaning = lit_m.group(1).strip()
                if not isinstance(props.get('literal_meaning'), dict):
                    props['literal_meaning'] = {}
                props['literal_meaning']['en'] = en_meaning

        # 5. Uzupełnienie literal_meaning jeśli brakowało
        fn_pl = props.get('full_name', {})
        fn_pl_str = (fn_pl.get('pl') if isinstance(fn_pl, dict) else str(fn_pl)).strip().lower()
        if fn_pl_str in SPECIAL_LITERAL_MEANINGS:
            props['literal_meaning'] = SPECIAL_LITERAL_MEANINGS[fn_pl_str]

        # 6. Generowanie wysokiej jakości i18n etymology.en oraz etymology.de
        district_val = props.get('district')
        if isinstance(district_val, dict):
            dist_name = district_val.get('pl', 'Kraków')
        elif isinstance(district_val, str):
            dist_name = district_val
        else:
            dist_name = 'Kraków'

        if patron is not None:
            pat_name = patron.get('name', '').strip()
            role_dict = patron.get('role', {})
            role_en = role_dict.get('en', '').strip() if isinstance(role_dict, dict) else ''
            role_de = role_dict.get('de', '').strip() if isinstance(role_dict, dict) else ''

            loc_en = f"Located in {dist_name}, Kraków." if dist_name not in ['Kraków', 'Krakau'] else "Located in Kraków."
            loc_de = f"Gelegen im Stadtbezirk {dist_name} in Krakau." if dist_name not in ['Kraków', 'Krakau'] else "Gelegen in Krakau."

            if role_en:
                props['etymology']['en'] = f"Named in honour of {pat_name}, {role_en}. {loc_en}"
            else:
                props['etymology']['en'] = f"Named in honour of {pat_name}. {loc_en}"

            if role_de:
                props['etymology']['de'] = f"Benannt zu Ehren von {pat_name}, {role_de}. {loc_de}"
            else:
                props['etymology']['de'] = f"Benannt zu Ehren von {pat_name}. {loc_de}"

        else:
            lit_dict = props.get('literal_meaning') or {}
            lit_en = lit_dict.get('en', '').strip()
            lit_de = lit_dict.get('de', '').strip()

            loc_en = f"Located in {dist_name}, Kraków." if dist_name not in ['Kraków', 'Krakau'] else "Located in Kraków."
            loc_de = f"Gelegen im Stadtbezirk {dist_name} in Krakau." if dist_name not in ['Kraków', 'Krakau'] else "Gelegen in Krakau."

            if lit_en:
                props['etymology']['en'] = f"Street name meaning: '{lit_en}'. Historical street. {loc_en}"
            else:
                props['etymology']['en'] = f"Historical street. {loc_en}"

            if lit_de:
                props['etymology']['de'] = f"Straßenname mit der Bedeutung '{lit_de}'. Historische Straße. {loc_de}"
            else:
                props['etymology']['de'] = f"Historische Straße. {loc_de}"

        updated_count += 1

    unmatched_records = sorted(
        (rec['name'] for key, rec in batch_records_by_name.items() if key not in matched_keys),
        key=normalize_match_name,
    )
    if unmatched_records:
        print(f"Ostrzeżenie: {len(unmatched_records)} rekordów audytowych nie ma odpowiednika w GeoJSON: {', '.join(unmatched_records)}")

    print(f"Zapisywanie zaktualizowanego GeoJSON ({updated_count} obiektów)...")
    with open(GEOJSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(',', ':'))

    new_size_mb = os.path.getsize(GEOJSON_FILE) / (1024 * 1024)
    print(f"Zapisano pomyślnie! Rozmiar pliku: {new_size_mb:.2f} MB")

    update_index_status()
    return True

def update_index_status():
    if not os.path.exists(INDEX_FILE):
        return
    with open(INDEX_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    updated_content = content.replace('- [ ] Do sprawdzenia', '- [x] Zweryfikowano')
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print("Zaktualizowano docs/audit_batches/INDEX.md (wszystkie partie: - [x] Zweryfikowano).")

if __name__ == '__main__':
    success = sync_to_geojson()
    if success:
        print("\n=== SYNCHRONIZACJA ZAKOŃCZONA SUKCESEM! ===")
    else:
        print("\n=== BŁĄD PODCZAS SYNCHRONIZACJI! ===")
        sys.exit(1)
