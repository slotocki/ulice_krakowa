# -*- coding: utf-8 -*-
import json
import os

CLASSIFIED_FILE = 'data/streets_classified.json'
OUTPUT_FILE = 'data/cache_etymologies.json'

LITERAL_DICTIONARY = {
    # Rzemiosło i stare miasto
    'szewska': ('Shoemakers\' Street', 'Schustergasse'),
    'grodzka': ('Castle Road', 'Burgstraße'),
    'garbarska': ('Tanners\' Street', 'Gerbergasse'),
    'stolarska': ('Carpenters\' Street', 'Tischlergasse'),
    'poselska': ('Envoys\' Street', 'Gesandtengasse'),
    'kanonicza': ('Canons\' Street', 'Kanonikergasse'),
    'szeroka': ('Broad / Wide Street', 'Breite Gasse'),
    'miodowa': ('Honey Street', 'Honiggasse'),
    'piwna': ('Beer Street', 'Biergasse'),
    'floriańska': ('St. Florian\'s Street', 'Floriansgasse'),
    'sławkowska': ('Sławków Street', 'Slawkauer Straße'),
    'bracka': ('Brothers\' / Friars\' Street', 'Brüdergasse'),
    'sienna': ('Hay Street', 'Heugasse'),
    'gołębia': ('Pigeon / Dove Street', 'Taubengasse'),
    'długa': ('Long Street', 'Lange Straße'),
    'krótka': ('Short Street', 'Kurze Gasse'),
    'wąska': ('Narrow Street', 'Enge Gasse'),
    'ciemna': ('Dark Lane', 'Dunkle Gasse'),
    'jasna': ('Bright Street', 'Helle Gasse'),
    'prosta': ('Straight Street', 'Gerade Straße'),
    'krzywa': ('Crooked Street', 'Krumme Gasse'),
    'cicha': ('Quiet Street', 'Stille Straße'),
    'spokojna': ('Peaceful Street', 'Ruhige Straße'),
    'zielona': ('Green Street', 'Grüne Straße'),
    'ogrodowa': ('Garden Street', 'Gartenstraße'),
    'polna': ('Field Road', 'Feldstraße'),
    'leśna': ('Forest Road', 'Waldstraße'),
    'słoneczna': ('Sunny Street', 'Sonnige Straße'),
    'lipowa': ('Linden / Lime Tree Street', 'Lindenstraße'),
    'dębowa': ('Oak Tree Street', 'Eichenstraße'),
    'brzozowa': ('Birch Tree Street', 'Birkenstraße'),
    'kwiatowa': ('Flower Street', 'Blumenstraße'),
    'różana': ('Rose Street', 'Rosenstraße'),
    'akacjowa': ('Acacia Street', 'Akazienstraße'),
    'kasztanowa': ('Chestnut Street', 'Kastanienstraße'),
    'sosnowa': ('Pine Tree Street', 'Kiefernstraße'),
    'wierzbowa': ('Willow Street', 'Weidenstraße'),
    'klonowa': ('Maple Street', 'Ahornstraße'),
    'topolowa': ('Poplar Street', 'Pappelstraße'),
    'świerkowa': ('Spruce Street', 'Fichtenstraße'),
    'jodłowa': ('Fir Tree Street', 'Tannenstraße'),
    'jaśminowa': ('Jasmine Street', 'Jasminstraße'),
    'lawendowa': ('Lavender Street', 'Lavendelstraße'),
    'konwaliowa': ('Lily of the Valley Street', 'Maiglöckchenstraße'),
    'fiołkowa': ('Violet Street', 'Veilchenstraße'),
    'młyńska': ('Mill Street', 'Mühlstraße'),
    'rybna': ('Fish Street', 'Fischgasse'),
    'rzeźnicza': ('Butchers\' Street', 'Fleischergasse'),
    'piekarska': ('Bakers\' Street', 'Bäckergasse'),
    'złotników': ('Goldsmiths\' Street', 'Goldschmiedgasse'),
    'kotlarska': ('Coppersmiths\' Street', 'Kesselschmiedstraße'),
    'kowalska': ('Blacksmiths\' Street', 'Schmiedgasse'),
    'krawiecka': ('Tailors\' Street', 'Schneidergasse'),
    'sukiennicza': ('Cloth Hall Street', 'Tuchmacherstraße'),
    'bednarska': ('Coopers\' Street', 'Böttchergasse'),
    'ciesielska': ('Carpenters\' Street', 'Zimmererstraße')
}

HISTORICAL_DESCRIPTIONS = {
    'szewska': {
        'pl': 'Jedna z najstarszych ulic lokacyjnego Krakowa (1257 r.), historyczna siedziba cechu szewców krakowskich.',
        'en': 'One of the oldest streets of medieval Kraków (chartered 1257), historically the quarter of the shoemakers guild.',
        'de': 'Eine der ältesten Straßen des mittelalterlichen Krakau (1257 gegründet), historisches Zentrum der Schuhmacherzunft.'
    },
    'grodzka': {
        'pl': 'Najstarszy trakt Krakowa, fragment dawnego szlaku handlowego z północy na południe, prowadzący z Rynku ku Zamkowi Królewskiemu na Wawelu.',
        'en': 'The oldest thoroughfare of Kraków, part of the ancient north-south trade route leading from the Main Square directly to the Wawel Royal Castle.',
        'de': 'Der älteste Straßenzug Krakaus, Teil des antiken Nord-Süd-Handelswegs, der vom Hauptmarkt direkt zum königlichen Wawel-Schloss führt.'
    },
    'floriańska': {
        'pl': 'Reprezentacyjna arteria Drogi Królewskiej (Via Regia), wytyczona w 1257 r., wiodąca od Rynku Głównego ku Bramie Floriańskiej i Kleparzowi.',
        'en': 'Prestigious street of the Royal Road (Via Regia), laid out in 1257, leading from the Main Square towards the medieval St. Florian\'s Gate.',
        'de': 'Prachtstraße des Königswegs (Via Regia), 1257 angelegt, die vom Hauptmarkt zum mittelalterlichen Florianstor führt.'
    },
    'kanonicza': {
        'pl': 'Zabytkowa, najlepiej zachowana renesansowa ulica Krakowa, dawna siedziba kanoników katedralnych Wawelu.',
        'en': 'The best-preserved historic Renaissance street in Kraków, former residential quarter of the Wawel Cathedral canons.',
        'de': 'Die am besten erhaltene historische Renaissancestraße Krakaus, ehemalige Residenz der Domherren des Wawels.'
    },
    'szeroka': {
        'pl': 'Główny plac i serce dawnego żydowskiego miasta Kazimierz, ośrodek życia religijnego i kulturalnego ze Starą Synagogą.',
        'en': 'The historic main square and beating heart of the former Jewish town of Kazimierz, home to the 15th-century Old Synagogue.',
        'de': 'Der historische Hauptplatz und das Herz der ehemaligen jüdischen Stadt Kazimierz, Zentrum jüdischer Kultur mit der Alten Synagoge.'
    }
}

def generate_etymologies():
    if not os.path.exists(CLASSIFIED_FILE):
        print(f'Brak pliku {CLASSIFIED_FILE}!')
        return

    with open(CLASSIFIED_FILE, 'r', encoding='utf-8') as f:
        classified = json.load(f)

    etymologies = {}

    for item in classified:
        raw_name = item['raw_name']
        clean_name = item['clean_name']
        lower_clean = clean_name.lower()
        cat = item['category']

        if cat == 'person':
            continue

        res = {
            'category': cat,
            'clean_name': clean_name,
            'literal_meaning': None,
            'etymology': {}
        }

        # 1. Dosłowne znaczenie
        if lower_clean in LITERAL_DICTIONARY:
            en_lit, de_lit = LITERAL_DICTIONARY[lower_clean]
            res['literal_meaning'] = {
                'en': en_lit,
                'de': de_lit
            }

        # 2. Specjalne opisy historyczne
        if lower_clean in HISTORICAL_DESCRIPTIONS:
            res['etymology'] = HISTORICAL_DESCRIPTIONS[lower_clean]
        elif cat == 'nature_flora':
            res['etymology'] = {
                'pl': f'Nazwa o motywacji przyrodniczej (flora), nadana podczas rozbudowy i parcelacji dawnych ogrodów podmiejskich Krakowa.',
                'en': f'Nature-inspired street name (flora), established during the suburban development of former orchards and green spaces.',
                'de': f'Naturbezogener Straßenname (Flora), vergeben während der städtebaulichen Entwicklung ehemaliger Gärten.'
            }
        elif cat == 'nature_fauna':
            res['etymology'] = {
                'pl': f'Nazwa o motywacji zoologicznej (fauna), typowa dla spójnych tematycznie krakowskich osiedli mieszkaniowych.',
                'en': f'Fauna-inspired street name, typical of thematic residential developments in suburban Kraków.',
                'de': f'Tierbezogener Straßenname (Fauna), charakteristisch für thematische Wohngebiete in Krakau.'
            }
        elif cat == 'directional':
            town = item.get('target_town', clean_name)
            res['etymology'] = {
                'pl': f'Nazwa kierunkowa (topograficzna). Dawny trakt wylotowy z Krakowa prowadzący w kierunku miejscowości {town}.',
                'en': f'Directional toponymic name. Historical highway leading from Kraków towards {town}.',
                'de': f'Richtungstoponym. Historische Ausfallstraße von Krakau in Richtung {town}.'
            }
            if not res['literal_meaning']:
                res['literal_meaning'] = {
                    'en': f'{town} Road',
                    'de': f'{town}er Straße'
                }
        elif cat == 'directional_regional':
            res['etymology'] = {
                'pl': f'Ulica o nazwie toponimicznej, wywodząca się od historycznego traktu, osady lub regionu Małopolski.',
                'en': f'Toponymic street name, derived from a historic trade route, district or region in Lesser Poland.',
                'de': f'Toponymischer Straßenname, abgeleitet von einem historischen Handelsweg, einer Siedlung oder Region in Kleinpolen.'
            }
        elif cat == 'historical_craft':
            res['etymology'] = {
                'pl': f'Historyczna nazwa o motywacji rzemieślniczej lub cechowej, wywodząca się z tradycji dawnego rzemiosła krakowskiego.',
                'en': f'Historic street name derived from traditional Kraków guild crafts and medieval artisan workshops.',
                'de': f'Historischer Straßenname, der auf die Traditionen des alten Krakauer Handwerks und der Zünfte zurückgeht.'
            }
        elif cat == 'event_date':
            res['etymology'] = {
                'pl': f'Nazwa pamiątkowa upamiętniająca doniosłe wydarzenie historyczne lub datę w dziejach oręża i państwowości polskiej.',
                'en': f'Commemorative street name honoring a significant milestone or date in Polish history.',
                'de': f'Gedenkstraßenname zur Erinnerung an ein bedeutendes historisches Datum der polnischen Geschichte.'
            }
        else:
            res['etymology'] = {
                'pl': f'Oficjalna ulica m. Krakowa. Nazwa o motywacji toponimicznej, utrwalona w tradycji miejskiej.',
                'en': f'Official street in Kraków with a historic toponymic background established in municipal tradition.',
                'de': f'Offizielle Straße in Krakau mit toponymischem Hintergrund, fest in der städtischen Tradition verankert.'
            }

        etymologies[raw_name] = res

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(etymologies, f, ensure_ascii=False, indent=2)

    print(f'Zapisano etymologie dla {len(etymologies)} ulic nieosobowych do {OUTPUT_FILE}.')

if __name__ == '__main__':
    generate_etymologies()
