#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/pipeline/04_scrape_bip_full.py
ZADANIE 3: Pełny Scraper Uchwał i Druków BIP RMK (1990–2026)

Przeszukuje rejestr uchwał Rady Miasta Krakowa w Biuletynie Informacji Publicznej (BIP),
obejmując wszystkie 9 kadencji (1990–2026) w sprawach nadania/zmiany nazw ulic, placów,
skwerów, rond, alei i parków.

Dla każdej uchwały pobiera:
- numer uchwały, datę, tytuł i odnośnik BIP
- plik PDF uchwały (oraz parsuje § 1 w poszukiwaniu nadanej nazwy)
- numer Druku RMK i odnośnik do ścieżki legislacyjnej projektu
- bezpośredni plik PDF druku z oficjalnym uzasadnieniem
- wyciąg z tekstu uzasadnienia (sekcja Uzasadnienie)
- dopasowanie do bazy 2 763 ulic Krakowa

Wyniki zapisuje przyrostowo w data/cache_bip_full.json.
"""

import sys
import io
import re
import os
import time
import json
import argparse
import urllib.parse
import requests
from bs4 import BeautifulSoup
import pypdf

BIP_BASE_URL = "https://www.bip.krakow.pl"
SEARCH_ENDPOINT = f"{BIP_BASE_URL}/?dok_id=166&sub_dok_id=166&sub=wyszukiwarkazq&query=&typ=u&kadencja_od=1&kadencja_do=9&aktualne="

STREET_NAMES_FILE = "data/krakow_street_names.json"
CACHE_FILE = "data/cache_bip_full.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KrakowStreetsBIPScraper/1.0 (https://github.com/ulice_krakowa)"
}

SEARCH_QUERIES = [
    'w_sprawie_nadania',
    'nadania_nazwy',
    'nadanie_nazwy',
    'nadania_nazw',
    'nadanie_nazw',
    'nazwy_ulicy',
    'nazw_ulic',
    'nazwy_placu',
    'nazwy_skweru',
    'nazwy_ronda',
    'nazwy_alei',
    'nazwy_parku',
    'zmiany_nazwy',
    'zmiany_nazw',
    'nadania_imienia',
    'nadanie_imienia',
    'nazw_ulicom',
    'ulicy',
    'alei',
    'placu',
    'skweru',
    'ronda'
]

TITLE_EXCLUDE_REGEX = re.compile(
    r'(?:szkoł|przedszkol|żłobk|statut|dzielnic[ey]|liceum|gimnazj|szpital|zespoł|hali\b|kompleks|domu\s+pomocy|ośrodk|instytuc|poradni|bibliotek|teatr|muzeum|planu\s+miejscowego|planu\s+inwestycyjnego|zagospodarowania|sprzedaż|nabyci|dzierżaw|nieruchomoś|lokal|pożyczk|dotacj|budżet|podatk)',
    re.IGNORECASE
)

TITLE_NAMING_REGEX = re.compile(
    r'(?:nadani[ae]|zmian[ya]|zniesieni[ae]|ustaleni[ae]|rozszerzeni[ae]).*?nazw[yęa]|'
    r'(?:nadani[ae]|zmian[ya]).*?imienia.*?(?:ulic|alei|plac|skwer|rond|park|most|bulwar)|'
    r'w\s+sprawie\s+nazw[yęa]|'
    r'nazw[yęa]\s+(?:dla\s+)?(?:ulic|alei|plac|skwer|rond|park|most)',
    re.IGNORECASE
)

TITLE_FEATURE_REGEX = re.compile(
    r'(?:ulic|alei|al\.|plac|pl\.|skwer|rond|park|most|bulwar|zaułk|drog[aię]|kładk|ciąg\w*\s+piesz)',
    re.IGNORECASE
)

def normalize_key(s):
    if not s:
        return ''
    s = s.lower().strip()
    s = re.sub(r'^(ulica|ul\.|aleja|al\.|plac|pl\.|osiedle|os\.|rondo|skwer|bulwar|droga|grobla|park)\s+', '', s)
    s = re.sub(r'[^a-ząćęłńóśźż0-9]', '', s)
    return s

def load_krakow_street_names():
    if os.path.exists(STREET_NAMES_FILE):
        try:
            with open(STREET_NAMES_FILE, 'r', encoding='utf-8') as f:
                names = json.load(f)
                return names
        except Exception as e:
            print(f"[!] Błąd wczytywania {STREET_NAMES_FILE}: {e}", file=sys.stderr)
    return []

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return {item.get('number', str(i)): item for i, item in enumerate(data)}
                elif isinstance(data, dict):
                    return data
        except Exception as e:
            print(f"[!] Błąd wczytywania cache {CACHE_FILE}: {e}", file=sys.stderr)
    return {}

def save_cache(cache_dict):
    items = list(cache_dict.values())
    items.sort(key=lambda x: x.get('date', ''), reverse=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

def create_session():
    session = requests.Session()
    session.headers.update(HEADERS)
    adapter = requests.adapters.HTTPAdapter(max_retries=requests.adapters.Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[500, 502, 503, 504]
    ))
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

def search_bip_registry(session, queries=None):
    """
    Przeszukuje rejestr BIP Kraków dla wszystkich zapytań i zwraca listę unikalnych
    uchwał związanych z nazewnictwem.
    """
    if queries is None:
        queries = SEARCH_QUERIES

    print(f"[*] Rozpoczynanie przeszukiwania BIP Kraków (kadencje 1–9, 1990–2026)...", flush=True)
    unique_candidates = {}

    for q in queries:
        url = f"{SEARCH_ENDPOINT}&queryu={q}&from_no=1&to_no=1000"
        try:
            resp = session.get(url, timeout=35)
            if resp.status_code != 200:
                print(f" [!] Błąd HTTP {resp.status_code} dla zapytania '{q}'", file=sys.stderr)
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            table = soup.find('table')
            if not table:
                continue

            count_q = 0
            for tr in table.find_all('tr')[1:]:
                tds = tr.find_all('td')
                if len(tds) >= 3:
                    num = tds[0].text.strip()
                    a = tds[1].find('a')
                    title = a.text.strip() if a else tds[1].text.strip()
                    title = re.sub(r'\s+', ' ', title).strip()
                    link = a['href'] if a and a.has_attr('href') else ''
                    dt = tds[2].text.strip()
                    if num and num not in unique_candidates:
                        unique_candidates[num] = {
                            'number': num,
                            'title': title,
                            'date': dt,
                            'url': link
                        }
                    count_q += 1

            print(f" [+] Zapytanie '{q}': {count_q} wyników (unikalnych łącznie: {len(unique_candidates)})", flush=True)
            time.sleep(0.3)
        except Exception as e:
            print(f" [!] Błąd pobierania zapytania '{q}': {e}", file=sys.stderr)

    # Filtrowanie uchwał dotyczących nazewnictwa miejskiego
    matched_resolutions = []
    for num, item in unique_candidates.items():
        title = item['title']
        if TITLE_EXCLUDE_REGEX.search(title) and not re.search(r'nadani[ae]\s+(?:nazw|imienia).*?(?:ulic|alei|plac|skwer|rond|park)', title, re.I):
            continue

        if TITLE_NAMING_REGEX.search(title) and TITLE_FEATURE_REGEX.search(title):
            matched_resolutions.append(item)

    print(f"\n[+] Przeszukiwanie zakończone: zidentyfikowano {len(matched_resolutions)} uchwał o nazewnictwie z lat 1990–2026.", flush=True)
    return matched_resolutions

def extract_subject_from_title(title):
    """Próbuje wyłuskać nazwę patrona/obiektu bezpośrednio z tytułu uchwały."""
    patterns = [
        r'nadania\s+(?:(?:ulicy|alei|placowi|skwerowi|rondu|parkowi|mostowi|kładce|ciągowi\s+pieszemu)(?:\s+miejskiemu)?\s+)?(?:im\.\s+|imienia\s+)?nazwy\s*[:\-–„"]?\s*([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż0-9\s\.\-–\',]+?)(?:[”"]|\.|\b(?:oraz|określenia|położon|biegnąc|w\s+dzielnicy|przy\s+ul|łącząc|uchylając|zmieniając)|$)',
        r'nadania\s+nazwy\s+(?:ulicy|alei|placu|skweru|ronda|parku|mostu)\s*[:\-–„"]?\s*(?:im\.\s+|imienia\s+)?([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż0-9\s\.\-–\',]+?)(?:[”"]|\.|\b(?:oraz|określenia|położon|biegnąc|w\s+dzielnicy|przy\s+ul|łącząc|uchylając|zmieniając)|$)',
        r'nadania\s+imienia\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż0-9\s\.\-–\',]+?)\s+(?:ulicy|alei|placowi|skwerowi|rondu|parkowi|mostowi)',
        r'zmiany\s+nazwy\s+(?:ulicy|alei|placu|skweru|ronda|parku)\s*[:\-–„"]?\s*([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż0-9\s\.\-–\',]+?)(?:[”"]|\.|\bna\b|\boraz\b|$)',
        r'nadania\s+nazwy\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż0-9\s\.\-–\',]+?)(?:[”"]|\.|\b(?:oraz|położon)|$)'
    ]
    for p in patterns:
        m = re.search(p, title, re.I)
        if m:
            candidate = m.group(1).strip().strip('„”"\'.,:')
            if len(candidate) > 2 and not candidate.lower().startswith(('uchwa', 'rady', 'miasta')):
                return candidate
    return None

def extract_street_from_resolution_text(pdf_text):
    """
    Wydobywa nazwę ulicy z treści uchwały (zwłaszcza z § 1, np. 'Nadaje się nazwę: ul. X').
    """
    if not pdf_text:
        return None

    m1 = re.search(r'(?:§\s*1\.?|nadaje\s+się\s+(?:następującą\s+)?nazw[ęy])\s*[:\-–]?\s*(?:(?:dla\s+)?(?:ulicy|drogi|alei|placu|skweru|ronda|parku)\s+)?(?:ul\.|ulicy|al\.|alei|pl\.|placu|skwer|rondo|park)\s*([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż0-9\s\.\-–„”"\'\/]+?)(?:\s+(?:dla|położon|biegnąc|w\s+dzielnicy|łącząc|od\s+działki|przecznicy|\.|\n|$))', pdf_text, re.IGNORECASE)
    if m1:
        cand = m1.group(1).strip().strip('„”"\'.,:')
        cand = re.sub(r'\s+', ' ', cand)
        if len(cand) > 2 and not cand.lower().startswith(('uchwa', 'rady', 'miasta')):
            return cand

    m2 = re.search(r'(?:1\)|1\.)\s*(?:ul\.|ulica|aleja|al\.|plac|pl\.|skwer|rondo|park)\s+([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż0-9\s\.\-–„”"\'\/]+?)(?:\s+(?:położon|biegnąc|w\s+dzielnicy|łącząc|przecznicy|\.|\n|$))', pdf_text, re.IGNORECASE)
    if m2:
        cand = m2.group(1).strip().strip('„”"\'.,:')
        cand = re.sub(r'\s+', ' ', cand)
        if len(cand) > 2 and not cand.lower().startswith(('uchwa', 'rady', 'miasta')):
            return cand

    return None

def extract_justification_text(pdf_text):
    """Ekstrahuje treść sekcji Uzasadnienie z tekstu PDF."""
    if not pdf_text:
        return None
    
    clean_text = re.sub(r'[ \t]+', ' ', pdf_text)
    match = re.search(r'UZASADNIENIE\s*[:\.]?\s*(.*?)(?:Druk\s+nr|Prezydent\s+Miasta\s+Krakowa|Przewodniczący\s+Rady|Radni\s+Miasta|$)', clean_text, re.DOTALL | re.IGNORECASE)
    if match:
        just = match.group(1).strip()
        just = re.sub(r'(?<!\n)\n(?!\n)', ' ', just)
        just = re.sub(r'\s+', ' ', just).strip()
        if len(just) > 30:
            return just[:2500]
    return None

def fetch_pdf_text(session, pdf_url):
    """Pobiera plik PDF do pamięci i zwraca wyekstrahowany tekst ze wszystkich stron."""
    if not pdf_url:
        return ""
    try:
        resp = session.get(pdf_url, timeout=25)
        if resp.status_code == 200 and resp.content[:4] == b'%PDF':
            reader = pypdf.PdfReader(io.BytesIO(resp.content))
            pages_text = []
            for p in reader.pages:
                t = p.extract_text() or ''
                pages_text.append(t)
            return "\n".join(pages_text)
    except Exception as e:
        pass
    return ""

def match_street_name(extracted_str, krakow_streets, street_keys_map):
    """
    Dopasowuje wyodrębnioną nazwę do bazy oficjalnych ulic Krakowa.
    """
    if not extracted_str:
        return None

    k = normalize_key(extracted_str)
    if k in street_keys_map:
        return street_keys_map[k]

    for s in krakow_streets:
        s_clean = re.sub(r'^(ulica|ul\.|aleja|al\.|plac|pl\.|osiedle|os\.|rondo|skwer|bulwar|droga|park)\s+', '', s, flags=re.I).strip()
        words = s_clean.split()
        if len(words) >= 2:
            if re.search(r'\b' + re.escape(s_clean) + r'\b', extracted_str, re.I):
                return s
        else:
            if len(s_clean) >= 4 and re.search(r'\b' + re.escape(s_clean) + r'[\w]*\b', extracted_str, re.I):
                return s

    return None

def process_resolution(session, resolution_item, krakow_streets, street_keys_map):
    """
    Pobiera szczegóły pojedynczej uchwały z BIP, ścieżkę druku i pliki PDF.
    """
    num = resolution_item['number']
    rel_url = resolution_item['url'].replace('&amp;', '&')
    full_res_url = urllib.parse.urljoin(BIP_BASE_URL, rel_url)

    record = {
        'number': num,
        'title': resolution_item['title'],
        'date': resolution_item['date'],
        'organ': 'Rada Miasta Krakowa',
        'url': full_res_url,
        'bip_url': full_res_url,
        'pdf_url': None,
        'legislative_path_url': None,
        'druk_url': None,
        'druk_number': None,
        'druk_pdf_url': None,
        'street': None,
        'street_key': None,
        'extracted_subject': None,
        'justification_excerpt': None,
        'has_resolution': True
    }

    try:
        resp = session.get(full_res_url, timeout=25)
        if resp.status_code != 200:
            return record
        html = resp.text
    except Exception as e:
        print(f"    [!] Błąd pobierania podstrony uchwały {num}: {e}", file=sys.stderr)
        return record

    pdf_match = re.search(r'href=[\"\']([^\"\']*show_pdf\.php\?id=\d+[^\"\']*)[\"\']', html, re.I)
    if pdf_match:
        record['pdf_url'] = urllib.parse.urljoin(BIP_BASE_URL, pdf_match.group(1).replace('&amp;', '&'))

    prid_match = re.search(r'href=[\"\']([^\"\']*sub=drukiuchw[^\"\']*prid=\d+[^\"\']*)[\"\']', html, re.I)
    if prid_match:
        leg_url = urllib.parse.urljoin(BIP_BASE_URL, prid_match.group(1).replace('&amp;', '&'))
        record['legislative_path_url'] = leg_url
        record['druk_url'] = leg_url

        try:
            resp_druk = session.get(leg_url, timeout=25)
            if resp_druk.status_code == 200:
                druk_html = resp_druk.text
                d_num = re.search(r'Druk\s+nr\s+\d+[\w/-]*', druk_html, re.I)
                if d_num:
                    record['druk_number'] = d_num.group(0).strip()

                soup_druk = BeautifulSoup(druk_html, 'html.parser')
                druk_pdfs = []
                for a in soup_druk.find_all('a', href=True):
                    href = a['href']
                    if 'show_pdfdoc.php' in href or href.endswith('.pdf'):
                        druk_pdfs.append(urllib.parse.urljoin(BIP_BASE_URL, href.replace('&amp;', '&')))

                if druk_pdfs:
                    record['druk_pdf_url'] = druk_pdfs[-1]
                    record['all_druk_pdfs'] = druk_pdfs
        except Exception as e:
            print(f"    [!] Ostrzeżenie przy pobieraniu ścieżki druku {num}: {e}", file=sys.stderr)

    res_pdf_text = ""
    if record['pdf_url']:
        res_pdf_text = fetch_pdf_text(session, record['pdf_url'])

    subj_from_title = extract_subject_from_title(record['title'])
    subj_from_body = extract_street_from_resolution_text(res_pdf_text)
    
    extracted_subject = subj_from_title or subj_from_body
    record['extracted_subject'] = extracted_subject

    matched_street = None
    if subj_from_title:
        matched_street = match_street_name(subj_from_title, krakow_streets, street_keys_map)
    if not matched_street and subj_from_body:
        matched_street = match_street_name(subj_from_body, krakow_streets, street_keys_map)
    if not matched_street:
        matched_street = match_street_name(record['title'], krakow_streets, street_keys_map)

    if matched_street:
        record['street'] = matched_street
        record['street_key'] = normalize_key(matched_street)
    elif extracted_subject:
        record['street'] = extracted_subject
        record['street_key'] = normalize_key(extracted_subject)

    justification = None
    all_pdfs = []
    if record.get('all_druk_pdfs'):
        all_pdfs.extend(record['all_druk_pdfs'])
    elif record.get('druk_pdf_url'):
        all_pdfs.append(record['druk_pdf_url'])

    for d_pdf in all_pdfs:
        d_text = fetch_pdf_text(session, d_pdf)
        just = extract_justification_text(d_text)
        if just:
            justification = just
            record['druk_pdf_url'] = d_pdf
            break

    if not justification and res_pdf_text:
        justification = extract_justification_text(res_pdf_text)

    if justification:
        record['justification_excerpt'] = justification
        record['official_justification'] = justification

    return record

def main():
    parser = argparse.ArgumentParser(description="Pełny scraper uchwał i druków BIP Kraków (1990–2026)")
    parser.add_argument("--limit", type=int, default=None, help="Maksymalna liczba uchwał do przetworzenia")
    parser.add_argument("--force", action="store_true", help="Wymuś ponowne pobranie nawet jeśli jest w cache")
    parser.add_argument("--output", default=CACHE_FILE, help="Ścieżka do pliku wyjściowego JSON")
    args = parser.parse_args()

    session = create_session()
    krakow_streets = load_krakow_street_names()
    street_keys_map = {normalize_key(s): s for s in krakow_streets if normalize_key(s)}
    print(f"[*] Wczytano {len(krakow_streets)} oficjalnych ulic Krakowa do dopasowywania.", flush=True)

    cache = {} if args.force else load_cache()
    print(f"[*] Zarejestrowanych uchwał w pamięci podręcznej (cache): {len(cache)}", flush=True)

    resolutions_to_process = search_bip_registry(session)
    if args.limit:
        resolutions_to_process = resolutions_to_process[:args.limit]

    print(f"\n[*] Przetwarzanie szczegółów dla {len(resolutions_to_process)} uchwał...", flush=True)
    saved_count = 0
    matched_count = 0

    for i, res_item in enumerate(resolutions_to_process, 1):
        num = res_item['number']
        
        if num in cache and not args.force:
            cached_rec = cache[num]
            if cached_rec.get('street'):
                matched_count += 1
            continue

        print(f"[{i}/{len(resolutions_to_process)}] Pobieranie: {num} ({res_item['date']})...", flush=True)
        processed = process_resolution(session, res_item, krakow_streets, street_keys_map)
        cache[num] = processed
        saved_count += 1

        street_info = processed.get('street') or processed.get('extracted_subject') or "Brak"
        has_pdf = "TAK" if processed.get('pdf_url') else "NIE"
        has_druk = processed.get('druk_number') or "NIE"
        has_just = "TAK" if processed.get('justification_excerpt') else "NIE"
        
        if processed.get('street'):
            matched_count += 1

        print(f"    -> Ulica/Obiekt: {street_info} | PDF: {has_pdf} | Druk: {has_druk} | Uzasadnienie: {has_just}", flush=True)

        if saved_count % 5 == 0:
            save_cache(cache)

        time.sleep(0.3)

    save_cache(cache)

    print("\n" + "=" * 60)
    print("=== RAPORT KOŃCOWY: ETAP 3 (BIP RMK 1990–2026) ===")
    print(f"Liczba uchwał w bazie cache: {len(cache)}")
    print(f"Nowo pobranych w tej sesji: {saved_count}")
    with_pdf = sum(1 for r in cache.values() if r.get('pdf_url'))
    with_druk = sum(1 for r in cache.values() if r.get('druk_number'))
    with_just = sum(1 for r in cache.values() if r.get('justification_excerpt'))
    with_street = sum(1 for r in cache.values() if r.get('street'))
    print(f"Uchwały z bezpośrednim PDF: {with_pdf}")
    print(f"Uchwały z przypisanym Drukiem RMK: {with_druk}")
    print(f"Uchwały z wyciągniętym oficjalnym uzasadnieniem: {with_just}")
    print(f"Uchwały powiązane z nazwami ulic/obiektów: {with_street}")
    print(f"Plik wyjściowy: {args.output}")
    print("=" * 60)

if __name__ == '__main__':
    main()
