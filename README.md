# 🗺️ Ulice Krakowa – Mapa, Etymologia i Uchwały RMK

Interaktywny portal miejski prezentujący ulice Krakowa na nowoczesnej, wektorowej mapie WebGL, wraz z historią, etymologią nazw oraz bezpośrednimi odnośnikami do aktów prawa miejscowego (uchwał Rady Miasta Krakowa w Biuletynie Informacji Publicznej).

---

## 🚀 Jak uruchomić aplikację WWW (PoC)?

Aplikacja jest w pełni gotowa do uruchomienia i **nie wymaga instalacji ciężkich modułów npm**.

### Opcja 1: Prosty lokalny serwer HTTP (Zalecane ze względu na pobieranie GeoJSON)
W terminalu przejdź do katalogu projektu i uruchom:
```bash
# Uruchomienie wbudowanego serwera Pythona:
python -m http.server 8000
```
Następnie otwórz w przeglądarce adres:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🌟 Główne zalety rozwiązania technicznego

1. **Nowoczesna mapa zamiast „brzydkiego” OpenStreetMap:**
   * Użycie **MapLibre GL JS v4** (silnik WebGL/WebGPU 60fps).
   * Kafelki wektorowe **CARTO Positron** (jasny minimalizm) oraz **CARTO Dark Matter** (tryb nocny).
   * Efekt poświaty (**neon halo glow**) na zaznaczonej ulicy składający się z dwóch niezależnych warstw renderujących (rozmycie `line-blur` + ostra linia główna).
   * Płynna animacja kamery 3D (`fitBounds` z kątem `pitch: 42°` i obrotem `bearing`).

2. **Błyskawiczna wyszukiwarka (0 ms):**
   * Normalizacja polskich znaków diakrytycznych (`ą`, `ę`, `ó`, `ś`, `ł`, `ż`, `ź`, `ć`, `ń`).
   * Wyszukiwanie po nazwisku patrona, pełnej nazwie oraz słowach kluczowych w etymologii.
   * Pełna obsługa klawiatury (strzałki góra/dół, Enter, Escape).

3. **Panel boczny z metryką ulicy:**
   * **Ulice z nowożytną uchwałą RMK (np. ul. Lema, ul. Szymborskiej):** wyświetla numer uchwały, datę, cytat z oficjalnego uzasadnienia i bezpośredni przycisk otwierający dokument w BIP Kraków.
   * **Ulice historyczne (np. ul. Floriańska, ul. Grodzka, ul. Szeroka):** wskazuje metrykę historyczną (XIII–XV w.) i linkuje do opracowania naukowego w Repozytorium Cyfrowym Instytutów Naukowych (RCIN).

---

## 🛠️ Skrypty automatyzacji i Data Engineering

W katalogu `scripts/` znajdują się skrypty do zbierania pełnych danych:

### 1. Pobieranie uchwał z BIP Kraków (`scripts/scrape_bip_krakow.py`)
Przeszukuje Biuletyn Informacji Publicznej Miasta Krakowa, parsuje wyniki, wyodrębnia sygnaturę uchwały, datę, wykrytą nazwę ulicy oraz treść sekcji **UZASADNIENIE**:
```bash
python scripts/scrape_bip_krakow.py --phrase "w sprawie nadania nazwy ulicy" --limit 10 --output data/uchwaly_bip.json
```

### 2. Pobieranie geometrii z OpenStreetMap (`scripts/fetch_osm_krakow.py`)
Odpytuje Overpass API o wszystkie ulice Krakowa i łączy odcinki drogowe w GeoJSON (MultiLineString):
```bash
# Pobranie konkretnej ulicy:
python scripts/fetch_osm_krakow.py --street "Stanisława Lema"

# Pobranie wszystkich dróg w Krakowie (może zająć 1-2 minuty):
python scripts/fetch_osm_krakow.py --output data/krakow_streets.geojson
```

---

## 📚 Źródła danych w projekcie

* **Biuletyn Informacji Publicznej Miasta Krakowa (BIP MK):** uchwały Rady Miasta Krakowa i uzasadnienia patronackie.
* **Główny Urząd Statystyczny (GUS):** Rejestr TERYT / baza ULIC (oficjalne słowniki nazw ulic w gminie 1261011 Kraków).
* **OpenStreetMap & CARTO:** wektorowe linie ulic i estetyczne kafelki kartograficzne.
* **Polska Akademia Nauk (PAN):** Elżbieta Supranowicz, *„Nazwy ulic Krakowa”* (1995) – legalnie dostępna w Repozytorium Cyfrowym Instytutów Naukowych (RCIN).
