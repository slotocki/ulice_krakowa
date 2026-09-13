# -*- coding: utf-8 -*-
"""
scripts/pipeline/02b_resolve_missing_patrons.py

Etap 1: Domknięcie Bazy Patronów Osobowych (~490 postaci).
Algorytm:
1. Dla każdego nieznalezionego patrona generuje inteligentne warianty zapytań (usuwanie tytułów,
   normalizacja mianownikowa dopełniacza, przywracanie 'e', obsługa postaci złożonych).
2. Weryfikuje istnienie artykułu w polskiej Wikipedii:
   - Faza A: Szybki lookup bezpośrednich tytułów i przekierowań (batch do 50).
   - Faza B: Wikipedia Search API (generator=search) ze ścisłą weryfikacją nazwiska i imienia.
3. Pobiera powiązany identyfikator Wikidata QID.
4. Odpytuje Wikidata SPARQL w batchach po QID i weryfikuje instancję postaci (wdt:P31 wd:Q5),
   pobierając:
   - birth_year (wdt:P569), death_year (wdt:P570),
   - role/description w pl, en, de,
   - oficjalny portret CDN Wikimedia Commons (wdt:P18) z ?width=360 i protokołem HTTPS,
   - link do artykułu w pl.wikipedia.org.
5. Zapisuje zaktualizowany cache do data/cache_patrons.json.
"""

import json
import os
import re
import time
import urllib.parse
import requests

CLASSIFIED_FILE = 'data/streets_classified.json'
CACHE_FILE = 'data/cache_patrons.json'
USER_AGENT = 'KrakowStreetsBot/1.0 (https://github.com/ulice_krakowa; contact@krakowstreets.pl)'
WIKI_API_URL = 'https://pl.wikipedia.org/w/api.php'
SPARQL_URL = 'https://query.wikidata.org/sparql'

TITLES = [
    'generał', 'generała', 'gen.', 'marszałek', 'marszałka', 'marsz.',
    'pułkownik', 'pułkownika', 'płk.', 'płk', 'podpułkownik', 'podpułkownika', 'ppłk.', 'ppłk',
    'major', 'majora', 'mjr.', 'mjr', 'kapitan', 'kapitana', 'kpt.', 'kpt',
    'porucznik', 'porucznika', 'por.', 'por', 'rotmistrz', 'rotmistrza', 'rtm.', 'rtm',
    'hetman', 'hetmana', 'profesor', 'profesora', 'prof.', 'doktor', 'doktora', 'dra', 'dr.', 'dr',
    'docent', 'doc.', 'inżynier', 'inżyniera', 'inż.', 'biskup', 'biskupa', 'bpa', 'bp',
    'arcybiskup', 'arcybiskupa', 'abpa', 'abp', 'kardynał', 'kardynała', 'kard.',
    'ksiądz', 'księdza', 'ks.', 'ojciec', 'ojca', 'o.', 'brat', 'brata', 'siostra', 'siostry',
    'święty', 'świętego', 'świętej', 'święta', 'św.', 'sw.', 'błogosławiony', 'błogosławionego', 'bł.',
    'król', 'króla', 'królowa', 'królowej', 'książę', 'księcia', 'księżna', 'księżnej',
    'prezydent', 'prezydenta', 'harcmistrz', 'harcmistrza', 'harcmistrzyni', 'komandor', 'komandora',
    'inspektor', 'inspektora', 'redaktor', 'redaktora', 'mecenas', 'mecenasa', 'mistrz', 'mistrza',
    'admirał', 'admirała', 'druhny', 'druhna', 'podharcmistrz', 'phm.', 'pilota', 'pilot', 'prałata',
    'prymasa', 'ojca'
]
TITLES_SET = set(TITLES)

FLEETING_MAP = {
    'brożk': 'Brożek', 'morcink': 'Morcinek', 'buszk': 'Buszek', 'wujk': 'Wujek',
    'dank': 'Danek', 'kadłubk': 'Kadłubek', 'sławk': 'Sławek', 'łokietk': 'Łokietek',
    'małk': 'Małek', 'flank': 'Flanek', 'mazank': 'Mazanek', 'łaczk': 'Łaczek',
    'dąbk': 'Dąbek', 'hynk': 'Hynek', 'dantyszk': 'Dantyszek', 'chwistk': 'Chwistek',
    'wyrobk': 'Wyrobek', 'pniak': 'Pniak', 'hollendr': 'Hollender', 'wierzynk': 'Wierzynek',
    'geremk': 'Geremek', 'siwk': 'Siwek', 'jaskr': 'Jaskier', 'misiołk': 'Misiołek'
}

SPECIAL_FIXES = {
    'chrobri': 'Bolesław I Chrobry',
    'krzywousti': 'Bolesław III Krzywousty',
    'śmiałi': 'Bolesław II Szczodry',
    'wstydliwi': 'Bolesław V Wstydliwy',
    'batori': 'Stefan Batory',
    'stari': 'Zygmunt I Stary',
    'czarni': 'Leszek Czarny',
    'białi': 'Leszek Biały',
    'brodati': 'Henryk I Brodaty',
    'wielkii': 'Kazimierz III Wielki',
    'sprawiedliwi': 'Kazimierz II Sprawiedliwy',
    'sahajdaczni': 'Piotr Konaszewicz-Sahajdaczny',
    'korfanti': 'Wojciech Korfanty',
    'śmigłi': 'Edward Rydz-Śmigły',
    'vetulanii': 'Adam Vetulani',
    'zbigniew herbert hoover': 'Herbert Hoover',
    'sereno fenn fenn\'a': 'Sereno Fenn',
    'andrzej i józefa załuskich': 'Józef Andrzej Załuski',
    'helena i leona patynów': 'Leon Patyna',
    'jan i józefa kotlarczyków': 'Mieczysław Kotlarczyk',
    'jan i jędrzeja śniadeckich': 'Jan Śniadecki',
    'karol i jerzego drozdowskich': 'Jerzy Drozdowski',
    'maksymilian i aleksandra gierymskich': 'Aleksander Gierymski',
    'maksymilian i stanisława cerchów': 'Maksymilian Cercha',
    'michał i stanisława jaglarzów': 'Michał Jaglarz',
    'wilhelm i jana ripperów': 'Jan Ripper',
    'zbigniew i andrzeja pronaszków': 'Zbigniew Pronaszko',
    'erazm i stanisława fabijańskich': 'Stanisław Fabijański',
    'józef i floriana sawiczewskich': 'Florian Sawiczewski',
    'maria i bolesława wysłouchów': 'Bolesław Wysłouch',
    'królowa jadwiga': 'Jadwiga Andegaweńska',
    'królowa bony': 'Bona Sforza',
    'święty brata albert': 'Adam Chmielowski',
    'święty rafał kalinowski': 'Rafał Kalinowski',
    'święty andrzej boboli': 'Andrzej Bobola',
    'bartosz': 'Wojciech Bartosz Głowacki',
    'beera meisels': 'Dow Ber Meisels',
    'konrad wallenrod': 'Konrad Wallenrod',
    'kordian': 'Kordian',
    'wernyhora': 'Wernyhora',
    'kronikarza galla': 'Gall Anonim',
    'pana tadeusza': 'Pan Tadeusz',
    'przemysław ii': 'Przemysł II',
    'władysław iv': 'Władysław IV Waza',
    'zygmunt august': 'Zygmunt II August',
    'władysław warneńczyk': 'Władysław III Warneńczyk',
    'władysław łokietk': 'Władysław I Łokietek',
    'stanisława augusta poniatowski': 'Stanisław August Poniatowski',
    'ignacy jana paderewski': 'Ignacy Jan Paderewski',
    'jan pawła ii': 'Jan Paweł II',
    'jan izydora sztaudynger': 'Jan Izydor Sztaudynger',
    'jan krzysztofa kluk': 'Krzysztof Kluk',
    'jan stanisława bystronia': 'Jan Stanisław Bystroń',
    'jan zygmunta robla': 'Jan Zygmunt Robel',
    'julian konstantego ordon': 'Juliusz Konstanty Ordon',
    'julian ursyna niemcewicz': 'Julian Ursyn Niemcewicz',
    'juliusz kadena-bandrowski': 'Juliusz Kaden-Bandrowski',
    'józef ignacego kraszewski': 'Józef Ignacy Kraszewski',
    'józef sawy-caliński': 'Józef Sawa-Caliński',
    'konstanty ildefonsa gałczyński': 'Konstanty Ildefons Gałczyński',
    'krzysztof kamila baczyński': 'Krzysztof Kamil Baczyński',
    'ksiądz biskupa władysława bandurski': 'Władysław Bandurski',
    'ksiądz grzegorz gerwazego gorczycki': 'Grzegorz Gerwazy Gorczycki',
    'ksiądz ignacy jana skorupki': 'Ignacy Skorupka',
    'ksiądz prałata mariana łaczk': 'Marian Łaczek',
    'ksiądz prymasa stefana wyszyński': 'Stefan Wyszyński',
    'ksiądz kardynała adama stefana sapiehy': 'Adam Stefan Sapieha',
    'legionów józefa piłsudski': 'Józef Piłsudski',
    'leon henryka sternbacha': 'Leon Sternbach',
    'ludwik hieronima morstin': 'Ludwik Hieronim Morstin',
    'major pilota mariana pisark': 'Marian Pisarek',
    'major pilota stefana janus': 'Stefan Janus',
    'marcin borelowskiego-lelewela': 'Marcin Borelowski',
    'profesor bolesław wiktora wicherkiewicz': 'Bolesław Wicherkiewicz',
    'profesor kazimierz tadeusza opałk': 'Kazimierz Opałek',
    'profesor wojciech marii bartla': 'Wojciech Maria Bartel',
    'pułkownik edward gardy-godlewski': 'Edward Godlewski',
    'pułkownik francesco nullo': 'Francesco Nullo',
    'pułkownik stanisława nazarkiewicz': 'Stanisław Nazarkiewicz',
    'pułkownik władysław beliny-prażmowski': 'Władysław Belina-Prażmowski',
    'pułkownik pilota stefana łaszkiewicz': 'Stefan Łaszkiewicz',
    'rotmistrz zbigniew dunin-wąsowicz': 'Zbigniew Dunin-Wąsowicz',
    'samuel bogumiła lindi': 'Samuel Bogumił Linde',
    'siostra magdalena marii epstein': 'Magdalena Maria Epstein',
    'siostra zygmunty zimmer': 'Zygmunta Zimmer',
    'tadeusz boya-żeleński': 'Tadeusz Boy-Żeleński',
    'tadeusz lehra-spławiński': 'Tadeusz Lehr-Spławiński',
    'tadeusz wyrwy-furgalski': 'Tadeusz Furgalski',
    'walery eliasza radzikowski': 'Walery Eljasz-Radzikowski',
    'wilhelm wilka-wyrwiński': 'Wilhelm Wilk-Wyrwiński',
    'wincenty weryhy-darowski': 'Wincenty Weryha-Darowski',
    'władysław ludwika anczyca': 'Władysław Ludwik Anczyc',
    'święta maria magdaleny': 'Maria Magdalena',
    'święty piotr': 'Piotr Apostoł',
    'święty jan': 'Jan Apostoł',
    'święty jacek': 'Jacek Odrowąż',
    'święty marek': 'Marek Ewangelista',
    'święty tomasz': 'Tomasz Apostoł',
    'święty sebastian': 'Święty Sebastian',
    'święty wawrzyniec': 'Wawrzyniec z Rzymu',
    'święty filip': 'Filip Apostoł',
    'święty łazarz': 'Łazarz z Betanii',
    'święty wincenty': 'Wincenty a Paulo',
    'święty stanisława': 'Stanisław ze Szczepanowa',
    'święta agnieszki': 'Agnieszka Rzymianka',
    'święta teresa': 'Teresa z Ávili',
    'święta katarzyna': 'Katarzyna Aleksandryjska',
    'święta kingi': 'Kinga (święta)',
    'święta gertruda': 'Gertruda z Nivelles',
    'święta bronisława': 'Bronisława (błogosławiona)',
    'profesor bronisław geremk': 'Bronisław Geremek',
    'kazimierz herwina-piątk': 'Kazimierz Herwin-Piątek',
    'władysław siwk': 'Władysław Siwek',
    'mikołaj jaskr': 'Mikołaj Jaskier',
    'mikołaj wierzynk': 'Mikołaj Wierzynek (starszy)',
    'kazimierz jagiellończyk': 'Kazimierz IV Jagiellończyk',
    'fryderyk zolla': 'Fryderyk Zoll (starszy)',
    'biskup piotr tomicki': 'Piotr Tomicki',
    'doktor judyma': 'Tomasz Judym',
    'doktor twardego': 'Stanisław Twardy',
    'doktor mieczysław owcy-orwicz': 'Mieczysław Owca-Orwicz',
    'grzegorz z sanok': 'Grzegorz z Sanoka',
    'wojciech z brudzew': 'Wojciech z Brudzewa',
    'jadwiga z łobzow': 'Jadwiga z Łobzowa',
    'książę józef': 'Józef Poniatowski',
    'konstanty ciołkowski': 'Konstantin Ciołkowski',
    'leon misiołk': 'Leon Misiołek',
    'leon ślósarczyk': 'Leon Ślósarczyk',
    'lech': 'Lech (postać legendarna)',
    'seweryn udzieli': 'Seweryn Udziela',
    'siostra faustyna': 'Faustyna Kowalska',
    'antoni hoborski': 'Antoni Maria Emilian Hoborski',
    'andrzej potebni': 'Andrij Potebnia',
    'grażyna': 'Grażyna (postać literacka)',
    'ernest solvaya': 'Ernest Solvay',
    'generał franciszek paszkowski': 'Franciszek Paszkowski',
    'generał henryk kamieński': 'Henryk Ignacy Kamieński',
    'generał kiwerskiego': 'Jan Wojciech Kiwerski',
    'generał witold urbanowicz': 'Witold Urbanowicz',
    'major mieczysław słabi': 'Mieczysław Słaby',
    'major łupaszki': 'Zygmunt Szendzielarz',
    'marcin wencla': 'Marcin Wencel',
    'iwon odrowąża': 'Iwo Odrowąż',
    'ksiądz stefan pawlicki': 'Stefan Zachariasz Pawlicki',
    'ksiądz zygmunt kaczyński': 'Zygmunt Kaczyński',
    'pułkownik barty': 'Przemysław Barthel de Weydenthal',
    'inżynier adam bielański': 'Adam Bielański',
    'henryk i karola czeczów': 'Karol Czecz de Lindenwald',
    'porucznik halszki': 'Stanisława Rachwałowa'
}

NON_PERSON_PATRONS = {
    'święty ducha', 'święty krzyża', 'święta rodziny', 'turzymy marii'
}

def strip_titles(text):
    words = text.split()
    while words and words[0].lower().rstrip('.') in TITLES_SET:
        words = words[1:]
    return ' '.join(words)

def fix_last_word(last):
    lw = last.lower()
    
    if lw.endswith('ii'):
        return last[:-1]
        
    if lw.endswith('ńca'):
        return last[:-3] + 'niec'
        
    if lw in FLEETING_MAP:
        return FLEETING_MAP[lw]

    if lw.endswith('ówny'):
        return last[:-4] + 'ówna'
    if lw.endswith('owej'):
        return last[:-4] + 'owa'
    if lw.endswith(('skiej', 'ckiej', 'zkiej')):
        suf = 'ska' if lw.endswith('skiej') else ('cka' if lw.endswith('ckiej') else 'zka')
        return last[:-5] + suf
    if lw.endswith('nki'):
        return last[:-3] + 'nka'

    if '-' in last:
        parts = last.split('-')
        p0 = parts[0]
        p1 = parts[1]
        p0_l = p0.lower()
        p1_l = p1.lower()
        
        if p0_l.endswith(('ki', 'gi')):
            p0 = p0[:-1] + 'o'
        elif p0_l.endswith(('a', 'i', 'y')) and len(p0_l) > 3:
            p0 = p0[:-1]
            
        if p1_l.endswith(('skiego', 'ckiego', 'zkiego')):
            suf = 'ski' if p1_l.endswith('skiego') else ('cki' if p1_l.endswith('ckiego') else 'zki')
            p1 = p1[:-6] + suf
        elif p1_l.endswith('ego'):
            p1 = p1[:-3] + 'y'
        elif p1_l.endswith(('a', 'i', 'y')) and len(p1_l) > 4:
            p1 = p1[:-1]
            
        return f'{p0}-{p1}'

    if lw.endswith(('chrobri', 'krzywousti', 'śmiałi', 'wstydliwi', 'batori', 'stari', 'czarni', 'białi', 'brodati', 'wielkii', 'sprawiedliwi', 'sahajdaczni', 'korfanti', 'śmigłi')):
        if lw == 'wielkii':
            return 'Wielki'
        return last[:-1] + 'y'

    if lw.endswith(('sza', 'cza', 'rza', 'cha', 'ka', 'ga', 'ba', 'da', 'fa', 'la', 'ła', 'ma', 'na', 'pa', 'ra', 'sa', 'ta', 'wa', 'za')) and len(lw) > 4:
        if not lw.endswith(('ska', 'cka', 'zka', 'ówna', 'owa', 'ewska', 'owska')):
            return last[:-1]

    if lw.endswith(('py', 'ły', 'by', 'my', 'hy', 'ry', 'ty', 'wy', 'zy', 'chy', 'szy', 'czy', 'rzy', 'ki', 'gi', 'li')):
        return last[:-1] + 'a'

    return last

def generate_query_variants(nom, clean_name=''):
    nom_lower = nom.lower().strip()
    if nom_lower in NON_PERSON_PATRONS:
        return []
    if nom_lower in SPECIAL_FIXES:
        return [SPECIAL_FIXES[nom_lower]]

    variants = []
    cleaned_nom = strip_titles(nom).strip()
    cleaned_clean = strip_titles(clean_name).strip() if clean_name else ''

    # Wariant 1: ze skorygowanym ostatnim słowem
    words = cleaned_nom.split()
    if words:
        words_fixed = list(words)
        words_fixed[-1] = fix_last_word(words[-1])
        cand1 = ' '.join(words_fixed)
        if cand1 not in variants:
            variants.append(cand1)

    # Wariant 2: cleaned_clean ze skorygowanym ostatnim słowem
    if cleaned_clean:
        c_words = cleaned_clean.split()
        if c_words:
            first_gen = c_words[0].lower()
            FIRST_MAP = {'adama': 'Adam', 'aleksandra': 'Aleksander', 'andrzeja': 'Andrzej',
                         'antoniego': 'Antoni', 'bolesława': 'Bolesław', 'bronisława': 'Bronisław',
                         'czesława': 'Czesław', 'edwarda': 'Edward', 'feliksa': 'Feliks',
                         'franciszka': 'Franciszek', 'henryka': 'Henryk', 'ignacego': 'Ignacy',
                         'jana': 'Jan', 'jerzego': 'Jerzy', 'juliana': 'Julian', 'juliusza': 'Juliusz',
                         'józefa': 'Józef', 'karola': 'Karol', 'kazimierza': 'Kazimierz',
                         'leona': 'Leon', 'ludwika': 'Ludwik', 'mariana': 'Marian', 'michała': 'Michał',
                         'mikołaja': 'Mikołaj', 'piotra': 'Piotr', 'stanisława': 'Stanisław',
                         'stefana': 'Stefan', 'tadeusza': 'Tadeusz', 'wacława': 'Wacław',
                         'walerego': 'Walery', 'wincentego': 'Wincenty', 'władysława': 'Władysław',
                         'wojciecha': 'Wojciech', 'zbigniewa': 'Zbigniew', 'zygmunta': 'Zygmunt'}
            if first_gen in FIRST_MAP:
                c_words[0] = FIRST_MAP[first_gen]
            c_words[-1] = fix_last_word(c_words[-1])
            cand2 = ' '.join(c_words)
            if cand2 not in variants:
                variants.append(cand2)

    # Wariant 3: cleaned_nom as-is
    if cleaned_nom and cleaned_nom not in variants:
        variants.append(cleaned_nom)

    # Wariant 4: cleaned_clean as-is
    if cleaned_clean and cleaned_clean not in variants:
        variants.append(cleaned_clean)

    # Wariant 5: clean_name
    if clean_name and clean_name not in variants:
        variants.append(clean_name)

    return variants

def batch_wikipedia_titles(titles_list):
    results = {}
    if not titles_list:
        return results

    headers = {'User-Agent': USER_AGENT}
    for i in range(0, len(titles_list), 50):
        chunk = titles_list[i:i + 50]
        titles_param = '|'.join(chunk)
        params = {
            'action': 'query',
            'titles': titles_param,
            'redirects': 1,
            'prop': 'pageprops|description',
            'ppprop': 'wikibase_item',
            'format': 'json'
        }
        try:
            r = requests.get(WIKI_API_URL, params=params, headers=headers, timeout=15)
            data = r.json()
            redirect_map = {}
            for red in data.get('query', {}).get('redirects', []):
                redirect_map[red['from']] = red['to']
            for norm in data.get('query', {}).get('normalized', []):
                redirect_map[norm['from']] = norm['to']

            pages_by_title = {}
            for p in data.get('query', {}).get('pages', {}).values():
                t = p.get('title')
                qid = p.get('pageprops', {}).get('wikibase_item')
                desc = p.get('description', '')
                if t and qid:
                    pages_by_title[t] = (t, qid, desc)

            for orig in chunk:
                target = orig
                seen_red = set()
                while target in redirect_map and target not in seen_red:
                    seen_red.add(target)
                    target = redirect_map[target]
                if target in pages_by_title:
                    results[orig] = pages_by_title[target]
        except Exception as e:
            print(f'Błąd direct titles batch: {e}')
        time.sleep(0.2)
    return results

def search_wikipedia_patron(cand):
    """
    Wyszukuje hasło w Wikipedii za pomocą Search API ze ścisłą walidacją nazwiska.
    """
    headers = {'User-Agent': USER_AGENT}
    params = {
        'action': 'query',
        'generator': 'search',
        'gsrsearch': cand,
        'gsrlimit': 5,
        'prop': 'pageprops|description',
        'ppprop': 'wikibase_item',
        'format': 'json'
    }
    try:
        r = requests.get(WIKI_API_URL, params=params, headers=headers, timeout=15)
        pages = sorted(r.json().get('query', {}).get('pages', {}).values(), key=lambda x: x.get('index', 99))
        cand_words = [w for w in re.findall(r'\w+', cand.lower()) if len(w) > 2 and w not in TITLES_SET]
        if not cand_words:
            return None

        surname = cand_words[-1]
        surname_stem = surname[:4] if len(surname) >= 5 else surname[:3]

        DISQUALIFY_PREFIXES = ('ulica ', 'aleja ', 'plac ', 'rondo ', 'park ', 'osiedle ',
                                'most ', 'pomnik ', 'bitwa ', 'film ', 'szkoła ', 'liceum ',
                                'cmentarz ', 'kościół ', 'parafia ', 'biblioteka ', 'uniwersytet ', 'akademia ')

        for p in pages:
            title = p.get('title', '')
            t_lower = title.lower()
            if any(t_lower.startswith(pref) for pref in DISQUALIFY_PREFIXES):
                continue
            qid = p.get('pageprops', {}).get('wikibase_item')
            if not qid:
                continue

            t_words = [w for w in re.findall(r'\w+', t_lower) if len(w) > 2]
            # Wymóg: nazwisko musi pasować
            matched_surname = any(
                w.startswith(surname_stem) or surname.startswith(w[:4] if len(w) >= 5 else w[:3])
                for w in t_words
            )
            if not matched_surname:
                continue

            # Jeśli były co najmniej 2 słowa, pierwsze imię nie może być sprzeczne
            if len(cand_words) >= 2 and len(t_words) >= 2:
                first_stem = cand_words[0][:3]
                if not any(w.startswith(first_stem) for w in t_words):
                    continue

            return (title, qid, p.get('description', ''))
    except Exception as e:
        print(f'Błąd wyszukiwania Wikipedii dla "{cand}": {e}')
    return None

def query_wikidata_details(qids_batch):
    if not qids_batch:
        return {}

    values_str = ' '.join(f'wd:{q}' for q in qids_batch)
    query = f'''
SELECT ?person ?label_pl ?label_mul ?label_en ?birth ?death ?image ?desc_pl ?desc_en ?desc_de ?article_pl ?p31 WHERE {{
  VALUES ?person {{ {values_str} }}
  OPTIONAL {{ ?person wdt:P31 ?p31. }}
  OPTIONAL {{ ?person wdt:P569 ?birth. }}
  OPTIONAL {{ ?person wdt:P570 ?death. }}
  OPTIONAL {{ ?person wdt:P18 ?image. }}
  OPTIONAL {{ ?person schema:description ?desc_pl. FILTER(LANG(?desc_pl) = "pl") }}
  OPTIONAL {{ ?person schema:description ?desc_en. FILTER(LANG(?desc_en) = "en") }}
  OPTIONAL {{ ?person schema:description ?desc_de. FILTER(LANG(?desc_de) = "de") }}
  OPTIONAL {{ ?person rdfs:label ?label_pl. FILTER(LANG(?label_pl) = "pl") }}
  OPTIONAL {{ ?person rdfs:label ?label_mul. FILTER(LANG(?label_mul) = "mul") }}
  OPTIONAL {{ ?person rdfs:label ?label_en. FILTER(LANG(?label_en) = "en") }}
  OPTIONAL {{
    ?article_pl schema:about ?person;
                schema:isPartOf <https://pl.wikipedia.org/>.
  }}
}}
'''
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/sparql-results+json'
    }
    try:
        r = requests.get(SPARQL_URL, params={'query': query, 'format': 'json'}, headers=headers, timeout=25)
        data = r.json()
        
        entities = {}
        for b in data.get('results', {}).get('bindings', []):
            uri = b.get('person', {}).get('value', '')
            qid = uri.split('/')[-1]
            if not qid:
                continue

            if qid not in entities:
                entities[qid] = {
                    'qid': uri,
                    'p31': set(),
                    'label_pl': b.get('label_pl', {}).get('value', ''),
                    'label_mul': b.get('label_mul', {}).get('value', ''),
                    'label_en': b.get('label_en', {}).get('value', ''),
                    'birth': b.get('birth', {}).get('value', ''),
                    'death': b.get('death', {}).get('value', ''),
                    'image': b.get('image', {}).get('value', ''),
                    'desc_pl': b.get('desc_pl', {}).get('value', ''),
                    'desc_en': b.get('desc_en', {}).get('value', ''),
                    'desc_de': b.get('desc_de', {}).get('value', ''),
                    'article_pl': b.get('article_pl', {}).get('value', '')
                }

            p31_val = b.get('p31', {}).get('value', '')
            if p31_val:
                entities[qid]['p31'].add(p31_val.split('/')[-1])

            e = entities[qid]
            if not e['image'] and b.get('image', {}).get('value'):
                e['image'] = b['image']['value']
            if not e['birth'] and b.get('birth', {}).get('value'):
                e['birth'] = b['birth']['value']
            if not e['death'] and b.get('death', {}).get('value'):
                e['death'] = b['death']['value']
            if not e['desc_pl'] and b.get('desc_pl', {}).get('value'):
                e['desc_pl'] = b['desc_pl']['value']
            if not e['desc_en'] and b.get('desc_en', {}).get('value'):
                e['desc_en'] = b['desc_en']['value']
            if not e['desc_de'] and b.get('desc_de', {}).get('value'):
                e['desc_de'] = b['desc_de']['value']
            if not e['article_pl'] and b.get('article_pl', {}).get('value'):
                e['article_pl'] = b['article_pl']['value']

        return entities
    except Exception as e:
        print(f'Błąd zapytania SPARQL Wikidata: {e}')
        return {}

def main():
    print('=== ETAP 1: DOMKNIĘCIE BAZY PATRONÓW OSOBOWYCH KRAKOWA ===\n', flush=True)

    if not os.path.exists(CLASSIFIED_FILE):
        print(f'Brak pliku {CLASSIFIED_FILE}!')
        return

    with open(CLASSIFIED_FILE, 'r', encoding='utf-8') as f:
        classified = json.load(f)

    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)

    nom_to_clean = {}
    for it in classified:
        if it.get('category') == 'person':
            nom = it.get('nominative')
            if nom and nom not in nom_to_clean:
                nom_to_clean[nom] = it.get('clean_name', '')

    all_person_noms = sorted(list(nom_to_clean.keys()))
    print(f'Łącznie unikalnych patronów w klasyfikacji: {len(all_person_noms)}')

    initial_found = sum(1 for v in cache.values() if v.get('found'))
    missing_noms = [nom for nom in all_person_noms if not cache.get(nom, {}).get('found')]
    print(f'Już znalezionych w cache: {initial_found}')
    print(f'Do rozwiązania w Etapie 1: {len(missing_noms)}\n')

    # Krok 1: Generowanie wariantów zapytań dla brakujących patronów
    nom_variants = {}
    for nom in missing_noms:
        clean_n = nom_to_clean.get(nom, '')
        vars_list = generate_query_variants(nom, clean_n)
        if vars_list:
            nom_variants[nom] = vars_list

    print(f'Wygenerowano warianty zapytań dla {len(nom_variants)} patronów.')

    # Krok 2A: Direct Title Lookup w Wikipedii
    primary_cands = {}
    for nom, vars_list in nom_variants.items():
        if vars_list:
            primary_cands[vars_list[0]] = nom

    print(f'Krok 2A: Sprawdzam {len(primary_cands)} bezpośrednich tytułów w Wikipedii...')
    direct_hits = batch_wikipedia_titles(list(primary_cands.keys()))
    print(f'Krok 2A: Trafienia bezpośrednie: {len(direct_hits)}')

    resolved_qids = {}  # nom -> (wiki_title, qid, desc)
    for cand_title, (w_title, qid, desc) in direct_hits.items():
        nom = primary_cands[cand_title]
        resolved_qids[nom] = (w_title, qid, desc)

    # Krok 2B: Wikipedia Search API dla pozostałych
    remaining_noms = [nom for nom in missing_noms if nom not in resolved_qids and nom in nom_variants]
    print(f'\nKrok 2B: Odpytuję Wikipedia Search API dla {len(remaining_noms)} postaci...')

    for idx, nom in enumerate(remaining_noms, 1):
        vars_list = nom_variants.get(nom, [])
        match = None
        for cand in vars_list:
            match = search_wikipedia_patron(cand)
            if match:
                break
            time.sleep(0.08)

        if match:
            w_title, qid, desc = match
            resolved_qids[nom] = (w_title, qid, desc)
            if idx % 20 == 0 or idx == len(remaining_noms):
                print(f'  [{idx}/{len(remaining_noms)}] Rozwiązano: {nom} -> {w_title} ({qid})', flush=True)
        else:
            if idx % 35 == 0:
                print(f'  [{idx}/{len(remaining_noms)}] Przetwarzanie...', flush=True)
        time.sleep(0.12)

    print(f'\nŁącznie wytypowano kandydatów QID: {len(resolved_qids)} / {len(missing_noms)}')

    # Krok 3: Wzbogacenie z Wikidata SPARQL (partie po 50 QID)
    unique_qids = sorted(list(set(qid for (_, qid, _) in resolved_qids.values())))
    print(f'Pobieranie metadanych z Wikidata SPARQL dla {len(unique_qids)} unikalnych QID...')

    wikidata_data = {}
    BATCH_SIZE = 50
    for i in range(0, len(unique_qids), BATCH_SIZE):
        chunk = unique_qids[i:i + BATCH_SIZE]
        print(f'  SPARQL batch {i+1}-{min(i+BATCH_SIZE, len(unique_qids))} / {len(unique_qids)}...')
        chunk_res = query_wikidata_details(chunk)
        wikidata_data.update(chunk_res)
        time.sleep(0.25)

    # Krok 4: Fuzja i aktualizacja cache ze ścisłą weryfikacją instancji
    VALID_P31 = {'Q5', 'Q215627', 'Q3658341', 'Q95074', 'Q15632617', 'Q17888', 'Q4271324', 'Q15773317', 'Q24229398'}
    INVALID_P31 = {'Q3918', 'Q79007', 'Q12280', 'Q7075', 'Q178561', 'Q11424', 'Q134556', 'Q11821942', 'Q4167410', 'Q1656682'}

    newly_enriched = 0
    rejected_non_human = 0

    for nom in missing_noms:
        if nom in resolved_qids:
            w_title, qid, search_desc = resolved_qids[nom]
            w_item = wikidata_data.get(qid)
            
            p31_types = w_item.get('p31', set()) if w_item else set()
            is_valid = bool(p31_types & VALID_P31) and not bool(p31_types & INVALID_P31)

            if not is_valid:
                rejected_non_human += 1
                continue

            if w_item:
                birth = w_item.get('birth', '')
                death = w_item.get('death', '')
                b_year = birth[:4] if birth and birth[:4].isdigit() else ''
                d_year = death[:4] if death and death[:4].isdigit() else ''

                img_raw = w_item.get('image', '')
                img_thumb = ''
                if img_raw:
                    clean_img = img_raw.replace('http://', 'https://')
                    if '?width=' not in clean_img:
                        img_thumb = f'{clean_img}?width=360'
                    else:
                        img_thumb = clean_img

                desc_pl = w_item.get('desc_pl', '') or search_desc or ''
                desc_en = w_item.get('desc_en', '')
                desc_de = w_item.get('desc_de', '')

                canonical_name = w_item.get('label_pl') or w_item.get('label_mul') or w_title or nom

                article_url = w_item.get('article_pl', '')
                if not article_url:
                    slug = urllib.parse.quote(w_title.replace(' ', '_'))
                    article_url = f'https://pl.wikipedia.org/wiki/{slug}'

                cache[nom] = {
                    'found': True,
                    'qid': w_item.get('qid', f'http://www.wikidata.org/entity/{qid}'),
                    'name': canonical_name,
                    'birth_year': b_year,
                    'death_year': d_year,
                    'image': img_thumb,
                    'role': {
                        'pl': desc_pl,
                        'en': desc_en,
                        'de': desc_de
                    },
                    'wiki_url': article_url
                }
                newly_enriched += 1

    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

    total_found_final = sum(1 for v in cache.values() if v.get('found'))
    total_images_final = sum(1 for v in cache.values() if v.get('image'))

    print('\n=== PODSUMOWANIE ETAPU 1 ===')
    print(f'Nowo rozwiązanych patronów w Etapie 1: {newly_enriched}')
    print(f'Odrzuconych nieosobowych trafień (QA/anty-halucynacja): {rejected_non_human}')
    print(f'Łączny stan bazy: {total_found_final} / {len(all_person_noms)} ({total_found_final / len(all_person_noms) * 100:.1f}%)')
    print(f'Patroni z oficjalnym portretem Wikimedia Commons CDN: {total_images_final}')
    print(f'Zapisano plik: {CACHE_FILE}')

if __name__ == '__main__':
    main()
