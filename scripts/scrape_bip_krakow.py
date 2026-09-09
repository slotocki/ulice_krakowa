#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do automatycznego przeszukiwania Biuletynu Informacji Publicznej (BIP) Miasta Krakowa
oraz pobierania uchwał Rady Miasta Krakowa dotyczących nadawania nazw ulicom, placom i skwerom.

Wyszukiwarka BIP Kraków (rejestr uchwał RMK):
dok_id=166 / sub=wyszukiwarkazq
"""

import sys
import re
import time
import json
import argparse
from urllib.request import Request, urlopen
from urllib.parse import quote, urljoin

BIP_BASE_URL = "https://www.bip.krakow.pl"
SEARCH_ENDPOINT = f"{BIP_BASE_URL}/?dok_id=166&sub_dok_id=166&sub=wyszukiwarkazq&kadencja_od=1&kadencja_do=9&query=typ%3Du"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def fetch_url(url):
    """Pobiera zawartość tekstową z podanego adresu URL z poprawnym dekodowaniem."""
    req = Request(url, headers=HEADERS)
    with urlopen(req, timeout=20) as response:
        charset = response.headers.get_content_charset() or 'utf-8'
        content = response.read()
        try:
            return content.decode(charset)
        except UnicodeDecodeError:
            return content.decode('utf-8', errors='replace')


def search_resolutions(query_phrase="nadania nazwy", limit=10):
    """
    Przeszukuje rejestr uchwał RMK w BIP Kraków.
    BIP wymaga słów kluczowych w parametrze `queryu`.
    """
    search_url = f"{SEARCH_ENDPOINT}&queryu={quote(query_phrase)}"
    print(f"[*] Wysyłanie zapytania do BIP Kraków: {search_url}")

    try:
        html = fetch_url(search_url)
    except Exception as e:
        print(f"[!] Błąd połączenia z BIP Kraków: {e}", file=sys.stderr)
        return []

    # Sprawdzenie liczby znalezionych rekordów
    count_match = re.search(r'Znaleziono\s+(\d+)\s+rekord', html)
    if count_match:
        total_found = count_match.group(1)
        print(f"[+] BIP Kraków: znaleziono {total_found} uchwał odpowiadających zapytaniu '{query_phrase}'.")
    else:
        print("[!] Nie udało się odczytać licznika wyników z BIP.")

    # Ekstrakcja wierszy z tabeli wyników
    # Wzorzec w tabeli BIP:
    # <tr><td ...>NUMER</td><td ...><a href="LINK">TYTUŁ</a></td><td ...>DATA</td></tr>
    row_pattern = re.compile(
        r"<tr>\s*<td[^>]*>(?P<number>[^<]+)</td>\s*<td[^>]*>\s*<a\s+href=[\"'](?P<link>[^\"']+)[\"']>(?P<title>.*?)</a>\s*</td>\s*<td[^>]*>(?P<date>[^<]+)</td>",
        re.DOTALL | re.IGNORECASE
    )

    matches = list(row_pattern.finditer(html))
    print(f"[+] Odczytano {len(matches)} pozycji z pierwszej strony wyników.")

    results = []
    for match in matches[:limit]:
        number = match.group('number').strip()
        relative_link = match.group('link').replace('&amp;', '&').strip()
        full_url = urljoin(BIP_BASE_URL + '/', relative_link)
        
        # Oczyszczenie tytułu
        title_raw = match.group('title')
        clean_title = re.sub(r'<[^>]+>', ' ', title_raw)
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()

        date_str = match.group('date').strip()

        # Wykrycie nazwy patrona/obiektu z tytułu
        # np. "w sprawie nadania Parkowi Miejskiemu nazwy Park Kleparski..."
        # np. "w sprawie nadania nazwy ulicy: Stanisława Lema..."
        subject_match = re.search(
            r'(?:nadania nazwy|nadania.*?nazwy|w sprawie nazwy)\s*[:\-–]?\s*([A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż\s\.\-–„”"]+?)(?:,|\.|\bw dzielnicy|\w\s+dniu|$)',
            clean_title,
            re.IGNORECASE
        )
        extracted_name = subject_match.group(1).strip() if subject_match else None

        results.append({
            "number": number,
            "title": clean_title,
            "date": date_str,
            "extracted_subject": extracted_name,
            "url": full_url
        })

    return results


def enrich_resolution_details(resolution):
    """
    Pobiera podstronę pojedynczej uchwały, aby wydobyć:
    - bezpośredni link do pliku PDF z treścią uchwały i uzasadnieniem
    - link do ścieżki legislacyjnej projektu (gdzie jest uzasadnienie wnioskodawcy)
    """
    print(f" -> Pobieranie szczegółów: {resolution['number']}...")
    try:
        page_html = fetch_url(resolution['url'])
    except Exception as e:
        print(f"    [!] Błąd pobierania podstrony: {e}")
        return resolution

    # 1. Wyszukanie linku do pliku PDF uchwały
    pdf_match = re.search(r'href=[\"\']([^\"\']*show_pdf\.php\?id=\d+[^\"\']*)[\"\']', page_html, re.IGNORECASE)
    if pdf_match:
        resolution["pdf_url"] = urljoin(BIP_BASE_URL, pdf_match.group(1).replace('&amp;', '&'))

    # 2. Wyszukanie linku do ścieżki legislacyjnej / druku uchwały
    druk_match = re.search(r'href=[\"\']([^\"\']*sub=drukiuchw[^\"\']*)[\"\']', page_html, re.IGNORECASE)
    if druk_match:
        leg_url = urljoin(BIP_BASE_URL, druk_match.group(1).replace('&amp;', '&'))
        resolution["legislative_path_url"] = leg_url
        resolution["druk_url"] = leg_url

        # Przejście do ścieżki legislacyjnej w celu wydobycia numeru Druku i PDF z uzasadnieniem
        try:
            leg_html = fetch_url(leg_url)
            d_num = re.search(r'Druk\s+nr\s+\d+', leg_html, re.IGNORECASE)
            if d_num:
                resolution["druk_number"] = d_num.group(0)

            d_pdf = re.search(r'href=[\"\']([^\"\']*show_pdfdoc\.php\?id=\d+[^\"\']*)[\"\']', leg_html, re.IGNORECASE)
            if d_pdf:
                resolution["druk_pdf_url"] = urljoin(BIP_BASE_URL, d_pdf.group(1).replace('&amp;', '&'))
        except Exception as e:
            print(f"    [!] Ostrzeżenie przy pobieraniu ścieżki druku: {e}")

    return resolution


def main():
    parser = argparse.ArgumentParser(description="Pobieracz uchwał z BIP Kraków o nazwach ulic")
    parser.add_argument("--phrase", default="nadania nazwy", help="Słowa kluczowe do wyszukiwarki (np. 'nadania nazwy', 'nazwy ulicy', 'Lema')")
    parser.add_argument("--street", help="Szukaj uchwały dla konkretnej ulicy/patrona (np. 'Lema', 'Szymborskiej')")
    parser.add_argument("--limit", type=int, default=10, help="Maksymalna liczba uchwał do pobrania")
    parser.add_argument("--output", default="data/uchwaly_bip.json", help="Ścieżka do pliku wyjściowego JSON")
    
    args = parser.parse_args()

    search_phrase = args.street if args.street else args.phrase
    
    items = search_resolutions(query_phrase=search_phrase, limit=args.limit)
    
    if not items:
        print("\n[INFO] Brak wyników dla podanej frazy.")
        return

    detailed_items = []
    for item in items:
        enriched = enrich_resolution_details(item)
        detailed_items.append(enriched)
        time.sleep(0.5) # Łagodne tempo zapytań

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(detailed_items, f, ensure_ascii=False, indent=2)

    print(f"\n[SUKCES] Zapisano {len(detailed_items)} uchwał do pliku: {args.output}")
    print("\nPrzykładowe pobrane uchwały:")
    for doc in detailed_items[:3]:
        print(f" • [{doc['date']}] {doc['number']}: {doc['title'][:80]}...")
        print(f"   URL: {doc['url']}")
        if "pdf_url" in doc:
            print(f"   PDF: {doc['pdf_url']}")


if __name__ == "__main__":
    main()
