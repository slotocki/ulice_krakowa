#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do automatycznego pobierania plików PDF uchwał z BIP Kraków
i wyciągania z nich tekstu sekcji 'UZASADNIENIE' przy użyciu biblioteki pypdf.
"""

import sys
import io
import re
import json
import argparse
import urllib.request
import pypdf

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KrakowStreetsPDFParser/1.0"
}

def extract_justification_from_pdf(pdf_url):
    """
    Pobiera plik PDF z BIP w pamięci RAM i wydobywa tekst Uzasadnienia.
    """
    print(f"[*] Pobieranie PDF: {pdf_url}...")
    try:
        req = urllib.request.Request(pdf_url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=25) as resp:
            pdf_bytes = resp.read()

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        full_text = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            full_text.append(page_text)

        joined_text = "\n".join(full_text)

        # Oczyszczenie tekstu
        clean_text = re.sub(r'[ \t]+', ' ', joined_text)

        # Wyszukanie sekcji Uzasadnienie
        # Wzorzec: UZASADNIENIE do końca dokumentu lub do podpisów
        match = re.search(r'UZASADNIENIE\s*[:\.]?\s*(.*?)(?:Druk\s+nr|Prezydent\s+Miasta\s+Krakowa|Przewodniczący\s+Rady|$)', clean_text, re.DOTALL | re.IGNORECASE)
        
        if match:
            justification = match.group(1).strip()
            # Usunięcie zbędnych znaków nowej linii wewnątrz zdań
            justification = re.sub(r'(?<!\n)\n(?!\n)', ' ', justification)
            justification = re.sub(r'\s+', ' ', justification).strip()
            return justification
        else:
            # Fallback: jeśli nie znaleziono nagłówka UZASADNIENIE, zwróć pierwsze 600 znaków
            return clean_text[:600].strip()

    except Exception as e:
        print(f"[!] Błąd przetwarzania PDF ({pdf_url}): {e}", file=sys.stderr)
        return None


def process_uchwaly_file(input_file="data/uchwaly_bip.json", output_file="data/uchwaly_bip_enriched.json"):
    """Przetwarza plik ze zeskrapowanymi uchwałami i dodaje wyciągnięte uzasadnienia."""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            resolutions = json.load(f)
    except Exception as e:
        print(f"[!] Błąd otwierania pliku {input_file}: {e}")
        return

    print(f"[+] Wczytano {len(resolutions)} uchwał. Rozpoczynanie ekstrakcji PDF...")

    for i, res in enumerate(resolutions, 1):
        pdf_url = res.get("pdf_url")
        if pdf_url:
            print(f"[{i}/{len(resolutions)}] Przetwarzanie uchwały: {res.get('number')}")
            justification = extract_justification_from_pdf(pdf_url)
            if justification:
                res["official_justification"] = justification
                print(f"    -> Sukces! Długość uzasadnienia: {len(justification)} znaków.")
            else:
                res["official_justification"] = None
        else:
            res["official_justification"] = None

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(resolutions, f, ensure_ascii=False, indent=2)

    print(f"\n[SUKCES] Zapisano wzbogacony plik: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Ekstraktor uzasadnień z PDF uchwał BIP Kraków")
    parser.add_argument("--input", default="data/uchwaly_bip.json", help="Plik wejściowy JSON")
    parser.add_argument("--output", default="data/uchwaly_bip_enriched.json", help="Plik wyjściowy JSON")
    parser.add_argument("--url", help="Bezpośredni link do testowego pliku PDF")

    args = parser.parse_args()

    if args.url:
        res = extract_justification_from_pdf(args.url)
        print("\n--- WYCIĄG Z UZASADNIENIA ---")
        print(res)
    else:
        process_uchwaly_file(args.input, args.output)


if __name__ == "__main__":
    main()
