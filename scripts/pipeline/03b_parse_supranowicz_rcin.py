#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/pipeline/03b_parse_supranowicz_rcin.py

Ekstrakcja monografii historyczno-onomastycznej:
Prof. Elżbieta Supranowicz, "Nazwy ulic Krakowa",
Instytut Języka Polskiego PAN, Kraków 1995 (RCIN publikacja 43027, wydanie 24551).

Etap 2 Pipeline:
1. Ominięcie zabezpieczenia Proof-of-Work (PoW) w Repozytorium Cyfrowym Instytutów Naukowych (RCIN).
2. Pobranie i buforowanie archiwum publikacji (format DjVu).
3. Dekompresja warstwy tekstowej OCR (BZZ/TXTz) w czystym Pythonie.
4. Ekstrakcja leksykonu haseł (strony 19-205): hasło, rok pierwszego poświadczenia, nazwy dawne, etymologia, biogramy patronów.
5. Zapis zindeksowanej bazy wiedzy do data/cache_supranowicz.json.
"""

import os
import sys
import re
import json
import struct
import zipfile
import hashlib
import urllib.request
import argparse

# Dodanie ścieżki bieżącego katalogu dla importu BZZDecoder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from djvubzzdec import BZZDecoder
except ImportError:
    alt_dir = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
    if alt_dir not in sys.path:
        sys.path.insert(0, alt_dir)
    from djvubzzdec import BZZDecoder

RCIN_EDITION_URL = "https://rcin.org.pl/dlibra/publication/43027/edition/24551"
RCIN_DOWNLOAD_URL = "https://rcin.org.pl/Content/24551/download/"
CACHE_ZIP_PATH = os.path.join("data", "supranowicz_rcin.zip")
OUTPUT_CACHE_PATH = os.path.join("data", "cache_supranowicz.json")

# Wykaz imion w dopełniaczu do naturalizacji szyku (np. "Dietla Józefa" -> "Józefa Dietla")
FIRST_NAMES_GENITIVE = {
    'adama', 'aleksandra', 'andrzeja', 'antoniego', 'artura', 'augusta', 'bartosza', 'bogusława',
    'bolesława', 'bronisława', 'cypriana', 'edwarda', 'emila', 'erazma', 'eugeniusza', 'feliksa',
    'franciszka', 'grzegorza', 'henryka', 'ignacego', 'iwana', 'jacka', 'jakuba', 'jana', 'janusza',
    'jerzego', 'joachima', 'józefa', 'juliana', 'juliusza', 'karola', 'kaspra', 'kazimierza', 'kornela',
    'krzysztofa', 'leona', 'leszka', 'lucjana', 'ludwika', 'macieja', 'maksymiliana', 'marcina',
    'mariana', 'marka', 'maurycego', 'michała', 'mieczysława', 'mikołaja', 'piotra', 'rafała', 'romana',
    'seweryna', 'stanisława', 'stefana', 'szczęsnego', 'szymona', 'tadeusza', 'teodora', 'tomasza',
    'wacława', 'walerego', 'wawrzyńca', 'władysława', 'włodzimierza', 'wojciecha', 'zdzisława',
    'zenona', 'zygmunta', 'królowej', 'księcia', 'biskupa', 'generała', 'hetmana', 'marszałka', 'profesora'
}

def normalize_key(s):
    """Normalizacja nazwy ulicy do jednolitego klucza porównawczego."""
    if not s:
        return ''
    s = s.lower().strip()
    s = re.sub(r'^(ulica|ul\.|aleja|al\.|plac|pl\.|osiedle|os\.|rondo|skwer|bulwar|droga|grobla|park)\s+', '', s)
    s = re.sub(r'[^a-ząćęłńóśźż0-9]', '', s)
    return s

def clean_ocr_name(name):
    """Koryguje drobne anomalie spacji w nagłówkach OCR DjVu."""
    fixes = {
        'C zarnowiej ska': 'Czarnowiejska',
        'Daj wór': 'Dajwór',
        'E stery': 'Estery',
        'Niep ołom ska': 'Niepołomska',
        'O rawska': 'Orawska',
        'Rybi twy': 'Rybitwy',
        'Pędzichów ': 'Pędzichów',
        'Sw. ': 'Św. ',
        'ŚW. ': 'Św. '
    }
    for k, v in fixes.items():
        if k in name:
            name = name.replace(k, v)
    return name.strip()

def solve_rcin_pow(url):
    """
    Omija zabezpieczenie Proof-of-Work (PoW) w RCIN dLibra.
    Wyszukuje timestamp, sygnaturę oraz wymagany prefiks zer i oblicza nonce MD5.
    Zwraca ciasteczko sesyjne captcha_pow.
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[!] Błąd połączenia z RCIN: {e}")
        return None

    ts_match = re.search(r'const ts = "(\d+)";', html)
    sig_match = re.search(r'const signature = "([a-f0-9]+)";', html)
    prefix_match = re.search(r'const prefix = "([0-9]+)";', html)

    if not (ts_match and sig_match and prefix_match):
        print("[i] RCIN nie wymaga w tej chwili rozwiązania PoW lub format strony uległ zmianie.")
        return None

    ts = ts_match.group(1)
    sig = sig_match.group(1)
    prefix = prefix_match.group(1)

    print(f"[+] Rozwiązuję wyzwanie PoW RCIN: ts={ts}, sig={sig}, prefix={prefix}...")
    nonce = 0
    while True:
        data = (sig + str(nonce)).encode('utf-8')
        h = hashlib.md5(data).hexdigest()
        if h.startswith(prefix):
            break
        nonce += 1

    cookie = f"captcha_pow={ts}_{nonce}"
    print(f"[+] PoW rozwiązany pomyślnie! Nonce={nonce}, Cookie={cookie}")
    return cookie

def ensure_rcin_archive(force_download=False):
    """
    Zapewnia obecność zbuforowanego archiwum ZIP z publikacją Supranowicz (1995).
    Jeśli plik nie istnieje lub force_download=True, pobiera go z RCIN po rozwiązaniu PoW.
    """
    if not force_download and os.path.exists(CACHE_ZIP_PATH) and os.path.getsize(CACHE_ZIP_PATH) > 10 * 1024 * 1024:
        print(f"[+] Znaleziono lokalne archiwum RCIN: {CACHE_ZIP_PATH} ({os.path.getsize(CACHE_ZIP_PATH):,} bajtów).")
        return CACHE_ZIP_PATH

    os.makedirs(os.path.dirname(CACHE_ZIP_PATH), exist_ok=True)
    cookie = solve_rcin_pow(RCIN_EDITION_URL)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    if cookie:
        headers['Cookie'] = cookie

    print(f"[+] Pobieram publikację z RCIN: {RCIN_DOWNLOAD_URL}...")
    req = urllib.request.Request(RCIN_DOWNLOAD_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as resp, open(CACHE_ZIP_PATH, 'wb') as f:
        chunk_size = 128 * 1024
        total_downloaded = 0
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            total_downloaded += len(chunk)
            if total_downloaded % (1024 * 1024) < chunk_size:
                print(f"    Pobrano: {total_downloaded / 1024 / 1024:.1f} MB...", flush=True)

    print(f"[+] Pobieranie ukończone: {CACHE_ZIP_PATH} ({os.path.getsize(CACHE_ZIP_PATH):,} bajtów).")
    return CACHE_ZIP_PATH

def extract_djvu_pages(zip_path):
    """
    Wypakowuje i dekoduje warstwę tekstową OCR (chunki TXTz) z pliku DjVu w archiwum ZIP.
    Zwraca listę krotek: (numer_strony, tekst_strony).
    """
    print("[+] Wczytuję i dekompresuję warstwę tekstową DjVu z archiwum...")
    with zipfile.ZipFile(zip_path, 'r') as z:
        djvu_files = [n for n in z.namelist() if n.lower().endswith('.djvu')]
        if not djvu_files:
            raise ValueError("Brak pliku .djvu w archiwum!")
        djvu_name = djvu_files[0]
        print(f"    Wybrany plik DjVu: {djvu_name}")
        with z.open(djvu_name) as f:
            data = f.read()

    pages = []
    idx = 0
    page_num = 0

    while True:
        idx = data.find(b'TXTz', idx)
        if idx == -1:
            break
        length = struct.unpack('>I', data[idx+4:idx+8])[0]
        chunk = data[idx+8:idx+8+length]
        idx += 8 + length
        page_num += 1

        # Dekompresja strumienia BZZ
        outbuf = bytearray()
        decoder = BZZDecoder(bytearray(chunk), outbuf)
        while decoder.convert(1024 * 1024):
            pass

        decomp = bytes(outbuf)
        if len(decomp) >= 3:
            # Pierwsze 3 bajty w standardzie DjVu TXTz to 24-bitowa długość tekstu UTF-8
            text_len = (decomp[0] << 16) | (decomp[1] << 8) | decomp[2]
            raw_text = decomp[3:3+text_len].decode('utf-8', errors='replace')
            # Normalizacja separatorów DjVu (\x1f, \x1e, \x1d)
            clean_text = raw_text.replace('\x1f', '\n').replace('\x1e', '\n').replace('\x1d', ' ')
            pages.append((page_num, clean_text))

    print(f"[+] Zdekompresowano łącznie {len(pages)} stron warstwy OCR DjVu.")
    return pages

def clean_entry_summary(body_text):
    """
    Generuje czyste, czytelne podsumowanie etymologiczne bez surowych sygnatur archiwalnych.
    """
    lines = [l.strip() for l in body_text.splitlines() if l.strip()]
    if not lines:
        return ''
    
    full_str = ' '.join(lines)
    full_str = re.sub(r'\s+', ' ', full_str)
    
    sentences = re.split(r'(?<=[.!?])\s+', full_str)
    summary_parts = []
    curr_len = 0
    for s in sentences:
        if curr_len + len(s) > 400 and summary_parts:
            break
        summary_parts.append(s)
        curr_len += len(s)
    
    return ' '.join(summary_parts)

def parse_entries_from_pages(pages):
    """
    Przetwarza tekst stron słownika (strony 19-205) na ustrukturyzowane hasła.
    """
    dict_pages = []
    for pnum, text in pages:
        if 19 <= pnum <= 205:
            lines = [l for l in text.splitlines() if not re.match(r'^\s*\d+\s*$', l)]
            dict_pages.append((pnum, '\n'.join(lines)))

    full_text = '\n'.join(p[1] for p in dict_pages)

    TYPE_WORDS = r'(?:ulica|aleja|alejka|plac|placyk|skwer|osiedle|droga|zaułek|przecznica|platea|via|contrata|forum|rynek|most|brama|bulwar|park|kopiec|błonia|ogród|grobla|osada|targ|targowisko|rondo|zjazd)'

    main_entry_pat = re.compile(
        rf'^\s*([0-9A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9\.\-\'’ ]{{1,50}},\s*{TYPE_WORDS})\s*[-–—]\s*([^.\n]+?)\.',
        re.MULTILINE
    )
    zob_entry_pat = re.compile(
        rf'^\s*([0-9A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9\.\-\'’ ]{{1,50}},\s*{TYPE_WORDS})\s+zob\.?\s+([^\n]+)',
        re.MULTILINE
    )

    main_matches = list(main_entry_pat.finditer(full_text))
    zob_matches = list(zob_entry_pat.finditer(full_text))

    all_markers = []
    for m in main_matches:
        all_markers.append((m.start(), m.end(), 'main', clean_ocr_name(m.group(1).strip()), m.group(2).strip()))
    for m in zob_matches:
        all_markers.append((m.start(), m.end(), 'zob', clean_ocr_name(m.group(1).strip()), clean_ocr_name(m.group(2).strip())))

    all_markers.sort(key=lambda x: x[0])
    print(f"[+] Zidentyfikowano {len(all_markers)} znaczników haseł ({len(main_matches)} głównych, {len(zob_matches)} odsyłaczy zob.).")

    # Mapa odsyłaczy zob.: cel -> lista dawnych nazw oraz nazwa zob -> cel
    zob_target_to_aliases = {}
    zob_alias_to_targets = {}

    for start_pos, end_pos, etype, name, extra in all_markers:
        if etype == 'zob':
            targets = [t.strip().rstrip('.') for t in extra.split(',')]
            zob_alias_to_targets[name] = targets
            for t in targets:
                if t:
                    if t not in zob_target_to_aliases:
                        zob_target_to_aliases[t] = []
                    zob_target_to_aliases[t].append(name)

    entries_dict = {}

    for i, (start_pos, match_end, etype, name, extra) in enumerate(all_markers):
        if etype != 'main':
            continue

        next_pos = all_markers[i+1][0] if i + 1 < len(all_markers) else len(full_text)
        body = full_text[match_end:next_pos].strip()

        name_parts = name.split(',')
        raw_title = clean_ocr_name(name_parts[0].strip())
        street_type = name_parts[1].strip() if len(name_parts) > 1 else 'ulica'
        district = extra

        # Naturalizacja szyku nazwy (np. "Dietla Józefa" -> "Józefa Dietla")
        words = raw_title.split()
        if len(words) == 2 and words[1].lower() in FIRST_NAMES_GENITIVE:
            clean_name = f"{words[1]} {words[0]}"
        elif len(words) == 3 and words[2].lower() in FIRST_NAMES_GENITIVE:
            clean_name = f"{words[2]} {words[0]} {words[1]}"
        elif len(words) == 2 and words[0].lower() in ('królowej', 'św.', 'świętej', 'świętego', 'księcia'):
            clean_name = raw_title
        else:
            clean_name = raw_title

        patron_bio = None
        patron_match = re.search(r'\n\s*([A-ZĄĆĘŁŃÓŚŹŻ\s\-]{4,45}\s*\(\d{4}[–\-]\d{4}\)[^\n]+(?:\n[^\n]+)*)', body)
        text_before_bio = body
        if patron_match:
            patron_bio = patron_match.group(1).strip()
            text_before_bio = body[:patron_match.start()].strip()

        first_year = None
        first_quote = None

        quote_matches = re.finditer(r'([A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s\.\-]{3,40}?\b(1[1-9]\d\d)\b\s+[A-Za-z0-9,\s]+)', text_before_bio)
        candidates = []
        for qm in quote_matches:
            q_text = qm.group(0).strip()
            q_year = int(qm.group(2))
            if 1150 <= q_year <= 1995:
                candidates.append((q_year, q_text))

        if candidates:
            candidates.sort(key=lambda x: x[0])
            first_year = candidates[0][0]
            first_quote = candidates[0][1]
            if len(first_quote) > 120:
                first_quote = first_quote[:120] + '...'
        else:
            year_matches = [int(y) for y in re.findall(r'\b(1[1-9]\d\d)\b', text_before_bio)]
            if year_matches:
                first_year = min(year_matches)

        if 'lokacj' in text_before_bio.lower() and ('1257' in text_before_bio or not first_year):
            first_year = 1257

        former_names = []
        if name in zob_target_to_aliases:
            for z in zob_target_to_aliases[name]:
                z_clean = z.split(',')[0].strip()
                if z_clean not in former_names:
                    former_names.append(z_clean)

        fn_matches = re.findall(r'(?:nosiła(?:\s+wówczas)?\s+nazwę|nazywała\s+się|nazwę\s+zmieniono\s+na|przemianowano(?:\s+ją|\s+go)?\s+na|określana\s+jako)\s+(?:ul\.|ulicy|placu|pl\.)?\s*([A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż\s\.\-]+?)(?:,|\.|\(|\s+w\s+r\.|\s+zmienion)', text_before_bio)
        for fn in fn_matches:
            fn_c = clean_ocr_name(fn.strip())
            if 3 <= len(fn_c) <= 35 and fn_c not in former_names:
                former_names.append(fn_c)

        latin_german = re.findall(r'(?:In der|Vor der|In platea|plateam|platea)\s+([A-Za-z\s]+?)(?:\d{4}|\bca\b|,|\.)', text_before_bio)
        for lg in latin_german:
            lg_c = lg.strip()
            if 3 <= len(lg_c) <= 35 and lg_c not in former_names:
                former_names.append(lg_c)

        summary = clean_entry_summary(text_before_bio)

        entry_obj = {
            'entry_name': name,
            'clean_name': clean_name,
            'raw_title': raw_title,
            'street_type': street_type,
            'district': district,
            'first_attestation_year': first_year,
            'first_attestation_quote': first_quote,
            'former_names': former_names,
            'etymology_summary': summary,
            'patron_bio': patron_bio,
            'etymology_raw': body,
            'source': {
                'author': 'prof. Elżbieta Supranowicz',
                'title': 'Nazwy ulic Krakowa',
                'publisher': 'Instytut Języka Polskiego PAN, Kraków',
                'year': 1995,
                'isbn': '83-85579-48-6',
                'rcin_url': RCIN_EDITION_URL
            }
        }
        entries_dict[name] = entry_obj

    # Budujemy indeks podwójny do natychmiastowego wyszukiwania
    by_normalized = {}
    for entry_name, obj in entries_dict.items():
        raw_title = obj['raw_title']
        clean_name = obj['clean_name']
        
        # 1. Klucze podstawowe
        by_normalized[normalize_key(entry_name)] = entry_name
        by_normalized[normalize_key(clean_name)] = entry_name
        by_normalized[normalize_key(raw_title)] = entry_name

        # 2. Klucz samego nazwiska (np. "Dietla", "Asnyka") jeśli nie jest to tytuł honorowy
        words = raw_title.split()
        if len(words) >= 2 and words[0].lower() not in ('św.', 'świętej', 'świętego', 'królowej', 'księcia', 'biskupa', 'plac', 'aleja'):
            by_normalized[normalize_key(words[0])] = entry_name

        # 3. Odwrócenie jeśli 2 słowa
        if len(words) == 2 and words[1].lower() in FIRST_NAMES_GENITIVE:
            inv = f"{words[1]} {words[0]}"
            by_normalized[normalize_key(inv)] = entry_name
        elif len(words) == 3 and words[2].lower() in FIRST_NAMES_GENITIVE:
            inv = f"{words[2]} {words[0]} {words[1]}"
            by_normalized[normalize_key(inv)] = entry_name

        # 4. Dawne nazwy z listy
        for fn in obj['former_names']:
            fn_k = normalize_key(fn)
            if fn_k and fn_k not in by_normalized:
                by_normalized[fn_k] = entry_name

    # 5. Zindeksowanie odsyłaczy zob. (dawne nazwy mapowane na hasło główne)
    for alias_name, targets in zob_alias_to_targets.items():
        alias_title = alias_name.split(',')[0].strip()
        alias_k = normalize_key(alias_title)
        
        # Znajdź docelowe hasło główne
        target_found = None
        for t in targets:
            # Sprawdź dokładne hasło
            if t in entries_dict:
                target_found = t
                break
            # Sprawdź po normalizacji
            t_k = normalize_key(t)
            if t_k in by_normalized:
                target_found = by_normalized[t_k]
                break

        if target_found and alias_k and alias_k not in by_normalized:
            by_normalized[alias_k] = target_found

    final_payload = {
        'metadata': {
            'monograph_title': 'Nazwy ulic Krakowa',
            'author': 'prof. Elżbieta Supranowicz',
            'publisher': 'Wydawnictwo Instytutu Języka Polskiego PAN, Kraków 1995',
            'isbn': '83-85579-48-6',
            'rcin_url': RCIN_EDITION_URL,
            'total_entries': len(entries_dict),
            'total_indexed_keys': len(by_normalized)
        },
        'entries': entries_dict,
        'by_normalized_name': by_normalized
    }

    return final_payload

def main():
    parser = argparse.ArgumentParser(description='Ekstrakcja monografii prof. E. Supranowicz (RCIN PAN) - Etap 2 Pipeline')
    parser.add_argument('--force-download', action='store_true', help='Wymuszenie ponownego pobrania archiwum z RCIN z rozwiązaniem PoW')
    args = parser.parse_args()

    print("=== ETAP 2: EKSTRAKCJA MONOGRAFII PROF. ELŻBIETY SUPRANOWICZ (RCIN PAN) ===")
    
    archive_path = ensure_rcin_archive(force_download=args.force_download)
    pages = extract_djvu_pages(archive_path)

    print("[+] Parsuję hasła leksykonu i buduję bazę danych...")
    cache_data = parse_entries_from_pages(pages)

    print(f"[+] Zapisuję zindeksowaną bazę wiedzy do {OUTPUT_CACHE_PATH}...")
    os.makedirs(os.path.dirname(OUTPUT_CACHE_PATH), exist_ok=True)
    with open(OUTPUT_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

    meta = cache_data['metadata']
    size_mb = os.path.getsize(OUTPUT_CACHE_PATH) / (1024 * 1024)
    print("\n=== ZAKOŃCZONO POMYŚLNIE ETAP 2 ===")
    print(f" * Łącznie wyekstrahowanych haseł głównych: {meta['total_entries']}")
    print(f" * Zindeksowanych wariantów nazw (kluczy): {meta['total_indexed_keys']}")
    print(f" * Rozmiar pliku wynikowego: {size_mb:.2f} MB ({OUTPUT_CACHE_PATH})")

if __name__ == '__main__':
    main()
