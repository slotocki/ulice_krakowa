# -*- coding: utf-8 -*-
import json
import os

with open('data/streets_sample.json', 'r', encoding='utf-8') as f:
    sample_data = json.load(f)

with open('data/temp_streets.json', 'r', encoding='utf-8') as f:
    temp_geom = json.load(f)

# Istniejące cechy indeksowane po ID
features_by_id = {feat['properties']['id']: feat for feat in sample_data['features']}

# 1. Definicja Szewska (rzemiosło, non-person)
szewska_feat = {
    "type": "Feature",
    "id": "szewska",
    "properties": {
        "id": "szewska",
        "name": {
            "pl": "Szewska",
            "en": "Szewska",
            "de": "Szewska"
        },
        "prefix": {
            "pl": "ulica",
            "en": "street",
            "de": "Straße"
        },
        "full_name": {
            "pl": "ulica Szewska",
            "en": "Szewska Street",
            "de": "Szewska-Straße"
        },
        "literal_meaning": {
            "en": "Shoemakers' / Cobblers' Street",
            "de": "Schustergasse"
        },
        "district": {
            "pl": "Stare Miasto",
            "en": "Old Town",
            "de": "Altstadt"
        },
        "district_id": "I",
        "category": {
            "pl": "Dawne Rzemiosło i Cechy",
            "en": "Medieval Guilds & Crafts",
            "de": "Mittelalterliche Zünfte & Handwerk"
        },
        "year": "1257",
        "length_meters": 330,
        "summary": {
            "pl": "Jedna z najstarszych ulic lokacyjnych, łącząca Rynek Główny z dawnym traktem śląskim.",
            "en": "One of Kraków's original 1257 charter streets, connecting the Main Market Square to the historic Silesian trade route.",
            "de": "Eine der ältesten Gründungsstraßen von 1257, die den Hauptmarkt mit der historischen schlesischen Handelsstraße verbindet."
        },
        "street_type": "crafts",
        "patron": None,
        "etymology": {
            "pl": "Wytyczona podczas wielkiej lokacji Krakowa w 1257 r. Jej nazwa pojawia się w źródłach miejskich już na początku XIV w. (1312 r. platea Cerdonum, platea Sutorum) i bezpośrednio nawiązuje do cechu szewców, garbarzy i rzemieślników skórzanych, którzy skupiali tu swoje warsztaty.",
            "en": "Laid out during Kraków's grand municipal charter in 1257. Documented in Latin archives as early as 1312 as 'platea Sutorum' (Shoemakers' Street), directly commemorating the medieval cobblers, tanners, and leathercraft masters who had workshops here.",
            "de": "Angelegt bei der großen Krakauer Stadtgründung im Jahr 1257. In den Stadtbüchern bereits 1312 als 'platea Sutorum' (Schustergasse) belegt, benannt nach den mittelalterlichen Schustern, Gerbern und Lederhandwerkern, die hier ihre Werkstätten betrieben."
        },
        "source": {
            "name": "E. Supranowicz, „Nazwy ulic Krakowa” (IJP PAN, 1995, ISBN 83-85579-48-6)",
            "url": None,
            "label": None
        },
        "resolution": {
            "has_resolution": False
        }
    },
    "geometry": {
        "type": "MultiLineString",
        "coordinates": temp_geom['szewska']
    }
}

# 2. Definicja Kwiatowa (flora, non-person)
kwiatowa_feat = {
    "type": "Feature",
    "id": "kwiatowa",
    "properties": {
        "id": "kwiatowa",
        "name": {
            "pl": "Kwiatowa",
            "en": "Kwiatowa",
            "de": "Kwiatowa"
        },
        "prefix": {
            "pl": "ulica",
            "en": "street",
            "de": "Straße"
        },
        "full_name": {
            "pl": "ulica Kwiatowa",
            "en": "Kwiatowa Street",
            "de": "Kwiatowa-Straße"
        },
        "literal_meaning": {
            "en": "Flower Street",
            "de": "Blumenstraße"
        },
        "district": {
            "pl": "Krowodrza",
            "en": "Krowodrza",
            "de": "Krowodrza"
        },
        "district_id": "V",
        "category": {
            "pl": "Przyroda i Roślinność",
            "en": "Flora & Nature",
            "de": "Natur & Flora"
        },
        "year": "1912",
        "length_meters": 210,
        "summary": {
            "pl": "Urokliwa uliczka w dzielnicy Krowodrza, powstała na terenach dawnych ogrodów podmiejskich.",
            "en": "Charming residential street in the Krowodrza district, developed on former suburban estate gardens.",
            "de": "Charmante Wohnstraße im Stadtteil Krowodrza, angelegt auf dem Gelände ehemaliger vorstädtischer Nutzgärten."
        },
        "street_type": "nature",
        "patron": None,
        "etymology": {
            "pl": "Nazwa o motywacji przyrodniczej, nadana w 1912 r. po włączeniu dawnej wsi Nowa Wieś Narodowa do Wielkiego Krakowa. Upamiętnia kwieciste ogrody warzywno-owocowe i sady podmiejskie, które dominowały w tym rejonie przed parcelacją pod zabudowę kamieniczną.",
            "en": "A botanical commemorative name established in 1912 following the incorporation of Nowa Wieś into Greater Kraków. It reflects the blooming orchards and suburban flower gardens that once covered the area before residential urban development.",
            "de": "Ein botanischer Straßenname aus dem Jahr 1912, vergeben nach der Eingemeindung von Nowa Wieś in Groß-Krakau. Er erinnert an die blühenden Obstgärten und ländlichen Gartenanlagen, die dieses Viertel vor der gründerzeitlichen Bebauung prägten."
        },
        "source": {
            "name": "E. Supranowicz, „Nazwy ulic Krakowa” (IJP PAN, 1995, ISBN 83-85579-48-6)",
            "url": None,
            "label": None
        },
        "resolution": {
            "has_resolution": False
        }
    },
    "geometry": {
        "type": "MultiLineString",
        "coordinates": temp_geom['kwiatowa']
    }
}

# 3. Wzbogacenie Floriańskiej o wielojęzyczność
if 'florianska' in features_by_id:
    p = features_by_id['florianska']['properties']
    p['name'] = {"pl": "Floriańska", "en": "Floriańska", "de": "Floriańska"}
    p['full_name'] = {"pl": "ulica Floriańska", "en": "Floriańska Street", "de": "Floriańska-Straße"}
    p['literal_meaning'] = {"en": "St. Florian's Street", "de": "Floriansgasse"}
    p['district'] = {"pl": "Stare Miasto", "en": "Old Town", "de": "Altstadt"}
    p['category'] = {"pl": "Historia i Patroni", "en": "History & Patrons", "de": "Geschichte & Patrone"}
    p['etymology'] = {
        "pl": p['etymology'] if isinstance(p['etymology'], str) else p['etymology']['pl'],
        "en": "Laid out in 1257 as part of the charter of Kraków. The street takes its name from St. Florian's Gate and the medieval collegiate church of St. Florian in Kleparz, forming the core of the Royal Road leading to Wawel Castle.",
        "de": "Angelegt 1257 im Zuge der Stadterweiterung. Benannt nach dem Florianstor und der St.-Florians-Kirche auf dem Kleparz. Die Straße bildete den Beginn des berühmten Krakauer Königswegs hinauf zum Wawel."
    }
    if p.get('patron'):
        p['patron']['role'] = {
            "pl": "rzymski oficer, męczennik wczesnochrześcijański i święty patron m.in. strażaków i Krakowa (ok. 250–304 n.e.)",
            "en": "Roman officer, early Christian martyr, and patron saint of firefighters and Kraków (c. 250–304 AD)",
            "de": "römischer Offizier, frühchristlicher Märtyrer und Schutzpatron der Feuerwehr und Krakaus (ca. 250–304 n. Chr.)"
        }

# 4. Wzbogacenie Szymborskiej o wielojęzyczność
if 'szymborskiej' in features_by_id:
    p = features_by_id['szymborskiej']['properties']
    p['name'] = {"pl": "Wisławy Szymborskiej", "en": "Wisława Szymborska", "de": "Wisława Szymborska"}
    p['full_name'] = {"pl": "Park im. Wisławy Szymborskiej", "en": "Wisława Szymborska Park", "de": "Wisława-Szymborska-Park"}
    p['literal_meaning'] = {"en": "Wisława Szymborska Park", "de": "Wisława-Szymborska-Park"}
    p['district'] = {"pl": "Stare Miasto", "en": "Old Town", "de": "Altstadt"}
    p['category'] = {"pl": "Literatura i Poezja", "en": "Literature & Poetry", "de": "Literatur & Poesie"}
    if p.get('patron'):
        p['patron']['role'] = {
            "pl": "polska poetka, eseistka, tłumaczka i laureatka Nagrody Nobla w dziedzinie literatury (1923–2012)",
            "en": "Polish poet, essayist, translator, and 1996 Nobel Prize laureate in Literature (1923–2012)",
            "de": "polnische Dichterin, Essayistin und Literaturnobelpreisträgerin 1996 (1923–2012)"
        }

# 5. Wzbogacenie Lema o wielojęzyczność
if 'lema' in features_by_id:
    p = features_by_id['lema']['properties']
    p['name'] = {"pl": "Stanisława Lema", "en": "Stanisław Lem", "de": "Stanisław Lem"}
    p['full_name'] = {"pl": "ulica Stanisława Lema", "en": "Stanisław Lem Street", "de": "Stanisław-Lem-Straße"}
    p['district'] = {"pl": "Czyżyny / Grzegórzki", "en": "Czyżyny / Grzegórzki", "de": "Czyżyny / Grzegórzki"}
    p['category'] = {"pl": "Literatura i Futurologia", "en": "Literature & Futurology", "de": "Literatur & Futurologie"}
    if p.get('patron'):
        p['patron']['role'] = {
            "pl": "pisarz science-fiction, filozof, futurolog i eseista (1921–2006)",
            "en": "world-renowned science fiction writer, philosopher, and futurologist (1921–2006)",
            "de": "weltbekannter Science-Fiction-Schriftsteller, Philosoph und Zukunftsforscher (1921–2006)"
        }

# 6. Wzbogacenie Słowackiego o wielojęzyczność
if 'slowackiego' in features_by_id:
    p = features_by_id['slowackiego']['properties']
    p['name'] = {"pl": "Juliusza Słowackiego", "en": "Juliusz Słowacki", "de": "Juliusz Słowacki"}
    p['full_name'] = {"pl": "aleja Juliusza Słowackiego", "en": "Juliusz Słowacki Avenue", "de": "Juliusz-Słowacki-Allee"}
    p['district'] = {"pl": "Stare Miasto / Krowodrza", "en": "Old Town / Krowodrza", "de": "Altstadt / Krowodrza"}
    p['category'] = {"pl": "Literatura i Romantyzm", "en": "Literature & Romanticism", "de": "Literatur & Romantik"}
    if p.get('patron'):
        p['patron']['role'] = {
            "pl": "jeden z Najwybitniejszych Polskich Poetów Romantycznych, wieszcz narodowy (1809–1849)",
            "en": "one of the greatest Polish Romantic poets and national bards (1809–1849)",
            "de": "einer der bedeutendsten polnischen Dichter der Romantik und Nationalbarde (1809–1849)"
        }

# 7. Wzbogacenie Dietla o wielojęzyczność
if 'dietla' in features_by_id:
    p = features_by_id['dietla']['properties']
    p['name'] = {"pl": "Józefa Dietla", "en": "Józef Dietl", "de": "Józef Dietl"}
    p['full_name'] = {"pl": "ulica Józefa Dietla", "en": "Józef Dietl Street", "de": "Józef-Dietl-Straße"}
    p['district'] = {"pl": "Stare Miasto / Kazimierz", "en": "Old Town / Kazimierz", "de": "Altstadt / Kazimierz"}
    p['category'] = {"pl": "Prezydenci i Medycyna", "en": "Mayors & Medicine", "de": "Bürgermeister & Medizin"}
    if p.get('patron'):
        p['patron']['role'] = {
            "pl": "lekarz, profesor i rektor UJ, prezydent Krakowa, twórca krakowskich Plant Dietlowskich (1804–1878)",
            "en": "physician, professor and rector of Jagiellonian University, Mayor of Kraków (1804–1878)",
            "de": "Mediziner, Professor und Rektor der Jagiellonen-Universität, Bürgermeister von Krakau (1804–1878)"
        }

# 8. Ulice bezpatronowe: Grodzka, Szeroka, Mogilska
if 'grodzka' in features_by_id:
    p = features_by_id['grodzka']['properties']
    p['literal_meaning'] = {"en": "Castle / Citadel Road", "de": "Burgstraße"}
    p['patron'] = None
    p['category'] = {"pl": "Trakt Królewski", "en": "Royal Route", "de": "Königsweg"}

if 'szeroka' in features_by_id:
    p = features_by_id['szeroka']['properties']
    p['literal_meaning'] = {"en": "Broad / Wide Street", "de": "Breite Gasse"}
    p['patron'] = None
    p['category'] = {"pl": "Dziedzictwo Żydowskie", "en": "Jewish Heritage", "de": "Jüdisches Erbe"}

if 'mogilska' in features_by_id:
    p = features_by_id['mogilska']['properties']
    p['literal_meaning'] = {"en": "Road to Mogiła Abbey", "de": "Mogiła-Straße"}
    p['patron'] = None
    p['category'] = {"pl": "Dawne Trakty", "en": "Historic Trade Routes", "de": "Historische Fernwege"}

# Złożenie ostatecznej listy
all_features = [szewska_feat, kwiatowa_feat]
for f in sample_data['features']:
    if f['properties']['id'] not in ['szewska', 'kwiatowa']:
        all_features.append(f)

output_data = {
    "type": "FeatureCollection",
    "features": all_features
}

with open('data/streets_sample.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"Sukces: zapisano {len(all_features)} ulic w data/streets_sample.json")
