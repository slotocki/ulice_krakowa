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
    'Dawne rzemiosło i historia': ('Historic Crafts and Heritage', 'Altes Handwerk und Geschichte'),
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
    m = re.search(r'\[(.*?)\]\((https?://.*?)\)(?:\s*(?:/|$))', src_str)
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

    # Załaduj 8 aktów historycznych z data/sources/
    act_files = {
        'drk_1880': 'drk_1880.json',
        'drk_1912': 'drk_1912.json',
        'podgorze_1917': 'podgorze_1917.json',
        'drk_1926_1933': 'drk_1926_1933.json',
        'okupacja_1940_1941': 'okupacja_1940_1941.json',
        'prl_1951_1955': 'prl_1951_1955.json',
        'rozszerzenie_1973_1975': 'rozszerzenie_1973_1975.json',
        'dekomunizacja_1991': 'dekomunizacja_1991.json',
    }
    acts_by_doc = {}
    for doc_id, fname in act_files.items():
        fpath = os.path.join('data', 'sources', fname)
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as af:
                adata = json.load(af)
                streets = adata.get('streets', [])
                by_gid = {}
                for s in streets:
                    gid = s.get('geojson_id')
                    if gid:
                        by_gid[gid] = {
                            'district_id': s.get('district_id') or '',
                            'district_name': s.get('district_name') or '',
                            'official_name': s.get('official_name_1880') or s.get('official_name_1912') or s.get('official_name_1917') or s.get('official_name_1926') or s.get('german_name') or s.get('official_name_1951') or s.get('official_name_1973') or s.get('official_name_1991') or s.get('name') or s.get('official_name') or '',
                            'page': s.get('page_printed') or s.get('page') or '',
                            'ref_id': s.get('id') or '',
                            'former_description': s.get('former_description') or s.get('former_name') or ''
                        }
                acts_by_doc[doc_id] = by_gid

    batch_records_by_name = parse_batches()

    updated_count = 0

    matched_keys = set()
    for feat in features:
        props = feat['properties']
        gid = props.get('id')
        for doc_id, by_gid in acts_by_doc.items():
            if gid in by_gid:
                props[doc_id] = by_gid[gid]
            elif doc_id in props:
                del props[doc_id]
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

        if rec['category'] in ['Postacie historyczne', 'Postacie fikcyjne i literatura'] and not lit_m:
            if patron is None:
                props['patron'] = {}
                patron = props['patron']
            if rec['patron_lit'].startswith('**'):
                patron['name'] = rec['patron_lit'].replace('**', '').strip()

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
            # Dedykowane aktualizacje patronów partii 09
            elif rec['lp'] == 819:
                patron['name'] = 'Władysław Leopold Jaworski'
                patron['birth_year'] = 1865
                patron['death_year'] = 1930
                patron['role'] = {
                    'pl': 'prawnik cywilista i konstytucjonalista, profesor i dziekan Wydziału Prawa UJ, prezes Naczelnego Komitetu Narodowego (1914–1917)',
                    'en': 'civil and constitutional jurist, professor and dean of law at Jagiellonian University, president of the Supreme National Committee (1914–1917)',
                    'de': 'Zivil- und Staatsrechtler, Professor und Dekan der Rechtswissenschaftlichen Fakultät der Jagiellonen-Universität, Präsident des Polnischen Obersten Nationalkomitees (1914–1917)'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/W%C5%82adys%C5%82aw%20Leopold%20Jaworski.png?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/W%C5%82adys%C5%82aw_Leopold_Jaworski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/W%C5%82adys%C5%82aw_Leopold_Jaworski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/W%C5%82adys%C5%82aw_Leopold_Jaworski',
                    'en': 'https://en.wikipedia.org/wiki/W%C5%82adys%C5%82aw_Leopold_Jaworski'
                }
            elif rec['lp'] == 820:
                patron['name'] = 'Jaksa Gryfita'
                patron['birth_year'] = 1120
                patron['death_year'] = 1176
                patron['role'] = {
                    'pl': 'możnowładca małopolski herbu Gryf, krzyżowiec, fundator klasztoru sióstr norbertanek na Zwierzyńcu oraz bożogrobców w Miechowie',
                    'en': 'Lesser Poland magnate of the Gryf coat of arms, crusader, founder of the Norbertine monastery in Zwierzyniec and Miechów',
                    'de': 'kleinpolnischer Magnat des Wappens Gryf, Kreuzfahrer, Stifter des Norbertinerinnenklosters in Zwierzyniec und Miechów'
                }
                patron['image'] = ''
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jaksa_z_Miechowa'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jaksa_z_Miechowa'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jaksa_z_Miechowa',
                    'en': 'https://en.wikipedia.org/wiki/Jaksa_of_Miech%C3%B3w'
                }
            elif rec['lp'] == 828:
                patron['name'] = 'Jeremi Wiśniowiecki'
                patron['birth_year'] = 1612
                patron['death_year'] = 1651
                patron['role'] = {
                    'pl': 'książę na Wiśniowcu i Łubniach, wojewoda ruski, dowódca wojsk koronnych w walkach z powstaniem Chmielnickiego, ojciec króla Michała Korybuta',
                    'en': 'Prince of Wiśniowiec and Łubnie, Voivode of Ruthenia, Crown army commander, father of King Michał Korybut Wiśniowiecki',
                    'de': 'Fürst von Wiśniowiec und Łubnie, Woiwode von Ruthenien, Heerführer der Kronarmee, Vater von König Michał Korybut Wiśniowiecki'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Jeremi_Wi%C5%9Bniowiecki.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jeremi_Wi%C5%9Bniowiecki'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jeremi_Wi%C5%9Bniowiecki'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jeremi_Wi%C5%9Bniowiecki',
                    'en': 'https://en.wikipedia.org/wiki/Jeremi_Wi%C5%9Bniowiecki',
                    'de': 'https://de.wikipedia.org/wiki/Jeremi_Wi%C5%9Bniowiecki'
                }
            elif rec['lp'] == 858:
                patron['name'] = 'Joseph Conrad'
                patron['birth_year'] = 1857
                patron['death_year'] = 1924
                patron['role'] = {
                    'pl': 'wybitny pisarz angielski pochodzenia polskiego, autor arcydzieł literatury światowej („Jądro ciemności”, „Lord Jim”, „Smuga cienia”)',
                    'en': 'prominent Polish-British novelist, author of world classics including Heart of Darkness and Lord Jim',
                    'de': 'bedeutender polnisch-britischer Schriftsteller, Autor von Weltklassikern wie Herz der Finsternis und Lord Jim'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Joseph_Conrad-remastered_to_black_and_white.png?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Joseph_Conrad'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Joseph_Conrad'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Joseph_Conrad',
                    'en': 'https://en.wikipedia.org/wiki/Joseph_Conrad',
                    'de': 'https://de.wikipedia.org/wiki/Joseph_Conrad'
                }
            elif rec['lp'] == 869:
                patron['name'] = 'Julia Nenko'
                patron['birth_year'] = 1903
                patron['death_year'] = 1983
                patron['role'] = {
                    'pl': 'major Wojska Polskiego, pielęgniarka 2 Korpusu Polskiego gen. Andersa spod Tobruku i Monte Cassino, dama Medalu Florence Nightingale',
                    'en': 'Polish Army major, military nurse of the Polish II Corps at Tobruk and Monte Cassino, Florence Nightingale Medal recipient',
                    'de': 'Majorin der polnischen Armee, Krankenschwester des 2. polnischen Korps bei Tobruk und Monte Cassino, Trägerin der Florence-Nightingale-Medaille'
                }
                patron['image'] = ''
                patron['wiki_url'] = 'http://www.wmpp.org.pl/pl/medalisci-florence-nightingale/julia-nenko.html'
                patron['wikipedia_url'] = 'http://www.wmpp.org.pl/pl/medalisci-florence-nightingale/julia-nenko.html'
                patron['wiki_urls'] = {
                    'pl': 'http://www.wmpp.org.pl/pl/medalisci-florence-nightingale/julia-nenko.html'
                }
            elif rec['lp'] == 875:
                patron['name'] = 'Juliusz Słowacki'
                patron['birth_year'] = 1809
                patron['death_year'] = 1849
                patron['role'] = {
                    'pl': 'wieszcz narodowy, poeta, dramaturg i epistolograf, czołowy twórca polskiego romantyzmu, autor „Kordiana”, „Balladyny” i „Beniowskiego”',
                    'en': 'national poet of Poland, prominent romantic playwright and essayist, author of Kordian, Balladyna, and Beniowski',
                    'de': 'polnischer Nationaldichter, bedeutender Dramatiker und Essayist der Romantik, Autor von Kordian, Balladyna und Beniowski'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Juliusz%20S%C5%82owacki%201.PNG?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Juliusz_S%C5%82owacki'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Juliusz_S%C5%82owacki'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Juliusz_S%C5%82owacki',
                    'en': 'https://en.wikipedia.org/wiki/Juliusz_S%C5%82owacki',
                    'de': 'https://de.wikipedia.org/wiki/Juliusz_S%C5%82owacki'
                }
            elif rec['lp'] == 879:
                patron['name'] = 'Jurek Bitschan'
                patron['birth_year'] = 1904
                patron['death_year'] = 1918
                patron['role'] = {
                    'pl': '14-letni gimnazjalista, harcerz, jeden z najsłynniejszych Orląt Lwowskich, poległy na Cmentarzu Łyczakowskim w obronie Lwowa',
                    'en': '14-year-old Polish scout and gymnasium student, one of the iconic Lwów Eaglets, killed defending Lwów in 1918',
                    'de': '14-jähriger polnischer Pfadfinder und Gymnasiast, einer der berühmtesten Lemberger Adlerjungen, gefallen 1918 bei der Verteidigung von Lwów'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Jurek_Bitschan.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jerzy_Bitschan'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jerzy_Bitschan'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jerzy_Bitschan',
                    'en': 'https://en.wikipedia.org/wiki/Jerzy_Bitschan',
                    'de': 'https://de.wikipedia.org/wiki/Jerzy_Bitschan'
                }
            elif rec['lp'] == 886:
                patron['name'] = 'Józef Brodowicz'
                patron['birth_year'] = 1790
                patron['death_year'] = 1885
                patron['role'] = {
                    'pl': 'lekarz internista, profesor i trzykrotny rektor Uniwersytetu Jagiellońskiego, prezes Towarzystwa Naukowego Krakowskiego, prekursor polskiej psychiatrii',
                    'en': 'internist physician, professor and three-time rector of the Jagiellonian University, president of the Kraków Scientific Society',
                    'de': 'Internist, Professor und dreifacher Rektor der Jagiellonen-Universität, Präsident der Krakauer Wissenschaftlichen Gesellschaft'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Maciej%20J%C3%B3zef%20Brodowicz.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Brodowicz'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Brodowicz'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Brodowicz'
                }
            elif rec['lp'] == 888:
                patron['name'] = 'Józef Dietl'
                patron['birth_year'] = 1804
                patron['death_year'] = 1878
                patron['role'] = {
                    'pl': 'lekarz, profesor i rektor Uniwersytetu Jagiellońskiego, ojciec polskiej balneologii, pierwszy prezydent autonomicznego Krakowa (1866–1874)',
                    'en': 'physician, professor and rector of Jagiellonian University, pioneer of balneology, first president of autonomous Kraków (1866–1874)',
                    'de': 'Arzt, Professor und Rektor der Jagiellonen-Universität, Vater der polnischen Balneologie, erster Präsident des autonomen Krakau (1866–1874)'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/J%C3%B3zef%20Dietl.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Dietl'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Dietl'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Dietl',
                    'en': 'https://en.wikipedia.org/wiki/J%C3%B3zef_Dietl',
                    'de': 'https://de.wikipedia.org/wiki/Joseph_Dietl'
                }
            elif rec['lp'] == 897:
                patron['name'] = 'Józef Korzeniowski'
                patron['birth_year'] = 1797
                patron['death_year'] = 1863
                patron['role'] = {
                    'pl': 'dramatopisarz i powieściopisarz epoki romantyzmu, pedagog, profesor Liceum Krzemienieckiego, autor „Karpaccich górali”',
                    'en': 'Romantic playwright, novelist and educator, professor at Krzemieniec Lyceum, author of The Carpathian Mountaineers',
                    'de': 'Dramatiker und Romanschriftsteller der Romantik, Pädagoge, Professor am Lyzeum Krzemieniec, Autor von Die Karpathen-Goralen'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/J%C3%B3zef%20Korzeniowski%20photography%20%28cropped%29.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Korzeniowski_(pisarz)'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Korzeniowski_(pisarz)'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Korzeniowski_(pisarz)',
                    'en': 'https://en.wikipedia.org/wiki/J%C3%B3zef_Korzeniowski',
                    'de': 'https://de.wikipedia.org/wiki/J%C3%B3zef_Korzeniowski'
                }
            elif rec['lp'] == 900:
                patron['name'] = 'Józef Mackiewicz'
                patron['birth_year'] = 1902
                patron['death_year'] = 1985
                patron['role'] = {
                    'pl': 'pisarz, prozaik i publicysta polityczny, świadek ekshumacji ofiar zbrodni katyńskiej (1943), autor powieści epickich „Droga donikąd” i „Nie trzeba głośno mówić”',
                    'en': 'writer, novelist and political essayist, witness to the Katyń massacre exhumation (1943), author of The Road to Nowhere',
                    'de': 'Schriftsteller und politischer Publizist, Zeuge der Exhumierung von Katyn (1943), Autor des Romans Der Weg ins Nirgendwo'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/J%C3%B3zef_Mackiewicz_1919.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Mackiewicz'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Mackiewicz'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Mackiewicz',
                    'en': 'https://en.wikipedia.org/wiki/J%C3%B3zef_Mackiewicz',
                    'de': 'https://de.wikipedia.org/wiki/J%C3%B3zef_Mackiewicz'
                }
            # Dedykowane aktualizacje patronów partii 10
            elif rec['lp'] == 910:
                patron['name'] = 'Józef Sare'
                patron['birth_year'] = 1850
                patron['death_year'] = 1929
                patron['role'] = {
                    'pl': 'architekt, inżynier budowlany, wieloletni wiceprezydent Krakowa (1905–1929) i poseł na Sejm Krajowy Galicji',
                    'en': 'architect, civil engineer, long-serving Vice-President of Kraków (1905–1929) and Galician Diet deputy',
                    'de': 'Architekt, Bauingenieur, langjähriger Vizepräsident von Krakau (1905–1929) und galizischer Landtagsabgeordneter'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/J%C3%B3zef_Sare.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Sare'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Sare'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/J%C3%B3zef_Sare',
                    'en': 'https://en.wikipedia.org/wiki/J%C3%B3zef_Sare'
                }
            elif rec['lp'] in (883, 921):
                patron['name'] = 'Józef II Habsburg'
                patron['birth_year'] = 1741
                patron['death_year'] = 1790
                patron['role'] = {
                    'pl': 'cesarz rzymsko-niemiecki (1765–1790), król Galicji i Lodomerii, założyciel wolnego miasta królewskiego Podgórza (Josephstadt)',
                    'en': 'Holy Roman Emperor (1765–1790), King of Galicia and Lodomeria, founder of the royal free city of Podgórze (Josephstadt)',
                    'de': 'Kaiser des Heiligen Römischen Reiches (1765–1790), König von Galizien und Lodomerien, Gründer der königlichen Freistadt Podgórze (Josephstadt)'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Anton_von_Maron_006.png?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_II_Habsburg'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/J%C3%B3zef_II_Habsburg'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/J%C3%B3zef_II_Habsburg',
                    'en': 'https://en.wikipedia.org/wiki/Joseph_II,_Holy_Roman_Emperor',
                    'de': 'https://de.wikipedia.org/wiki/Joseph_II.'
                }
            elif rec['lp'] == 951:
                patron['name'] = 'Karol Bohdanowicz'
                patron['birth_year'] = 1864
                patron['death_year'] = 1947
                patron['role'] = {
                    'pl': 'wybitny geolog, geograf i inżynier górniczy, profesor i rektor Akademii Górniczej w Krakowie (1938–1939), dyrektor Państwowego Instytutu Geologicznego',
                    'en': 'prominent geologist, geographer and mining engineer, professor and rector of the Academy of Mining in Kraków (1938–1939), director of the Polish Geological Institute',
                    'de': 'bedeutender Geologe, Geograph und Bergbauingenieur, Professor und Rektor der Bergakademie Krakau (1938–1939), Direktor des Staatlichen Geologischen Instituts'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Karol%20Bohdanowicz1.png?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Karol_Bohdanowicz'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Karol_Bohdanowicz'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Karol_Bohdanowicz',
                    'en': 'https://en.wikipedia.org/wiki/Karol_Bohdanowicz',
                    'de': 'https://de.wikipedia.org/wiki/Karol_Bohdanowicz'
                }
            elif rec['lp'] == 952:
                patron['name'] = 'Karol Bunsch'
                patron['birth_year'] = 1898
                patron['death_year'] = 1987
                patron['role'] = {
                    'pl': 'pisarz historyczny, autor cyklu powieści piastowskich, tłumacz literatury niemieckiej, radca prawny w Krakowie',
                    'en': 'historical novelist, author of the Piast cycle, translator of German literature, legal counsel in Kraków',
                    'de': 'Schriftsteller historischer Romane, Autor des Piasten-Zyklus, Übersetzer deutscher Literatur, Jurist in Krakau'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Karol_Bunsch'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Karol_Bunsch'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Karol_Bunsch',
                    'en': 'https://en.wikipedia.org/wiki/Karol_Bunsch',
                    'de': 'https://de.wikipedia.org/wiki/Karol_Bunsch'
                }
            elif rec['lp'] == 953:
                patron['name'] = 'Jan Karol Chodkiewicz'
                patron['birth_year'] = 1560
                patron['death_year'] = 1621
                patron['role'] = {
                    'pl': 'hetman wielki litewski, wojewoda wileński, jeden z najwybitniejszych wodzów I Rzeczypospolitej, zwycięzca pod Kircholmem (1605) i obrońca Chocimia (1621)',
                    'en': 'Grand Hetman of Lithuania, Voivode of Vilnius, legendary military commander of the Commonwealth, victor at Kircholm (1605) and Chocim (1621)',
                    'de': 'Großhetman von Litauen, Woiwode von Vilnius, legendärer Feldherr Polen-Litauens, Sieger bei Kircholm (1605) und Chocim (1621)'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Jan_Karol_Chodkiewicz.PNG?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jan_Karol_Chodkiewicz'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jan_Karol_Chodkiewicz'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jan_Karol_Chodkiewicz',
                    'en': 'https://en.wikipedia.org/wiki/Jan_Karol_Chodkiewicz',
                    'de': 'https://de.wikipedia.org/wiki/Jan_Karol_Chodkiewicz'
                }
            elif rec['lp'] == 978:
                patron['name'] = 'Kazimierz Chałupnik'
                patron['birth_year'] = 1908
                patron['death_year'] = 1978
                patron['role'] = {
                    'pl': 'działacz robotniczy, spółdzielczy i sportowy, żołnierz AK i powstaniec warszawski, prezes RKS Juvenia Kraków',
                    'en': 'labor, cooperative and sports activist, Home Army soldier and Warsaw Uprising participant, president of RKS Juvenia Kraków',
                    'de': 'Arbeiter-, Genossenschafts- und Sportaktivist, Soldat der Heimatarmee, Teilnehmer des Warschauer Aufstands, Präsident von RKS Juvenia Krakau'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_Cha%C5%82upnik'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_Cha%C5%82upnik'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Kazimierz_Cha%C5%82upnik'
                }
            elif rec['lp'] == 979:
                patron['name'] = 'Kazimierz Czapiński'
                patron['birth_year'] = 1882
                patron['death_year'] = 1941
                patron['role'] = {
                    'pl': 'działacz socjalistyczny, publicysta, poseł na Sejm RP (1922–1935), więzień Brześcia, zamordowany w obozie Auschwitz-Birkenau',
                    'en': 'socialist activist, publicist, Member of the Polish Parliament (1922–1935), Brest prisoner, murdered in Auschwitz-Birkenau',
                    'de': 'sozialistischer Politiker, Publizist, Abgeordneter des Sejm (1922–1935), Brester Häftling, ermordet im KZ Auschwitz-Birkenau'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Czapinski.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_Czapi%C5%84ski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_Czapi%C5%84ski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Kazimierz_Czapi%C5%84ski',
                    'en': 'https://en.wikipedia.org/wiki/Kazimierz_Czapi%C5%84ski'
                }
            elif rec['lp'] == 981:
                patron['name'] = 'Kazimierz IV Jagiellończyk'
                patron['birth_year'] = 1427
                patron['death_year'] = 1492
                patron['role'] = {
                    'pl': 'wielki książę litewski (1440–1492) i król Polski (1447–1492), jeden z najwybitniejszych władców z dynastii Jagiellonów, zwycięzca w wojnie trzynastoletniej',
                    'en': 'Grand Duke of Lithuania (1440–1492) and King of Poland (1447–1492), prominent Jagiellonian ruler who triumphed in the Thirteen Years\' War',
                    'de': 'Großfürst von Litauen (1440–1492) und König von Polen (1447–1492), bedeutender Herrscher der Jagiellonen-Dynastie, Sieger im Dreizehnjährigen Krieg'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kazimierz_IV_Jagiellonczyk.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_IV_Jagiello%C5%84czyk'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_IV_Jagiello%C5%84czyk'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Kazimierz_IV_Jagiello%C5%84czyk',
                    'en': 'https://en.wikipedia.org/wiki/Casimir_IV_Jagiellon',
                    'de': 'https://de.wikipedia.org/wiki/Kasimir_IV._Andreas'
                }
            elif rec['lp'] == 987:
                patron['name'] = 'Kazimierz I Odnowiciel'
                patron['birth_year'] = 1016
                patron['death_year'] = 1058
                patron['role'] = {
                    'pl': 'książę Polski z dynastii Piastów (1034–1058), odnowiciel państwa polskiego po najeździe czeskim, przeniósł główną siedzibę książęcą do Krakowa (ok. 1038/1040)',
                    'en': 'Duke of Poland of the Piast dynasty (1034–1058), Restorer of the Polish realm, established Kraków as the ducal capital (c. 1038/1040)',
                    'de': 'Herzog von Polen aus der Piastendynastie (1034–1058), Erneuerer des polnischen Staates, verlegte die Residenz nach Krakau (ca. 1038/1040)'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kazimierz_I_Odnowiciel.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_I_Odnowiciel'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_I_Odnowiciel'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Kazimierz_I_Odnowiciel',
                    'en': 'https://en.wikipedia.org/wiki/Casimir_I_the_Restorer',
                    'de': 'https://de.wikipedia.org/wiki/Kasimir_I._Karl'
                }
            elif rec['lp'] == 992:
                patron['name'] = 'Kazimierz II Sprawiedliwy'
                patron['birth_year'] = 1138
                patron['death_year'] = 1194
                patron['role'] = {
                    'pl': 'książę krakowski i zwierzchni książę Polski (princeps) z dynastii Piastów (1177–1194), mecenas kultury i Kościoła',
                    'en': 'High Duke of Kraków and princeps of Poland of the Piast dynasty (1177–1194), patron of culture and the Church',
                    'de': 'Seniorherzog von Krakau und Herrscher von Polen aus der Piastendynastie (1177–1194), Förderer von Kultur und Kirche'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kazimierz_II_Sprawiedliwy.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_II_Sprawiedliwy'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_II_Sprawiedliwy'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Kazimierz_II_Sprawiedliwy',
                    'en': 'https://en.wikipedia.org/wiki/Casimir_II_the_Just',
                    'de': 'https://de.wikipedia.org/wiki/Kasimir_II._(Polen)'
                }
            elif rec['lp'] == 994:
                patron['name'] = 'Kazimierz III Wielki'
                patron['birth_year'] = 1310
                patron['death_year'] = 1370
                patron['role'] = {
                    'pl': 'król Polski (1333–1370), ostatni monarcha z dynastii Piastów na polskim tronie, fundator Akademii Krakowskiej (1364) i miasta Kazimierz',
                    'en': 'King of Poland (1333–1370), last Piast monarch, founder of the Kraków Academy (1364) and the royal city of Kazimierz',
                    'de': 'König von Polen (1333–1370), letzter Piastenkönig, Stifter der Krakauer Akademie (1364) und Gründer der Stadt Kazimierz'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kazimierz_III_Wielki.PNG?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_III_Wielki'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Kazimierz_III_Wielki'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Kazimierz_III_Wielki',
                    'en': 'https://en.wikipedia.org/wiki/Casimir_III_the_Great',
                    'de': 'https://de.wikipedia.org/wiki/Kasimir_III._(Polen)'
                }
            elif rec['lp'] == 998:
                patron['name'] = 'Hassling-Ketling of Elgin'
                patron['role'] = {
                    'pl': 'fikcyjna postać literacka z Trylogii Henryka Sienkiewicza („Pan Wołodyjowski”), oficer artylerii pochodzenia szkockiego, obrońca Kamieńca Podolskiego',
                    'en': 'fictional character from Henryk Sienkiewicz\'s Trilogy ("Colonel Wolodyjowski"), Scottish artillery officer and defender of Kamianets-Podilskyi',
                    'de': 'literarische Figur aus Henryk Sienkiewiczs Trilogie („Herr Wołodyjowski“), schottischer Artillerieoffizier und Verteidiger von Kamieniec Podolski'
                }
                patron['image'] = ''
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Hassling-Ketling_of_Elgin'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Hassling-Ketling_of_Elgin'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Hassling-Ketling_of_Elgin'
                }
            elif rec['lp'] == 999:
                patron['name'] = 'Kiejstut Żemaitis'
                patron['birth_year'] = 1906
                patron['death_year'] = 1973
                patron['role'] = {
                    'pl': 'inżynier hutnik, profesor i rektor Akademii Górniczo-Hutniczej w Krakowie (1956–1962), minister hutnictwa PRL (1952–1957)',
                    'en': 'metallurgical engineer, professor and rector of the AGH University of Science and Technology (1956–1962), Minister of Metallurgy of Poland',
                    'de': 'Hütteningenieur, Professor und Rektor der AGH Wissenschaftlich-Technischen Universität (1956–1962), Minister für Hüttenwesen der VR Polen'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kiejstut_Zemaitis.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Kiejstut_%C5%BBemaitis'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Kiejstut_%C5%BBemaitis'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Kiejstut_%C5%BBemaitis',
                    'en': 'https://en.wikipedia.org/wiki/Kiejstut_%C5%BBemaitis'
                }
            elif rec['lp'] == 707:
                patron['name'] = 'Ivo Andrić'
                patron['birth_year'] = 1892
                patron['death_year'] = 1975
                patron['role'] = {
                    'pl': 'pisarz jugosłowiański (bośniacki i serbski), laureat Nagrody Nobla w dziedzinie literatury (1961), autor powieści „Most na Drinie”',
                    'en': 'Yugoslav writer, Nobel Prize laureate in Literature (1961), author of The Bridge on the Drina',
                    'de': 'jugoslawischer Schriftsteller, Nobelpreisträger für Literatur (1961), Autor von Die Brücke über die Drina'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/S._Kragujevic%2C_Ivo_Andric%2C_1961.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Ivo_Andri%C4%87'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Ivo_Andri%C4%87'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Ivo_Andri%C4%87',
                    'en': 'https://en.wikipedia.org/wiki/Ivo_Andri%C4%87',
                    'de': 'https://de.wikipedia.org/wiki/Ivo_Andri%C4%87'
                }
            elif rec['lp'] == 710:
                patron['name'] = 'Iwona Borowicka'
                patron['birth_year'] = 1929
                patron['death_year'] = 1984
                patron['role'] = {
                    'pl': 'polska śpiewaczka operowa i operetkowa (sopran dramatyczny), primadonna Opery i Operetki Krakowskiej',
                    'en': 'Polish opera and operetta singer (dramatic soprano), primadonna of the Kraków Opera',
                    'de': 'polnische Opern- und Operettensängerin (dramatischer Sopran), Primadonna der Krakauer Oper'
                }
                patron['image'] = ''
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Iwona_Borowicka'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Iwona_Borowicka'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Iwona_Borowicka'
                }
            elif rec['lp'] == 743:
                patron['name'] = 'Jan Długosz'
                patron['birth_year'] = 1415
                patron['death_year'] = 1480
                patron['role'] = {
                    'pl': 'najwybitniejszy kronikarz i historyk polskiego średniowiecza, kanonik krakowski, autor „Roczników czyli Kronik sławnego Królestwa Polskiego”',
                    'en': 'greatest chronicler and historian of medieval Poland, canon of Kraków, author of the Annals of the Kingdom of Poland',
                    'de': 'bedeutendster polnischer Chronist und Historiker des Mittelalters, Krakauer Domherr, Autor der Annalen des Königreichs Polen'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Jan%20Dlugosz%20%2892089616%29.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jan_D%C5%82ugosz'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jan_D%C5%82ugosz'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jan_D%C5%82ugosz',
                    'en': 'https://en.wikipedia.org/wiki/Jan_D%C5%82ugosz'
                }
            elif rec['lp'] == 800:
                patron['name'] = 'Janusz Korczak'
                patron['birth_year'] = 1878
                patron['death_year'] = 1942
                patron['role'] = {
                    'pl': 'lekarz, pedagog, pisarz, prekursor praw dziecka, twórca Domu Sierot w Warszawie',
                    'en': 'pediatrician, educator, author, pioneer of children rights, founder of the Orphanage in Warsaw',
                    'de': 'Arzt, Pädagoge, Schriftsteller, Pionier der Kinderrechte, Leiter des Waisenhauses in Warschau'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Janusz%20Korczak%20%28cropped%29.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Janusz_Korczak'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Janusz_Korczak'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Janusz_Korczak',
                    'en': 'https://en.wikipedia.org/wiki/Janusz_Korczak'
                }
            # Dedykowane aktualizacje patronów partii 11
            elif rec['lp'] == 1004:
                patron['name'] = 'Klemens Bąkowski'
                patron['birth_year'] = 1860
                patron['death_year'] = 1938
                patron['role'] = {
                    'pl': 'prawnik, historyk, wybitny badacz dziejów Krakowa, współzałożyciel Towarzystwa Miłośników Historii i Zabytków Krakowa',
                    'en': 'jurist, historian, prominent researcher of Kraków history, co-founder of the Society of Friends of Kraków History and Monuments',
                    'de': 'Jurist, Historiker, bedeutender Erforscher der Krakauer Geschichte, Mitbegründer der Gesellschaft der Freunde der Krakauer Geschichte'
                }
            elif rec['lp'] == 1005:
                patron['name'] = 'Klemens Janicki'
                patron['birth_year'] = 1516
                patron['death_year'] = 1543
                patron['role'] = {
                    'pl': 'wybitny poeta polsko-łaciński renesansu, uwieńczony cesarskim laurem poetyckim (poeta laureatus) w Padwie',
                    'en': 'prominent Polish-Latin Renaissance poet, imperial poet laureate in Padua',
                    'de': 'bedeutender polnisch-lateinischer Dichter der Renaissance, Dichterpreisträger in Padua'
                }
            elif rec['lp'] == 1006:
                patron['name'] = 'Klemens Junosza'
                patron['birth_year'] = 1849
                patron['death_year'] = 1898
                patron['role'] = {
                    'pl': 'pisarz, nowelista i felietonista pozytywizmu, piewca tradycji wsi polskiej i folkloru małomiasteczkowego',
                    'en': 'Positivist writer, novelist and essayist, chronicler of Polish rural life and small-town folklore',
                    'de': 'Schriftsteller, Novellist und Feuilletonist des Positivismus, Chronist des polnischen Dorflebens'
                }
            elif rec['lp'] == 1007:
                patron['name'] = 'Klemens z Ruszczy'
                patron['death_year'] = 1256
                patron['role'] = {
                    'pl': 'możnowładca małopolski herbu Gryf, kasztelan i wojewoda krakowski, obrońca Wawelu (1243)',
                    'en': 'Lesser Poland magnate of the Gryf coat of arms, Castellan and Voivode of Kraków, defender of Wawel (1243)',
                    'de': 'kleinpolnischer Magnat des Wappens Gryf, Kastellan und Woiwode von Krakau, Verteidiger des Wawels (1243)'
                }
            elif rec['lp'] == 1008:
                patron['name'] = 'Klementyna Hoffmanowa'
                patron['birth_year'] = 1798
                patron['death_year'] = 1845
                patron['role'] = {
                    'pl': 'pisarka, pedagożka i działaczka oświatowa, prekursorka nowoczesnej polskiej literatury dla dzieci i młodzieży',
                    'en': 'writer, educator and activist, pioneer of modern Polish children and youth literature',
                    'de': 'Schriftstellerin, Pädagogin und Bildungsaktivistin, Pionierin der modernen polnischen Kinder- und Jugendliteratur'
                }
            elif rec['lp'] == 1009:
                patron['name'] = 'Klemens Bachleda (Klimek)'
                patron['birth_year'] = 1849
                patron['death_year'] = 1910
                patron['role'] = {
                    'pl': 'legendarny przewodnik tatrzański I klasy i ratownik TOPR, nazywany „królem przewodników tatrzańskich”',
                    'en': 'legendary Tatra mountain guide and TOPR mountain rescuer, known as the "King of Tatra Guides"',
                    'de': 'legendärer Bergführer der Hohen Tatra und TOPR-Bergretter, bekannt als „König der Tatra-Führer“'
                }
            elif rec['lp'] == 1013:
                patron['name'] = 'Andrzej Kmicic'
                patron['role'] = {
                    'pl': 'fikcyjna postać literacka z Trylogii Henryka Sienkiewicza („Potop”), chorąży orszański i bohaterski obrońca Jasnej Góry',
                    'en': 'fictional character from Henryk Sienkiewicz\'s Trilogy ("The Deluge"), Orsza ensign and heroic defender of Jasna Góra',
                    'de': 'literarische Figur aus Henryk Sienkiewiczs Trilogie („Die Sintflut“), Fähnrich von Orsza und heldenhafter Verteidiger von Jasna Góra'
                }
            elif rec['lp'] == 1027:
                patron['name'] = 'Bohdan Wroński'
                patron['birth_year'] = 1908
                patron['death_year'] = 1983
                patron['role'] = {
                    'pl': 'komandor porucznik Marynarki Wojennej RP, nawigator ORP „Wilk”, dowódca okrętów „Jastrząb”, „Kujawiak”, „Ślązak” i „Błyskawica”',
                    'en': 'Commander of the Polish Navy, navigator of ORP Wilk, commander of ORP Jastrząb, Kujawiak, Ślązak, and Błyskawica',
                    'de': 'Fregattenkapitän der polnischen Marine, Navigator von ORP Wilk, Kommandant der Schiffe Jastrząb, Kujawiak, Ślązak und Błyskawica'
                }
            elif rec['lp'] == 1032:
                patron['name'] = 'Konrad Srzednicki'
                patron['birth_year'] = 1894
                patron['death_year'] = 1993
                patron['role'] = {
                    'pl': 'malarz i grafik, profesor i dziekan Wydziału Grafiki ASP w Krakowie, mistrz litografii barwnej',
                    'en': 'painter and printmaker, professor and dean of graphic arts at the Jan Matejko Academy of Fine Arts in Kraków',
                    'de': 'Maler und Grafiker, Professor und Dekan der Fakultät für Grafik an der Kunstakademie Krakau'
                }
            elif rec['lp'] == 1033:
                patron['name'] = 'Konrad Wallenrod'
                patron['role'] = {
                    'pl': 'fikcyjny bohater powieści poetyckiej Adama Mickiewicza (1828), uosobienie tragicznego patriotyzmu i walki o wolność ojczyzny',
                    'en': 'fictional protagonist of Adam Mickiewicz\'s poetic novel (1828), embodiment of tragic patriotism',
                    'de': 'literarischer Protagonist des Versepos von Adam Mickiewicz (1828), Sinnbild tragischen Patriotismus'
                }
            elif rec['lp'] == 1034:
                patron['name'] = 'Konstanty Brandel'
                patron['birth_year'] = 1880
                patron['death_year'] = 1970
                patron['role'] = {
                    'pl': 'malarz i grafik, mistrz akwaforty, uczeń Leona Wyczółkowskiego na krakowskiej ASP',
                    'en': 'painter and printmaker, master of etching, student of Leon Wyczółkowski at the Kraków Academy',
                    'de': 'Maler und Grafiker, Meister der Radierung, Schüler von Leon Wyczółkowski an der Krakauer Kunstakademie'
                }
            elif rec['lp'] == 1035:
                patron['name'] = 'Konstantin Ciołkowski'
                patron['birth_year'] = 1857
                patron['death_year'] = 1935
                patron['role'] = {
                    'pl': 'uczony pochodzenia polskiego, pionier astronautyki i teorii wielostopniowych rakiet kosmicznych',
                    'en': 'scientist of Polish descent, pioneer of astronautics and rocket dynamics theory',
                    'de': 'Wissenschaftler polnischer Herkunft, Pionier der Raumfahrt und der mehrstufigen Raketendynamik'
                }
            elif rec['lp'] == 1036:
                patron['name'] = 'Konstanty Ildefons Gałczyński'
                patron['birth_year'] = 1905
                patron['death_year'] = 1953
                patron['role'] = {
                    'pl': 'wybitny polski poeta i satyryk XX wieku, twórca „Teatrzyku Zielona Gęś”, mieszkaniec krakowskiego Domu Literatów',
                    'en': 'prominent Polish poet and satirist of the 20th century, creator of the Green Goose Theatre, resident of the Kraków Writers\' House',
                    'de': 'bedeutender polnischer Dichter und Satiriker des 20. Jahrhunderts, Schöpfer des Theaters Die Grüne Gans, Bewohner des Krakauer Literaturhauses'
                }
            elif rec['lp'] == 1037:
                patron['name'] = 'Konstanty Jelski'
                patron['birth_year'] = 1837
                patron['death_year'] = 1896
                patron['role'] = {
                    'pl': 'zoolog, przyrodnik, podróżnik, badacz fauny Ameryki Południowej, kustosz zbiorów przyrodniczych Akademii Umiejętności w Krakowie',
                    'en': 'zoologist, naturalist and explorer of South American fauna, curator of natural history collections at the Academy of Learning in Kraków',
                    'de': 'Zoologe, Naturforscher und Erforscher der südamerikanischen Fauna, Kustos der naturkundlichen Sammlungen der Krakauer Akademie der Gelehrsamkeit'
                }
            elif rec['lp'] == 1038:
                patron['name'] = 'Konstanty Krumłowski'
                patron['birth_year'] = 1872
                patron['death_year'] = 1938
                patron['role'] = {
                    'pl': 'krakowski dramatopisarz i satyryk, autor tekstów Zielonego Balonika, twórca słynnego wodewilu „Królowa przedmieścia”',
                    'en': 'Kraków playwright and satirist, author of Green Balloon cabaret sketches, creator of the popular vaudeville Queen of the Suburbs',
                    'de': 'Krakauer Dramatiker und Satiriker, Autor von Texten des Grünen Luftballons, Schöpfer des berühmten Vaudevilles Die Königin der Vorstadt'
                }
            elif rec['lp'] == 1039:
                patron['name'] = 'Konstanty Laszczka'
                patron['birth_year'] = 1865
                patron['death_year'] = 1956
                patron['role'] = {
                    'pl': 'rzeźbiarz, ceramik i malarz okresu Młodej Polski, profesor oraz rektor Akademii Sztuk Pięknych w Krakowie',
                    'en': 'sculptor, ceramic artist and painter of Young Poland, professor and rector of the Jan Matejko Academy of Fine Arts in Kraków',
                    'de': 'Bildhauer, Keramiker und Maler des Jungen Polen, Professor und Rektor der Kunstakademie Krakau'
                }
            elif rec['lp'] == 1047:
                patron['name'] = 'Kordian'
                patron['role'] = {
                    'pl': 'tytułowy bohater dramatu romantycznego Juliusza Słowackiego (1834), uosobienie walki z caratem i poświęcenia za wolność ojczyzny',
                    'en': 'title protagonist of Juliusz Słowacki\'s romantic drama (1834), symbol of struggle against tsarist rule and patriotic sacrifice',
                    'de': 'Titelheld des romantischen Dramas von Juliusz Słowacki (1834), Sinnbild des Kampfes gegen die zaristische Herrschaft und patriotischer Aufopferung'
                }
            elif rec['lp'] == 1049:
                patron['name'] = 'Kornel Makuszyński'
                patron['birth_year'] = 1884
                patron['death_year'] = 1953
                patron['role'] = {
                    'pl': 'prozaik, poeta i felietonista, członek Polskiej Akademii Literatury, autor klasyki literatury dziecięcej i młodzieżowej',
                    'en': 'novelist, poet and columnist, member of the Polish Academy of Literature, author of classic children and youth literature',
                    'de': 'Schriftsteller, Dichter und Kolumnist, Mitglied der Polnischen Akademie für Literatur, Autor klassischer Kinder- und Jugendliteratur'
                }
            elif rec['lp'] == 1050:
                patron['name'] = 'Kornel Ujejski'
                patron['birth_year'] = 1823
                patron['death_year'] = 1897
                patron['role'] = {
                    'pl': 'poeta i publicysta późnego romantyzmu, autor patriotycznych „Skarg Jeremiego” oraz hymnu „Chorał”',
                    'en': 'prominent poet and publicist of late Romanticism, author of patriotic Jeremiah\'s Laments and the national hymn Chorał',
                    'de': 'Dichter und Publizist der Spätromantik, Autor der patriotischen Jeremias-Klagen und der Nationalhymne Chorał'
                }
            elif rec['lp'] == 1077:
                patron['name'] = 'Książę Krak (Krakus)'
                patron['role'] = {
                    'pl': 'legendarny praojciec i wódz plemienny Wiślan, założyciel grodu Krakowa, pogromca Smoka Wawelskiego',
                    'en': 'legendary founder of Kraków, tribal prince of the Vistulans, slayer of the Wawel Dragon',
                    'de': 'legendärer Gründer von Krakau, Stammesfürst der Wislanen, Bezwinger des Wawel-Drachen'
                }
            elif rec['lp'] == 1080:
                patron['name'] = 'Książę Krakus'
                patron['role'] = {
                    'pl': 'legendarny założyciel grodu Krakowa, patron pobliskiego przedhistorycznego Kopca Krakusa na Wzgórzu Lasoty',
                    'en': 'legendary founder of Kraków, namesake of the nearby prehistoric Krakus Mound on Lasota Hill',
                    'de': 'legendärer Gründer von Krakau, Namensgeber des nahegelegenen prähistorischen Krakus-Hügels auf dem Lasota-Hügel'
                }
            elif rec['lp'] == 1090:
                patron['name'] = 'Gall Anonim'
                patron['role'] = {
                    'pl': 'pierwszy kronikarz i dziejopisarz Polski (XI/XII w.), autor „Kroniki polskiej” spisanej na krakowskim dworze Bolesława Krzywoustego',
                    'en': 'first chronicler and historian of Poland (11th/12th c.), author of the Polish Chronicle composed at the court of Bolesław III Wrymouth',
                    'de': 'erster Chronist und Geschichtsschreiber Polens (11./12. Jh.), Autor der Polnischen Chronik am Hofe von Bolesław III. Schiefmund'
                }
            elif rec['lp'] == 1099:
                patron['name'] = 'Krystyn z Ostrowa'
                patron['birth_year'] = 1352
                patron['death_year'] = 1430
                patron['role'] = {
                    'pl': 'kasztelan krakowski, wojewoda sandomierski, zaufany dyplomata i doradca Władysława II Jagiełły, dowódca pod Grunwaldem (1410)',
                    'en': 'Castellan of Kraków, Voivode of Sandomierz, trusted advisor to King Władysław II Jagiełło, commander at the Battle of Grunwald (1410)',
                    'de': 'Kastellan von Krakau, Woiwode von Sandomierz, Berater von König Władysław II. Jagiełło, Heerführer in der Schlacht bei Tannenberg (1410)'
                }
            # Dedykowane aktualizacje patronów partii 17
            elif rec['lp'] == 1603:
                patron['name'] = 'Olga Boznańska'
                patron['birth_year'] = 1865
                patron['death_year'] = 1940
                patron['role'] = {
                    'pl': 'jedna z najwybitniejszych polskich malarek przełomu XIX i XX w., przedstawicielka postimpresjonizmu i modernizmu',
                    'en': 'one of the most renowned Polish painters of the turn of the 20th century, representative of Post-Impressionism and modernism',
                    'de': 'eine der bedeutendsten polnischen Malerinnen der Jahrhundertwende, Vertreterin des Postimpressionismus und der Moderne'
                }
            elif rec['lp'] == 1611:
                patron['name'] = 'Ondraszek'
                patron['birth_year'] = 1680
                patron['death_year'] = 1715
                patron['role'] = {
                    'pl': 'legendarny beskidzki zbójnik ze Śląska Cieszyńskiego, bohater ludowych podań, pieśni i literatury',
                    'en': 'legendary Beskid brigand from Cieszyn Silesia, folk hero of regional legends, songs and literature',
                    'de': 'legendärer Räuberführer der Beskiden aus Teschener Schlesien, Gestalt der Volksüberlieferung, Lieder und Literatur'
                }
            elif rec['lp'] == 1613:
                patron['name'] = 'Opat Erazm Salwiński'
                patron['death_year'] = 1572
                patron['role'] = {
                    'pl': 'opat klasztoru oo. Cystersów w Mogile (1537–1552), renesansowy mecenas sztuki i humanista',
                    'en': 'Abbot of the Cistercian Abbey in Mogiła (1537–1552), Renaissance humanist and patron of the arts',
                    'de': 'Abt der Zisterzienserabtei in Mogiła (1537–1552), Renaissance-Humanist und Kunstmäzen'
                }
            elif rec['lp'] == 1631:
                patron['name'] = 'Oskar Kolberg'
                patron['birth_year'] = 1814
                patron['death_year'] = 1890
                patron['role'] = {
                    'pl': 'wybitny polski etnograf, folklorysta i kompozytor, autor monumentalnego dzieła „Lud”',
                    'en': 'prominent Polish ethnographer, folklorist and composer, author of the monumental work "The People"',
                    'de': 'bedeutender polnischer Ethnograph, Folklorist und Komponist, Schöpfer des monumentalen Werks „Das Volk“'
                }
            elif rec['lp'] == 1640:
                patron['name'] = 'Pál Teleki'
                patron['birth_year'] = 1879
                patron['death_year'] = 1941
                patron['role'] = {
                    'pl': 'hrabia, węgierski geograf i mąż stanu, dwukrotny premier Węgier, wybitny przyjaciel narodu polskiego',
                    'en': 'Count, Hungarian geographer and statesman, two-time Prime Minister of Hungary, devoted friend of Poland',
                    'de': 'Graf, ungarischer Geograph und Staatsmann, zweimaliger Premierminister Ungarns, herausragender Freund Polens'
                }
            elif rec['lp'] == 1661:
                patron['name'] = 'Paweł Jasienica'
                patron['birth_year'] = 1909
                patron['death_year'] = 1970
                patron['role'] = {
                    'pl': 'pisarz historyczny, eseista, oficer Armii Krajowej, autor dzieł „Polska Piastów”, „Polska Jagiellonów” i „Rzeczpospolita Obojga Narodów”',
                    'en': 'historical writer, essayist, Home Army officer, author of renowned syntheses of Polish history',
                    'de': 'Geschichtsschreiber, Essayist, Offizier der Heimatarmee, Autor bedeutender Synthesen der polnischen Geschichte'
                }
            elif rec['lp'] == 1662:
                patron['name'] = 'Paweł Włodkowic'
                patron['birth_year'] = 1370
                patron['death_year'] = 1435
                patron['role'] = {
                    'pl': 'wybitny uczony, prawnik kanonista, rektor Akademii Krakowskiej, prekursor prawa międzynarodowego na soborze w Konstancji',
                    'en': 'prominent scholar, canon jurist, Rector of the Kraków Academy, pioneer of international law at the Council of Constance',
                    'de': 'bedeutender Gelehrter, Kanonist, Rektor der Krakauer Akademie, Vorläufer des Völkerrechts auf dem Konzil von Konstanz'
                }
            elif rec['lp'] == 1663:
                patron['name'] = 'Paweł z Krosna'
                patron['birth_year'] = 1470
                patron['death_year'] = 1517
                patron['role'] = {
                    'pl': 'poeta nowołaciński, humanista renesansowy, profesor Akademii Krakowskiej i sekretarz królewski',
                    'en': 'Neo-Latin poet, Renaissance humanist, professor of the Kraków Academy, and royal secretary',
                    'de': 'neulateinischer Dichter, Renaissance-Humanist, Professor der Krakauer Akademie und königlicher Sekretär'
                }
            elif rec['lp'] == 1669:
                patron['name'] = 'Piast Kołodziej'
                patron['role'] = {
                    'pl': 'legendarny protoplasta dynastii Piastów, symbol gościnności, mądrości i rolniczych korzeni państwowości polskiej',
                    'en': 'legendary founder of the Piast dynasty, symbol of hospitality, wisdom, and early Polish statehood',
                    'de': 'legendärer Stammvater der Piasten-Dynastie, Symbol für Gastfreundschaft, Weisheit und frühe polnische Staatlichkeit'
                }
            elif rec['lp'] == 1678:
                patron['name'] = 'Piotr Bardowski'
                patron['birth_year'] = 1846
                patron['death_year'] = 1886
                patron['role'] = {
                    'pl': 'polski prawnik, sędzia pokoju, czołowy działacz partii I Proletariat, stracony na stokach Cytadeli Warszawskiej',
                    'en': 'Polish jurist, justice of the peace, leading activist of the First Proletariat party, executed at the Warsaw Citadel',
                    'de': 'polnischer Jurist, Friedensrichter, führender Aktivist der Partei Erstes Proletariat, hingerichtet auf der Warschauer Zitadelle'
                }
            elif rec['lp'] == 1679:
                patron['name'] = 'Piotr Borowy'
                patron['birth_year'] = 1858
                patron['death_year'] = 1932
                patron['role'] = {
                    'pl': 'orawski działacz ludowy i niepodległościowy, apostoł oświaty, delegat Polski na konferencję pokojową w Paryżu (1919)',
                    'en': 'Orava civic and independence activist, popular educator, Polish delegate to the Paris Peace Conference (1919)',
                    'de': 'Volks- und Unabhängigkeitsaktivist der Arwa, Bildungsreformer, polnischer Delegierter auf der Pariser Friedenskonferenz (1919)'
                }
            elif rec['lp'] == 1680:
                patron['name'] = 'Józef Piotr Brzeziński'
                patron['birth_year'] = 1862
                patron['death_year'] = 1939
                patron['role'] = {
                    'pl': 'biolog, botanik i ogrodnik, profesor Uniwersytetu Jagiellońskiego, dyrektor Ogrodu Botanicznego UJ',
                    'en': 'biologist, botanist and horticulturist, professor of the Jagiellonian University, director of the Botanic Garden in Kraków',
                    'de': 'Biologe, Botaniker und Gartenbauer, Professor der Jagiellonen-Universität, Direktor des Botanischen Gartens in Krakau'
                }
            elif rec['lp'] == 1681:
                patron['name'] = 'Piotr Kluzek'
                patron['birth_year'] = 1860
                patron['death_year'] = 1927
                patron['role'] = {
                    'pl': 'długoletni naczelnik (wójt) gminy Prądnik Biały (1906–1912), zasłużony działacz samorządowy i społeczny',
                    'en': 'longtime mayor (wójt) of the Prądnik Biały commune (1906–1912), local government leader and social activist',
                    'de': 'langjähriger Gemeindevorsteher (Vogt) von Prądnik Biały (1906–1912), Kommunalpolitiker und Sozialaktivist'
                }
            elif rec['lp'] == 1682:
                patron['name'] = 'Piotr Michałowski'
                patron['birth_year'] = 1800
                patron['death_year'] = 1855
                patron['role'] = {
                    'pl': 'wybitny malarz romantyczny, genialny batalista i portrecista, prezes Rady Administracyjnej Okręgu Krakowskiego (1848)',
                    'en': 'prominent Polish Romantic painter, master battle and portrait painter, civic leader in Kraków during the 1848 revolution',
                    'de': 'bedeutender polnischer Maler der Romantik, herausragender Schlachten- und Porträtmaler, Krakauer Bürgerführer (1848)'
                }
            elif rec['lp'] == 1683:
                patron['name'] = 'Piotr Stachiewicz'
                patron['birth_year'] = 1858
                patron['death_year'] = 1938
                patron['role'] = {
                    'pl': 'malarz i ilustrator okresu Młodej Polski, prezes Towarzystwa Przyjaciół Sztuk Pięknych w Krakowie, ilustrator dzieł Sienkiewicza i Mickiewicza',
                    'en': 'painter and illustrator of Young Poland, president of the Society of Friends of Fine Arts in Kraków',
                    'de': 'Maler und Illustrator des Jungen Polen, Präsident der Gesellschaft der Freunde der Schönen Künste in Krakau'
                }
            elif rec['lp'] == 1684:
                patron['name'] = 'Piotr Trębacz'
                patron['birth_year'] = 1875
                patron['death_year'] = 1939
                patron['role'] = {
                    'pl': 'krakowski mistrz budowlany, cechmistrz rzemiosła, radny miasta Podgórza i Krakowa, działacz społeczny i charytatywny',
                    'en': 'Kraków master builder, guild master, municipal councillor of Podgórze and Kraków, civic and philanthropic activist',
                    'de': 'Krakauer Baumeister, Zunftmeister, Stadtrat von Podgórze und Krakau, Sozialaktivist und Philanthrop'
                }
            elif rec['lp'] == 1685:
                patron['name'] = 'Piotr Wysocki'
                patron['birth_year'] = 1797
                patron['death_year'] = 1875
                patron['role'] = {
                    'pl': 'pułkownik Wojska Polskiego, przywódca sprzysiężenia podchorążych, inicjator powstania listopadowego (1830), bohater narodowy',
                    'en': 'Polish Army colonel, leader of the officer cadet conspiracy initiating the November Uprising (1830), national hero',
                    'de': 'Oberst der polnischen Armee, Anführer der Kadettenverschwörung zum Ausbruch des Novemberaufstandes (1830), Nationalheld'
                }
            elif rec['lp'] == 1687:
                patron['name'] = 'Pius Weloński'
                patron['birth_year'] = 1849
                patron['death_year'] = 1931
                patron['role'] = {
                    'pl': 'wybitny polski rzeźbiarz akademicki, dyrektor Szkoły Sztuk Pięknych w Warszawie, twórca słynnej rzeźby „Gladiator” w krakowskich Sukiennicach',
                    'en': 'prominent Polish academic sculptor, director of the School of Fine Arts in Warsaw, creator of the famous sculpture "Gladiator"',
                    'de': 'bedeutender polnischer akademischer Bildhauer, Direktor der Kunstschule in Warschau, Schöpfer der Skulptur „Gladiator“'
                }
            elif rec['lp'] == 1733:
                patron['name'] = 'Karol Pniak'
                patron['birth_year'] = 1910
                patron['death_year'] = 1980
                patron['role'] = {
                    'pl': 'podpułkownik pilot Wojska Polskiego, as myśliwski II wojny światowej, dowódca 308 Dywizjonu Krakowskiego',
                    'en': 'Polish Air Force Lieutenant Colonel, WWII flying ace, commander of No. 308 Kraków Squadron',
                    'de': 'Oberstleutnant der polnischen Luftwaffe, Jagdfliegerass des Zweiten Weltkriegs, Kommandeur der 308. Staffel'
                }
            elif rec['lp'] == 1760:
                patron['name'] = 'Antoni Stawarz'
                patron['birth_year'] = 1889
                patron['death_year'] = 1955
                patron['role'] = {
                    'pl': 'porucznik Wojska Polskiego, inicjator i przywódca oswobodzenia Krakowa z rąk austriackich 31 X 1918 r.',
                    'en': 'Polish Army lieutenant, leader of the liberation of Kraków from Austrian rule on 31 October 1918',
                    'de': 'Leutnant der polnischen Armee, Anführer der Befreiung Krakaus von der österreichischen Herrschaft am 31. Oktober 1918'
                }
            elif rec['lp'] == 1761:
                patron['name'] = 'Stanisław Pióro'
                patron['birth_year'] = 1923
                patron['death_year'] = 1949
                patron['role'] = {
                    'pl': 'porucznik podziemia niepodległościowego ps. „Emir”, dowódca Polskiej Podziemnej Armii Niepodległościowców',
                    'en': 'anti-communist underground lieutenant, commander of the Polish Underground Independence Army',
                    'de': 'Leutnant des antikommunistischen Untergrunds, Kommandeur der Polnischen Untergrund-Unabhängigkeitsarmee'
                }
            elif rec['lp'] == 1762:
                patron['name'] = 'Stanisława Rachwałowa'
                patron['birth_year'] = 1903
                patron['death_year'] = 1985
                patron['role'] = {
                    'pl': 'porucznik ZWZ-AK ps. „Halszka”, kurierka KG AK, więźniarka Auschwitz i Ravensbrück',
                    'en': 'Home Army lieutenant, courier of the AK Headquarters, Auschwitz and Ravensbrück survivor',
                    'de': 'Leutnant der Heimatarmee, Kurierin des Oberkommandos der AK, Überlebende von Auschwitz und Ravensbrück'
                }
            elif rec['lp'] == 1763:
                patron['name'] = 'Stanisław Szczeklik'
                patron['birth_year'] = 1905
                patron['death_year'] = 1940
                patron['role'] = {
                    'pl': 'porucznik rezerwy piechoty WP, adwokat, oficer 20 PP Ziemi Krakowskiej, ofiara zbrodni katyńskiej w Charkowie',
                    'en': 'Polish Army reserve lieutenant, lawyer, officer of the 20th Infantry Regiment, victim of the Katyn massacre in Kharkiv',
                    'de': 'Leutnant der Reserve, Rechtsanwalt, Offizier des 20. Infanterieregiments, Opfer des Massakers von Katyn in Charkiw'
                }
            elif rec['lp'] == 1764:
                patron['name'] = 'Jan Wąchała'
                patron['birth_year'] = 1922
                patron['death_year'] = 1946
                patron['role'] = {
                    'pl': 'porucznik Armii Krajowej ps. „Łazik”, dowódca oddziału partyzanckiego 1 PSP AK',
                    'en': 'Home Army lieutenant, commander of the 1st Podhale Rifles partisan detachment',
                    'de': 'Leutnant der Heimatarmee, Kommandeur der Partisanenabteilung des 1. Podhale-Schützenregiments'
                }
            elif rec['lp'] == 1769:
                patron['name'] = 'Powała z Taczewa'
                patron['birth_year'] = 1370
                patron['death_year'] = 1415
                patron['role'] = {
                    'pl': 'rycerz polski herbu Ogończyk, dyplomata króla Władysława Jagiełły, bohater bitwy pod Grunwaldem (1410)',
                    'en': 'Polish knight, diplomat of King Władysław II Jagiełło, hero of the Battle of Grunwald (1410)',
                    'de': 'polnischer Ritter, Diplomat von König Władysław II. Jagiełło, Held der Schlacht bei Tannenberg (1410)'
                }
            elif rec['lp'] == 1783:
                patron['name'] = 'Biskup Prandota z Białaczewa'
                patron['birth_year'] = 1200
                patron['death_year'] = 1266
                patron['role'] = {
                    'pl': 'biskup krakowski (1242–1266), doradca Bolesława Wstydliwego, inicjator kanonizacji św. Stanisława',
                    'en': 'Bishop of Kraków (1242–1266), advisor to Bolesław the Chaste, initiated the canonization of Saint Stanislaus',
                    'de': 'Bischof von Krakau (1242–1266), Berater von Bolesław dem Keuschen, Initiator der Heiligsprechung des hl. Stanislaus'
                }
            elif rec['lp'] == 1786:
                patron['name'] = 'Janina Bieniarzówna'
                patron['birth_year'] = 1916
                patron['death_year'] = 1997
                patron['role'] = {
                    'pl': 'historyczka, profesor WSP w Krakowie, autorka monografii dziejów Krakowa i współautorka „Dziejów Krakowa”',
                    'en': 'historian, professor at the Pedagogical University of Kraków, co-author of the seminal "History of Kraków"',
                    'de': 'Historikerin, Professorin an der Pädagogischen Universität Krakau, Mitautorin der „Geschichte Krakaus“'
                }
            elif rec['lp'] == 1787:
                patron['name'] = 'Adam Bochnak'
                patron['birth_year'] = 1899
                patron['death_year'] = 1974
                patron['role'] = {
                    'pl': 'historyk sztuki, profesor UJ, dyrektor Muzeum Narodowego w Krakowie i Muzeum UJ w Collegium Maius',
                    'en': 'art historian, professor at Jagiellonian University, director of the National Museum in Kraków',
                    'de': 'Kunsthistoriker, Professor an der Jagiellonen-Universität, Direktor des Nationalmuseums in Krakau'
                }
            elif rec['lp'] == 1788:
                patron['name'] = 'Adam Różański'
                patron['birth_year'] = 1874
                patron['death_year'] = 1940
                patron['role'] = {
                    'pl': 'inżynier hydrotechnik, profesor i dziekan Wydziału Rolniczego UJ, ofiara Sonderaktion Krakau',
                    'en': 'hydrotechnical engineer, professor and dean at Jagiellonian University, victim of Sonderaktion Krakau',
                    'de': 'Wasserbauingenieur, Professor und Dekan an der Jagiellonen-Universität, Opfer der Sonderaktion Krakau'
                }
            elif rec['lp'] == 1789:
                patron['name'] = 'Bolesław Wicherkiewicz'
                patron['birth_year'] = 1847
                patron['death_year'] = 1915
                patron['role'] = {
                    'pl': 'lekarz okulista, profesor Uniwersytetu Jagiellońskiego, twórca krakowskiej kliniki okulistycznej',
                    'en': 'ophthalmologist, professor at Jagiellonian University, founder of the Kraków ophthalmology clinic',
                    'de': 'Augenarzt, Professor an der Jagiellonen-Universität, Gründer der Krakauer Augenklinik'
                }
            elif rec['lp'] == 1790:
                patron['name'] = 'Bronisław Geremek'
                patron['birth_year'] = 1932
                patron['death_year'] = 2008
                patron['role'] = {
                    'pl': 'historyk mediewista, działacz „Solidarności”, minister spraw zagranicznych RP, eurodeputowany',
                    'en': 'medieval historian, Solidarity activist, Polish Minister of Foreign Affairs, Member of the European Parliament',
                    'de': 'Mittelalterhistoriker, Solidarność-Aktivist, polnischer Außenminister, Mitglied des Europäischen Parlaments'
                }
            elif rec['lp'] == 1791:
                patron['name'] = 'Henryk Wereszycki'
                patron['birth_year'] = 1898
                patron['death_year'] = 1990
                patron['role'] = {
                    'pl': 'historyk, profesor UJ, badacz dziejów XIX i XX w. oraz monarchii habsburskiej, autorytet opozycji',
                    'en': 'historian, professor at Jagiellonian University, scholar of 19th-20th century history and Habsburg monarchy',
                    'de': 'Historiker, Professor an der Jagiellonen-Universität, Erforscher des 19. und 20. Jahrhunderts und der Habsburgermonarchie'
                }
            elif rec['lp'] == 1792:
                patron['name'] = 'Jan Studniarski'
                patron['birth_year'] = 1876
                patron['death_year'] = 1946
                patron['role'] = {
                    'pl': 'elektrotechnik, profesor i rektor Akademii Górniczej w Krakowie, pionier elektryfikacji Małopolski',
                    'en': 'electrical engineer, professor and rector of the AGH University of Science and Technology',
                    'de': 'Elektrotechniker, Professor und Rektor der Bergakademie Krakau, Pionier der Elektrifizierung Kleinpolens'
                }
            elif rec['lp'] == 1793:
                patron['name'] = 'Jan Ślaski'
                patron['birth_year'] = 1893
                patron['death_year'] = 1984
                patron['role'] = {
                    'pl': 'pomolog i sadownik, profesor i dziekan Wydziału Rolniczo-Leśnego UJ, rektor WSR w Poznaniu',
                    'en': 'pomologist and horticulturist, professor and dean at Jagiellonian University, rector in Poznań',
                    'de': 'Pomologe und Obstbauer, Professor und Dekan an der Jagiellonen-Universität, Rektor in Posen'
                }
            elif rec['lp'] == 1794:
                patron['name'] = 'Jerzy Wiśniewski'
                patron['birth_year'] = 1928
                patron['death_year'] = 1983
                patron['role'] = {
                    'pl': 'historyk, demograf i genealog, badacz osadnictwa i stosunków własnościowych Małopolski',
                    'en': 'historian, demographer and genealogist, researcher of historical settlement and land ownership in Little Poland',
                    'de': 'Historiker, Demograf und Genealoge, Erforscher der historischen Besiedlung Kleinpolens'
                }
            elif rec['lp'] == 1795:
                patron['name'] = 'Kazimierz Opałek'
                patron['birth_year'] = 1918
                patron['death_year'] = 1995
                patron['role'] = {
                    'pl': 'prawnik, teoretyk i filozof prawa, profesor i prorektor UJ, członek rzeczywisty PAN',
                    'en': 'jurist, philosopher of law, professor and prorector of Jagiellonian University, member of PAN',
                    'de': 'Jurist, Rechtsphilosoph, Professor und Prorektor der Jagiellonen-Universität, Mitglied der PAN'
                }
            elif rec['lp'] == 1796:
                patron['name'] = 'Marian Mięsowicz'
                patron['birth_year'] = 1907
                patron['death_year'] = 1992
                patron['role'] = {
                    'pl': 'fizyk jądrowy, profesor AGH i UJ, wiceprezes PAN, twórca krakowskiej szkoły fizyki wysokich energii',
                    'en': 'nuclear physicist, professor at AGH and Jagiellonian University, vice-president of PAN',
                    'de': 'Kernphysiker, Professor an der AGH und der Jagiellonen-Universität, Vizepräsident der PAN'
                }
            elif rec['lp'] == 1797:
                patron['name'] = 'Marek Stachowski'
                patron['birth_year'] = 1936
                patron['death_year'] = 2004
                patron['role'] = {
                    'pl': 'kompozytor i pedagog, profesor i rektor Akademii Muzycznej w Krakowie',
                    'en': 'classical composer and educator, professor and rector of the Academy of Music in Kraków',
                    'de': 'Komponist und Hochschullehrer, Professor und Rektor der Musikakademie Krakau'
                }
            elif rec['lp'] == 1798:
                patron['name'] = 'Michał Bobrzyński'
                patron['birth_year'] = 1849
                patron['death_year'] = 1935
                patron['role'] = {
                    'pl': 'historyk prawa, profesor UJ, namiestnik Galicji (1908–1913), autor „Dziejów Polski w zarysie”',
                    'en': 'legal historian, professor at Jagiellonian University, Governor of Galicia (1908–1913)',
                    'de': 'Rechtshistoriker, Professor an der Jagiellonen-Universität, Statthalter von Galizien (1908–1913)'
                }
            elif rec['lp'] == 1799:
                patron['name'] = 'Michał Życzkowski'
                patron['birth_year'] = 1930
                patron['death_year'] = 2006
                patron['role'] = {
                    'pl': 'mechanik stosowany, profesor i rektor Politechniki Krakowskiej, członek rzeczywisty PAN i PAU',
                    'en': 'applied mechanics scholar, professor and rector of Tadeusz Kościuszko Cracow University of Technology',
                    'de': 'Professor für angewandte Mechanik, Rektor der Technischen Universität Krakau, Mitglied der PAN und PAU'
                }
            elif rec['lp'] == 1800:
                patron['name'] = 'Stanisław Łojasiewicz'
                patron['birth_year'] = 1926
                patron['death_year'] = 2002
                patron['role'] = {
                    'pl': 'matematyk, profesor Uniwersytetu Jagiellońskiego, członek PAN i PAU, twórca nierówności Łojasiewicza',
                    'en': 'mathematician, professor at Jagiellonian University, discoverer of the Łojasiewicz inequality',
                    'de': 'Mathematiker, Professor an der Jagiellonen-Universität, Entdecker der Łojasiewicz-Ungleichung'
                }
            elif rec['lp'] == 1801:
                patron['name'] = 'Stefan Myczkowski'
                patron['birth_year'] = 1923
                patron['death_year'] = 1977
                patron['role'] = {
                    'pl': 'leśnik, geobotanik i ekolog, profesor i prorektor Akademii Rolniczej w Krakowie, przewodniczący Komitetu Ochrony Przyrody PAN',
                    'en': 'forester, geobotanist and ecologist, professor and prorector of the Agricultural University of Kraków, head of Nature Conservation Committee PAN',
                    'de': 'Forstwissenschaftler, Geobotaniker und Ökologe, Professor und Prorektor der Landwirtschaftlichen Universität Krakau, Naturschützer'
                }
            elif rec['lp'] == 1802:
                patron['name'] = 'Tadeusz Seweryn'
                patron['birth_year'] = 1894
                patron['death_year'] = 1975
                patron['role'] = {
                    'pl': 'etnograf, muzeolog, prawnik, dyrektor Muzeum Etnograficznego w Krakowie, szef KWC Okręgu Kraków AK ps. „Zawisza”, Sprawiedliwy wśród Narodów Świata',
                    'en': 'ethnographer, museologist, director of the Ethnographic Museum in Kraków, Home Army civilian resistance chief, Righteous Among the Nations',
                    'de': 'Ethnograph, Museologe, Direktor des Ethnographischen Museums in Krakau, Heimatarmee-Widerstandsleiter, Gerechter unter den Völkern'
                }
            elif rec['lp'] == 1803:
                patron['name'] = 'Wojciech Bartel'
                patron['birth_year'] = 1923
                patron['death_year'] = 1992
                patron['role'] = {
                    'pl': 'historyk państwa i prawa polskiego oraz prawa kanonicznego, profesor Uniwersytetu Jagiellońskiego i Papieskiej Akademii Teologicznej w Krakowie',
                    'en': 'legal and church historian, professor at Jagiellonian University and the Pontifical Academy of Theology in Kraków',
                    'de': 'Rechts- und Kirchenhistoriker, Professor an der Jagiellonen-Universität und der Päpstlichen Theologischen Akademie in Krakau'
                }
            elif rec['lp'] == 1804:
                patron['name'] = 'Władysław Konopczyński'
                patron['birth_year'] = 1880
                patron['death_year'] = 1952
                patron['role'] = {
                    'pl': 'jeden z najwybitniejszych historyków polskich XX w., profesor UJ, członek PAU, twórca i pierwszy redaktor naczelny Polskiego Słownika Biograficznego',
                    'en': 'prominent Polish historian of the 20th century, professor at Jagiellonian University, founder and editor-in-chief of the Polish Biographical Dictionary',
                    'de': 'bedeutender polnischer Historiker des 20. Jahrhunderts, Professor an der Jagiellonen-Universität, Gründer des Polnischen Biographischen Wörterbuchs'
                }
            elif rec['lp'] == 1805:
                patron['name'] = 'Władysław Szafer'
                patron['birth_year'] = 1886
                patron['death_year'] = 1970
                patron['role'] = {
                    'pl': 'światowej sławy botanik, paleobotanik i ekolog, profesor i rektor Uniwersytetu Jagiellońskiego, pionier ochrony przyrody w Polsce i twórca parków narodowych',
                    'en': 'world-renowned botanist, paleobotanist and ecologist, professor and rector of Jagiellonian University, pioneer of nature conservation in Poland',
                    'de': 'weltbekannter Botaniker, Paläobotaniker und Ökologe, Professor und Rektor der Jagiellonen-Universität, Pionier des polnischen Naturschutzes'
                }
            elif rec['lp'] == 1806:
                patron['name'] = 'Włodzimierz Demetrykiewicz'
                patron['birth_year'] = 1859
                patron['death_year'] = 1937
                patron['role'] = {
                    'pl': 'archeolog, profesor Uniwersytetu Jagiellońskiego, dyrektor Muzeum Archeologicznego PAU, c.k. konserwator zabytków przedhistorycznych na Galicję Zachodnią',
                    'en': 'archaeologist, professor at Jagiellonian University, director of the Archaeological Museum of PAU, pioneer of modern excavation methodology',
                    'de': 'Archäologe, Professor an der Jagiellonen-Universität, Direktor des Archäologischen Museums der PAU, Konservator prähistorischer Denkmäler'
                }
            elif rec['lp'] == 1807:
                patron['name'] = 'Zygmunt Chyliński'
                patron['birth_year'] = 1930
                patron['death_year'] = 1994
                patron['role'] = {
                    'pl': 'fizyk teoretyk i jądrowy, profesor Instytutu Fizyki Jądrowej PAN w Krakowie, twórca relacyjnej teorii czasoprzestrzeni',
                    'en': 'theoretical and nuclear physicist, professor at the Institute of Nuclear Physics PAN in Kraków, creator of the relational spacetime theory',
                    'de': 'theoretischer Physiker und Kernphysiker, Professor am Institut für Kernphysik der PAN in Krakau, Begründer der relationalen Raum-Zeit-Theorie'
                }
            elif rec['lp'] == 1822:
                patron['name'] = 'Przemysł II'
                patron['birth_year'] = 1257
                patron['death_year'] = 1296
                patron['role'] = {
                    'pl': 'książę wielkopolski, poznański i krakowski, król Polski od 1295 r., odnowiciel herbu Orła Białego jako herbu państwa polskiego',
                    'en': 'Duke of Greater Poland and Kraków, King of Poland from 1295, restorer of the White Eagle as the national emblem of Poland',
                    'de': 'Herzog von Großpolen und Krakau, König von Polen ab 1295, Erneuerer des Weißen Adlers als polnisches Staatswappen'
                }
            elif rec['lp'] == 1857:
                patron['name'] = 'Przemysław Barthel de Weydenthal'
                patron['birth_year'] = 1893
                patron['death_year'] = 1919
                patron['role'] = {
                    'pl': 'pułkownik Wojska Polskiego ps. „Barty”, oficer I Brygady Legionów Polskich, komendant naczelny POW na Wschodzie, kawaler Orderu Virtuti Militari',
                    'en': 'Polish Army colonel, officer of the Polish Legions First Brigade, commander-in-chief of the Polish Military Organisation in the East',
                    'de': 'Oberst der polnischen Armee, Offizier der 1. Brigade der Polnischen Legionen, Oberkommandierender der Polnischen Militärorganisation im Osten'
                }
            elif rec['lp'] == 1858:
                patron['name'] = 'Edward Godlewski'
                patron['birth_year'] = 1895
                patron['death_year'] = 1945
                patron['role'] = {
                    'pl': 'pułkownik dyplomowany kawalerii WP ps. „Garda”, dowódca 14 Pułku Ułanów Jazłowieckich, komendant Okręgu Kraków Armii Krajowej, zamordowany w Mauthausen',
                    'en': 'Polish cavalry colonel, commander of the 14th Jazłowiecki Uhlan Regiment, commander of the Kraków District of the Home Army, murdered in Mauthausen',
                    'de': 'polnischer Kavallerieoberst, Kommandeur des 14. Ulanenregiments, Kommandant des Heimatarmee-Distrikts Krakau, ermordet im KZ Mauthausen'
                }
            elif rec['lp'] == 1859:
                patron['name'] = 'Francesco Nullo'
                patron['birth_year'] = 1826
                patron['death_year'] = 1863
                patron['role'] = {
                    'pl': 'włoski pułkownik, bohater walk o zjednoczenie Włoch, dowódca ochotników w powstaniu styczniowym 1863 r., poległy pod Krzykawką',
                    'en': 'Italian colonel, hero of the Italian unification, commander of foreign volunteers in the January Uprising 1863, fallen at Krzykawka',
                    'de': 'italienischer Oberst, Held der italienischen Einigung, Kommandeur der Freiwilligen im Januaraufstand 1863, gefallen bei Krzykawka'
                }
            elif rec['lp'] == 1860:
                patron['name'] = 'Józef Spychalski'
                patron['birth_year'] = 1898
                patron['death_year'] = 1944
                patron['role'] = {
                    'pl': 'pułkownik dyplomowany piechoty WP, cichociemny, komendant Okręgu Kraków Armii Krajowej (1942–1944), zamordowany w Sachsenhausen',
                    'en': 'Polish Army infantry colonel, Silent Unseen (Cichociemny), commander of the Kraków District of the Home Army (1942–1944), murdered in Sachsenhausen',
                    'de': 'Oberst der polnischen Infanterie, Cichociemny-Fallschirmspringer, Kommandant des Distrikts Krakau der Heimatarmee, ermordet in Sachsenhausen'
                }
            elif rec['lp'] == 1861:
                patron['name'] = 'Stefan Łaszkiewicz'
                patron['birth_year'] = 1905
                patron['death_year'] = 2002
                patron['role'] = {
                    'pl': 'pułkownik pilot Wojska Polskiego i RAF, as myśliwski, dowódca 308 Dywizjonu Krakowskiego, 303 Dywizjonu oraz 131 Skrzydła Myśliwskiego',
                    'en': 'Polish Air Force and RAF colonel pilot, fighter ace, commander of No. 308 Kraków Squadron, No. 303 Squadron and 131st Fighter Wing',
                    'de': 'Oberst und Jagdflieger der polnischen Luftwaffe und der RAF, Fliegerass, Kommandeur der Jagdstaffeln 308 und 303 sowie des 131. Jagdgeschwaders'
                }
            elif rec['lp'] == 1862:
                patron['name'] = 'Ryszard Kukliński'
                patron['birth_year'] = 1930
                patron['death_year'] = 2004
                patron['role'] = {
                    'pl': 'pułkownik Wojska Polskiego ps. „Jack Strong”, oficer Sztabu Generalnego WP, tajny współpracownik CIA, Honorowy Obywatel Miasta Krakowa',
                    'en': 'Polish Army colonel ("Jack Strong"), General Staff officer, secret CIA operative during the Cold War, Honorary Citizen of Kraków',
                    'de': 'Oberst der polnischen Armee („Jack Strong“), Offizier des Generalstabs, geheimer CIA-Informant im Kalten Krieg, Ehrenbürger von Krakau'
                }
            elif rec['lp'] == 1863:
                patron['name'] = 'Stanisław Dąbek'
                patron['birth_year'] = 1892
                patron['death_year'] = 1939
                patron['role'] = {
                    'pl': 'pułkownik piechoty Wojska Polskiego, dowódca Lądowej Obrony Wybrzeża w 1939 r., poległy bohatersko na Kępie Oksywskiej, pośmiertnie generał brygady',
                    'en': 'Polish Army infantry colonel, commander of the Coastal Land Defence in 1939, heroically fallen at Kępa Oksywska, posthumously promoted to general',
                    'de': 'Oberst der polnischen Infanterie, Kommandeur der Küstenlandverteidigung 1939, heldenhaft gefallen auf der Kępa Oksywska, postum zum General ernannt'
                }
            elif rec['lp'] == 1864:
                patron['name'] = 'Władysław Belina-Prażmowski'
                patron['birth_year'] = 1888
                patron['death_year'] = 1938
                patron['role'] = {
                    'pl': 'pułkownik kawalerii WP, organizator „siódemki Beliny”, dowódca 1 Pułku Ułanów Legionów Polskich, prezydent Krakowa (1931–1933) i wojewoda lwowski',
                    'en': 'Polish cavalry colonel, founder of the famous 1914 patrol and 1st Uhlan Regiment of the Polish Legions, Mayor of Kraków (1931–1933), voivode of Lwów',
                    'de': 'polnischer Kavallerieoberst, Schöpfer des 1. Ulanenregiments der Polnischen Legionen, Stadtpräsident von Krakau (1931–1933), Woiwode von Lemberg'
                }
            elif rec['lp'] == 1887:
                patron['name'] = 'Rafał Józef Czerwiakowski'
                patron['birth_year'] = 1743
                patron['death_year'] = 1816
                patron['role'] = {
                    'pl': 'lekarz, anatom, chirurg i położnik, profesor Szkoły Głównej Koronnej (UJ), reformator medycyny uniwersyteckiej, „ojciec polskiej chirurgii”',
                    'en': 'physician, anatomist and surgeon, professor at Jagiellonian University, reformer of Polish academic medicine, "father of Polish surgery"',
                    'de': 'Arzt, Anatom und Chirurg, Professor an der Jagiellonen-Universität, Reformer der polnischen Hochschulmedizin, „Vater der polnischen Chirurgie“'
                }
            elif rec['lp'] == 1899:
                patron['name'] = 'Robert Jahoda'
                patron['birth_year'] = 1862
                patron['death_year'] = 1947
                patron['role'] = {
                    'pl': 'mistrz introligatorski, twórca słynnego krakowskiego Zakładu Artystyczno-Introligatorskiego, artysta opraw książkowych, nestor polskiego introligatorstwa',
                    'en': 'master bookbinder, founder of renowned artistic bookbinding atelier in Kraków, creator of artistic book bindings, doyen of Polish craft bookbinding',
                    'de': 'Buchbindermeister, Gründer des berühmten Krakauer Kunstbuchbinderei-Ateliers, Nestor des polnischen Buchbinderhandwerks'
                }
            elif rec['lp'] == 2303:
                patron['name'] = 'Teodor Axentowicz'
                patron['birth_year'] = 1859
                patron['death_year'] = 1938
                patron['role'] = {
                    'pl': 'malarz, pastelista i pedagog ormiańskiego pochodzenia, profesor i pierwszy wybrany rektor krakowskiej ASP',
                    'en': 'painter, pastellist and educator of Armenian origin, professor and first elected rector of the Kraków Academy of Fine Arts',
                    'de': 'Maler, Pastellist und Pädagoge armenischer Herkunft, Professor und erster gewählter Rektor der Krakauer Akademie der Bildenden Künste'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Teodor_Axentowicz'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Teodor_Axentowicz'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Teodor_Axentowicz',
                    'en': 'https://en.wikipedia.org/wiki/Teodor_Axentowicz'
                }
            elif rec['lp'] == 2304:
                patron['name'] = 'Teodor Parnicki'
                patron['birth_year'] = 1908
                patron['death_year'] = 1988
                patron['role'] = {
                    'pl': 'wybitny pisarz, twórca nowoczesnej polskiej powieści historycznej i historiozoficznej („Srebrne orły”, „Tylko Beatrycze”)',
                    'en': 'prominent Polish writer, creator of modern Polish historiosophical and psychological historical novels',
                    'de': 'bedeutender polnischer Schriftsteller, Schöpfer moderner historiosophischer und psychologischer historischer Romane'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Teodor_Parnicki'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Teodor_Parnicki'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Teodor_Parnicki',
                    'en': 'https://en.wikipedia.org/wiki/Teodor_Parnicki'
                }
            elif rec['lp'] == 2305:
                patron['name'] = 'Teodor Rygier'
                patron['birth_year'] = 1841
                patron['death_year'] = 1913
                patron['role'] = {
                    'pl': 'rzeźbiarz, twórca pomnika Adama Mickiewicza na Rynku Głównym w Krakowie oraz rzeźb alegorycznych w Sukiennicach',
                    'en': 'sculptor, creator of the Adam Mickiewicz Monument on the Main Market Square in Kraków and allegorical sculptures in the Cloth Hall',
                    'de': 'Bildhauer, Schöpfer des Adam-Mickiewicz-Denkmals auf dem Hauptmarkt in Krakau und allegorischer Skulpturen in den Tuchhallen'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Teodor_Rygier'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Teodor_Rygier'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Teodor_Rygier',
                    'en': 'https://en.wikipedia.org/wiki/Teodor_Rygier'
                }
            elif rec['lp'] == 2306:
                patron['name'] = 'Teodor Talowski'
                patron['birth_year'] = 1857
                patron['death_year'] = 1910
                patron['role'] = {
                    'pl': 'wybitny architekt historyzmu i modernizmu, zwany „polskim Gaudim”, autor słynnych kamienic, kościołów i wiaduktu przy ul. Lubicz',
                    'en': 'prominent historicist and modernist architect ("Polish Gaudi"), designer of celebrated Kraków townhouses and churches',
                    'de': 'herausragender Architekt des Historismus und Jugendstils („polnischer Gaudí“), Schöpfer berühmter Krakauer Bürgerhäuser und Kirchen'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Teodor_Talowski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Teodor_Talowski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Teodor_Talowski',
                    'en': 'https://en.wikipedia.org/wiki/Teodor_Talowski'
                }
            elif rec['lp'] == 2307:
                patron['name'] = 'Teofil Lenartowicz'
                patron['birth_year'] = 1822
                patron['death_year'] = 1893
                patron['role'] = {
                    'pl': 'poeta romantyczny zwany „Lirnikiem mazowieckim”, rzeźbiarz, konspirator niepodległościowy, spoczywający na Skałce',
                    'en': 'Romantic poet ("Mazovian Lyrist"), sculptor and independence conspirator, buried in the Crypt of the Meritorious on Skałka',
                    'de': 'romantischer Dichter („Masowischer Lyriker“), Bildhauer und Unabhängigkeitskämpfer, begraben in der Krypta auf dem Skałka'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Teofil_Lenartowicz'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Teofil_Lenartowicz'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Teofil_Lenartowicz',
                    'en': 'https://en.wikipedia.org/wiki/Teofil_Lenartowicz'
                }
            elif rec['lp'] == 2310:
                patron['name'] = 'Tomasz Arciszewski'
                patron['birth_year'] = 1877
                patron['death_year'] = 1955
                patron['role'] = {
                    'pl': 'działacz socjalistyczny, bojowiec OB PPS, poseł na Sejm II RP, premier Rządu RP na Uchodźstwie (1944–1947)',
                    'en': 'socialist leader, PPS combatant, member of parliament of the Second Polish Republic, Prime Minister of the Polish Government in Exile (1944–1947)',
                    'de': 'sozialistischer Politiker, PPS-Kämpfer, Abgeordneter der Zweiten Polnischen Republik, Ministerpräsident der polnischen Exilregierung (1944–1947)'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Tomasz_Arciszewski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Tomasz_Arciszewski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Tomasz_Arciszewski',
                    'en': 'https://en.wikipedia.org/wiki/Tomasz_Arciszewski'
                }
            elif rec['lp'] == 2311:
                patron['name'] = 'Tomasz Janiszewski'
                patron['birth_year'] = 1867
                patron['death_year'] = 1939
                patron['role'] = {
                    'pl': 'lekarz epidemiolog, higienista, profesor UJ, pierwszy minister zdrowia publicznego i opieki społecznej II RP (1919)',
                    'en': 'epidemiologist and hygienist, professor at Jagiellonian University, first Minister of Public Health of the Second Polish Republic (1919)',
                    'de': 'Epidemiologe und Hygieniker, Professor an der Jagiellonen-Universität, erster Minister für öffentliche Gesundheit der Zweiten Polnischen Republik (1919)'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Tomasz_Janiszewski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Tomasz_Janiszewski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Tomasz_Janiszewski',
                    'en': 'https://en.wikipedia.org/wiki/Tomasz_Janiszewski'
                }
            elif rec['lp'] == 2312:
                patron['name'] = 'Tomasz Pryliński'
                patron['birth_year'] = 1847
                patron['death_year'] = 1895
                patron['role'] = {
                    'pl': 'architekt i konserwator zabytków, autor projektu wielkiej restauracji i neorenesansowych arkad krakowskich Sukiennic (1875–1879)',
                    'en': 'architect and conservator, designer of the grand restoration and neo-Renaissance arcades of the Kraków Cloth Hall (1875–1879)',
                    'de': 'Architekt und Denkmalpfleger, Schöpfer der großen Restaurierung und der Neorenaissance-Arkaden der Krakauer Tuchhallen (1875–1879)'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Tomasz_Pryli%C5%84ski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Tomasz_Pryli%C5%84ski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Tomasz_Pryli%C5%84ski',
                    'en': 'https://en.wikipedia.org/wiki/Tomasz_Pryli%C5%84ski'
                }
            elif rec['lp'] == 2313:
                patron['name'] = 'Tomasz Zan'
                patron['birth_year'] = 1796
                patron['death_year'] = 1855
                patron['role'] = {
                    'pl': 'poeta preromantyczny, współzałożyciel Towarzystwa Filomatów i przywódca Zgromadzenia Filaretów w Wilnie, przyjaciel Adama Mickiewicza',
                    'en': 'pre-Romantic poet, co-founder of the Philomaths and leader of the Filarets in Vilnius, friend of Adam Mickiewicz',
                    'de': 'vorromantischer Dichter, Mitbegründer der Philomaten und Führer der Philareten in Wilna, Freund von Adam Mickiewicz'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Tomasz_Zan'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Tomasz_Zan'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Tomasz_Zan',
                    'en': 'https://en.wikipedia.org/wiki/Tomasz_Zan'
                }
            elif rec['lp'] == 2345:
                patron['name'] = 'Maria Turzyma'
                patron['birth_year'] = 1860
                patron['death_year'] = 1922
                patron['role'] = {
                    'pl': 'publicystka, pisarka i pionierka galicyjskiego ruchu emancypacji kobiet, założycielka i redaktorka krakowskiego pisma „Nowe Słowo”',
                    'en': 'publicist, writer and pioneer of the Galician women\'s emancipation movement, founder and editor of "Nowe Słowo" in Kraków',
                    'de': 'Publizistin, Schriftstellerin und Pionierin der galizischen Frauenbewegung, Gründerin und Herausgeberin von „Nowe Słowo“ in Krakau'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Maria_Turzyma'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Maria_Turzyma'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Maria_Turzyma'
                }
            elif rec['lp'] == 2351:
                patron['name'] = 'Tytus Chałubiński'
                patron['birth_year'] = 1820
                patron['death_year'] = 1889
                patron['role'] = {
                    'pl': 'lekarz internista, profesor medycyny, przyrodnik, pionier polskiej balneologii i klimatologii, współtwórca Towarzystwa Tatrzańskiego',
                    'en': 'physician, professor of medicine, naturalist, pioneer of Polish balneology and climatology, co-founder of the Tatra Society',
                    'de': 'Arzt, Medizinprofessor, Naturforscher, Pionier der polnischen Balneologie und Klimatologie, Mitbegründer der Tatra-Gesellschaft'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Tytus_Cha%C5%82ubi%C5%84ski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Tytus_Cha%C5%82ubi%C5%84ski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Tytus_Cha%C5%82ubi%C5%84ski',
                    'en': 'https://en.wikipedia.org/wiki/Tytus_Cha%C5%82ubi%C5%84ski'
                }
            elif rec['lp'] == 2352:
                patron['name'] = 'Tytus Czyżewski'
                patron['birth_year'] = 1880
                patron['death_year'] = 1945
                patron['role'] = {
                    'pl': 'malarz awangardowy, poeta futurystyczny i krytyk sztuki, współtwórca krakowskiej grupy „Formiści” (1917)',
                    'en': 'avant-garde painter, futurist poet and art theorist, co-founder of the Kraków "Formists" group (1917)',
                    'de': 'Avantgarde-Maler, futuristischer Dichter und Kunsttheoretiker, Mitbegründer der Krakauer Künstlergruppe „Formisten“ (1917)'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Tytus_Czy%C5%BCewski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Tytus_Czy%C5%BCewski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Tytus_Czy%C5%BCewski',
                    'en': 'https://en.wikipedia.org/wiki/Tytus_Czy%C5%BCewski'
                }
            elif rec['lp'] == 2369:
                patron['name'] = 'Vlastimil Hofman'
                patron['birth_year'] = 1881
                patron['death_year'] = 1970
                patron['role'] = {
                    'pl': 'malarz symbolista pochodzenia czesko-polskiego, uczeń Jacka Malczewskiego, tworzący przez dziesięciolecia na krakowskim Zwierzyńcu',
                    'en': 'symbolist painter of Czech-Polish heritage, student of Jacek Malczewski, working for decades in Kraków\'s Zwierzyniec',
                    'de': 'symbolistischer Maler tschechisch-polnischer Herkunft, Schüler von Jacek Malczewski, jahrzehntelang im Krakauer Zwierzyniec tätig'
                }
                patron['image'] = ''
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Vlastimil_Hofman'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Vlastimil_Hofman'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Vlastimil_Hofman',
                    'en': 'https://en.wikipedia.org/wiki/Vlastimil_Hofman'
                }
            elif rec['lp'] == 2370:
                patron['name'] = 'Wacław Gąsiorowski'
                patron['birth_year'] = 1869
                patron['death_year'] = 1939
                patron['role'] = {
                    'pl': 'pisarz, publicysta i działacz niepodległościowy, autor popularnych powieści historycznych z epoki napoleońskiej („Huragan”)',
                    'en': 'writer, publicist and independence activist, author of celebrated Napoleonic historical novels ("Huragan")',
                    'de': 'Schriftsteller, Publizist und Unabhängigkeitsaktivist, Autor populärer historischer Romane aus der napoleonischen Zeit („Huragan“)'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_G%C4%85siorowski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_G%C4%85siorowski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_G%C4%85siorowski',
                    'en': 'https://en.wikipedia.org/wiki/Wac%C5%82aw_G%C4%85siorowski'
                }
            elif rec['lp'] == 2371:
                patron['name'] = 'Wacław Król'
                patron['birth_year'] = 1915
                patron['death_year'] = 1991
                patron['role'] = {
                    'pl': 'pułkownik pilot Wojska Polskiego, as myśliwski II wojny światowej, dowódca dywizjonu 302 i Polskiego Skrzydła Myśliwskiego',
                    'en': 'colonel pilot of the Polish Air Force, World War II fighter ace, commander of No. 302 Squadron and the Polish Fighter Wing',
                    'de': 'Oberst der polnischen Luftwaffe, Jagdfliegerass des Zweiten Weltkriegs, Kommandeur der 302. Staffel und des polnischen Jagdgeschwaders'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Kr%C3%B3l_(pilot)'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Kr%C3%B3l_(pilot)'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Kr%C3%B3l_(pilot)',
                    'en': 'https://en.wikipedia.org/wiki/Wac%C5%82aw_Kr%C3%B3l'
                }
            elif rec['lp'] == 2372:
                patron['name'] = 'Wacław Lipiński'
                patron['birth_year'] = 1896
                patron['death_year'] = 1949
                patron['role'] = {
                    'pl': 'podpułkownik WP, historyk wojskowości, szef propagandy Dowództwa Obrony Warszawy (1939), prezes KPOPP, ofiara zbrodni komunistycznej',
                    'en': 'lieutenant colonel of the Polish Army, military historian, head of propaganda for the Warsaw Defence Command (1939), anti-communist resistance leader',
                    'de': 'Oberstleutnant der polnischen Armee, Militärhistoriker, Propagandachef des Verteidigungskommandos Warschau (1939), antikommunistischer Widerstandsführer'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Lipi%C5%84ski_(historyk)'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Lipi%C5%84ski_(historyk)'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Lipi%C5%84ski_(historyk)',
                    'en': 'https://en.wikipedia.org/wiki/Wac%C5%82aw_Lipi%C5%84ski'
                }
            elif rec['lp'] == 2373:
                patron['name'] = 'Wacław Nałkowski'
                patron['birth_year'] = 1851
                patron['death_year'] = 1911
                patron['role'] = {
                    'pl': 'wybitny geograf, pedagog, publicysta i działacz społeczny, twórca nowoczesnej polskiej geografii rozumowej (antropogeografii)',
                    'en': 'prominent geographer, educator and publicist, pioneer of modern conceptual human geography in Poland',
                    'de': 'herausragender Geograph, Pädagoge und Publizist, Pionier der modernen Humangeographie in Polen'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Na%C5%82kowski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Na%C5%82kowski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Na%C5%82kowski',
                    'en': 'https://en.wikipedia.org/wiki/Wac%C5%82aw_Na%C5%82kowski'
                }
            elif rec['lp'] == 2374:
                patron['name'] = 'Wacław Popławski'
                patron['birth_year'] = 1866
                patron['death_year'] = 1936
                patron['role'] = {
                    'pl': 'inżynier kolejowy, długoletni zawiadowca stacji Kraków-Prokocim, prezes Spółdzielni Mieszkaniowej Kolejarzy, Honorowy Obywatel Prokocimia',
                    'en': 'railway engineer, stationmaster of Kraków-Prokocim, chairman of the Railway Workers\' Housing Cooperative, Honorary Citizen of Prokocim',
                    'de': 'Eisenbahningenieur, Bahnhofsvorsteher von Kraków-Prokocim, Vorsitzender der Eisenbahner-Wohnungsbaugenossenschaft, Ehrenbürger von Prokocim'
                }
                patron['image'] = ''
            elif rec['lp'] == 2375:
                patron['name'] = 'Wacław Sieroszewski'
                patron['birth_year'] = 1858
                patron['death_year'] = 1945
                patron['role'] = {
                    'pl': 'pisarz, podróżnik, badacz etnografii Syberii i Jakucji, legionista I Brygady, senator II RP i prezes Polskiej Akademii Literatury',
                    'en': 'writer, explorer, ethnographer of Siberia and Yakutia, Polish Legions soldier, senator and president of the Polish Academy of Literature',
                    'de': 'Schriftsteller, Forscher, Ethnograph Sibiriens und Jakutiens, Legionär, Senator und Präsident der Polnischen Literaturakademie'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Sieroszewski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Sieroszewski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Wac%C5%82aw_Sieroszewski',
                    'en': 'https://en.wikipedia.org/wiki/Wac%C5%82aw_Sieroszewski'
                }
            elif rec['lp'] == 2378:
                patron['name'] = 'Walenty Florkowski'
                patron['birth_year'] = 1795
                patron['death_year'] = None
                patron['role'] = {
                    'pl': 'gospodarz, samorządowiec i działacz społeczności włościańskiej w podkrakowskim Pleszowie i Krzesławicach',
                    'en': 'farmer, local official and rural community activist in sub-Kraków Pleszów and Krzesławice',
                    'de': 'Landwirt, Kommunalpolitiker und ländlicher Aktivist in Pleszów und Krzesławice bei Krakau'
                }
                patron['image'] = ''
            elif rec['lp'] == 2379:
                patron['name'] = 'Walery Eljasz-Radzikowski'
                patron['birth_year'] = 1841
                patron['death_year'] = 1905
                patron['role'] = {
                    'pl': 'malarz i grafik historyczny, pionier taternictwa, autor pierwszego nowoczesnego przewodnika po Tatrach (1870), współtwórca Towarzystwa Tatrzańskiego',
                    'en': 'history painter and graphic artist, pioneer of Tatra mountaineering, author of the first modern Tatra guide (1870), co-founder of the Tatra Society',
                    'de': 'Historienmaler und Grafiker, Pionier des Tatra-Bergsteigens, Verfasser des ersten modernen Tatra-Führers (1870), Mitbegründer der Tatra-Gesellschaft'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Walery_Eljasz-Radzikowski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Walery_Eljasz-Radzikowski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Walery_Eljasz-Radzikowski',
                    'en': 'https://en.wikipedia.org/wiki/Walery_Eljasz-Radzikowski'
                }
            elif rec['lp'] == 2380:
                patron['name'] = 'Walery Gadomski'
                patron['birth_year'] = 1833
                patron['death_year'] = 1911
                patron['role'] = {
                    'pl': 'rzeźbiarz, profesor krakowskiej Szkoły Sztuk Pięknych, powstaniec styczniowy 1863 r., twórca rzeźb w Sukiennicach i krakowskich kościołach',
                    'en': 'sculptor, professor at the Kraków School of Fine Arts, January Uprising 1863 veteran, creator of sculptures in the Cloth Hall',
                    'de': 'Bildhauer, Professor an der Krakauer Schule der Bildenden Künste, Januaraufständischer von 1863, Schöpfer von Skulpturen in den Tuchhallen'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Walery_Gadomski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Walery_Gadomski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Walery_Gadomski',
                    'en': 'https://en.wikipedia.org/wiki/Walery_Gadomski'
                }
            elif rec['lp'] == 2381:
                patron['name'] = 'Walery Goetel'
                patron['birth_year'] = 1889
                patron['death_year'] = 1972
                patron['role'] = {
                    'pl': 'geolog, profesor i rektor AGH (1939–1951), członek rzeczywisty PAN, pionier sozologii i twórca parków narodowych w Tatrach i Pieninach',
                    'en': 'geologist, professor and rector of AGH (1939–1951), member of PAN, pioneer of sozology and founder of national parks in Tatras and Pieniny',
                    'de': 'Geologe, Professor und Rektor der AGH (1939–1951), Mitglied der PAN, Pionier der Sozologie und Gründer der Nationalparks in der Tatra und den Pieninen'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Walery_Goetel'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Walery_Goetel'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Walery_Goetel',
                    'en': 'https://en.wikipedia.org/wiki/Walery_Goetel'
                }
            elif rec['lp'] == 2382:
                patron['name'] = 'Walery Sławek'
                patron['birth_year'] = 1879
                patron['death_year'] = 1939
                patron['role'] = {
                    'pl': 'podpułkownik WP, trzykrotny premier Rzeczypospolitej Polskiej, marszałek Sejmu II RP, współtwórca Konstytucji kwietniowej 1935 r.',
                    'en': 'lieutenant colonel of the Polish Army, three-time Prime Minister of Poland, Marshal of the Sejm, co-author of the April Constitution 1935',
                    'de': 'Oberstleutnant der polnischen Armee, dreifacher Ministerpräsident Polens, Sejmmarschall, Mitverfasser der April-Verfassung von 1935'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Walery_S%C5%82awek'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Walery_S%C5%82awek'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Walery_S%C5%82awek',
                    'en': 'https://en.wikipedia.org/wiki/Walery_S%C5%82awek'
                }
            elif rec['lp'] == 2383:
                patron['name'] = 'Walerian Tumanowicz'
                patron['birth_year'] = 1894
                patron['death_year'] = 1947
                patron['role'] = {
                    'pl': 'major piechoty WP, oficer Legionów Polskich i AK, prezes Okręgu Kraków WiN, ofiara zbrodni komunistycznej skazana w procesie krakowskim',
                    'en': 'major of the Polish Army, Polish Legions and Home Army officer, WiN Kraków District president, victim of communist judicial murder',
                    'de': 'Major der polnischen Infanterie, Offizier der Legionen und der Heimatarmee, WiN-Bezirksvorsitzender Krakau, Opfer kommunistischer Justizmorde'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Walerian_Tumanowicz'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Walerian_Tumanowicz'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Walerian_Tumanowicz',
                    'en': 'https://en.wikipedia.org/wiki/Walerian_Tumanowicz'
                }
            elif rec['lp'] == 2384:
                patron['name'] = 'Walerian Łukasiński'
                patron['birth_year'] = 1786
                patron['death_year'] = 1868
                patron['role'] = {
                    'pl': 'major 4 Pułku Piechoty Liniowej (Czwartaków), założyciel Wolnomularstwa Narodowego i Towarzystwa Patriotycznego, więzień caratu przez 46 lat',
                    'en': 'major of the 4th Line Infantry Regiment, founder of the National Freemasonry and Patriotic Society, prisoner of Tsarist Russia for 46 years',
                    'de': 'Major des 4. Linien-Infanterieregiments, Gründer der Nationalen Freimaurerei und Patriotischen Gesellschaft, 46 Jahre zaristischer Häftling'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Walerian_%C5%81ukasi%C5%84ski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Walerian_%C5%81ukasi%C5%84ski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Walerian_%C5%81ukasi%C5%84ski',
                    'en': 'https://en.wikipedia.org/wiki/Walerian_%C5%81ukasi%C5%84ski'
                }
            elif rec['lp'] == 2392:
                patron['name'] = 'Jonatan Warszauer'
                patron['birth_year'] = 1820
                patron['death_year'] = 1888
                patron['role'] = {
                    'pl': 'lekarz, uczestnik powstania krakowskiego 1846 r., filantrop i działacz społeczny asymilacji krakowskich Żydów',
                    'en': 'physician, participant of the 1846 Kraków Uprising, philanthropist and social activist for Jewish assimilation',
                    'de': 'Arzt, Teilnehmer am Krakauer Aufstand 1846, Philanthrop und Förderer der jüdischen Assimilation in Krakau'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jonatan_Warszauer'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jonatan_Warszauer'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jonatan_Warszauer'
                }
            elif rec['lp'] == 2399:
                patron['name'] = 'Wernyhora'
                patron['birth_year'] = None
                patron['death_year'] = None
                patron['role'] = {
                    'pl': 'legendarny XVIII-wieczny lirnik i wieszcz kozacki, przepowiadający odrodzenie niepodległej Polski, bohater „Wesela” Wyspiańskiego',
                    'en': 'legendary 18th-century Cossack bard and seer, prophesying the resurrection of Poland, prominent figure in Wyspiański\'s "The Wedding"',
                    'de': 'legendärer Kosakenbarde und Seher des 18. Jahrhunderts, Weissager der Wiedergeburt Polens, Gestalt in Wyspiańskis „Die Hochzeitsfeier“'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Wernyhora'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Wernyhora'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Wernyhora',
                    'en': 'https://en.wikipedia.org/wiki/Wernyhora'
                }
            # Dedykowane aktualizacje patronów partii 27
            elif rec['lp'] == 2606:
                patron['name'] = 'Zawisza Czarny'
                patron['birth_year'] = 1370
                patron['death_year'] = 1428
                patron['role'] = {
                    'pl': 'najsłynniejszy rycerz polskiego średniowiecza, dyplomata króla Władysława Jagiełły, bohater bitwy pod Grunwaldem (1410), symbol cnót rycerskich',
                    'en': 'most renowned Polish medieval knight, diplomat of King Władysław II Jagiełło, hero of the Battle of Grunwald (1410), symbol of chivalric virtue',
                    'de': 'berühmtester polnischer Ritter des Mittelalters, Diplomat von König Władysław II. Jagiełło, Held der Schlacht bei Tannenberg (1410), Symbol ritterlicher Tugenden'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zawisza%20Czarny%20z%20Garbowa.JPG?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zawisza_Czarny'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zawisza_Czarny'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zawisza_Czarny',
                    'en': 'https://en.wikipedia.org/wiki/Zawisza_Czarny',
                    'de': 'https://de.wikipedia.org/wiki/Zawisza_Czarny'
                }
            elif rec['lp'] == 2612:
                patron['name'] = 'Zbigniew Herbert'
                patron['birth_year'] = 1924
                patron['death_year'] = 1998
                patron['role'] = {
                    'pl': 'wybitny poeta, eseista i dramaturg, autor cyklu „Pan Cogito”, kawaler Orderu Orła Białego, studiował na UJ i ASP w Krakowie',
                    'en': 'renowned poet, essayist, and playwright, author of the "Pan Cogito" series, recipient of the Order of the White Eagle, studied in Kraków',
                    'de': 'bedeutender Dichter, Essayist und Dramatiker, Autor des Zyklus „Herr Cogito“, Träger des Weißen Adlerordens, studierte in Krakau'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zbigniew%20Herbert.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zbigniew_Herbert'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zbigniew_Herbert'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zbigniew_Herbert',
                    'en': 'https://en.wikipedia.org/wiki/Zbigniew_Herbert',
                    'de': 'https://de.wikipedia.org/wiki/Zbigniew_Herbert'
                }
            elif rec['lp'] == 2613:
                patron['name'] = 'Zbigniew i Andrzej Pronaszkowie'
                patron['birth_year'] = 1885
                patron['death_year'] = 1961
                patron['role'] = {
                    'pl': 'bracia artyści: Zbigniew (malarz, rzeźbiarz, współtwórca formizmu i profesor ASP) oraz Andrzej (malarz, reformator scenografii teatralnej)',
                    'en': 'artist brothers: Zbigniew (painter, sculptor, co-founder of Formism, ASP professor) and Andrzej (painter and theatrical set designer)',
                    'de': 'Künstlerbrüder: Zbigniew (Maler, Bildhauer, Mitbegründer des Formismus, ASP-Professor) und Andrzej (Maler und Bühnenbildner)'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zbigniew%20Pronaszko%20Polish%20painter.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zbigniew_Pronaszko'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zbigniew_Pronaszko'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zbigniew_Pronaszko',
                    'en': 'https://en.wikipedia.org/wiki/Zbigniew_Pronaszko',
                    'de': 'https://de.wikipedia.org/wiki/Zbigniew_Pronaszko'
                }
            elif rec['lp'] == 2614:
                patron['name'] = 'Zbigniew Małek'
                patron['birth_year'] = 1927
                patron['death_year'] = 2003
                patron['role'] = {
                    'pl': 'harcmistrz, żołnierz Szarych Szeregów i AK w Krakowie ps. „Wrzos”, wieloletni prezes krakowskiego Stowarzyszenia Szarych Szeregów',
                    'en': 'Scoutmaster, Gray Ranks and Home Army soldier in Kraków, long-time president of the Kraków Gray Ranks Association',
                    'de': 'Pfadfinderleiter, Soldat der Grauen Reihen und der Heimatarmee in Krakau, langjähriger Vorsitzender der Krakauer Vereinigung der Grauen Reihen'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Szare_Szeregi'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Szare_Szeregi'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Szare_Szeregi'
                }
            elif rec['lp'] == 2615:
                patron['name'] = 'Zbigniew Seifert'
                patron['birth_year'] = 1946
                patron['death_year'] = 1979
                patron['role'] = {
                    'pl': 'genialny skrzypek jazzowy i saksofonista, czołowa postać polskiego i europejskiego jazz-rocka, absolwent krakowskiej PWSM',
                    'en': 'virtuoso jazz violinist and saxophonist, prominent figure in European jazz-rock fusion, graduate of Kraków State Higher School of Music',
                    'de': 'virtuoser Jazzgeiger und Saxophonist, führende Persönlichkeit des europäischen Jazz-Rock, Absolvent der Staatlichen Musikhochschule Krakau'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zbigniew_Seifert'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zbigniew_Seifert'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zbigniew_Seifert',
                    'en': 'https://en.wikipedia.org/wiki/Zbigniew_Seifert',
                    'de': 'https://de.wikipedia.org/wiki/Zbigniew_Seifert'
                }
            elif rec['lp'] == 2625:
                patron['name'] = 'Zdzisław Jachimecki'
                patron['birth_year'] = 1882
                patron['death_year'] = 1953
                patron['role'] = {
                    'pl': 'wybitny muzykolog, historyk muzyki i kompozytor, profesor Uniwersytetu Jagiellońskiego, członek PAU, twórca krakowskiej muzykologii akademickiej',
                    'en': 'prominent musicologist, music historian and composer, professor at Jagiellonian University, member of PAU, founder of academic musicology in Kraków',
                    'de': 'bedeutender Musikwissenschaftler, Musikhistoriker und Komponist, Professor an der Jagiellonen-Universität, Mitglied der PAU, Begründer der Krakauer Musikwissenschaft'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zdzis%C5%82aw%20Jachimecki%20foto%20%28cropped%29.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zdzis%C5%82aw_Jachimecki'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zdzis%C5%82aw_Jachimecki'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zdzis%C5%82aw_Jachimecki',
                    'en': 'https://en.wikipedia.org/wiki/Zdzis%C5%82aw_Jachimecki',
                    'de': 'https://de.wikipedia.org/wiki/Zdzis%C5%82aw_Jachimecki'
                }
            elif rec['lp'] == 2626:
                patron['name'] = 'Zdzisław Opial'
                patron['birth_year'] = 1930
                patron['death_year'] = 1974
                patron['role'] = {
                    'pl': 'wybitny matematyk, profesor Uniwersytetu Jagiellońskiego, twórca twierdzenia Opiala i nierówności Opiala w teorii równań różniczkowych',
                    'en': 'eminent mathematician, professor at Jagiellonian University, formulator of Opial\'s theorem and Opial\'s inequality in differential equations',
                    'de': 'herausragender Mathematiker, Professor an der Jagiellonen-Universität, Entdecker des Opial-Theorems und der Opial-Ungleichung in Differentialgleichungen'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zdzis%C5%82aw_Opial'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zdzis%C5%82aw_Opial'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zdzis%C5%82aw_Opial',
                    'en': 'https://en.wikipedia.org/wiki/Zdzis%C5%82aw_Opial',
                    'de': 'https://de.wikipedia.org/wiki/Zdzis%C5%82aw_Opial'
                }
            elif rec['lp'] == 2627:
                patron['name'] = 'Zdzisław Przebindowski'
                patron['birth_year'] = 1902
                patron['death_year'] = 1986
                patron['role'] = {
                    'pl': 'artysta malarz nurtu koloryzmu, profesor i prorektor Akademii Sztuk Pięknych w Krakowie, długoletni prezes Okręgu Krakowskiego ZPAP',
                    'en': 'colourist painter, professor and vice-rector of the Academy of Fine Arts in Kraków, long-serving president of the Kraków branch of ZPAP',
                    'de': 'Maler des Kolorismus, Professor und Prorektor der Kunstakademie Krakau, langjähriger Vorsitzender des Krakauer Bezirks des ZPAP'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zdzis%C5%82aw_Przebindowski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zdzis%C5%82aw_Przebindowski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zdzis%C5%82aw_Przebindowski'
                }
            elif rec['lp'] == 2630:
                patron['name'] = 'Zenon Klemensiewicz'
                patron['birth_year'] = 1899
                patron['death_year'] = 1969
                patron['role'] = {
                    'pl': 'wybitny językoznawca polski, profesor i prorektor Uniwersytetu Jagiellońskiego, członek rzeczywisty PAN, autor fundamentalnej „Historii języka polskiego”',
                    'en': 'prominent Polish linguist, professor and vice-rector of the Jagiellonian University, member of PAN, author of the History of the Polish Language',
                    'de': 'bedeutender polnischer Linguist, Professor und Prorektor der Jagiellonen-Universität, Mitglied der PAN, Autor der Geschichte der polnischen Sprache'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zenon%20Klemensiewicz%20Polish%20scientist.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zenon_Klemensiewicz'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zenon_Klemensiewicz'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zenon_Klemensiewicz',
                    'en': 'https://en.wikipedia.org/wiki/Zenon_Klemensiewicz',
                    'de': 'https://de.wikipedia.org/wiki/Zenon_Klemensiewicz'
                }
            elif rec['lp'] == 2646:
                patron['name'] = 'Zofia Kossak-Szczucka'
                patron['birth_year'] = 1889
                patron['death_year'] = 1968
                patron['role'] = {
                    'pl': 'powieściopisarka historyczna, współtwórczyni Frontu Odrodzenia Polski i Żegoty, więźniarka KL Auschwitz, Sprawiedliwa wśród Narodów Świata',
                    'en': 'historical novelist, co-founder of the Front for the Rebirth of Poland and Żegota, KL Auschwitz survivor, Righteous Among the Nations',
                    'de': 'historische Schriftstellerin, Mitbegründerin der Żegota, Überlebende des KZ Auschwitz, Gerechte unter den Völkern'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/ZOFIA%20KOSSAK.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zofia_Kossak-Szczucka'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zofia_Kossak-Szczucka'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zofia_Kossak-Szczucka',
                    'en': 'https://en.wikipedia.org/wiki/Zofia_Kossak-Szczucka',
                    'de': 'https://de.wikipedia.org/wiki/Zofia_Kossak-Szczucka'
                }
            elif rec['lp'] == 2647:
                patron['name'] = 'Zofia Kulinowska'
                patron['birth_year'] = 1907
                patron['death_year'] = 1994
                patron['role'] = {
                    'pl': 'działaczka społeczna, pamiętnikarka, ostatnia prywatna właścicielka zabytkowego dworu Badenich w Wadowie (1930–1945)',
                    'en': 'social activist, memoirist, last private owner of the historic Badeni manor house in Wadów (1930–1945)',
                    'de': 'Aktivistin, Memoirenautorin, letzte private Besitzerin des historischen Badeni-Gutshofs in Wadów (1930–1945)'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Dw%C3%B3r_Badenich_w_Wadowie'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Dw%C3%B3r_Badenich_w_Wadowie'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Dw%C3%B3r_Badenich_w_Wadowie'
                }
            elif rec['lp'] == 2648:
                patron['name'] = 'Zofia Nałkowska'
                patron['birth_year'] = 1884
                patron['death_year'] = 1954
                patron['role'] = {
                    'pl': 'wybitna pisarka, dramatopisarka i publicystka, posłanka na Sejm, członkini Głównej Komisji Badania Zbrodni Niemieckich w Polsce, autorka „Medalionów” i „Granicy”',
                    'en': 'distinguished novelist, playwright and essayist, member of the Main Commission for the Investigation of German Crimes, author of "Medallions" and "Granica"',
                    'de': 'herausragende Schriftstellerin, Dramatikerin und Publizistin, Mitglied der Hauptkommission zur Untersuchung der deutschen Verbrechen, Autorin von „Medaillons“'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zofia%20Na%C5%82kowska%201.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zofia_Na%C5%82kowska'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zofia_Na%C5%82kowska'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zofia_Na%C5%82kowska',
                    'en': 'https://en.wikipedia.org/wiki/Zofia_Na%C5%82kowska',
                    'de': 'https://de.wikipedia.org/wiki/Zofia_Na%C5%82kowska'
                }
            elif rec['lp'] == 2649:
                patron['name'] = 'Zofia Stryjeńska'
                patron['birth_year'] = 1891
                patron['death_year'] = 1969
                patron['role'] = {
                    'pl': 'czołowa malarka, graficzka i ilustratorka polskiego art déco, zwana „księżniczką sztuki polskiej”, autorka paneli w Pawilonie Polskim w Paryżu (1925)',
                    'en': 'foremost Polish Art Deco painter, graphic artist and illustrator, known as the "princess of Polish art", decorated the Polish Pavilion in Paris (1925)',
                    'de': 'führende polnische Malerin, Grafikerin und Illustratorin des Art déco, Schöpferin der Wandpaneele im Polnischen Pavillon in Paris (1925)'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zofia%20Stryjenska%20%28photo%29.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zofia_Stryje%C5%84ska'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zofia_Stryje%C5%84ska'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zofia_Stryje%C5%84ska',
                    'en': 'https://en.wikipedia.org/wiki/Zofia_Stryje%C5%84ska',
                    'de': 'https://de.wikipedia.org/wiki/Zofia_Stryje%C5%84ska'
                }
            elif rec['lp'] == 2653:
                patron['name'] = 'Zygmunt II August'
                patron['birth_year'] = 1520
                patron['death_year'] = 1572
                patron['role'] = {
                    'pl': 'król Polski i wielki książę litewski (1548–1572), ostatni z Jagiellonów, twórca unii lubelskiej (1569), ofiarodawca Srebrnego Kura dla Bractwa Kurkowego (1565)',
                    'en': 'King of Poland and Grand Duke of Lithuania (1548–1572), last Jagiellonian king, architect of the Union of Lublin (1569), benefactor of the Kraków Fowler Brotherhood',
                    'de': 'König von Polen und Großfürst von Litauen (1548–1572), letzter Jagiellonenkönig, Schöpfer der Union von Lublin (1569), Stifter des Silbernen Hahns'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Cranach%20the%20Younger%20Sigismund%20II%20Augustus.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_II_August'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_II_August'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zygmunt_II_August',
                    'en': 'https://en.wikipedia.org/wiki/Sigismund_II_Augustus',
                    'de': 'https://de.wikipedia.org/wiki/Sigismund_II._August'
                }
            elif rec['lp'] == 2654:
                patron['name'] = 'Zygmunt Gloger'
                patron['birth_year'] = 1845
                patron['death_year'] = 1910
                patron['role'] = {
                    'pl': 'wybitny historyk, archeolog, etnograf i krajoznawca, pierwszy prezes Polskiego Towarzystwa Krajoznawczego, autor „Encyklopedii staropolskiej ilustrowanej”',
                    'en': 'prominent historian, archaeologist, ethnographer and folklorist, first president of the Polish Sightseeing Society, author of the Old Polish Encyclopedia',
                    'de': 'bedeutender Historiker, Archäologe, Ethnograph und Volkskundler, erster Präsident der Polnischen Gesellschaft für Landeskunde, Autor der Altpolnischen Enzyklopädie'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zygmunt%20Gloger-Detail.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Gloger'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Gloger'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zygmunt_Gloger',
                    'en': 'https://en.wikipedia.org/wiki/Zygmunt_Gloger',
                    'de': 'https://de.wikipedia.org/wiki/Zygmunt_Gloger'
                }
            elif rec['lp'] == 2655:
                patron['name'] = 'Zygmunt Krasiński'
                patron['birth_year'] = 1812
                patron['death_year'] = 1859
                patron['role'] = {
                    'pl': 'hrabia, jeden z Trzech Wieszczów polskiego romantyzmu, wybitny poeta i dramatopisarz, autor „Nie-Boskiej komedii” i „Irydiona”',
                    'en': 'Count, one of the Three Bards of Polish Romanticism, eminent poet and dramatist, author of "The Undivine Comedy" and "Irydion"',
                    'de': 'Graf, einer der Drei Barden der polnischen Romantik, bedeutender Dichter und Dramatiker, Autor von „Die Ungöttliche Komödie“ und „Irydion“'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zygmunt%20Krasi%C5%84ski%20portrait.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Krasi%C5%84ski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Krasi%C5%84ski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zygmunt_Krasi%C5%84ski',
                    'en': 'https://en.wikipedia.org/wiki/Zygmunt_Krasi%C5%84ski',
                    'de': 'https://de.wikipedia.org/wiki/Zygmunt_Krasi%C5%84ski'
                }
            elif rec['lp'] == 2656:
                patron['name'] = 'Zygmunt Miłkowski'
                patron['birth_year'] = 1894
                patron['death_year'] = 1945
                patron['role'] = {
                    'pl': 'pułkownik dyplomowany kawalerii Wojska Polskiego, legionista, dowódca 16 Pułku Ułanów Wielkopolskich w bitwie nad Bzurą (1939), kawaler Virtuti Militari',
                    'en': 'certified cavalry colonel of the Polish Army, Legionnaire, commander of the 16th Greater Poland Uhlan Regiment at the Battle of the Bzura (1939)',
                    'de': 'Oberst der polnischen Kavallerie, Legionär, Kommandeur des 16. Großpolnischen Ulanenregiments in der Schlacht an der Bzura (1939)'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/P%C5%82k.%20Zygmunt%20Mi%C5%82kowski.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Mi%C5%82kowski_(oficer)'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Mi%C5%82kowski_(oficer)'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zygmunt_Mi%C5%82kowski_(oficer)'
                }
            elif rec['lp'] == 2657:
                patron['name'] = 'Zygmunt Mysłakowski'
                patron['birth_year'] = 1890
                patron['death_year'] = 1971
                patron['role'] = {
                    'pl': 'wybitny pedagog i filozof, profesor i dziekan Uniwersytetu Jagiellońskiego, członek PAU, czołowy twórca polskiej pedagogiki kultury',
                    'en': 'prominent educator and philosopher, professor and dean at Jagiellonian University, member of PAU, leading pioneer of cultural pedagogy',
                    'de': 'bedeutender Pädagoge und Philosoph, Professor und Dekan an der Jagiellonen-Universität, Mitglied der PAU, Pionier der Kulturpädagogik'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zygmunt%20Mys%C5%82akowski.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Mys%C5%82akowski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Mys%C5%82akowski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zygmunt_Mys%C5%82akowski',
                    'en': 'https://en.wikipedia.org/wiki/Zygmunt_Mys%C5%82akowski',
                    'de': 'https://de.wikipedia.org/wiki/Zygmunt_Mys%C5%82akowski'
                }
            elif rec['lp'] == 2658:
                patron['name'] = 'Zygmunt Radnicki'
                patron['birth_year'] = 1894
                patron['death_year'] = 1969
                patron['role'] = {
                    'pl': 'krakowski artysta malarz, profesor i prorektor Akademii Sztuk Pięknych w Krakowie, członek ugrupowania „Jednoróg”, współtwórca tradycji koloryzmu',
                    'en': 'Kraków painter, professor and vice-rector of the Academy of Fine Arts in Kraków, member of the "Jednoróg" group, colourist master',
                    'de': 'Krakauer Maler, Professor und Prorektor der Kunstakademie Krakau, Mitglied der Gruppe „Jednoróg“, Meister des Kolorismus'
                }
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Radnicki'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Radnicki'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zygmunt_Radnicki'
                }
            elif rec['lp'] == 2659:
                patron['name'] = 'Zygmunt I Stary'
                patron['birth_year'] = 1467
                patron['death_year'] = 1548
                patron['role'] = {
                    'pl': 'król Polski i wielki książę litewski (1506–1548), mecenas złotego wieku renesansu, fundator Kaplicy Zygmuntowskiej i Dzwonu Zygmunta na Wawelu',
                    'en': 'King of Poland and Grand Duke of Lithuania (1506–1548), patron of the Renaissance Golden Age, founder of the Sigismund Chapel and Sigismund Bell at Wawel',
                    'de': 'König von Polen und Großfürst von Litauen (1506–1548), Förderer des Goldenen Zeitalters der Renaissance, Stifter der Sigismundkapelle und der Sigismund-Glocke auf dem Wawel'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Sigismund%20I%20of%20Poland.PNG?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_I_Stary'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_I_Stary'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zygmunt_I_Stary',
                    'en': 'https://en.wikipedia.org/wiki/Sigismund_I_the_Old',
                    'de': 'https://de.wikipedia.org/wiki/Sigismund_I._(Polen)'
                }
            elif rec['lp'] == 2660:
                patron['name'] = 'Zygmunt Wróblewski'
                patron['birth_year'] = 1845
                patron['death_year'] = 1888
                patron['role'] = {
                    'pl': 'wybitny fizyk, profesor Uniwersytetu Jagiellońskiego, powstaniec styczniowy; w kwietniu 1883 r. wraz z Karolem Olszewskim dokonał pierwszego w świecie skroplenia tlenu i azotu',
                    'en': 'eminent physicist, professor at Jagiellonian University, January Uprising veteran; along with Karol Olszewski in 1883 first in the world to liquefy oxygen and nitrogen',
                    'de': 'bedeutender Physiker, Professor an der Jagiellonen-Universität, Januaraufständischer; verflüssigte 1883 mit Karol Olszewski erstmals Sauerstoff und Stickstoff'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zygmunt%20Wr%C3%B3blewski.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Wr%C3%B3blewski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Wr%C3%B3blewski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zygmunt_Wr%C3%B3blewski',
                    'en': 'https://en.wikipedia.org/wiki/Zygmunt_Wr%C3%B3blewski',
                    'de': 'https://de.wikipedia.org/wiki/Zygmunt_Wr%C3%B3blewski'
                }
            elif rec['lp'] == 2661:
                patron['name'] = 'Zygmunt Wyrobek'
                patron['birth_year'] = 1872
                patron['death_year'] = 1939
                patron['role'] = {
                    'pl': 'instruktor harcerski, harcmistrz Rzeczypospolitej, działacz TG „Sokół”, współzałożyciel I Krakowskiej Drużyny Harcerskiej, pionier skautingu w Polsce',
                    'en': 'scouting instructor, Scoutmaster of the Republic, activist of the "Sokół" Movement, co-founder of the 1st Kraków Scout Troop, pioneer of Polish scouting',
                    'de': 'Pfadfinderleiter, Pfadfindermeister der Republik, Aktivist der Turnerbewegung „Sokół“, Mitbegründer des 1. Krakauer Pfadfinderstammes'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Zygmunt%20Wyrobek.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Wyrobek'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zygmunt_Wyrobek'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zygmunt_Wyrobek',
                    'en': 'https://en.wikipedia.org/wiki/Zygmunt_Wyrobek'
                }
            elif rec['lp'] == 2663:
                patron['name'] = 'Zyndram z Maszkowic'
                patron['birth_year'] = 1355
                patron['death_year'] = 1414
                patron['role'] = {
                    'pl': 'rycerz herbu Słońce, miecznik krakowski i oboźny wojsk królewskich, dowódca naczelnej chorągwi krakowskiej w bitwie pod Grunwaldem (1410)',
                    'en': 'knight of the Słońce coat of arms, Sword-Bearer of Kraków and Royal Quartermaster, commanded the leading Kraków Banner at the Battle of Grunwald (1410)',
                    'de': 'Ritter des Wappens Słońce, Schwertträger von Krakau und königlicher Quartiermeister, Kommandeur des Krakauer Hauptbanners in der Schlacht bei Tannenberg (1410)'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Grunwald%20Zyndram.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Zyndram_z_Maszkowic'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Zyndram_z_Maszkowic'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Zyndram_z_Maszkowic',
                    'en': 'https://en.wikipedia.org/wiki/Zyndram_of_Maszkowice',
                    'de': 'https://de.wikipedia.org/wiki/Zyndram_von_Maszkowice'
                }
            elif rec['lp'] == 2685:
                patron['name'] = 'Łukasz Ciepliński'
                patron['birth_year'] = 1913
                patron['death_year'] = 1951
                patron['role'] = {
                    'pl': 'podpułkownik piechoty Wojska Polskiego ps. „Pług”, oficer AK, prezes IV Zarządu Głównego WiN, zamordowany na Mokotowie, kawaler Orderu Orła Białego',
                    'en': 'Lieutenant Colonel of the Polish Army ("Pług"), Home Army officer, president of the 4th WiN Directorate, executed at Mokotów Prison, Order of the White Eagle',
                    'de': 'Oberstleutnant der polnischen Armee („Pług“), Offizier der Heimatarmee, Präsident des 4. WiN-Hauptvorstands, hingerichtet im Mokotów-Gefängnis'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/%C5%81ukasz%20Ciepli%C5%84ski.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/%C5%81ukasz_Ciepli%C5%84ski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/%C5%81ukasz_Ciepli%C5%84ski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/%C5%81ukasz_Ciepli%C5%84ski',
                    'en': 'https://en.wikipedia.org/wiki/%C5%81ukasz_Ciepli%C5%84ski',
                    'de': 'https://de.wikipedia.org/wiki/%C5%81ukasz_Ciepli%C5%84ski'
                }
            elif rec['lp'] == 2686:
                patron['name'] = 'Łukasz Górnicki'
                patron['birth_year'] = 1527
                patron['death_year'] = 1603
                patron['role'] = {
                    'pl': 'wybitny humanista, pisarz i tłumacz renesansowy, sekretarz i bibliotekarz króla Zygmunta II Augusta, autor „Dworzanina polskiego”',
                    'en': 'eminent Renaissance humanist, writer and translator, secretary and librarian to King Sigismund II Augustus, author of "The Polish Courtier"',
                    'de': 'bedeutender Renaissance-Humanist, Schriftsteller und Übersetzer, Sekretär und Bibliothekar von König Sigismund II. August, Autor von „Der polnische Höfling“'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/%C5%81ukasz%20G%C3%B3rnicki.PNG?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/%C5%81ukasz_G%C3%B3rnicki'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/%C5%81ukasz_G%C3%B3rnicki'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/%C5%81ukasz_G%C3%B3rnicki',
                    'en': 'https://en.wikipedia.org/wiki/%C5%81ukasz_G%C3%B3rnicki',
                    'de': 'https://de.wikipedia.org/wiki/%C5%81ukasz_G%C3%B3rnicki'
                }
            elif rec['lp'] == 2687:
                patron['name'] = 'Łukasz Opaliński'
                patron['birth_year'] = 1612
                patron['death_year'] = 1662
                patron['role'] = {
                    'pl': 'marszałek nadworny koronny, wybitny pisarz polityczny, poeta i satyryk epoki baroku, autor traktatów „De officiis” i „Poeta nowy”',
                    'en': 'Court Marshal of the Crown, prominent political writer, poet and satirist of the Baroque era, author of "De officiis" and "The New Poet"',
                    'de': 'Kronhofmarschall, bedeutender politischer Schriftsteller, Dichter und Satiriker des Barock, Autor von „De officiis“ und „Der neue Dichter“'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/%C5%81ukasz%20Opali%C5%84ski%20m%C5%82odszy.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/%C5%81ukasz_Opali%C5%84ski_(marsza%C5%82ek_nadworny_koronny)'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/%C5%81ukasz_Opali%C5%84ski_(marsza%C5%82ek_nadworny_koronny)'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/%C5%81ukasz_Opali%C5%84ski_(marsza%C5%82ek_nadworny_koronny)',
                    'en': 'https://en.wikipedia.org/wiki/%C5%81ukasz_Opali%C5%84ski_(1612%E2%80%931662)',
                    'de': 'https://de.wikipedia.org/wiki/%C5%81ukasz_Opali%C5%84ski_(1612%E2%80%931662)'
                }
            elif rec['lp'] == 2713:
                patron['name'] = 'Andrzej Bobola'
                patron['birth_year'] = 1591
                patron['death_year'] = 1657
                patron['role'] = {
                    'pl': 'jezuita, misjonarz i kaznodzieja, męczennik wojny polsko-kozackiej, święty Kościoła katolickiego, patron Polski',
                    'en': 'Jesuit missionary, preacher and martyr, Saint of the Catholic Church, secondary patron of Poland',
                    'de': 'Jesuit, Missionar und Prediger, Märtyrer, Heiliger der katholischen Kirche, Schutzpatron Polens'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Bobola.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Andrzej_Bobola'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Andrzej_Bobola'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Andrzej_Bobola',
                    'en': 'https://en.wikipedia.org/wiki/Andrew_Bobola',
                    'de': 'https://de.wikipedia.org/wiki/Andreas_Bobola'
                }
            elif rec['lp'] == 2714:
                patron['name'] = 'Święty Benedykt z Nursji'
                patron['birth_year'] = 480
                patron['death_year'] = 547
                patron['role'] = {
                    'pl': 'mnich chrześcijański, prawodawca zachodniego monastycyzmu, autor Reguły benedyktyńskiej, główny patron Europy',
                    'en': 'Christian abbot, father of Western monasticism, author of the Rule of Saint Benedict, patron saint of Europe',
                    'de': 'christlicher Abt, Vater des westlichen Mönchtums, Verfasser der Benediktsregel, Hauptpatron Europas'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Arundel_155_F133r_%28cropped%29.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Benedykt_z_Nursji'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Benedykt_z_Nursji'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Benedykt_z_Nursji',
                    'en': 'https://en.wikipedia.org/wiki/Benedict_of_Nursia',
                    'de': 'https://de.wikipedia.org/wiki/Benedikt_von_Nursia'
                }
            elif rec['lp'] == 2715:
                patron['name'] = 'Adam Chmielowski (Brat Albert)'
                patron['birth_year'] = 1845
                patron['death_year'] = 1916
                patron['role'] = {
                    'pl': 'powstaniec styczniowy, wybitny artysta malarz, tercjarz franciszkański, założyciel zgromadzeń albertynów i albertynek posługujących ubogim w Krakowie',
                    'en': 'January Uprising veteran, renowned painter, Franciscan tertiary, founder of the Albertine Brothers and Sisters helping the homeless in Kraków',
                    'de': 'Aufständischer von 1863, Kunstmaler, Franziskaner-Terziar, Gründer der Albertiner und Albertinerinnen für Arme und Obdachlose in Krakau'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Brat%20Albert.png?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Adam_Chmielowski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Adam_Chmielowski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Adam_Chmielowski',
                    'en': 'https://en.wikipedia.org/wiki/Albert_Chmielowski',
                    'de': 'https://de.wikipedia.org/wiki/Albert_Chmielowski'
                }
            elif rec['lp'] == 2717:
                patron['name'] = 'Święty Filip Apostoł'
                patron['birth_year'] = 5
                patron['death_year'] = 80
                patron['role'] = {
                    'pl': 'jeden z dwunastu apostołów Jezusa Chrystusa, głosiciel Ewangelii w Azji Mniejszej, męczennik w Hierapolis',
                    'en': 'one of the Twelve Apostles of Jesus Christ, Christian evangelist in Asia Minor, martyred in Hierapolis',
                    'de': 'einer der zwölf Apostel Jesu Christi, Evangelist in Kleinasien, Märtyrer in Hierapolis'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Rubens_apostel_philippus.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Filip_Aposto%C5%82'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Filip_Aposto%C5%82'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Filip_Aposto%C5%82',
                    'en': 'https://en.wikipedia.org/wiki/Philip_the_Apostle',
                    'de': 'https://de.wikipedia.org/wiki/Philippus_(Apostel)'
                }
            elif rec['lp'] == 2718:
                patron['name'] = 'Święty Idzi'
                patron['birth_year'] = 640
                patron['death_year'] = 720
                patron['role'] = {
                    'pl': 'prowansalski eremita i opat, jeden z Czternastu Świętych Wspomożycieli, patron matek, bezdzietnych małżeństw i rodzicielstwa',
                    'en': 'Provençal hermit and abbot, one of the Fourteen Holy Helpers, patron saint of nursing mothers, disabled persons and parenthood',
                    'de': 'provenzalischer Einsiedler und Abt, einer der Vierzehn Nothelfer, Schutzpatron der Mütter und Eltern'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Saint%20Giles%20closeup.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Idzi_(opat)'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Idzi_(opat)'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Idzi_(opat)',
                    'en': 'https://en.wikipedia.org/wiki/Saint_Giles',
                    'de': 'https://de.wikipedia.org/wiki/%C3%84gidius_(Heiliger)'
                }
            elif rec['lp'] == 2719:
                patron['name'] = 'Jacek Odrowąż'
                patron['birth_year'] = 1183
                patron['death_year'] = 1257
                patron['role'] = {
                    'pl': 'duchowny dominikański, apostoł północnej i wschodniej Europy, założyciel pierwszego polskiego klasztoru dominikanów przy kościele Świętej Trójcy w Krakowie',
                    'en': 'Dominican friar, Apostle of the North and Slavic lands, founder of the first Polish Dominican monastery at Holy Trinity Church in Kraków',
                    'de': 'Dominikanermönch, Apostel des Nordens, Gründer des ersten polnischen Dominikanerklosters bei der Dreifaltigkeitskirche in Krakau'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Friesach%20-%20Dominikanerkirche%20-%20Hochaltar%20-%20Hl%20Hyazinth.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jacek_Odrow%C4%85%C5%BC'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jacek_Odrow%C4%85%C5%BC'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jacek_Odrow%C4%85%C5%BC',
                    'en': 'https://en.wikipedia.org/wiki/Saint_Hyacinth',
                    'de': 'https://de.wikipedia.org/wiki/Hyazinth_von_Polen'
                }
            elif rec['lp'] == 2720:
                patron['name'] = 'Święty Jan Ewangelista'
                patron['birth_year'] = 6
                patron['death_year'] = 100
                patron['role'] = {
                    'pl': 'apostoł, jeden z najbliższych uczniów Chrystusa, autor czwartej Ewangelii, Listów i Apokalipsy, patron kościoła św. Jana w Krakowie',
                    'en': 'Apostle, beloved disciple of Jesus, author of the Fourth Gospel, Epistles and Revelation, patron of St. John’s Church in Kraków',
                    'de': 'Apostel, Jünger Jesu, Verfasser des vierten Evangeliums, der Briefe und der Offenbarung, Patron der Johanneskirche in Krakau'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Grandes%20Heures%20Anne%20de%20Bretagne%20Saint%20Jean.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Jan_Ewangelista'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Jan_Ewangelista'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Jan_Ewangelista',
                    'en': 'https://en.wikipedia.org/wiki/John_the_Apostle',
                    'de': 'https://de.wikipedia.org/wiki/Johannes_(Apostel)'
                }
            elif rec['lp'] == 2722:
                patron['name'] = 'Marek Ewangelista'
                patron['birth_year'] = 10
                patron['death_year'] = 68
                patron['role'] = {
                    'pl': 'apostoł pomocnik św. Piotra, autor najstarszej kanonicznej Ewangelii, biskup Aleksandrii, patron kościoła św. Marka w Krakowie',
                    'en': 'companion of Saint Peter, author of the Gospel of Mark, traditional founder of the Church of Alexandria',
                    'de': 'Begleiter des Heiligen Petrus, Verfasser des Markusevangeliums, Bischof von Alexandria'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Emmanuel%20Tzanes%20-%20St.%20Mark%20the%20Evangelist%20-%201657.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Marek_Ewangelista'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Marek_Ewangelista'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Marek_Ewangelista',
                    'en': 'https://en.wikipedia.org/wiki/Mark_the_Evangelist',
                    'de': 'https://de.wikipedia.org/wiki/Markus_(Evangelist)'
                }
            elif rec['lp'] == 2723:
                patron['name'] = 'Piotr Apostoł'
                patron['birth_year'] = 1
                patron['death_year'] = 64
                patron['role'] = {
                    'pl': 'pierwszy z dwunastu apostołów, pierwszy biskup Rzymu, męczennik za wiarę na Wzgórzu Watykańskim',
                    'en': 'first among the Twelve Apostles, first Bishop of Rome, early Christian leader martyred in Rome',
                    'de': 'Erster der zwölf Apostel, erster Bischof von Rom, frühchristlicher Führer und Märtyrer in Rom'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Pope-peter%20pprubens.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Piotr_Aposto%C5%82'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Piotr_Aposto%C5%82'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Piotr_Aposto%C5%82',
                    'en': 'https://en.wikipedia.org/wiki/Saint_Peter',
                    'de': 'https://de.wikipedia.org/wiki/Simon_Petrus'
                }
            elif rec['lp'] == 2724:
                patron['name'] = 'Rafał Kalinowski'
                patron['birth_year'] = 1835
                patron['death_year'] = 1907
                patron['role'] = {
                    'pl': 'inżynier wojskowy, dowódca w powstaniu styczniowym na Litwie, syberyjski katorżnik, karmelita bosy, przeor w Czernej i Wadowicach',
                    'en': 'military engineer, leader in the January Uprising, Siberian exile, Discalced Carmelite friar, prior in Czerna and Wadowice',
                    'de': 'Militäringenieur, Anführer des Januaraufstands in Litauen, sibirischer Verbannter, Unbeschuhter Karmelit, Prior in Czerna und Wadowice'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Kalinowski1897.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Rafa%C5%82_Kalinowski'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Rafa%C5%82_Kalinowski'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Rafa%C5%82_Kalinowski',
                    'en': 'https://en.wikipedia.org/wiki/Raphael_Kalinowski',
                    'de': 'https://de.wikipedia.org/wiki/Raphael_Kalinowski'
                }
            elif rec['lp'] == 2725:
                patron['name'] = 'Święty Sebastian'
                patron['birth_year'] = 256
                patron['death_year'] = 288
                patron['role'] = {
                    'pl': 'rzymski oficer gwardii pretoriańskiej cesarza Dioklecjana, męczennik chrześcijański, tradycyjny patron chroniący od dżumy i zarazy',
                    'en': 'Roman officer in the Praetorian Guard, early Christian saint and martyr, traditional protector against plague and epidemics',
                    'de': 'römischer Offizier der Prätorianergarde, frühchristlicher Märtyrer, traditioneller Schutzpatron gegen die Pest'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Sebastia.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Sebastian_(m%C4%99czennik)'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Sebastian_(m%C4%99czennik)'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Sebastian_(m%C4%99czennik)',
                    'en': 'https://en.wikipedia.org/wiki/Saint_Sebastian',
                    'de': 'https://de.wikipedia.org/wiki/Sebastian_(Heiliger)'
                }
            elif rec['lp'] == 2726:
                patron['name'] = 'Stanisław ze Szczepanowa'
                patron['birth_year'] = 1030
                patron['death_year'] = 1079
                patron['role'] = {
                    'pl': 'biskup krakowski, męczennik, główny patron Polski i archidiecezji krakowskiej, kanonizowany w 1253 r. w Asyżu',
                    'en': 'Bishop of Kraków, martyr, primary patron saint of Poland and the Archdiocese of Kraków, canonized in 1253',
                    'de': 'Bischof von Krakau, Märtyrer, Hauptpatron Polens und des Erzbistums Krakau, heiliggesprochen 1253 in Assisi'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Stanis%C5%82aw_Samostrzelnik%2C_%C5%9Aw_Stanis%C5%82aw.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Stanis%C5%82aw_ze_Szczepanowa'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Stanis%C5%82aw_ze_Szczepanowa'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Stanis%C5%82aw_ze_Szczepanowa',
                    'en': 'https://en.wikipedia.org/wiki/Stanislaus_of_Szczepan%C3%B3w',
                    'de': 'https://de.wikipedia.org/wiki/Stanislaus_von_Szczepan%C3%B3w'
                }
            elif rec['lp'] == 2727:
                patron['name'] = 'Tomasz Apostoł'
                patron['birth_year'] = 1
                patron['death_year'] = 72
                patron['role'] = {
                    'pl': 'jeden z dwunastu apostołów Jezusa Chrystusa, apostoł Syrii i Indii, męczennik w Mailapurze, patron kościoła św. Tomasza w Krakowie',
                    'en': 'one of the Twelve Apostles of Jesus Christ, evangelist of Syria and India, martyred at Mylapore',
                    'de': 'einer der zwölf Apostel Jesu Christi, Evangelisator Syriens und Indiens, Märtyrer in Mylapore'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/El_Greco_-_St._Thomas_-_Google_Art_Project.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Tomasz_Aposto%C5%82'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Tomasz_Aposto%C5%82'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Tomasz_Aposto%C5%82',
                    'en': 'https://en.wikipedia.org/wiki/Thomas_the_Apostle',
                    'de': 'https://de.wikipedia.org/wiki/Thomas_(Apostel)'
                }
            elif rec['lp'] == 2728:
                patron['name'] = 'Wawrzyniec z Rzymu'
                patron['birth_year'] = 225
                patron['death_year'] = 258
                patron['role'] = {
                    'pl': 'diakon Kościoła rzymskiego, męczennik za wiarę spalony na kracie żelaznej za cesarza Waleriana, patron ubogich i kościoła na Bawóle',
                    'en': 'Roman deacon, early Christian martyr roasted on a gridiron under Emperor Valerian, patron of the poor and cooks',
                    'de': 'römischer Diakon, frühchristlicher Märtyrer unter Kaiser Valerian, Schutzpatron der Armen und Köche'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/St.%20Laurentius%20in%20Dorfkirche%20St.%20Laurentius%20in%20Hornstorf.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Wawrzyniec_z_Rzymu'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Wawrzyniec_z_Rzymu'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Wawrzyniec_z_Rzymu',
                    'en': 'https://en.wikipedia.org/wiki/Saint_Lawrence',
                    'de': 'https://de.wikipedia.org/wiki/Laurentius_von_Rom'
                }
            elif rec['lp'] == 2729:
                patron['name'] = 'Święty Wincenty z Saragossy'
                patron['birth_year'] = 270
                patron['death_year'] = 304
                patron['role'] = {
                    'pl': 'diakon diecezji w Saragossie, hiszpański męczennik z czasów prześladowań cesarza Dioklecjana, patron winiarzy i kościoła w Pleszowie',
                    'en': 'deacon of Zaragoza, Spanish martyr during the Diocletianic Persecution, patron saint of winemakers and vinegar-makers',
                    'de': 'Diakon von Saragossa, spanischer Märtyrer unter Kaiser Diokletian, Schutzpatron der Winzer und Dachdecker'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Vicente_de_Zaragoza_%28School_of_Francisco_Ribalta%29_XVII_century.jpeg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Wincenty_z_Saragossy'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Wincenty_z_Saragossy'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Wincenty_z_Saragossy',
                    'en': 'https://en.wikipedia.org/wiki/Vincent_of_Saragossa',
                    'de': 'https://de.wikipedia.org/wiki/Vinzenz_von_Valencia'
                }
            elif rec['lp'] == 2730:
                patron['name'] = 'Święty Łazarz z Betanii'
                patron['birth_year'] = 1
                patron['death_year'] = 60
                patron['role'] = {
                    'pl': 'postać nowotestamentowa z Betanii, brat Marii i Marty wskrzeszony przez Jezusa, tradycyjny patron trędowatych i szpitalnictwa',
                    'en': 'New Testament figure from Bethany, brother of Mary and Martha whom Jesus raised from the dead, patron of hospitals and lepers',
                    'de': 'Gestalt des Neuen Testaments aus Betanien, Bruder von Maria und Martha, von Jesus auferweckt, Patron der Hospitäler und Leprakranken'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Eduard_von_Gebhardt_-_The_Raising_of_Lazarus_-_Google_Art_Project_%28cropped%29.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/%C5%81azarz_z_Betanii'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/%C5%81azarz_z_Betanii'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/%C5%81azarz_z_Betanii',
                    'en': 'https://en.wikipedia.org/wiki/Lazarus_of_Bethany',
                    'de': 'https://de.wikipedia.org/wiki/Lazarus_(Neues_Testament)'
                }
            elif rec['lp'] == 2731:
                patron['name'] = 'Agnieszka Rzymianka'
                patron['birth_year'] = 291
                patron['death_year'] = 304
                patron['role'] = {
                    'pl': 'rzymska dziewica i męczennica z czasów prześladowań Dioklecjana, patronka dziewic, narzeczonych i dzieci, patronka kościoła na Stradomiu',
                    'en': 'Roman virgin and martyr during the Diocletianic Persecution, patron saint of virgins, chastity, and betrothed couples',
                    'de': 'römische Jungfrau und Märtyrerin unter Kaiser Diokletian, Schutzpatronin der Jungfrauen und Verlobten'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Santa%20Agnese%20-%20mosaico%20Santa%20Agnese%20fuori%20le%20mura.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Agnieszka_Rzymianka'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Agnieszka_Rzymianka'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Agnieszka_Rzymianka',
                    'en': 'https://en.wikipedia.org/wiki/Agnes_of_Rome',
                    'de': 'https://de.wikipedia.org/wiki/Agnes_von_Rom'
                }
            elif rec['lp'] == 2732:
                patron['name'] = 'Święta Anna'
                patron['birth_year'] = -50
                patron['death_year'] = 15
                patron['role'] = {
                    'pl': 'matka Maryi i babka Jezusa Chrystusa, patronka matek, małżeństw i górników, patronka uniwersyteckiej kolegiaty św. Anny w Krakowie',
                    'en': 'mother of the Virgin Mary and grandmother of Jesus Christ, patron saint of mothers, marriage and miners',
                    'de': 'Mutter der Jungfrau Maria und Großmutter Jesu Christi, Schutzpatronin der Mütter, Eheleute und Bergleute'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Chanter%20Angelos%20Akotandos%20-%20St%20Anne%20with%20the%20Virgin%20-%20Google%20Art%20Project.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/%C5%9Awi%C4%99ta_Anna'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/%C5%9Awi%C4%99ta_Anna'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/%C5%9Awi%C4%99ta_Anna',
                    'en': 'https://en.wikipedia.org/wiki/Saint_Anne',
                    'de': 'https://de.wikipedia.org/wiki/Anna_(Heilige)'
                }
            elif rec['lp'] == 2733:
                patron['name'] = 'Błogosławiona Bronisława'
                patron['birth_year'] = 1200
                patron['death_year'] = 1259
                patron['role'] = {
                    'pl': 'norbertanka ze zwierzynieckiego klasztoru w Krakowie, mistyczka i pustelnica na wzgórzu Sikornik, orędowniczka w czasie zarazy i wojen',
                    'en': 'Norbertine nun at Zwierzyniec monastery in Kraków, mystic and hermit on Sikornik hill, intercessor in plague and distress',
                    'de': 'Prämonstratenserin im Zwierzyniec-Kloster in Krakau, Mystikerin und Eremitin auf dem Sikornik-Hügel'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Blogoslawiona%20Bronislawa.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Bronis%C5%82awa_(b%C5%82ogos%C5%82awiona)'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Bronis%C5%82awa_(b%C5%82ogos%C5%82awiona)'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Bronis%C5%82awa_(b%C5%82ogos%C5%82awiona)',
                    'en': 'https://en.wikipedia.org/wiki/Bronislava_of_Poland',
                    'de': 'https://de.wikipedia.org/wiki/Bronislawa_von_Polen'
                }
            elif rec['lp'] == 2734:
                patron['name'] = 'Święta Gertruda z Nivelles'
                patron['birth_year'] = 626
                patron['death_year'] = 659
                patron['role'] = {
                    'pl': 'mniszka merowińska, pierwsza ksieni podwójnego opactwa w Nivelles, patronka podróżnych, pielgrzymów i ogrodników',
                    'en': 'Merovingian abbess of Nivelles, patron saint of travelers, pilgrims, gardeners and the poor',
                    'de': 'fränkische Äbtissin von Nivelles, Schutzpatronin der Reisenden, Pilger und Gärtner'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/GetrudNivelles.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Gertruda_z_Nivelles'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Gertruda_z_Nivelles'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Gertruda_z_Nivelles',
                    'en': 'https://en.wikipedia.org/wiki/Gertrude_of_Nivelles',
                    'de': 'https://de.wikipedia.org/wiki/Gertrud_von_Nivelles'
                }
            elif rec['lp'] == 2735:
                patron['name'] = 'Katarzyna Aleksandryjska'
                patron['birth_year'] = 282
                patron['death_year'] = 305
                patron['role'] = {
                    'pl': 'dziewica i męczennica chrześcijańska z Aleksandrii, jedna z Czternastu Świętych Wspomożycieli, patronka filozofów, uczonych i kościoła na Kazimierzu',
                    'en': 'Christian virgin and martyr of Alexandria, one of the Fourteen Holy Helpers, patron saint of philosophers and scholars',
                    'de': 'christliche Jungfrau und Märtyrerin aus Alexandria, eine der Vierzehn Nothelfer, Schutzpatronin der Philosophen und Gelehrten'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Saint%20Catherine%20by%20cretan%20Victor%20%2817th%20c.%2C%20Byzantine%20museum%29.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Katarzyna_Aleksandryjska'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Katarzyna_Aleksandryjska'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Katarzyna_Aleksandryjska',
                    'en': 'https://en.wikipedia.org/wiki/Catherine_of_Alexandria',
                    'de': 'https://de.wikipedia.org/wiki/Katharina_von_Alexandrien'
                }
            elif rec['lp'] == 2736:
                patron['name'] = 'Święta Kinga (Kunegunda)'
                patron['birth_year'] = 1224
                patron['death_year'] = 1292
                patron['role'] = {
                    'pl': 'księżna krakowska i sandomierska z dynastii Arpadów, żona Bolesława Wstydliwego, fundatorka klasztoru klarysek w Starym Sączu, patronka górników solnych',
                    'en': 'High Duchess of Poland, wife of Bolesław V the Chaste, foundress of the Poor Clares monastery in Stary Sącz, patron saint of salt miners',
                    'de': 'Herzogin von Krakau und Sandomir aus dem Arpaden-Geschlecht, Gemahlin von Bolesław V., Gründerin des Klarissenklosters in Stary Sącz, Patronin der Salzbergleute'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/%C5%9Awi%C4%99ta%20Kinga.jpeg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Kinga_(%C5%9Bwi%C4%99ta)'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Kinga_(%C5%9Bwi%C4%99ta)'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Kinga_(%C5%9Bwi%C4%99ta)',
                    'en': 'https://en.wikipedia.org/wiki/Kinga_of_Poland',
                    'de': 'https://de.wikipedia.org/wiki/Kinga_von_Polen'
                }
            elif rec['lp'] == 2737:
                patron['name'] = 'Maria Magdalena'
                patron['birth_year'] = 1
                patron['death_year'] = 70
                patron['role'] = {
                    'pl': 'uczennica i wierna towarzyszka Jezusa Chrystusa, pierwszy świadek Zmartwychwstania Pańskiego, Apostołka Apostołów',
                    'en': 'follower and companion of Jesus Christ, first witness to the Resurrection, honored as the Apostle to the Apostles',
                    'de': 'Jüngerin und treue Begleiterin Jesu Christi, erste Zeugin der Auferstehung, geehrt als Apostelin der Apostel'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Maria_Magdalene_icon.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Maria_Magdalena'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Maria_Magdalena'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Maria_Magdalena',
                    'en': 'https://en.wikipedia.org/wiki/Mary_Magdalene',
                    'de': 'https://de.wikipedia.org/wiki/Maria_Magdalena'
                }
            elif rec['lp'] == 2739:
                patron['name'] = 'Teresa z Ávili'
                patron['birth_year'] = 1515
                patron['death_year'] = 1582
                patron['role'] = {
                    'pl': 'hiszpańska karmelitanka, mistyczka, reformatorka zakonu karmelitańskiego, pierwsza kobieta z tytułem Doktora Kościoła',
                    'en': 'Spanish Carmelite nun, prominent mystic, reformer of the Carmelite Order, first female Doctor of the Church',
                    'de': 'spanische Karmelitin, herausragende Mystikerin, Reformerin des Karmeliterordens, erste Kirchenlehrerin'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Santa%20Teresa%20de%20Jes%C3%BAs%20%28Museo%20del%20Prado%29.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Teresa_z_%C3%81vili'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Teresa_z_%C3%81vili'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Teresa_z_%C3%81vili',
                    'en': 'https://en.wikipedia.org/wiki/Teresa_of_%C3%81vila',
                    'de': 'https://de.wikipedia.org/wiki/Teresa_von_%C3%81vila'
                }
            elif rec['lp'] == 2756:
                patron['name'] = 'Franciszek Żwirko i Stanisław Wigura'
                patron['birth_year'] = 1895
                patron['death_year'] = 1932
                patron['role'] = {
                    'pl': 'legendarni polscy lotnicy: pilot por. Franciszek Żwirko i inż. konstruktor Stanisław Wigura, zwycięzcy zawodów Challenge 1932 na samolocie RWD-6',
                    'en': 'legendary Polish aviators: pilot Lt. Franciszek Żwirko and engineer Stanisław Wigura, winners of the Challenge 1932 on RWD-6 aircraft',
                    'de': 'legendäre polnische Flieger: Pilot Franciszek Żwirko und Ingenieur Stanisław Wigura, Sieger des Wettbewerbs Challenge 1932 mit der RWD-6'
                }
                patron['image'] = 'https://commons.wikimedia.org/wiki/Special:FilePath/Franciszek_%C5%BBwirko.jpg?width=360'
                patron['wiki_url'] = 'https://pl.wikipedia.org/wiki/Franciszek_%C5%BBwirko'
                patron['wikipedia_url'] = 'https://pl.wikipedia.org/wiki/Franciszek_%C5%BBwirko'
                patron['wiki_urls'] = {
                    'pl': 'https://pl.wikipedia.org/wiki/Franciszek_%C5%BBwirko',
                    'en': 'https://en.wikipedia.org/wiki/Franciszek_%C5%BBwirko',
                    'de': 'https://de.wikipedia.org/wiki/Franciszek_%C5%BBwirko'
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
        # Upewnij się, że props['name'] jest słownikiem i18n
        name_val = props.get('name')
        if isinstance(name_val, str):
            props['name'] = {'pl': name_val, 'en': name_val, 'de': name_val}

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
