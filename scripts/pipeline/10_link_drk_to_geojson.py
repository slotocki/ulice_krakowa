# -*- coding: utf-8 -*-
"""
Linker DRK 1912 do krakow_streets.geojson.
Wzbogaca pasujące obiekty w GeoJSON o metadane uchwały z 1912 roku:
dawny przebieg/nazwę, dzielnicę oraz referencję do strony i czytnika.
"""

import json
import os
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEOJSON_PATH = os.path.join(BASE_DIR, "data", "krakow_streets.geojson")
DRK_PATH = os.path.join(BASE_DIR, "data", "sources", "drk_1912.json")

def link_drk_to_geojson():
    print(f"Loading DRK dataset from {DRK_PATH}...")
    with open(DRK_PATH, "r", encoding="utf-8") as f:
        drk_data = json.load(f)

    # Build map by geojson_id
    drk_by_gid = {}
    for item in drk_data["streets"]:
        gid = item.get("geojson_id")
        if gid:
            drk_by_gid[gid] = item

    print(f"Loaded {len(drk_by_gid)} matched DRK entries.")

    print(f"Loading GeoJSON from {GEOJSON_PATH}...")
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson = json.load(f)

    updated_count = 0
    for feat in geojson["features"]:
        props = feat["properties"]
        gid = props.get("id")
        
        if gid in drk_by_gid:
            drk_item = drk_by_gid[gid]
            props["drk_1912"] = {
                "district_id": drk_item["district_id"],
                "district_name": drk_item["district_name"],
                "former_description": drk_item["former_description"],
                "official_name": drk_item["official_name_1912"],
                "page": drk_item["page_printed"],
                "ref_id": drk_item["id"],
                "council_debate": drk_item.get("council_debate")
            }
            
            # Wzbogać listę źródeł, jeśli istnieje
            sources = props.get("source", [])
            if isinstance(sources, list):
                if not any("1912" in str(s) for s in sources):
                    sources.append("Dziennik Rozporządzeń dla Stoł. Król. Miasta Krakowa z 1912 r.")
                    props["source"] = sources
            elif isinstance(sources, str):
                if "1912" not in sources:
                    props["source"] = [sources, "Dziennik Rozporządzeń dla Stoł. Król. Miasta Krakowa z 1912 r."]

            updated_count += 1
        else:
            # Jeżeli ulica nie ma wpisu DRK, usuń ewentualne stare pozostałości
            if "drk_1912" in props:
                del props["drk_1912"]

    print(f"Updated {updated_count} street features with DRK 1912 reference.")

    with open(GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(geojson, f, ensure_ascii=False, separators=(',', ':'))

    sz = os.path.getsize(GEOJSON_PATH)
    print(f"GeoJSON saved successfully ({round(sz/(1024*1024), 2)} MB).")

if __name__ == "__main__":
    link_drk_to_geojson()
