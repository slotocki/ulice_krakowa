#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aktualizuje metadane w data/streets_sample.json z zachowaniem precyzyjnych geometrii OSM:
- Rozdzielenie patrona (z rolą, zdjęciem i linkiem do Wikipedii) od samej ulicy
- Usunięcie mylących sformułowań (np. wyjaśnienie roli Bolesława Wstydliwego w lokacji miasta)
- Działające linki do BIP z parametrem %26typ%3Du oraz do plików PDF
"""

import json

RICH_METADATA = {
    "lema": {
        "prefix": "ulica",
        "name": "Stanisława Lema",
        "full_name": "ulica Stanisława Lema",
        "district": "Czyżyny / Grzegórzki",
        "category": "Literatura / Nauka",
        "year": "2007",
        "length_meters": 1150,
        "summary": "Łączy al. Pokoju z al. Jana Pawła II, przebiegając obok Tauron Areny i Parku Lotników Polskich.",
        "etymology": "Ulica została wytyczona i nazwana w 2007 roku w celu uhonorowania Stanisława Lema – światowej sławy pisarza science-fiction i myśliciela, który przez ponad pół wieku mieszkał i tworzył w Krakowie. W pobliżu ulicy znajduje się również Ogród Doświadczeń noszący jego imię.",
        "patron": {
            "name": "Stanisław Lem",
            "role": "pisarz science-fiction, filozof, futurolog i eseista (1921–2006)",
            "image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/1/1b/Stanislaw_Lem_2_manually_dusted.jpg/330px-Stanislaw_Lem_2_manually_dusted.jpg",
            "wikipedia_url": "https://pl.wikipedia.org/wiki/Stanis%C5%82aw_Lem"
        },
        "resolution": {
            "has_resolution": True,
            "number": "Uchwała Nr XLVIII/1070/26",
            "organ": "Rada Miasta Krakowa",
            "date": "22 kwietnia 2026 r.",
            "bip_url": "https://www.bip.krakow.pl/?dok_id=167&sub_dok_id=167&sub=uchwala&query=id%3D29003%26typ%3Du",
            "pdf_url": "https://www.bip.krakow.pl/_inc/rada/uchwaly/show_pdf.php?id=144708",
            "search_bip_url": "https://www.bip.krakow.pl/?dok_id=166&sub_dok_id=166&sub=wyszukiwarkazq&kadencja_od=1&kadencja_do=9&query=typ%3Du&queryu=Lema",
            "official_basis": "Ulica dedykowana pamięci Stanisława Lema, Obywatela Honorowego Miasta Krakowa."
        }
    },
    "szymborskiej": {
        "prefix": "park miejski / aleja",
        "name": "Wisławy Szymborskiej",
        "full_name": "Park im. Wisławy Szymborskiej",
        "district": "Stare Miasto / Piasek",
        "category": "Literatura / Nobliści",
        "year": "2023",
        "length_meters": 220,
        "summary": "Zielona przestrzeń literacka przy ul. Karmelickiej 26 z instalacjami poetyckimi i alejami spacerowymi.",
        "etymology": "Park miejski i aleja spacerowa powstały na terenie dawnego parkingu przy ul. Karmelickiej dzięki inicjatywie mieszkańców w Budżecie Obywatelskim. Nazwę nadano oficjalnie w 100-lecie urodzin noblistki dla uczczenia jej twórczości i trwałego związku z Krakowem.",
        "patron": {
            "name": "Wisława Szymborska",
            "role": "wybitna poetka, eseistka, laureatka Nagrody Nobla w dziedzinie literatury (1923–2012)",
            "image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b3/Szymborska_2011_%282%29.jpg/330px-Szymborska_2011_%282%29.jpg",
            "wikipedia_url": "https://pl.wikipedia.org/wiki/Wis%C5%82awa_Szymborska"
        },
        "resolution": {
            "has_resolution": True,
            "number": "Uchwała Nr CXIII/3060/23",
            "organ": "Rada Miasta Krakowa",
            "date": "28 czerwca 2023 r.",
            "bip_url": "https://www.bip.krakow.pl/?dok_id=167&sub_dok_id=167&sub=uchwala&query=id%3D27176%26typ%3Du",
            "pdf_url": "https://www.bip.krakow.pl/_inc/rada/uchwaly/show_pdf.php?id=131772",
            "search_bip_url": "https://www.bip.krakow.pl/?dok_id=166&sub_dok_id=166&sub=wyszukiwarkazq&kadencja_od=1&kadencja_do=9&query=typ%3Du&queryu=Szymborsk",
            "official_basis": "Nadanie Parkowi Miejskiemu nazwy Park im. Wisławy Szymborskiej, określenie granic Parku oraz przyjęcie regulaminu Parku w 100. rocznicę urodzin Poetki."
        }
    },
    "florianska": {
        "prefix": "ulica",
        "name": "Floriańska",
        "full_name": "ulica Floriańska",
        "district": "Stare Miasto",
        "category": "Historia / Szlak Królewski",
        "year": "1257",
        "length_meters": 335,
        "summary": "Początek Drogi Królewskiej (Via Regia), łączący Rynek Główny z Bramą Floriańską.",
        "etymology": "Wytyczona podczas lokacji Krakowa w 1257 r. Nazwa ma charakter kierunkowy – była to droga wiodąca w stronę kościoła św. Floriana na Kleparzu przez Bramę Floriańską. Jest to jedna z najstarszych niezmienionych nazw ulicznych w Europie.",
        "patron": {
            "name": "św. Florian",
            "role": "rzymski oficer, wczesnochrześcijański męczennik, patron Krakowa, strażaków i hutników",
            "image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2f/St_Florian_statue.jpg/330px-St_Florian_statue.jpg",
            "wikipedia_url": "https://pl.wikipedia.org/wiki/Florian_(m%C4%99czennik)"
        },
        "resolution": {
            "has_resolution": False,
            "era": "Średniowiecze (Lokacja miasta w 1257 r.)",
            "monarch_context": "Książę Bolesław V Wstydliwy nadał Krakowowi akt lokacyjny na prawie magdeburskim, w którym wytyczono geometryczny układ ulic i Rynku.",
            "source_title": "Kodeks Dyplomatyczny Miasta Krakowa / E. Supranowicz 'Nazwy ulic Krakowa' (PAN, 1995)",
            "source_url": "https://rcin.org.pl/dlibra/publication/20560",
            "historical_explanation": "Brak współczesnej uchwały RMK – nazwa funkcjonuje nieprzerwanie od ponad 750 lat na mocy prawa lokacyjnego."
        }
    },
    "grodzka": {
        "prefix": "ulica",
        "name": "Grodzka",
        "full_name": "ulica Grodzka",
        "district": "Stare Miasto",
        "category": "Historia / Trakt Królewski",
        "year": "Przedlokacyjna (XI/XII w.)",
        "length_meters": 540,
        "summary": "Najstarszy krakowski trakt handlowy wiodący z Rynku Głównego na Wawel.",
        "etymology": "Nazwa pochodzi wprost od słowa 'gród' – był to trakt biegnący z północy ku obwarowanemu grodowi książęcemu i królewskiemu na wzgórzu wawelskim. Stanowiła oś dawnej osady przedlokacyjnej Okół.",
        "patron": None,
        "resolution": {
          "has_resolution": False,
          "era": "Początki XII w. (Okres przedlokacyjny)",
          "monarch_context": "Trakt handlowy Szlaku Bursztynowego z czasów pierwszych Piastów.",
          "source_title": "Najstarsze księgi miejskie Krakowa / E. Supranowicz (PAN, 1995)",
          "source_url": "https://rcin.org.pl/dlibra/publication/20560",
          "historical_explanation": "Nazwa ugruntowana tysiącletnią tradycją miejską."
        }
    },
    "dietla": {
        "prefix": "ulica",
        "name": "Józefa Dietla",
        "full_name": "ulica Józefa Dietla",
        "district": "Stare Miasto / Kazimierz",
        "category": "Medycyna / Prezydenci Krakowa",
        "year": "1879",
        "length_meters": 1380,
        "summary": "Szeroka aleja plantowa w miejscu zasypanego koryta Starej Wisły.",
        "etymology": "Powstała po zasypaniu w latach 1878–1880 północnego ramienia Wisły, które oddzielało Kraków od Kazimierza. Rada Miasta nadała ulicy imię zmarłego prezydenta Dietla w dowód wdzięczności za doprowadzenie do modernizacji sanitarnej miasta.",
        "patron": {
            "name": "Józef Dietl",
            "role": "lekarz balneolog, rektor Uniwersytetu Jagiellońskiego, prezydent Krakowa (1866–1874)",
            "image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d4/J%C3%B3zef_Dietl.jpg/330px-J%C3%B3zef_Dietl.jpg",
            "wikipedia_url": "https://pl.wikipedia.org/wiki/J%C3%B3zef_Dietl"
        },
        "resolution": {
          "has_resolution": False,
          "era": "Autonomia Galicyjska (1879 r.)",
          "monarch_context": "Uchwała Rady Miejskiej Krakowa podjęta w czasach cesarza Franciszka Józefa I.",
          "source_title": "Akta miejskie Krakowa z 1879 r. / E. Supranowicz (PAN 1995)",
          "source_url": "https://rcin.org.pl/dlibra/publication/20560",
          "historical_explanation": "Uhonorowanie prezydenta Dietla za uporządkowanie gospodarki wodno-ściekowej Krakowa."
        }
    },
    "slowackiego": {
        "prefix": "aleja",
        "name": "Juliusza Słowackiego",
        "full_name": "aleja Juliusza Słowackiego",
        "district": "Krowodrza / Stare Miasto",
        "category": "Literatura / Wieszczowie",
        "year": "1912",
        "length_meters": 1780,
        "summary": "Część Alei Trzech Wieszczów, główna arteria obwodowa śródmieścia Krakowa.",
        "etymology": "Wytyczona na miejscu dawnych austriackich wałów twierdzy Kraków i zlikwidowanej kolei obwodowej. Nazwa nadana na pamiątkę stulecia urodzin wieszcza i sprowadzenia jego prochów do Katedry Wawelskiej.",
        "patron": {
            "name": "Juliusz Słowacki",
            "role": "jeden z Trzech Wieszczów, wielki poeta polskiego romantyzmu i dramaturg (1809–1849)",
            "image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/60/Juliusz_S%C5%82owacki.PNG/330px-Juliusz_S%C5%82owacki.PNG",
            "wikipedia_url": "https://pl.wikipedia.org/wiki/Juliusz_S%C5%82owacki"
        },
        "resolution": {
          "has_resolution": False,
          "era": "Przełom XIX i XX w. (1912 r.)",
          "monarch_context": "Decyzja Rady Miejskiej z 1912 r. związana z realizacją planu Wielkiego Krakowa.",
          "source_title": "Dziennik Rozporządzeń dla Stoł. Król. Miasta Krakowa, 1912",
          "source_url": "https://rcin.org.pl/dlibra/publication/20560",
          "historical_explanation": "Nazwa historyczna nadana z okazji sprowadzenia prochów poety do Krypty Wieszczów na Wawelu."
        }
    },
    "szeroka": {
        "prefix": "ulica / plac",
        "name": "Szeroka",
        "full_name": "ulica Szeroka",
        "district": "Kazimierz",
        "category": "Historia / Dziedzictwo Żydowskie",
        "year": "XV w.",
        "length_meters": 260,
        "summary": "Serce dawnego Miasta Żydowskiego na Kazimierzu (Oppidum Judaeorum) ze Starą Synagogą.",
        "etymology": "Nazwa ma charakter topograficzny – plac ma nietypowy, wydłużony wrzecionowaty kształt dawnego rynku targowego wsi Bawół, zanim włączono ją w mury Kazimierza.",
        "patron": None,
        "resolution": {
          "has_resolution": False,
          "era": "Późne Średniowiecze (XV wiek)",
          "monarch_context": "Władze miejskie Kazimierza i król Jan Olbracht (wydzielenie dzielnicy żydowskiej w 1495 r.).",
          "source_title": "Księgi miejskie kazimierskie / E. Supranowicz (PAN, 1995)",
          "source_url": "https://rcin.org.pl/dlibra/publication/20560",
          "historical_explanation": "Średniowieczna nazwa placu targowego osady żydowskiej."
        }
    },
    "mogilska": {
        "prefix": "ulica",
        "name": "Mogilska",
        "full_name": "ulica Mogilska",
        "district": "Grzegórzki",
        "category": "Historia / Toponim",
        "year": "XIX w. (trakt od XIII w.)",
        "length_meters": 1650,
        "summary": "Historyczny trakt handlowy łączący rondo Mogilskie z Nową Hutą i opactwem Cystersów.",
        "etymology": "Nazwa kierunkowa od dawnej wsi Mogiła (dziś część Nowej Huty), gdzie od 1222 roku istnieje opactwo oo. Cystersów. Nazwa Mogiła wg krakowskiej legendy odnosi się do kurhanu córki księcia Kraka – Wandy.",
        "patron": None,
        "resolution": {
          "has_resolution": False,
          "era": "Tradycja od XIII w. (włączona do Krakowa w 1912 r.)",
          "monarch_context": "Biskup Iwo Odrowąż (założyciel opactwa w Mogile w 1222 r.).",
          "source_title": "Urzędowy wykaz ulic i placów miasta Krakowa (1912)",
          "source_url": "https://rcin.org.pl/dlibra/publication/20560",
          "historical_explanation": "Starodawny trakt wylotowy na wschód ku Mogile i Sandomierzowi."
        }
    }
}

def main():
    with open("data/streets_sample.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    for feature in data["features"]:
        sid = feature["properties"]["id"]
        if sid in RICH_METADATA:
            meta = RICH_METADATA[sid]
            # Zachowujemy geometrię!
            feature["properties"]["prefix"] = meta["prefix"]
            feature["properties"]["name"] = meta["name"]
            feature["properties"]["full_name"] = meta["full_name"]
            feature["properties"]["district"] = meta["district"]
            feature["properties"]["category"] = meta["category"]
            feature["properties"]["year"] = meta["year"]
            feature["properties"]["length_meters"] = meta["length_meters"]
            feature["properties"]["summary"] = meta["summary"]
            feature["properties"]["etymology"] = meta["etymology"]
            feature["properties"]["patron"] = meta["patron"]
            feature["properties"]["resolution"] = meta["resolution"]

    with open("data/streets_sample.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("[SUKCES] Zaktualizowano metadane w data/streets_sample.json!")

if __name__ == "__main__":
    main()
