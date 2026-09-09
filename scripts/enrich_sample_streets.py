#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do pobierania oficjalnych, dokładnych geometrii z OpenStreetMap (Overpass API)
oraz portretów/biogramów z polskiej Wikipedii dla przykładowych ulic w Krakowie.
Dzięki temu ulice idealnie pokrywają się z podkładem mapy (bez żadnych przesunięć).
"""

import sys
import json
import time
import urllib.request
import urllib.parse

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
WIKI_API_URL = "https://pl.wikipedia.org/api/rest_v1/page/summary/"

# Mapowanie patronów do haseł w Wikipedii
WIKI_PATRONS = {
    "lema": "Stanisław_Lem",
    "szymborskiej": "Wisława_Szymborska",
    "florianska": "Florian_(męczennik)",
    "grodzka": "Grodzka_(Kraków)",
    "dietla": "Józef_Dietl",
    "szeroka": "Ulica_Szeroka_w_Krakowie",
    "slowackiego": "Juliusz_Słowacki",
    "mogilska": "Mogiła_(Kraków)"
}

HEADERS = {
    "User-Agent": "KrakowStreetsEnricher/1.0 (+https://bip.krakow.pl)"
}

def fetch_osm_geometry(street_name):
    """Pobiera precyzyjną geometrię z OpenStreetMap przez Overpass API."""
    print(f"[*] Overpass OSM: pobieranie geometrii dla '{street_name}'...")
    query = f"""
    [out:json][timeout:30];
    area["name"="Kraków"]["admin_level"="8"]->.krakow;
    (
      way["highway"]["name"="{street_name}"](area.krakow);
    );
    out body geom;
    """
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(OVERPASS_URL, data=data, headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            content = json.loads(resp.read().decode("utf-8"))

        elements = [el for el in content.get("elements", []) if el.get("type") == "way" and "geometry" in el]
        if not elements:
            print(f"    [!] Brak geometrii OSM dla: {street_name}")
            return None

        lines = []
        for el in elements:
            pts = [[pt["lon"], pt["lat"]] for pt in el["geometry"]]
            if len(pts) >= 2:
                lines.append(pts)

        if not lines:
            return None

        if len(lines) == 1:
            return {
                "type": "LineString",
                "coordinates": lines[0]
            }
        else:
            return {
                "type": "MultiLineString",
                "coordinates": lines
            }

    except Exception as e:
        print(f"    [!] Błąd Overpass: {e}")
        return None


def fetch_wikipedia_info(wiki_title):
    """Pobiera opis i zdjęcie patrona z Wikipedii."""
    if not wiki_title:
        return None

    print(f"[*] Wikipedia API: pobieranie danych dla '{wiki_title}'...")
    url = WIKI_API_URL + urllib.parse.quote(wiki_title)
    req = urllib.request.Request(url, headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        return {
            "title": data.get("title"),
            "description": data.get("description"),
            "thumbnail_url": data.get("thumbnail", {}).get("source"),
            "wikipedia_url": data.get("content_urls", {}).get("desktop", {}).get("page")
        }
    except Exception as e:
        print(f"    [!] Błąd Wikipedia: {e}")
        return None


def main():
    sample_file = "data/streets_sample.json"
    print(f"[+] Otwieranie {sample_file}...")
    with open(sample_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for feature in data.get("features", []):
        sid = feature["properties"]["id"]
        sname = feature["properties"]["name"]

        # 1. Pobranie precyzyjnej geometrii OSM
        exact_geom = fetch_osm_geometry(sname)
        if exact_geom:
            feature["geometry"] = exact_geom
            print(f"    -> Zaktualizowano geometrię OSM ({exact_geom['type']}).")

        # 2. Pobranie portretu i danych z Wikipedii
        wiki_key = WIKI_PATRONS.get(sid)
        if wiki_key:
            wiki_info = fetch_wikipedia_info(wiki_key)
            if wiki_info:
                feature["properties"]["patron_image"] = wiki_info.get("thumbnail_url")
                feature["properties"]["wikipedia_url"] = wiki_info.get("wikipedia_url")
                feature["properties"]["patron_role"] = wiki_info.get("description")
                print(f"    -> Dodano portret patrona z Wikimedia Commons.")

        time.sleep(1.0) # Throttling

    with open(sample_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n[SUKCES] Zaktualizowano plik {sample_file} o precyzyjne geometrie OSM i portrety patronów!")


if __name__ == "__main__":
    main()
