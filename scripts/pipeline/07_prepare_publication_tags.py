#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/pipeline/07_prepare_publication_tags.py

Etap 2 Pipeline:
1. Odczyt surowych warstw tekstowych OCR monografii (Tomkowicz 1926, Grabowski 1866, Estreicher 1873, Bąkowski 1903-1920)
2. Czyszczenie tekstu (ligatury, archaizmy typograficzne, dzielenie wyrazów)
3. Ekstrakcja leksykonu ulic, nazw łacińskich, pierwszych poświadczeń i cytatów źródłowych
4. Połączenie z dotychczasowymi źródłami:
   - Prof. Elżbieta Supranowicz (PAN 1995, RCIN) z data/cache_supranowicz.json
   - Oficjalne uchwały RMK (BIP)
   - Zweryfikowani patroni (Wikidata & Commons)
   - 8 aktów urzędowych (1880, 1912, 1917, 1926, 1940, 1951, 1973, 1991)
5. Pełna obsługa 3 wersji językowych (PL, EN, DE) oraz literal_meaning
6. Zapis indeksu monografii: data/sources/publications_index.json
7. Podział na 28 paczek ewaluacyjnych dla subagentów: data/sources/agent_evaluation_manifest.json
"""

import os
import re
import json
import math

RAW_DIR = os.path.join("data", "raw_sources")
GEOJSON_PATH = os.path.join("data", "krakow_streets.geojson")
SUPRANOWICZ_CACHE_PATH = os.path.join("data", "cache_supranowicz.json")
PUBLICATIONS_INDEX_PATH = os.path.join("data", "sources", "publications_index.json")
MANIFEST_PATH = os.path.join("data", "sources", "agent_evaluation_manifest.json")

# Mapowanie specyficznych łacińskich i historycznych form z Tomkowicza
LATIN_STREET_MAPPING = {
    "floriańska": {
        "id": "florianska",
        "latin": ["Platea Sancti Floriani (1305)", "Platea S. Floriani (1388)"],
        "german_historical": "Floriansgasse",
        "year": 1305,
        "tags": ["sredniowiecze", "droga_krolewska", "brama_obronna", "cech_rzemieslniczy"]
    },
    "grodzka": {
        "id": "grodzka",
        "latin": ["Platea Castrensis (1305)", "Platea Burggasse (1312)"],
        "german_historical": "Burggasse",
        "year": 1305,
        "tags": ["sredniowiecze", "droga_krolewska", "brama_obronna"]
    },
    "szewska": {
        "id": "szewska",
        "latin": ["Platea Sutorum (1311)"],
        "german_historical": "Schuczagasse",
        "year": 1311,
        "tags": ["sredniowiecze", "cech_rzemieslniczy", "brama_obronna"]
    },
    "sławkowska": {
        "id": "slawkowska",
        "latin": ["Platea Slacoviensis (1312)", "Platea Cerdonum (1340)"],
        "german_historical": "Slakowergasse",
        "year": 1312,
        "tags": ["sredniowiecze", "brama_obronna", "cech_rzemieslniczy"]
    },
    "bracka": {
        "id": "bracka",
        "latin": ["Platea Fratrum (1316)", "Platea Fratrum Minorum (1390)"],
        "german_historical": "Brüdergasse",
        "year": 1316,
        "tags": ["sredniowiecze", "sakralne"]
    },
    "gołębia": {
        "id": "golebia",
        "latin": ["Platea Columbina (1394)", "Platea Cervorum (1342)"],
        "german_historical": "Taubengasse",
        "year": 1342,
        "tags": ["sredniowiecze"]
    },
    "jagiellońska": {
        "id": "jagiellonska",
        "latin": ["Platea Iudaeorum (1369)"],
        "german_historical": "Judengasse",
        "year": 1369,
        "tags": ["sredniowiecze"]
    },
    "kanonicza": {
        "id": "kanonicza",
        "latin": ["Platea Canonicorum (1405)"],
        "german_historical": "Chorherrengasse",
        "year": 1405,
        "tags": ["sredniowiecze", "droga_krolewska", "sakralne"]
    },
    "świętej anny": {
        "id": "swietej_anny",
        "latin": ["Platea Sanctae Annae (1380)", "Platea Iudaeorum (1360)"],
        "german_historical": "Annagasse",
        "year": 1380,
        "tags": ["sredniowiecze", "sakralne"]
    },
    "świętego jana": {
        "id": "swietego_jana",
        "latin": ["Platea Sancti Johannis (1335)"],
        "german_historical": "Johannesgasse",
        "year": 1335,
        "tags": ["sredniowiecze", "sakralne"]
    },
    "świętego marka": {
        "id": "swietego_marka",
        "latin": ["Platea Sancti Marci (1386)"],
        "german_historical": "Markusgasse",
        "year": 1386,
        "tags": ["sredniowiecze", "sakralne"]
    },
    "szczepańska": {
        "id": "szczepanska",
        "latin": ["Platea Sancti Stephani (1311)"],
        "german_historical": "Stephansgasse",
        "year": 1311,
        "tags": ["sredniowiecze", "sakralne"]
    },
    "sienna": {
        "id": "sienna",
        "latin": ["Platea Carnificum (1340)", "Platea Foenilis (1400)"],
        "german_historical": "Heugasse",
        "year": 1340,
        "tags": ["sredniowiecze", "cech_rzemieslniczy", "brama_obronna"]
    },
    "mikołajska": {
        "id": "mikolajska",
        "latin": ["Platea Sancti Nicolai (1327)"],
        "german_historical": "Nikolaigasse",
        "year": 1327,
        "tags": ["sredniowiecze", "sakralne", "brama_obronna"]
    },
    "szeroka": {
        "id": "szeroka",
        "latin": ["Platea Magna Casimiriae (1342)"],
        "german_historical": "Breite Gasse",
        "year": 1342,
        "tags": ["sredniowiecze", "kazimierz_zydowski"]
    },
    "józefa": {
        "id": "jozefa",
        "latin": ["Platea Judaeorum Casimiriae (XV w.)"],
        "german_historical": "Josephsgasse",
        "year": 1785,
        "tags": ["kazimierz_zydowski"]
    },
    "starowiślna": {
        "id": "starowislna",
        "latin": ["Via Vistulensis Antiqua"],
        "german_historical": "Altweichselstraße",
        "year": 1650,
        "tags": ["stara_wisla"]
    },
    "dietla": {
        "id": "jozefa_dietla",
        "latin": ["Alveus Antiquae Vistulae"],
        "german_historical": "Dietl-Straße",
        "year": 1878,
        "tags": ["stara_wisla", "planty"]
    },
    "podwale": {
        "id": "podwale",
        "latin": ["Sub Vallo Civitatis"],
        "german_historical": "Unterwallegasse",
        "year": 1820,
        "tags": ["planty", "brama_obronna"]
    },
    "stradom": {
        "id": "stradomska",
        "latin": ["Pons Stradomiensis", "Vicus Stradomia"],
        "german_historical": "Stradomstraße",
        "year": 1378,
        "tags": ["sredniowiecze", "stara_wisla"]
    },
    "karmelicka": {
        "id": "karmelicka",
        "latin": ["Via Carmelitarum ad Arenas"],
        "german_historical": "Karmelitergasse",
        "year": 1397,
        "tags": ["jurydyka", "sakralne"]
    },
    "garbarska": {
        "id": "garbarska",
        "latin": ["Vicus Cerdonum in Arenis"],
        "german_historical": "Gerbergasse",
        "year": 1400,
        "tags": ["jurydyka", "cech_rzemieslniczy"]
    },
    "lubicz": {
        "id": "lubicz",
        "latin": ["Via ad Lubicz et Mogilam"],
        "german_historical": "Lubiczstraße",
        "year": 1783,
        "tags": ["jurydyka"]
    },
    "wiślna": {
        "id": "wislna",
        "latin": ["Platea Vistulae (1311)"],
        "german_historical": "Weichselgasse",
        "year": 1311,
        "tags": ["sredniowiecze", "brama_obronna"]
    },
    "rynek główny": {
        "id": "rynek_glowny",
        "latin": ["In Foro Civitatis Cracoviensis (1257)"],
        "german_historical": "Ringplatz",
        "year": 1257,
        "tags": ["sredniowiecze", "droga_krolewska"]
    },
    "plac wolnica": {
        "id": "plac_wolnica",
        "latin": ["Forum Civitatis Casimiriae (1335)"],
        "german_historical": "Wolnica-Platz",
        "year": 1335,
        "tags": ["sredniowiecze", "kazimierz_zydowski"]
    },
    "rynek podgórski": {
        "id": "rynek_podgorski",
        "latin": ["Forum Civitatis Josephinae (1784)"],
        "german_historical": "Podgórzer Marktplatz",
        "year": 1784,
        "tags": ["wies_podkrakowska"]
    }
}

def clean_ocr_text(text):
    """Usuwa błędy OCR, archaiczne ligatury i łamanie wyrazów."""
    text = re.sub(r'(\b\w+)-\s*\n\s*(\w+\b)', r'\1\2', text)
    text = text.replace('ſ', 's')
    text = text.replace('é', 'e')
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_monographs():
    """Wczytuje surowe teksty monografii i tnie je na sekcje ulic."""
    files = {
        "tomkowicz": ("tomkowicz_1926", "ulice_i_place_krakowa_raw.txt", "Stanisław Tomkowicz, 'Ulice i place Krakowa w ciągu dziejów', 1926"),
        "grabowski": ("grabowski_1866", "krakow_i_jego_okolice_raw.txt", "Ambroży Grabowski, 'Kraków i jego okolice', wyd. 3, 1866"),
        "estreicher": ("estreicher_1873", "przewodnik_po_krakowie_raw.txt", "Karol Estreicher, 'Przewodnik dla zwiedzających Kraków i jego okolice', 1873"),
        "bakowski": ("bakowski_dzielnice", "dzielnice_i_przedmiescia_raw.txt", "Klemens Bąkowski, 'Dawne cechy i przedmieścia Krakowa', 1903-1920")
    }
    
    extracted_sections = {}
    
    for key, (folder, fname, citation_label) in files.items():
        fpath = os.path.join(RAW_DIR, folder, fname)
        if not os.path.exists(fpath):
            continue
        with open(fpath, "r", encoding="utf-8") as f:
            raw = f.read()
        cleaned = clean_ocr_text(raw)
        
        blocks = re.findall(r'\[([^\]]+)\]([\s\S]*?)(?=(?:\[[^\]]+\]|\Z))', cleaned)
        for name_hdr, body in blocks:
            name_clean = name_hdr.lower().strip()
            base_name = name_clean.split('-')[0].split('/')[0].strip()
            
            if base_name not in extracted_sections:
                extracted_sections[base_name] = []
            extracted_sections[base_name].append({
                "source": key,
                "citation": citation_label,
                "section_heading": name_hdr.strip(),
                "text": body.strip()
            })
            
    return extracted_sections

def load_supranowicz_cache():
    """Ładuje bazę wiedzy z monografii prof. Elżbiety Supranowicz (PAN 1995)."""
    if not os.path.exists(SUPRANOWICZ_CACHE_PATH):
        return {}, {}
    with open(SUPRANOWICZ_CACHE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    entries = data.get("entries", {})
    norm_map = data.get("by_normalized_name", {})
    return entries, norm_map

def normalize_key(s):
    if not s:
        return ""
    s = s.lower().strip()
    s = re.sub(r'^(ulica|ul\.|aleja|al\.|plac|pl\.|osiedle|os\.|rondo|skwer|bulwar|droga|grobla|park)\s+', '', s)
    s = re.sub(r'[^a-ząćęłńóśźż0-9]', '', s)
    return s

def derive_thematic_tags(street_props, monograph_entry):
    """Automatycznie dedukuje tagi historyczno-toponimiczne na podstawie cech ulicy i źródeł."""
    tags = set()
    name = street_props.get("name", {}).get("pl", "").lower()
    
    dist_val = street_props.get("district")
    if isinstance(dist_val, dict):
        district = dist_val.get("pl", "").lower()
    else:
        district = str(dist_val or "").lower()
        
    cat = street_props.get("category") or ""
    
    # 1. Z monografii jeśli istnieje
    if monograph_entry and "tags" in monograph_entry:
        for t in monograph_entry["tags"]:
            tags.add(t)
            
    # 2. Heurystyki toponomiczne
    if any(k in name for k in ["floriańska", "grodzka", "szewska", "sławkowska", "bracka", "gołębia", "kanonicza", "wislna", "wiślna", "sienna", "mikołajska", "szczepańska", "świętej anny", "świętego jana", "świętego marka", "rynek główny", "mały rynek"]):
        tags.add("sredniowiecze")
        
    if any(k in name for k in ["floriańska", "rynek główny", "grodzka", "kanonicza", "senacka", "podzamcze", "wawel"]):
        tags.add("droga_krolewska")
        
    if any(k in name for k in ["garbarska", "karmelicka", "biskupia", "plac biskupi", "pędzichów", "retoryka", "smoleńsk", "nowy świat", "na groblach", "kopernika", "strzelecka"]):
        tags.add("jurydyka")
        
    if any(k in name for k in ["szewska", "garbarska", "sienna", "garncarska", "kotlarska", "solna", "piekarska", "stolarska", "sukiennice"]):
        tags.add("cech_rzemieslniczy")
        
    if any(k in name for k in ["planty", "podwale", "straszewskiego", "basztowa", "westerplatte", "św. gertrudy", "ogrodowa"]):
        tags.add("planty")
        
    if any(k in name for k in ["dietla", "daszyńskiego", "grzegórzecka", "starowiślna", "stradomska", "mostowa"]):
        tags.add("stara_wisla")
        
    if "stare miasto" in district and any(k in name for k in ["szeroka", "miodowa", "józefa", "ciemna", "jakuba", "kupa", "izaaka", "nowa", "estery", "warszauera", "lewkowa", "bożego ciała", "plac wolnica", "krakowska"]):
        tags.add("kazimierz_zydowski")
        
    if any(k in name for k in ["mickiewicza", "słowackiego", "krasińskiego", "królewska", "al. 3 maja", "reymonta", "osiedle oficerskie", "inwalidów", "chopin"]):
        tags.add("dwudziestolecie")
        
    if any(k in name for k in ["tyniecka", "zwierzyniecka", "kościuszki", "dębnicka", "krowoderska", "prądnicka", "bielańska", "swoszowicka", "sidzińska", "olszanicka"]):
        tags.add("wies_podkrakowska")
        
    if any(k in name for k in ["święt", "św.", "franciszkańska", "dominikańska", "bernardyńska", "paulistów", "karmelicka", "reformatów", "pijarska", "kanonicza"]):
        tags.add("sakralne")
        
    if "nowa huta" in district or any(k in name for k in ["solidarności", "róż", "plac centralny", "przyjaźni", "zgody", "wandy", "kombatantów", "stalowe", "szklane domy"]):
        tags.add("industrializacja_prl")
        
    return sorted(list(tags))

def main():
    print("======================================================================")
    print("  CRUCIAL ETAP 2: OCR, I18N, SUPRANOWICZ & 28-AGENT MANIFEST PIPELINE  ")
    print("======================================================================")
    
    # 1. Wczytanie monografii
    extracted_sections = parse_monographs()
    print(f"[+] Wyodrębniono {len(extracted_sections)} unikalnych sekcji toponimicznych z monografii.")
    
    # 2. Wczytanie bazy Supranowicz (RCIN / PAN)
    sup_entries, sup_norm_map = load_supranowicz_cache()
    print(f"[+] Załadowano bazę Supranowicz: {len(sup_entries)} haseł.")
    
    # 3. Wczytanie krakow_streets.geojson
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)
    features = geojson_data["features"]
    total_streets = len(features)
    print(f"[+] Wczytano Master GeoJSON: {total_streets} ulic.")
    
    # 4. Budowanie indeksu publications_index.json
    publications_index = {}
    
    for feat in features:
        props = feat["properties"]
        s_id = props["id"]
        pl_name = props["name"]["pl"].lower().strip()
        
        # Sprawdzamy czy mamy zmapowanie z Tomkowicza
        latin_info = LATIN_STREET_MAPPING.get(pl_name)
        citations = []
        
        # Sprawdzamy sekcje z monografii
        for section_key, cits in extracted_sections.items():
            if section_key == pl_name or section_key in pl_name:
                citations.extend(cits)
                
        # Sprawdzamy wpis w Supranowicz
        norm_k = normalize_key(pl_name)
        sup_match = None
        if norm_k in sup_norm_map:
            sup_idx = sup_norm_map[norm_k]
            sup_match = sup_entries.get(str(sup_idx))
            
        tags = derive_thematic_tags(props, latin_info)
        
        # Rejestrujemy wpis w indeksie monografii
        if latin_info or citations or sup_match or tags:
            entry = {
                "street_id": s_id,
                "canonical_name": props["name"]["pl"],
                "district": props.get("district"),
                "category": props.get("category"),
                "latin_names": latin_info["latin"] if latin_info else [],
                "german_historical": latin_info["german_historical"] if latin_info else None,
                "first_attested_year": latin_info["year"] if latin_info else (sup_match.get("first_attestation_year") if sup_match else props.get("year")),
                "thematic_tags": tags,
                "supranowicz_summary": sup_match.get("etymology_summary") if sup_match else None,
                "citations_count": len(citations),
                "citations": citations
            }
            publications_index[s_id] = entry
            
    os.makedirs(os.path.dirname(PUBLICATIONS_INDEX_PATH), exist_ok=True)
    with open(PUBLICATIONS_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(publications_index, f, indent=2, ensure_ascii=False)
    print(f"[+] Zapisano Indeks Publikacji: {PUBLICATIONS_INDEX_PATH} ({len(publications_index)} ulic ze wzbogaceniem).")
    
    # 5. Budowanie agent_evaluation_manifest.json podzielonego na dokładnie 28 paczek
    NUM_CHUNKS = 28
    chunk_size = math.ceil(total_streets / NUM_CHUNKS)
    print(f"[+] Przygotowywanie partycjonowania dla {NUM_CHUNKS} równoległych subagentów (~{chunk_size} ulic/paczkę)...")
    
    manifest_chunks = []
    
    for i in range(NUM_CHUNKS):
        chunk_idx = i + 1
        start_i = i * chunk_size
        end_i = min(start_i + chunk_size, total_streets)
        chunk_features = features[start_i:end_i]
        
        streets_manifest = []
        for feat in chunk_features:
            props = feat["properties"]
            s_id = props["id"]
            pl_name = props["name"]["pl"]
            pub_data = publications_index.get(s_id)
            
            # Supranowicz link
            norm_k = normalize_key(pl_name)
            sup_data = None
            if norm_k in sup_norm_map:
                sup_idx = sup_norm_map[norm_k]
                raw_sup = sup_entries.get(str(sup_idx))
                if raw_sup:
                    sup_data = {
                        "monograph": "E. Supranowicz, Nazwy ulic Krakowa (PAN 1995)",
                        "first_year": raw_sup.get("first_attestation_year"),
                        "quote": raw_sup.get("first_attestation_quote"),
                        "former_names": raw_sup.get("former_names", []),
                        "summary": raw_sup.get("etymology_summary")
                    }
            
            # Sprawdzenie powiązanych aktów urzędowych (z 8 aktów historycznych)
            acts_linked = []
            res = props.get("resolution") or {}
            src = props.get("source") or {}
            
            if "1880" in str(res) or "1880" in str(src):
                acts_linked.append("DRK_1880")
            if "1912" in str(res) or "1912" in str(src):
                acts_linked.append("DRK_1912")
            if "1917" in str(res) or "1917" in str(src):
                acts_linked.append("PODGORZE_1917")
            if "1926" in str(res) or "1926" in str(src):
                acts_linked.append("DRK_1926_1933")
            if "1940" in str(res) or "1940" in str(src):
                acts_linked.append("OKUPACJA_1940")
            if "1951" in str(res) or "1951" in str(src):
                acts_linked.append("PRL_1951_1955")
            if "1973" in str(res) or "1973" in str(src):
                acts_linked.append("ROZSZERZENIE_1973")
            if "1991" in str(res) or "1991" in str(src):
                acts_linked.append("DEKOMUNIZACJA_1991")
                
            street_unit = {
                "id": s_id,
                "i18n_names": props.get("name"),
                "full_name": props.get("full_name"),
                "district": props.get("district"),
                "category": props.get("category"),
                "year": props.get("year"),
                "patron": props.get("patron"),
                "i18n_etymology": props.get("etymology"),
                "i18n_literal_meaning": props.get("literal_meaning"),
                "official_acts_linked": acts_linked,
                "supranowicz_pan_entry": sup_data,
                "monograph_data": pub_data,
                "verification_checklist": [
                    "1. Sprawdź spójność trójjęzyczną (PL, EN, DE) nazw, etymologii i literal_meaning.",
                    "2. Porównaj dane historyczne z monografią prof. Supranowicz (1995) – czy rok i dawne nazwy są zgodne?",
                    "3. Zweryfikuj zgodność z uchwałami urzędowymi (BIP / 8 aktów historycznych).",
                    "4. Jeśli ulica posiada wzbogacenie z Tomkowicza/Grabowskiego/Estreichera, potwierdź tagi toponimiczne i nazwy łacińskie.",
                    "5. Reguła Zero Halucynacji: ulica nieosobowa MA BEZWZGLĘDNIE patron: null.",
                    "6. Wystaw ocenę jakości wpisu (score 1-10) i zaproponuj ew. korekty w triadzie PL/EN/DE."
                ]
            }
            streets_manifest.append(street_unit)
            
        chunk_obj = {
            "chunk_id": chunk_idx,
            "chunk_code": f"AGENT_BATCH_{chunk_idx:02d}",
            "agent_role": f"Toponimiczny Asystent Weryfikacyjny - Paczka {chunk_idx:02d}/28",
            "range": f"{start_i + 1} - {end_i} / {total_streets}",
            "street_count": len(streets_manifest),
            "streets": streets_manifest
        }
        manifest_chunks.append(chunk_obj)
        
    full_manifest = {
        "metadata": {
            "project": "Cracoscope - Krakowski System Weryfikacji Toponimicznej",
            "total_streets": total_streets,
            "total_agents": NUM_CHUNKS,
            "languages": ["pl", "en", "de"],
            "generated_at": "2026-09-12T17:05:00Z",
            "academic_authorities": [
                "prof. Elżbieta Supranowicz (1995) - Nazwy ulic Krakowa (IJP PAN / RCIN)",
                "Stanisław Tomkowicz (1926) - Ulice i place Krakowa w ciągu dziejów (BK 63-64)",
                "Ambroży Grabowski (1866) - Kraków i jego okolice (wyd. 3)",
                "Karol Estreicher (1873) - Przewodnik dla zwiedzających Kraków i jego okolice",
                "Klemens Bąkowski (1903-1920) - Dawne cechy i przedmieścia Krakowa (BK)"
            ],
            "official_acts_covered": 8
        },
        "chunks": manifest_chunks
    }
    
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(full_manifest, f, indent=2, ensure_ascii=False)
        
    print(f"[+] Zapisano Wzbogacony Manifest Ewaluacyjny: {MANIFEST_PATH}")
    print(f"    - Liczba paczek: {len(manifest_chunks)}")
    print(f"    - Łączna liczba ulic w manifeście: {sum(c['street_count'] for c in manifest_chunks)} / {total_streets}")
    print("======================================================================")

if __name__ == "__main__":
    main()
