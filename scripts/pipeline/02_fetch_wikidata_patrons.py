# -*- coding: utf-8 -*-
import json
import os
import time
import urllib.request
import urllib.parse

CLASSIFIED_FILE = 'data/streets_classified.json'
CACHE_FILE = 'data/cache_patrons.json'
USER_AGENT = 'KrakowStreetsBot/1.0 (https://github.com/ulice_krakowa; contact@krakowstreets.pl)'
BATCH_SIZE = 25

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def query_wikidata_batch(names_batch):
    safe_labels = []
    for n in names_batch:
        escaped = n.replace('"', '').replace('\\', '')
        safe_labels.append(f'\"{escaped}\"@pl')
    
    values_str = ' '.join(safe_labels)
    
    query = f'''
SELECT ?person ?label ?birth ?death ?image ?desc_pl ?desc_en ?desc_de ?article_pl WHERE {{
  VALUES ?label {{ {values_str} }}
  ?person rdfs:label ?label;
          wdt:P31 wd:Q5.
  OPTIONAL {{ ?person wdt:P569 ?birth. }}
  OPTIONAL {{ ?person wdt:P570 ?death. }}
  OPTIONAL {{ ?person wdt:P18 ?image. }}
  OPTIONAL {{ ?person schema:description ?desc_pl. FILTER(LANG(?desc_pl) = "pl") }}
  OPTIONAL {{ ?person schema:description ?desc_en. FILTER(LANG(?desc_en) = "en") }}
  OPTIONAL {{ ?person schema:description ?desc_de. FILTER(LANG(?desc_de) = "de") }}
  OPTIONAL {{
    ?article_pl schema:about ?person;
                schema:isPartOf <https://pl.wikipedia.org/>.
  }}
}}
'''
    url = 'https://query.wikidata.org/sparql?query=' + urllib.parse.quote(query) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            results = {}
            for b in data.get('results', {}).get('bindings', []):
                lbl = b.get('label', {}).get('value')
                if not lbl or lbl in results:
                    continue
                
                birth = b.get('birth', {}).get('value', '')
                death = b.get('death', {}).get('value', '')
                b_year = birth[:4] if birth else ''
                d_year = death[:4] if death else ''

                img_raw = b.get('image', {}).get('value', '')
                img_thumb = ''
                if img_raw:
                    clean_img = img_raw.replace('http://', 'https://')
                    img_thumb = f'{clean_img}?width=360'

                article_url = b.get('article_pl', {}).get('value', '')
                if not article_url:
                    wiki_slug = urllib.parse.quote(lbl.replace(' ', '_'))
                    article_url = f'https://pl.wikipedia.org/wiki/{wiki_slug}'

                results[lbl] = {
                    'found': True,
                    'qid': b.get('person', {}).get('value', ''),
                    'name': lbl,
                    'birth_year': b_year,
                    'death_year': d_year,
                    'image': img_thumb,
                    'role': {
                        'pl': b.get('desc_pl', {}).get('value', ''),
                        'en': b.get('desc_en', {}).get('value', ''),
                        'de': b.get('desc_de', {}).get('value', '')
                    },
                    'wiki_url': article_url
                }
            return results
    except Exception as e:
        print(f'Blad zapytania SPARQL: {e}')
        return {}

def main():
    if not os.path.exists(CLASSIFIED_FILE):
        print(f'Brak pliku {CLASSIFIED_FILE}!')
        return

    with open(CLASSIFIED_FILE, 'r', encoding='utf-8') as f:
        classified = json.load(f)

    person_streets = [it for it in classified if it.get('category') == 'person']
    unique_names = sorted(list(set(it['nominative'] for it in person_streets)))
    print(f'Liczba unikalnych postaci do sprawdzenia w Wikidata: {len(unique_names)}')

    cache = load_cache()
    print(f'Liczba patronow juz w cache: {len(cache)}')

    to_query = [name for name in unique_names if name not in cache]
    print(f'Pozostalo do odpytania: {len(to_query)}')

    for i in range(0, len(to_query), BATCH_SIZE):
        batch = to_query[i:i + BATCH_SIZE]
        print(f'Odpytywanie {i + 1}-{min(i + BATCH_SIZE, len(to_query))} / {len(to_query)}...')
        
        batch_results = query_wikidata_batch(batch)
        
        for name in batch:
            if name in batch_results:
                cache[name] = batch_results[name]
            else:
                slug = urllib.parse.quote(name.replace(' ', '_'))
                cache[name] = {
                    'found': False,
                    'name': name,
                    'role': {'pl': '', 'en': '', 'de': ''},
                    'image': '',
                    'wiki_url': f'https://pl.wikipedia.org/wiki/{slug}'
                }
        
        save_cache(cache)
        time.sleep(0.35)

    print('\n=== WYNIKI ZASILANIA Z WIKIDATA ===')
    total_found = sum(1 for v in cache.values() if v.get('found'))
    with_images = sum(1 for v in cache.values() if v.get('image'))
    print(f'Znaleziono w Wikidata: {total_found} / {len(unique_names)} patronow ({total_found/len(unique_names)*100:.1f}%)')
    print(f'Posiada oficjalny portret z Wikimedia Commons: {with_images} postaci')
    print(f'Zapisano cache do {CACHE_FILE}.')

if __name__ == '__main__':
    main()
