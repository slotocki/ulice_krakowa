import json
import os
import difflib

def get_name(fn):
    if isinstance(fn, dict):
        return fn.get('pl', '')
    return str(fn) if fn else ''

def norm(s):
    if not s:
        return ''
    s = s.lower().replace('ulica ', '').replace('plac ', '').replace('aleja ', '').replace('osiedle ', '')
    s = s.replace('św.', 'świętego').replace('gen.', 'generała').replace('im.', '')
    s = s.replace('"', '').replace("'", '').replace('–', '-').replace('—', '-')
    return ''.join(c for c in s if c.isalnum())

act_files = {
    'drk_1880': 'drk_1880.json',
    'drk_1912': 'drk_1912.json',
    'podgorze_1917': 'podgorze_1917.json',
    'drk_1926_1933': 'drk_1926_1933.json',
    'okupacja_1940_1941': 'okupacja_1940_1941.json',
    'prl_1951_1955': 'prl_1951_1955.json',
    'rozszerzenie_1973_1975': 'rozszerzenie_1973_1975.json',
    'dekomunizacja_1991': 'dekomunizacja_1991.json',
}

geojson = json.load(open('data/krakow_streets.geojson', encoding='utf-8'))
valid_gids = {f['properties']['id']: get_name(f['properties'].get('full_name')) for f in geojson['features']}

for doc_id, fname in act_files.items():
    fpath = os.path.join('data', 'sources', fname)
    if not os.path.exists(fpath):
        continue
    data = json.load(open(fpath, encoding='utf-8'))
    streets = data.get('streets', [])
    mismatches = []
    for s in streets:
        gid = s.get('geojson_id')
        sid = s.get('id')
        name_in_act = (s.get('current_full_name') or 
                       s.get('official_name_1991') or 
                       s.get('official_name_1951') or 
                       s.get('official_name_1917') or 
                       s.get('official_name_1973') or 
                       s.get('official_name_1926') or 
                       s.get('official_name_1912') or 
                       s.get('official_name_1880') or 
                       s.get('official_name') or '')
        if not gid:
            continue
        if gid not in valid_gids:
            mismatches.append((sid, name_in_act, gid, "NOT_FOUND_IN_GEOJSON", 0))
            continue
        gname = valid_gids[gid]
        n1 = norm(name_in_act)
        n2 = norm(gname)
        if n1 != n2 and n1 not in n2 and n2 not in n1:
            ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
            if ratio < 0.6:
                mismatches.append((sid, name_in_act, gid, gname, round(ratio, 2)))
    print(f"=== {doc_id} (total {len(streets)} streets) ===")
    if mismatches:
        print(f"  Found {len(mismatches)} potential mismatches:")
        for m in mismatches:
            print(f"    {m[0]}: act says '{m[1]}' -> linked to '{m[2]}' ('{m[3]}') [sim={m[4]}]")
    else:
        print("  0 mismatches found.")
