# Specyfikacja Techniczna i Plan Wykonawczy: Zasilenie Bazy 2 763 Ulic Krakowa
**Dokumentacja i Instrukcja Realizacji dla Agenta Kodujacego / Inzyniera Danych**

---

## 1. Cel i Zakres Projektu

Celem jest doprowadzenie bazy danych data/krakow_streets.geojson (2 763 ulice w granicach administracyjnych Krakowa) do 100% kompletnosci i rzetelnosci historycznej.

Projekt realizowany jest w oparciu o 4 filary:
1. Zero naruszen praw autorskich i zero puchniecia repozytorium: Zadne pliki JPEG/PNG nie sa pobierane na dysk; uzywamy wylacznie oficjalnego globalnego CDN Wikimedia Commons z parametrem szerokosci (?width=360).
2. Zero halucynacji: Ulice nieosobowe (Kwiatowa, Szewska, Wielicka) maja bezwzglednie patron: null.
3. Trójjezycznosc (i18n): Kazdy rekord posiada zlokalizowane klucze pl, en, de dla nazw, ról, etymologii i kategorii.
4. Weryfikowalnosc urzedowa: Tam, gdzie ulica powstala po 1990 r., podpinamy Druk RMK z oficjalnym uzasadnieniem merytorycznym i uchwale z BIP Kraków.

---

## 2. Stan Obecny (Co zostalo juz zrobione)

* Baza geometrii: 2 763 ulice dociente geometrycznie do oficjalnego wielokata granic Krakowa.
* Klasyfikator: Podzial w data/streets_classified.json (919 osób, 421 traktów, 107 obiektów przyrody, 46 rzemiosl, 27 dat, 1 243 toponimy ogólne).
* Zasilenie Wikidata (v1): 423 dopasowanych patronów, 307 portretów CDN w data/cache_patrons.json.
* Zasilenie etymologii (v1): 1 848 ulic nieosobowych w data/cache_etymologies.json.
* Frontend: Dzialajacy portal MapLibre GL JS, przelacznik PL/EN/DE, responsywny drawer, warstwa granic Krakowa.

---

## 3. Zadania do Wykonania przez Agenta Kodujacego (Krok po Kroku)

### ZADANIE 1: Domkniecie Bazy Patronów Osobowych (~490 brakujacych postaci)
* Skrypt: scripts/pipeline/02b_resolve_missing_patrons.py
* Algorytm:
  1. Dla kazdego nieznalezionego patrona wyslij zapytanie do Wikipedia Search API (pl.wikipedia.org).
  2. Jesli artykul istnieje, pobierz powiazany identyfikator Wikidata QID.
  3. Pobierz z Wikidata: birth_date, death_date, description (pl, en, de) oraz obraz wdt:P18 (?width=360).
  4. Zapisz do data/cache_patrons.json.

### ZADANIE 2: Ekstrakcja Monografii prof. Elzbiety Supranowicz (RCIN PAN)
* Skrypt: scripts/pipeline/03b_parse_supranowicz_rcin.py
* Zródlo: Nazwy ulic Krakowa, prof. Elzbieta Supranowicz, IJP PAN Kraków 1995 (RCIN publikacja 43027, wydanie 24551).
* Algorytm:
  1. Ominiecie zabezpieczenia PoW w RCIN (obliczenie nonce MD5 z prefiksem 00000).
  2. Pobranie i ekstrakcja leksykonu hasel: haslo, rok pierwszego poswiadczenia, nazwy dawne, etymologia.
  3. Zapis do data/cache_supranowicz.json.

### ZADANIE 3: Pelny Scraper Uchwal i Druków BIP RMK (1990-2026)
* Skrypt: scripts/pipeline/04_scrape_bip_full.py (na bazie scripts/scrape_bip_krakow.py).
* Zródlo: Biuletyn Informacji Publicznej Miasta Krakowa (rejestr uchwal RMK, dok_id=166).
* Algorytm:
  1. Przeszukanie 9 kadencji Rady Miasta Krakowa dla spraw: nadanie nazwy ulicy/alei/placu/skweru/ronda/parku.
  2. Wyciagniecie: numer uchwaly, data, link do PDF uchwaly, numer Druku RMK, link do oficjalnego uzasadnienia PDF.
  3. Zapis do data/cache_bip_full.json.

### ZADANIE 4: Pipeline Tlumaczen i Doslownych Znaczen (i18n)
* Skrypt: scripts/pipeline/03_generate_etymologies.py
* Rozszerzenie slownika doslownych znaczen (literal_meaning) dla turystów zagranicznych w EN i DE.

### ZADANIE 5: Fuzja Danych i Walidacja Jakosci (QA Master)
* Skrypt fuzji: scripts/pipeline/05_merge_all_data.py
* Skrypt testowy: scripts/pipeline/06_validate_dataset.py
* Asercje QA:
  - Dokladnie 2 763 ulice w GeoJSON.
  - Zero linii wystajacych poza granice Krakowa.
  - Ulice nieosobowe maja patron: null.
  - Wszystkie zdjecia to bezpieczne linki HTTPS do CDN Wikimedia Commons (?width=360).
  - Waga bazy: < 6.5 MB.
