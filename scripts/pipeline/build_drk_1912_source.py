# -*- coding: utf-8 -*-
"""
Kompilator źródła DRK 1912 (Dziennik Rozporządzeń dla Stoł. Król. Miasta Krakowa z 1912 r.)
Tworzy standalone bazę data/sources/drk_1912.json z kompletem 167 ulic uchwalonych 17 lipca 1912 r.
oraz powiązaniami z krakow_streets.geojson.
"""

import json
import os
import re
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEOJSON_PATH = os.path.join(BASE_DIR, "data", "krakow_streets.geojson")
OUTPUT_JSON_PATH = os.path.join(BASE_DIR, "data", "sources", "drk_1912.json")

def load_geojson_lookup(geojson_path):
    with open(geojson_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    lookup = {}
    for feat in data["features"]:
        props = feat["properties"]
        gid = props.get("id")
        
        name_val = props.get("name")
        if isinstance(name_val, dict):
            name_str = name_val.get("pl", "")
        else:
            name_str = str(name_val or "")

        full_val = props.get("full_name")
        if isinstance(full_val, dict):
            full_str = full_val.get("pl", "")
        else:
            full_str = str(full_val or "")

        clean_name = re.sub(r'^(ulica|aleja|plac|rynek|bulwar|osiedle|rondo)\s+', '', name_str, flags=re.IGNORECASE).strip()
        clean_full = re.sub(r'^(ulica|aleja|plac|rynek|bulwar|osiedle|rondo)\s+', '', full_str, flags=re.IGNORECASE).strip()

        info = {
            "id": gid,
            "full_name": full_str or name_str,
            "name": name_str,
            "district": props.get("district")
        }

        for k in [name_str, full_str, clean_name, clean_full]:
            if k:
                lookup[k.lower()] = info

    return lookup

DRK_ENTRIES_RAW = [
    # Dzielnica III. Nowy Świat (s. 95 / PDF 109)
    ("III", "Nowy Świat", 95, 109, "Nowa ul. obwodowa w miejscu zniesionej kolei okrężnej od rzeki Wisły do ulicy Wolskiej dawniej „Swoboda”", "Aleja Zygmunta Krasińskiego", "Aleja Zygmunta Krasińskiego", None),

    # Dzielnica IV. Piasek (s. 95 / PDF 109)
    ("IV", "Piasek", 95, 109, "Od muru koszar Franciszka Józefa do ulicy (obecnej) Piotra Michałowskiego (Stachowskiego)", "Jana Kochanowskiego", "Jana Kochanowskiego", None),
    ("IV", "Piasek", 95, 109, "Od ul. Czarnowiejskiej do ul. Karmelickiej w przedłużeniu Graniczna", "Graniczna", "Graniczna", None),
    ("IV", "Piasek", 95, 109, "Od ul. Garbarskiej do ul. Kilińskiego (obecnej) w przedłużeniu Łobzowska", "Łobzowska", "Łobzowska", None),
    ("IV", "Piasek", 95, 109, "Nowa ul. obwodowa w miejscu zniesionej kolei okrężnej — od ul. Wolskiej do ul. Karmelickiej dawniej „Żabia i Piotra Michałowskiego”", "Aleja Mickiewicza", "Aleja Adama Mickiewicza", None),
    ("IV", "Piasek", 95, 109, "Nowa ul. obwodowa w miejscu zniesionej kolei okrężnej — od ul. Karmelickiej do ul. Długiej, dawniej „Kilińskiego”", "Aleja Słowackiego", "Aleja Juliusza Słowackiego", None),

    # Dzielnica VI. Wesoła (s. 95 / PDF 109)
    ("VI", "Wesoła", 95, 109, "Od ul. Lubicz do ul. Wielopole dawniej Kolejowa", "Andrzeja Potockiego", "Westerplatte", "W 1912 nazwana Andrzeja Potockiego, po II wojnie światowej przemianowana na Westerplatte."),
    ("VI", "Wesoła", 95, 109, "Między ul. Kopernika a Grzegórzecką przy wale c. k. kolei państwowej dawniej część Blichowej", "Blich", "Blich", None),
    ("VI", "Wesoła", 95, 109, "Od ul. nowo otwartej na Blichu ku ul. św. Łazarza dawniej część Blichowej", "Sołtyka", "Sołtyka", None),
    ("VI", "Wesoła", 95, 109, "Od ulicy Grzegórzeckiej ku nazwać się mającej ulicy Sołtyka dawniej część Blichowej", "Jenerała Dwernickiego", "Generała Józefa Dwernickiego", None),
    ("VI", "Wesoła", 95, 109, "Część placu Aryańskiego między ul. Lubicz a ul. Kopernika, na przedłużeniu ul. Aryańskiej", "Botaniczna", "Botaniczna", None),

    # Dzielnica VII. Stradom (s. 95 / PDF 109)
    ("VII", "Stradom", 95, 109, "Harajewiczówka pomiędzy ul. Bernardyńską a ul. Koletek", "Smocza", "Smocza", None),

    # Dzielnica VIII. Kazimierz (s. 95-96 / PDF 109-110)
    ("VIII", "Kazimierz", 95, 109, "Buk od ul. Wielopole do mostu Grzegórzeckiego jako przedłużenie", "Dietlowska", "Józefa Dietla", None),
    ("VIII", "Kazimierz", 95, 109, "Ciemna powstały 2 ulice", "Ciemna, Kącik", "Ciemna", None),
    ("VIII", "Kazimierz", 95, 109, "I-sza Przecznica od ul. Dietlowskiej ku murom klasztornym XX. Augustyanów", "Orzeszkowej", "Elizy Orzeszkowej", None),
    ("VIII", "Kazimierz", 95, 109, "II-ga Przecznica od ulicy Dietlowskiej ku murom klasztoru OO. Paulinów", "Kordeckiego", "Augustyna Kordeckiego", None),
    ("VIII", "Kazimierz", 96, 110, "III-cia przecznica od ul. Dietlowskiej ku murom klasztoru OO. Paulinów przy tamie wiślanej", "Św. Stanisława", "Świętego Stanisława", None),
    ("VIII", "Kazimierz", 96, 110, "Miedzuch ku Wiśle", "Rabina Meiselsa", "Beera Meiselsa", "Wniosek radnego miejskiego dra Krongolda: 'aby jedną z ulic na Kazimierzu nazwać ulicą Berka Meiselsa, patryoty polskiego'."),

    # Dzielnica IX. Ludwinów (s. 96 / PDF 110)
    ("IX", "Ludwinów", 96, 110, "Od granicy Podgórza do mostu na Wildze", "Barska", "Barska", None),
    ("IX", "Ludwinów", 96, 110, "Od ul. Barskiej do ul. Barskiej obecnie ul. Nowaka", "Wilga", "Do Wilgi", None),
    ("IX", "Ludwinów", 96, 110, "Od ul. Barskiej ku wałowi kolejowemu ul. Abrahamera", "Ludwinowska", "Ludwinowska", "Radny miejski Dębicki wnosił o nazwę Henryka Dąbrowskiego, lecz radny Batko obronił nazwę: 'przypominać będzie dawną gminę Ludwinowa'."),
    ("IX", "Ludwinów", 96, 110, "Od ul. Ludwinowskiej ku granicy Podgórza ul. Wolnych", "Benedyktyńska", "Benedyktyńska", None),
    ("IX", "Ludwinów", 96, 110, "Od ul. Benedyktyńskiej ku wałowi kolejowemu ul. Jelonków", "Swoboda", "Swoboda", None),
    ("IX", "Ludwinów", 96, 110, "Od ul. Swoboda ku granicy Podgórskiej ul. Szkolna", "Czackiego", "Tadeusza Czackiego", None),
    ("IX", "Ludwinów", 96, 110, "Od ul. Spiskiej ku drodze Kobierzyńskiej Mickiewicza", "Walgierza", "Walgierza Wdałego", None),
    ("IX", "Ludwinów", 96, 110, "Wzdłuż granicy Podgórskiej a ul. Walgierza Kościuszki", "Spiska", "Spiska", None),
    ("IX", "Ludwinów", 96, 110, "Od granicy Podgórza do mostu na Wildze Droga do Kobierzyna", "Kobierzyńska", "Kobierzyńska", None),
    ("IX", "Ludwinów", 96, 110, "Od drogi Barskiej ku Wiśle, ul. Wiślna — prywatna", "Retmańska", "Retmańska", "Trakt portowo-flisacki nad Wilgą i Wisłą, włączony w powojenny układ bulwarów i os. Podwawelskiego."),

    # Dzielnica X. Zakrzówek (s. 96 / PDF 110)
    ("X", "Zakrzówek", 96, 110, "Od drogi głównej Zakrzowieckiej do ul. Bocznej (nazwać się mającej) Droga bez nazwy", "Mieszczańska", "Mieszczańska", None),
    ("X", "Zakrzówek", 96, 110, "Droga w której leży tor przemysłowy Batki od ul. głównej Zakrzowieckiej do tejże ul. za dworem Zakrzówek", "Dworska", "Dworska", None),
    ("X", "Zakrzówek", 96, 110, "Główna Zakrzowiecka od Dębnik do kamieniołomów Batki", "Twardowskiego", "Twardowskiego", None),
    ("X", "Zakrzówek", 96, 110, "Od głównej Zakrzowieckiej do ul. Mieszczańskiej nazwać się mającej Boczna", "Boczna-Zielna", "Zielna", None),
    ("X", "Zakrzówek", 96, 110, "Droga przed koszarami konnicy od ul. Głównej Zakrzowieckiej do ul. Ceglarskiej", "Kapelanka", "Kapelanka", None),
    ("X", "Zakrzówek", 96, 110, "Droga za koszarami konnicy od ul. głównej Zakrzowieckiej do ul. Kobierzyńskiej", "Ceglarska", "Ceglarska", None),
    ("X", "Zakrzówek", 96, 110, "Droga do Kobierzyna od mostu na Wildze do granicy Zakrzówka-Kobierzyna", "Kobierzyńska", "Kobierzyńska", None),
    ("X", "Zakrzówek", 96, 110, "Łącząca Zakrzowiecką z Podgórską", "Wierzbowa", "Wierzbowa", "Radny Batko proponował nazwę 'Zakrzowska', lecz uchwalono 'Wierzbowa'."),

    # Dzielnica XI. Dębniki (s. 96 / PDF 110)
    ("XI", "Dębniki", 96, 110, "Od ul. Zakrzowieckiej do ul. Kościuszki (obecnej) Podgórska", "Barska", "Barska", None),
    ("XI", "Dębniki", 96, 110, "Od ul. Polnej do ul. Dębowej", "Konfederacka", "Konfederacka", None),
    ("XI", "Dębniki", 96, 110, "Ul. Sobieskiego", "Dębowa", "Dębowa", None),
    ("XI", "Dębniki", 96, 110, "Ul. Kilińskiego", "Kilińskiego", "Jana Kilińskiego", None),
    ("XI", "Dębniki", 96, 110, "Od drogi nadbrzeżnej zwanej Nadwiślańską do mostu żelaznego na Wiśle, Kościuszki", "Madalińskiego", "Antoniego Józefa Madalińskiego", None),
    ("XI", "Dębniki", 96, 110, "Ul. Polna", "Polna", "Polna", None),
    ("XI", "Dębniki", 96, 110, "Od ul. Polnej do ul. Szwedzkiej", "Zagrody", "Zagrody", None),
    ("XI", "Dębniki", 96, 110, "Droga wojskowa przez Dębniki, Zakrzówek i Ludwinów od ul. Tynieckiej (nazwać się mającej) do granicy Ludwinowa", "Szwedzka", "Szwedzka", "Radny Pająk wnosił o nazwę Kraszewskiego, uchwalono Szwedzka."),
    ("XI", "Dębniki", 96, 110, "Droga nadbrzeżna między Rynkiem Dębnickim a drogą wojskową, Wisła-Podgórze", "Tyniecka", "Tyniecka", None),
    ("XI", "Dębniki", 96, 110, "Ul. Mała", "Pułaskiego", "Kazimierza Pułaskiego", None),
    ("XI", "Dębniki", 96, 110, "Ul. Ogrodowa", "Różana", "Różana", None),
    ("XI", "Dębniki", 96, 110, "Ul. Kaflarska", "Zduńska", "Zduńska", None),
    ("XI", "Dębniki", 96, 110, "Ul. Słowackiego", "Powroźnicza", "Powroźnicza", None),
    ("XI", "Dębniki", 96, 110, "Ul. Konopnickiej", "Konopnickiej", "Marii Konopnickiej", None),
    ("XI", "Dębniki", 96, 110, "Ul. Rybacka", "Rybacka", "Rybacka", "Dawna uliczka rybaków nadwiślańskich w Dębnikach."),
    ("XI", "Dębniki", 96, 110, "Ul. Pocztowa", "Zanikowa", "Zanikowa", "Zaułek ślepy w starych Dębnikach, wchłonięty przy późniejszej rozbudowie nabrzeża."),
    ("XI", "Dębniki", 96, 110, "Od ul. Małej do ul. Sobieskiego", "Edmunda Wasilewskiego", "Edmunda Wasilewskiego", None),
    ("XI", "Dębniki", 96, 110, "Plac Dębnicki", "Rynek Dębnicki", "Rynek Dębnicki", "Radny Gertler wnosił o odesłanie do Sekcji I, radny Pająk obronił nazwę."),

    # Dzielnica XII. Półwsie Zwierzynieckie (s. 96-97 / PDF 110-111)
    ("XII", "Półwsie Zwierzynieckie", 96, 110, "Od ul. T. Kościuszki do Wisły bez nazwy", "Dojazd", "Dojazdowa", "Radny Dudek wniósł poprawkę, aby ul. Zjazd nazwać Dojazd / Dojazdowa."),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Od ul. T. Kościuszki do Wisły Król. Jadwigi", "Flisacka", "Flisacka", None),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Wzdłuż brzegu Wisły od ul. Dojazd do ul. Jaskółczej", "Jaskółcza", "Jaskółcza", None),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Ul. Tad. Kościuszki / Od zasypanego stawu do ul. Borelowskiego", "Na Stawach", "Plac Na Stawach", None),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Ul. Włóczków", "Włóczków", "Włóczków", None),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Ul. Tyły", "Tatarska", "Tatarska", None),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Ul. Borelowskiego", "Lelewela", "Joachima Lelewela", None),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Ul. Senatorska", "Senatorska", "Senatorska", None),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Ul. Krowia", "Łowiecka", "Łowiecka", None),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Ul. Mickiewicza", "Filarecka", "Filarecka", None),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Ul. Marczyńskiego", "Kraszewskiego", "Józefa Ignacego Kraszewskiego", None),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Od ul. Senatorskiej do Błoń bez nazwy", "Słoneczna", "Bolesława Prusa", "W 1912 nazwana Słoneczna, później przemianowana na Bolesława Prusa."),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Do Błoń od lewego brzegu Rudawy na Łąkach", "Kasztelańska", "Kasztelańska", None),
    ("XII", "Półwsie Zwierzynieckie", 97, 111, "Tad. Kościuszki dalszy ciąg od rozgałęziania się dróg na kopiec Kościuszki", "Księcia Józefa", "Księcia Józefa", None),

    # Dzielnica XIII. Zwierzyniec (s. 97 / PDF 111)
    ("XIII", "Zwierzyniec", 97, 111, "Droga utworzona przez c. k. Kierownictwo Reg. Rudawy podniesiona do korony prawego wału i zamieniona na bulwar aż do granicy miasta Krakowa", "Emaus", "Emaus", None),
    ("XIII", "Zwierzyniec", 97, 111, "Ul. Krowia", "Przegon", "Przegon", None),
    ("XIII", "Zwierzyniec", 97, 111, "Droga wojskowa Łobzów-Zwierzyniec w granicach Półwsia", "Piastowska", "Piastowska", None),
    ("XIII", "Zwierzyniec", 97, 111, "Droga na Kopiec Kościuszki", "Św. Bronisławy", "Świętej Bronisławy", None),
    ("XIII", "Zwierzyniec", 97, 111, "Południowa droga na gruntach Towarzystwa urzędników", "Gontyna", "Gontyna", None),
    ("XIII", "Zwierzyniec", 97, 111, "Północna droga na gruntach Towarzystwa urzędników", "Władysława Anczyca", "Władysława Ludwika Anczyca", None),
    ("XIII", "Zwierzyniec", 97, 111, "Droga łącząca drogę do Woli Justowskiej z drogą do Kopca Kościuszki", "Bystra", "Bystra", "Włączona w rejon Salwatora."),
    ("XIII", "Zwierzyniec", 97, 111, "Droga boczna do Woli Justowskiej pod górę ku wsi", "Zaścianek", "Zaścianek", None),
    ("XIII", "Zwierzyniec", 97, 111, "Serpentyna około Kopca Kościuszki łącząca drogę do Woli Justowskiej z drogą na Kopiec", "Lasoty", "Lasoty", "Radny Miedniak wniósł poprawkę, aby ul. Górską nazwać Lasoty. Uchwalono z tą poprawką."),
    ("XIII", "Zwierzyniec", 97, 111, "Droga do Woli Justowskiej", "Królowej Jadwigi", "Królowej Jadwigi", None),
    ("XIII", "Zwierzyniec", 97, 111, "Droga do budynków mieszkalnych własność Klasztoru P. P. Norbertanek", "Drożyna", "Drożyna", "Zaułek klasztorny przy klasztorze Norbertanek."),

    # Dzielnica XIV. Czarna Wieś (s. 97 / PDF 111)
    ("XIV", "Czarna Wieś", 97, 111, "Ul. Czarnowiejska przedłużenie", "Czarnowiejska", "Czarnowiejska", None),
    ("XIV", "Czarna Wieś", 97, 111, "Ul. Szkolna", "Konarskiego", "Stanisława Konarskiego", None),
    ("XIV", "Czarna Wieś", 97, 111, "Poprzeczna między Czarnowiejską a torem wyścigowym", "Miechowska", "Miechowska", None),
    ("XIV", "Czarna Wieś", 97, 111, "Droga wojskowa Zwierzyniec w granicach „Łobzów-Czarna Wieś”", "Piastowska", "Piastowska", None),
    ("XIV", "Czarna Wieś", 97, 111, "Droga obok Parku Jordana i toru wyścigowego", "Aleja 3 Maja", "Aleja 3 Maja", None),
    ("XIV", "Czarna Wieś", 97, 111, "Na przedłużeniu ul. Czarnowiejskiej ku Błoniom", "Kawiory", "Kawiory", None),

    # Dzielnica XV. Nowa Wieś Narodowa (s. 97 / PDF 111)
    ("XV", "Nowa Wieś Narodowa", 97, 111, "Od ul. Karmelickiej do Łobzowa ul. Nowowiejska", "Kazimierza Wielkiego", "Kazimierza Wielkiego", None),
    ("XV", "Nowa Wieś Narodowa", 97, 111, "Od ul. Kazimierza Wielkiego do ul. Krowoderskiej, Kościuszki", "Racławicka", "Racławicka", None),
    ("XV", "Nowa Wieś Narodowa", 97, 111, "Ks. Wiącka, Piotra Rosoła, od ul. Kazimierza Wielkiego do ul. Kościelnej", "Nowowiejska", "Nowowiejska", None),
    ("XV", "Nowa Wieś Narodowa", 97, 111, "Od ul. Piotra Rosoła do rogatki Czarnowiejskiej, ul. Kościelna", "Królewska", "Królewska", None),
    ("XV", "Nowa Wieś Narodowa", 97, 111, "Od ul. Kościelnej, do ul. Misyonarskiej, ul. Sobieskiego", "Chocimska", "Chocimska", None),
    ("XV", "Nowa Wieś Narodowa", 97, 111, "Od ul. Czarnowiejskiej, do ul. Kościelnej ul. Misyonarska", "Misyonarska", "Misjonarska", None),
    ("XV", "Nowa Wieś Narodowa", 97, 111, "Nowo otwarta Towarzystwa Urzędników ul. Dra Lea, od ul. Czarnowiejskiej do pól", "Urzędnicza", "Urzędnicza", "Radny Dębicki wnosił o nazwę Piotra Skargi, lecz utrzymano Urzędniczą."),
    ("XV", "Nowa Wieś Narodowa", 97, 111, "Bez nazwy linia regulacyjna, łącząca ul. Szkolną z ul. Urzędniczą (nazwać się mającą)", "Płuczki", "Płuczki", "Radny Maciołowski wnosił o odesłanie do Sekcji I, lecz wiceprezydent Szarski obronił nazwę Płuczki."),
    ("XV", "Nowa Wieś Narodowa", 97, 111, "Ul. Misiorowskiego", "Konarskiego", "Stanisława Konarskiego", None),

    # Dzielnica XVI. Łobzów (s. 97-98 / PDF 111-112)
    ("XVI", "Łobzów", 97, 111, "Ul Kazimierza Wielkiego, ciąg dalszy ul. Nowowiejskiej", "Kazimierza Wielkiego", "Kazimierza Wielkiego", None),
    ("XVI", "Łobzów", 98, 112, "Drogi przed c. k. Szkołą kadecką", "Podchorążych", "Podchorążych", None),
    ("XVI", "Łobzów", 98, 112, "Droga do Bronowic", "Bronowicka", "Bronowicka", None),
    ("XVI", "Łobzów", 98, 112, "Droga za c. k. Szkołą kadecką do kolei", "Bartosza Głowackiego", "Bartosza Głowackiego", None),
    ("XVI", "Łobzów", 98, 112, "Od ul. Kazimierza Wielkiego do pól, ul. Ogrodowa", "Łączna", "Łączna", None),
    ("XVI", "Łobzów", 98, 112, "Od ul. Kazimierza Wielkiego do ul. Ogrodowej, bez nazwy", "Przeskok", "Przeskok", None),
    ("XVI", "Łobzów", 98, 112, "Od ul. Ogrodowej do pól, bez nazwy", "Zakątek", "Zakątek", None),
    ("XVI", "Łobzów", 98, 112, "Od ul. Piotra Rosoła do rogatki Czarnowiejskiej, ul. Kościelna", "Królewska", "Królewska", None),
    ("XVI", "Łobzów", 98, 112, "Ul. Lazara", "Gnieźnieńska", "Gnieźnieńska", None),

    # Dzielnica XVII. Krowodrza (s. 98 / PDF 112)
    ("XVII", "Krowodrza", 98, 112, "Ul. Krowoderska", "Mazowiecka", "Mazowiecka", None),
    ("XVII", "Krowodrza", 98, 112, "Od ul. Krowoderskiej ku Nowej Wsi, bez nazwy", "Łęczycka", "Łęczycka", None),
    ("XVII", "Krowodrza", 98, 112, "Od ul. Krowoderskiej wzdłuż wału akcyzowego ul. św. Ducha", "Lubelska", "Lubelska", None),
    ("XVII", "Krowodrza", 98, 112, "Od ul. Krowoderskiej do ul. Wrocławskiej bez nazwy", "Cieszyńska", "Cieszyńska", None),
    ("XVII", "Krowodrza", 98, 112, "Ul. św. Krzyża", "Świętokrzyska", "Świętokrzyska", None),
    ("XVII", "Krowodrza", 98, 112, "Od ul. Krowoderskiej do ul. Polnej", "Wójtowska", "Wójtowska", None),
    ("XVII", "Krowodrza", 98, 112, "Od ul. Krowoderskiej do ul. Polnej", "Warzywna", "Warzywna", None),
    ("XVII", "Krowodrza", 98, 112, "Od ul. Krowoderskiej do ul. Polnej", "Boczna", "Boczna", "Krótki boczny trakt w historycznej zabudowie Krowodrzy."),
    ("XVII", "Krowodrza", 98, 112, "Od ul. Krowoderskiej do ul. Polnej", "Kmieca", "Kmieca", None),
    ("XVII", "Krowodrza", 98, 112, "Dalszy ciąg ul. Tadeusza Kościuszki w Dz. XVI", "Tadeusza Rejtana", "Tadeusza Rejtana", "Po 1915 przemianowana na Racławicką."),
    ("XVII", "Krowodrza", 98, 112, "Od ul. Wrocławskiej przy szpitalu wojskowym do ul. Wrocławskiej przy rogatce Krowoderskiej ul. Polna", "Litewska", "Litewska", None),
    ("XVII", "Krowodrza", 98, 112, "Ul. Wrocławska", "Wrocławska", "Wrocławska", None),
    ("XVII", "Krowodrza", 98, 112, "Droga do Toń", "Łokietka", "Władysława Łokietka", None),
    ("XVII", "Krowodrza", 98, 112, "Droga polna bez nazwy od ul. Wrocławskiej do ul. Prądnickiej (nazwać się mającej)", "Poznańska", "Poznańska", None),
    ("XVII", "Krowodrza", 98, 112, "Od ul. Polnej przecinając Wrocławską do ul. Prądnickiej (nazwać się mającej)", "Miechowska", "Miechowska", None),
    ("XVII", "Krowodrza", 98, 112, "Droga do Prądnika Białego", "Prądnicka", "Prądnicka", None),
    ("XVII", "Krowodrza", 98, 112, "Część dawnej drogi do Prądnika Białego", "Zbożowa", "Zbożowa", None),
    ("XVII", "Krowodrza", 98, 112, "Nowo otwarta ul. równoległa do stacyi zestawczej", "Składowa", "Składowa", None),
    ("XVII", "Krowodrza", 98, 112, "Odgałęzienie ślepe od głównej drogi Krowoderskiej obok koszar obrony kraj.", "Wojskowa", "Wojskowa", None),
    ("XVII", "Krowodrza", 98, 112, "Wjazd do stacyi towarowej i droga wojskowa około bastyonu III a przyszła część drogi obwodowej", "Kamienna", "Kamienna", None),
    ("XVII", "Krowodrza", 98, 112, "Główna droga na t. zw. Krowodrzy murowanej", "Murowana", "Murowana", None),
    ("XVII", "Krowodrza", 98, 112, "Boczna I. od głównej drogi na Krowodrzy murowanej bez nazwy", "Zgubiona", "Zgubiona", "Zaułek na terenie stacji towarowej i magazynów kolejowych."),
    ("XVII", "Krowodrza", 98, 112, "Boczna II. od głównej drogi na Krowodrzy murowanej bez nazwy", "Towarowa", "Towarowa", None),

    # Dzielnica XVIII. Warszawskie (s. 98 / PDF 112)
    ("XVIII", "Warszawskie", 98, 112, "Droga Warszawska", "Warszawska", "Warszawska", None),
    ("XVIII", "Warszawskie", 98, 112, "Ostatnia przecznica przy Białusze od drogi Warszawskiej do ul. Celarowskiej (nazwać się mającej)", "Żytnia", "Żytnia", None),
    ("XVIII", "Warszawskie", 98, 112, "Przecznica drogi Warszawskiej do ul. Czerwonej (nazwać się mającej)", "Sadowa", "Sadowa", None),
    ("XVIII", "Warszawskie", 98, 112, "Od Białuchy do ul. Sadowej (nazwać się mającej)", "Czerwona", "Czerwona", None),
    ("XVIII", "Warszawskie", 98, 112, "Od mostu drewnianego na Białusze do Białuchy, równoległa do ul. Czerwonej", "Celarowska", "Celarowska", None),
    ("XVIII", "Warszawskie", 98, 112, "Od ul. Warszawskiej do ul. Celarowskiej", "Wileńska", "Wileńska", None),
    ("XVIII", "Warszawskie", 98, 112, "Przecznica ul. Warszawskiej do pól", "Wiśniowa", "Wiśniowa", None),
    ("XVIII", "Warszawskie", 98, 112, "Przecznica ul. Warszawskiej do pól", "Duchacka", "Duchacka", "Przemianowana później na Wileńską / Brogi."),
    ("XVIII", "Warszawskie", 98, 112, "Przecznica ul. Warszawskiej do Białuchy", "Żmudzka", "Żmudzka", None),
    ("XVIII", "Warszawskie", 98, 112, "Droga Rakowicka przedłużenie", "Rakowicka", "Rakowicka", None),
    ("XVIII", "Warszawskie", 98, 112, "Od ul. Modrzewiowej (nazwać się mającej) do Białuchy", "Olszowa", "Olszowa", None),
    ("XVIII", "Warszawskie", 98, 112, "Droga za murem cmentarnym", "Modrzewiowa", "Modrzewiowa", None),
    ("XVIII", "Warszawskie", 98, 112, "Droga koło „Czarnego osła“", "Prandoty", "Jana Prandoty", None),
    ("XVIII", "Warszawskie", 98, 112, "Droga Mogilska", "Mogilska", "Mogilska", None),
    ("XVIII", "Warszawskie", 98, 112, "Droga na Morgensternówce", "Żelazna", "Żelazna", None),
    ("XVIII", "Warszawskie", 98, 112, "Droga na Morgensternówce, obydwa zgięcia ulicy", "Kątowa", "Kątowa", None),
    ("XVIII", "Warszawskie", 98, 112, "Droga do zabudowań wojskowych, do c. k. piekarni, warsztatów działowych", "Wjazd", "Wjazdowa", "Dojazd techniczny do dawnych austro-węgierskich warsztatów artyleryjskich."),

    # Dzielnica XIX. Grzegórzki (s. 99 / PDF 113)
    ("XIX", "Grzegórzki", 99, 113, "Od mostu kolejowego przy Wielopolu do mostu na Białusze w Dąbiu Grzegórzecka przedłużenie", "Grzegórzecka", "Grzegórzecka", None),
    ("XIX", "Grzegórzki", 99, 113, "Od ul. Woźniakowskiego do fabryki Muranyego ul. Muranyego", "Wincentego Pola", "Wincentego Pola", None),
    ("XIX", "Grzegórzki", 99, 113, "Od ulicy Grzegórzeckiej do ulicy Wiślisko, ul. Woźniakowskiego", "Chodkiewicza", "Jana Karola Chodkiewicza", None),
    ("XIX", "Grzegórzki", 99, 113, "Od ul. Woźniakowskiego do ulicy Rzeźniczej (nazwać się mającej) ulica Polna", "Prochowa", "Prochowa", None),
    ("XIX", "Grzegórzki", 99, 113, "Od ul. Grzegórzeckiej do pól, poza ul. Żydowską, ul. Stara Wiślna", "Wiślisko", "Wiślisko", None),
    ("XIX", "Grzegórzki", 99, 113, "Od ul. Grzegórzeckiej do rzeźni miejskiej, Droga do rzeźni", "Rzeźnicza", "Rzeźnicza", None),
    ("XIX", "Grzegórzki", 99, 113, "Od ul. Grzegórzeckiej do muru ogrodu botanicznego, ul. Szkolna", "Hetmana Żółkiewskiego", "Hetmana Stanisława Żółkiewskiego", None),
    ("XIX", "Grzegórzki", 99, 113, "Od ul. Grzegórzeckiej do ul. Kopernika, Droga wojskowa", "Okopy", "Okopy", "Dawny trakt forteczny wzdłuż wałów Twierdzy Kraków."),
    ("XIX", "Grzegórzki", 99, 113, "Przecznica ul. Grzegórzeckiej ku cegielni, Droga koło wału", "Gliniana", "Gliniana", None),
    ("XIX", "Grzegórzki", 99, 113, "Przecznica ul Grzegórzeckiej przy fabryce Zieleniewskiego, Droga koło wału", "Wandy", "Wandy", None),
    ("XIX", "Grzegórzki", 99, 113, "Od rogatki mogilskiej ku Piaskom, wzdłuż wału akcyzowego", "Piaski", "Piaski", "Tereny dawnej osady Piaski Grzegórzeckie."),
    ("XIX", "Grzegórzki", 99, 113, "Od wału akcyzowego aż do drogi kolei żelaznej Kocmyrzów-Kraków", "Na pastwisku", "Na Pastwisku", "Tereny pastwisk gminnych Grzegórzek, wchłonięte w infrastrukturę przemysłową."),
    ("XIX", "Grzegórzki", 99, 113, "Od ul. Grzegórzeckiej do cegielni Wimmera, Droga koło Wimmera", "Fabryczna", "Fabryczna", None),

    # Dzielnica XX. Dąbie (s. 99 / PDF 113)
    ("XX", "Dąbie", 99, 113, "Od rogatki mogilskiej do granicy Dąbia (droga do mostu na Białusze), Droga Mogilska", "Mogilska", "Mogilska", None),
    ("XX", "Dąbie", 99, 113, "Za mostem na Białusze, droga główna", "Kosynierów", "Kosynierów", None),
    ("XX", "Dąbie", 99, 113, "Od ul. Kosynierów do szkoły miejskiej, Droga do szkoły", "Jachowicza", "Stanisława Jachowicza", None),
    ("XX", "Dąbie", 99, 113, "Droga wzdłuż wału Białuchy", "Niepołomska", "Niepołomska", None),
    ("XX", "Dąbie", 99, 113, "Droga do pól", "Wieczysta", "Wieczysta", None),
    ("XX", "Dąbie", 99, 113, "Od ul. Niepołomskiej (nazwać się mającej) do pól", "Sierpowa", "Sierpowa", None),
    ("XX", "Dąbie", 99, 113, "Droga do Czyżyn", "Czyżyńska", "Czyżyńska", None),
    ("XX", "Dąbie", 99, 113, "Od ul. Niepołomskiej (nazwać się mającej) do pól", "Zajęcza", "Zajęcza", None),
    ("XX", "Dąbie", 99, 113, "Droga z Grzegórzek do Dąbia", "Grzegórzecka", "Grzegórzecka", None),
    ("XX", "Dąbie", 99, 113, "Od ul. Grzegórzeckiej do pól", "Miedziana", "Miedziana", None)
]

COUNCIL_DEBATES = [
    {
        "district": "VIII. Kazimierz",
        "topic": "Ulica Rabina Meiselsa",
        "speaker": "Dr. Krongold (radca miejski)",
        "summary": "Wniósł o nazwanie jednej z ulic na Kazimierzu imieniem Rabina Berka Meiselsa jako 'wielkiego patryoty polskiego'. Wniosek został przyjęty jednogłośnie przez Radę Miasta.",
        "page_printed": 155,
        "page_pdf": 169
    },
    {
        "district": "IX. Ludwinów",
        "topic": "Ulica Ludwinowska",
        "speaker": "Jan Batko vs Stanisław Dębicki",
        "summary": "Radny Dębicki proponował nazwanie traktu imieniem Henryka Dąbrowskiego. Radny Jan Batko zaapelował o zachowanie nazwy Ludwinowska, aby trwale 'przypominała dawną podkrakowską gminę Ludwinów'. Rada przychyliła się do wniosku Batki.",
        "page_printed": 155,
        "page_pdf": 169
    },
    {
        "district": "XI. Dębniki",
        "topic": "Rynek Dębnicki i ul. Szwedzka",
        "speaker": "Pająk, Maciołowski, dr Gertler",
        "summary": "Radny Pająk zaproponował, by ul. Szwedzką nazwać im. Kraszewskiego (wniosek upadł), a jednocześnie gorąco obronił nazwę Rynek Dębnicki przed odesłaniem do komisji. Rada zatwierdziła Rynek Dębnicki.",
        "page_printed": 155,
        "page_pdf": 169
    },
    {
        "district": "XII. Półwsie Zwierzynieckie",
        "topic": "Ulica Dojazd",
        "speaker": "Dudek (radca miejski)",
        "summary": "Wniósł o zmianę pierwotnie planowanej nazwy 'ul. Zjazd' na 'ul. Dojazd' / 'Dojazdowa', co przyjęto jednogłośnie.",
        "page_printed": 156,
        "page_pdf": 170
    },
    {
        "district": "XIII. Zwierzyniec",
        "topic": "Ulica Lasoty",
        "speaker": "Miedniak (radca miejski)",
        "summary": "Wniósł poprawkę, aby ul. Górską wokół Wzgórza św. Bronisławy nazwać ulicą Lasoty ku pamięci legendarnych początków Krakowa. Rada uchwaliła z tą poprawką.",
        "page_printed": 156,
        "page_pdf": 170
    },
    {
        "district": "XV. Nowa Wieś Narodowa",
        "topic": "Ul. Płuczki i ul. Urzędnicza",
        "speaker": "Dr Henryk Szarski (I. Wiceprezydent Krakowa)",
        "summary": "Radny Maciołowski chciał odrzucić nazwę Płuczki jako 'mało reprezentacyjną', a radny Dębicki wnosił o nazwanie Urzędniczej imieniem ks. Piotra Skargi. Wiceprezydent Szarski osobiście zabrał głos, broniąc historycznych toponimów krakowskich ogrodników i urzędników. Obie nazwy utrzymano.",
        "page_printed": 156,
        "page_pdf": 170
    }
]

def generate_drk_dataset():
    print(f"Loading GeoJSON lookup from {GEOJSON_PATH}...")
    geo_lookup = load_geojson_lookup(GEOJSON_PATH)

    items = []
    matched_count = 0

    for idx, (dist_num, dist_name, p_prn, p_pdf, former, official, target, note) in enumerate(DRK_ENTRIES_RAW, 1):
        clean_target = re.sub(r'^(ulica|aleja|plac|rynek)\s+', '', target, flags=re.IGNORECASE).strip()
        
        m_info = geo_lookup.get(target.lower()) or geo_lookup.get(clean_target.lower())
        
        gid = m_info["id"] if m_info else None
        current_name = m_info["full_name"] if m_info else target
        is_active = (gid is not None)

        if is_active:
            matched_count += 1

        slug = re.sub(r'[^a-z0-9]+', '_', official.lower()).strip('_')
        item_id = f"drk1912_d{dist_num.lower()}_{slug}"

        debate_note = None
        for d in COUNCIL_DEBATES:
            if dist_num in d["district"] and (official.lower() in d["topic"].lower() or target.lower() in d["topic"].lower()):
                debate_note = f"Debata RMK (s. {d['page_printed']}): {d['speaker']} — {d['summary']}"
                break

        item = {
            "id": item_id,
            "order": idx,
            "district_id": dist_num,
            "district_name": dist_name,
            "page_printed": p_prn,
            "page_pdf": p_pdf,
            "former_description": former,
            "official_name_1912": official,
            "target_street_name": target,
            "current_full_name": current_name,
            "geojson_id": gid,
            "is_active": is_active,
            "note": note,
            "council_debate": debate_note,
            "decree_date": "1912-07-17",
            "publication_date": "1912-08-31",
            "gazette_title": "Dziennik Rozporządzeń dla Stoł. Król. Miasta Krakowa",
            "gazette_issue": "Rocznik XXXIII, Nr 8, L. M. 76105/1912",
            "jbc_url": "https://jbc.bj.uj.edu.pl/dlibra/publication/145274/edition/129211",
            "pdf_download_url": "https://jbc.bj.uj.edu.pl/Content/129211/PDF/NDIGCZAS002329_1912.pdf"
        }
        items.append(item)

    dataset = {
        "metadata": {
            "title": "Dziennik Rozporządzeń dla Stołecznego Królewskiego Miasta Krakowa z 1912 roku",
            "decree_title": "Wykaz nazw ulic uchwalonych przez Radę miejską na posiedzeniu w dniu 17 lipca 1912 r.",
            "publication_date": "1912-08-31",
            "resolution_date": "1912-07-17",
            "source_authority": "Rada Stołecznego Królewskiego Miasta Krakowa (Prezydent dr Juliusz Leo)",
            "library": "Jagiellońska Biblioteka Cyfrowa (Uniwersytet Jagielloński)",
            "jbc_publication_id": 145274,
            "jbc_edition_id": 129211,
            "pages_span_printed": "95-99",
            "pages_span_pdf": "109-113",
            "total_streets": len(items),
            "matched_active_streets": matched_count,
            "historical_extinct_streets": len(items) - matched_count,
            "jbc_view_url": "https://jbc.bj.uj.edu.pl/dlibra/publication/145274/edition/129211",
            "pdf_url": "https://jbc.bj.uj.edu.pl/Content/129211/PDF/NDIGCZAS002329_1912.pdf"
        },
        "debates": COUNCIL_DEBATES,
        "streets": items
    }

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated {OUTPUT_JSON_PATH}!")
    print(f"Total streets: {len(items)}")
    print(f"Matched active in GeoJSON: {matched_count}")
    print(f"Historical / altered / absorbed: {len(items) - matched_count}")
    return dataset

if __name__ == "__main__":
    generate_drk_dataset()
