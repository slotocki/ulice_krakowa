# -*- coding: utf-8 -*-
import json

with open('data/streets_sample.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for feat in data['features']:
    p = feat['properties']
    pid = p['id']

    if pid == 'szymborskiej':
        p['name'] = {"pl": "Wisławy Szymborskiej", "en": "Wisława Szymborska", "de": "Wisława Szymborska"}
        p['full_name'] = {"pl": "Park im. Wisławy Szymborskiej", "en": "Wisława Szymborska Park", "de": "Wisława-Szymborska-Park"}
        p['literal_meaning'] = {"en": "Wisława Szymborska Memorial Park", "de": "Wisława-Szymborska-Park"}
        p['district'] = {"pl": "Stare Miasto", "en": "Old Town", "de": "Altstadt"}
        p['category'] = {"pl": "Literatura i Poezja", "en": "Literature & Poetry", "de": "Literatur & Poesie"}
        p['summary'] = {
            "pl": "Zielona przestrzeń literacka przy ul. Karmelickiej 26 z instalacjami poetyckimi i alejami spacerowymi.",
            "en": "Literary green park at 26 Karmelicka Street featuring poetic art installations and walking promenades.",
            "de": "Literarische Parkanlage in der Karmelicka-Straße 26 mit poetischen Installationen und Spazierwegen."
        }
        p['etymology'] = {
            "pl": "Park miejski i aleja spacerowa powstały na terenie dawnego parkingu przy ul. Karmelickiej dzięki wieloletniej inicjatywie mieszkańców w Krakowskim Budżecie Obywatelskim. Nazwę nadano oficjalnie w 100-lecie urodzin noblistki dla uczczenia jej twórczości i trwałego związku z Krakowem.",
            "en": "A modern urban park and promenade created on the site of a former parking lot on Karmelicka Street through a civic initiative in Kraków's Participatory Budget. Officially named on the centennial of the Nobel laureate's birth to honor her poetry and lifelong bond with Kraków.",
            "de": "Ein moderner Stadtpark und Flanierweg, der auf dem Areal eines ehemaligen Parkplatzes in der Karmelicka-Straße durch eine Bürgerinitiative im Bürgerhaushalt entstand. Offiziell zum 100. Geburtstag der Nobelpreisträgerin benannt, um ihr literarisches Schaffen und ihre tiefe Verbundenheit mit Krakau zu würdigen."
        }
        if p.get('patron'):
            p['patron']['name'] = "Wisława Szymborska"
            p['patron']['role'] = {
                "pl": "polska poetka, eseistka, tłumaczka, laureatka Nagrody Nobla w dziedzinie literatury z 1996 r. (1923–2012)",
                "en": "celebrated Polish poet, essayist, translator, and 1996 Nobel Prize laureate in Literature (1923–2012)",
                "de": "bedeutende polnische Dichterin, Essayistin, Übersetzerin und Literaturnobelpreisträgerin von 1996 (1923–2012)"
            }

    elif pid == 'lema':
        p['name'] = {"pl": "Stanisława Lema", "en": "Stanisław Lem", "de": "Stanisław Lem"}
        p['full_name'] = {"pl": "ulica Stanisława Lema", "en": "Stanisław Lem Street", "de": "Stanisław-Lem-Straße"}
        p['literal_meaning'] = {"en": "Stanisław Lem Street", "de": "Stanisław-Lem-Straße"}
        p['district'] = {"pl": "Czyżyny / Grzegórzki", "en": "Czyżyny / Grzegórzki", "de": "Czyżyny / Grzegórzki"}
        p['category'] = {"pl": "Literatura i Futurologia", "en": "Literature & Futurology", "de": "Literatur & Futurologie"}
        p['summary'] = {
            "pl": "Łączy al. Pokoju z al. Jana Pawła II, przebiegając obok Tauron Areny i Parku Lotników Polskich.",
            "en": "Connects Pokoju Avenue with Jana Pawła II Avenue, running past Tauron Arena and Polish Aviators Park.",
            "de": "Verbindet die Pokoju-Allee mit der Jana-Pawła-II-Allee und führt an der Tauron Arena sowie dem Park der Polnischen Flieger vorbei."
        }
        p['etymology'] = {
            "pl": "Ulica została wytyczona i nazwana w 2007 roku w celu uhonorowania Stanisława Lema – światowej sławy pisarza science-fiction i myśliciela, który przez ponad pół wieku mieszkał i tworzył w Krakowie. W pobliżu ulicy znajduje się również Ogród Doświadczeń noszący jego imię.",
            "en": "Laid out and named in 2007 to honor Stanisław Lem – world-renowned science fiction writer, philosopher, and futurologist who lived and worked in Kraków for over half a century. Nearby stands the Garden of Experiments named after him.",
            "de": "Im Jahr 2007 angelegt und benannt zu Ehren von Stanisław Lem – weltberühmter Science-Fiction-Schriftsteller, Philosoph und Zukunftsforscher, der über ein halbes Jahrhundert in Krakau lebte und wirkte. In der Nähe befindet sich der nach ihm benannte Garten der Experimente."
        }
        if p.get('patron'):
            p['patron']['name'] = "Stanisław Lem"
            p['patron']['role'] = {
                "pl": "światowej sławy pisarz science-fiction, filozof, futurolog i eseista (1921–2006)",
                "en": "world-renowned science fiction writer, philosopher, futurologist, and essayist (1921–2006)",
                "de": "weltbekannter Science-Fiction-Schriftsteller, Philosoph, Futurolooge und Essayist (1921–2006)"
            }

    elif pid == 'slowackiego':
        p['name'] = {"pl": "Juliusza Słowackiego", "en": "Juliusz Słowacki", "de": "Juliusz Słowacki"}
        p['full_name'] = {"pl": "aleja Juliusza Słowackiego", "en": "Juliusz Słowacki Avenue", "de": "Juliusz-Słowacki-Allee"}
        p['literal_meaning'] = {"en": "Juliusz Słowacki Avenue", "de": "Juliusz-Słowacki-Allee"}
        p['district'] = {"pl": "Stare Miasto / Krowodrza", "en": "Old Town / Krowodrza", "de": "Altstadt / Krowodrza"}
        p['category'] = {"pl": "Literatura i Romantyzm", "en": "Literature & Romanticism", "de": "Literatur & Romantik"}
        p['summary'] = {
            "pl": "Główna arteria zachodniej części Alei Trzech Wieszczów, wytyczona wzdłuż dawnego nasypu kolei cyrkumwalacyjnej.",
            "en": "Main artery of the western Three Bards Avenues, laid out along the former circular railway embankment.",
            "de": "Hauptverkehrsachse der Drei-Barden-Alleen, angelegt entlang des ehemaligen Eisenbahn-Rings."
        }
        p['etymology'] = {
            "pl": "Wytyczona na początku XX wieku po zlikwidowaniu wałów Twierdzy Kraków i likwidacji torowiska kolei obwodowej. W 1912 r. uroczyście nadano jej imię Juliusza Słowackiego w ramach reprezentacyjnych Alei Trzech Wieszczów, obok alei Mickiewicza i Krasińskiego.",
            "en": "Laid out in the early 20th century after dismantling the Austrian Fortress Kraków ramparts and circular railway tracks. In 1912, it was named after Juliusz Słowacki as part of the grand Three Bards Avenues, alongside Mickiewicz and Krasiński avenues.",
            "de": "Zu Beginn des 20. Jahrhunderts nach dem Rückbau der Festungswälle und der Eisenbahntrasse angelegt. 1912 feierlich nach Juliusz Słowacki benannt als Teil der repräsentativen Alleen der Drei Barden neben Mickiewicz und Krasiński."
        }

    elif pid == 'dietla':
        p['name'] = {"pl": "Józefa Dietla", "en": "Józef Dietl", "de": "Józef Dietl"}
        p['full_name'] = {"pl": "ulica Józefa Dietla", "en": "Józef Dietl Street", "de": "Józef-Dietl-Straße"}
        p['literal_meaning'] = {"en": "Józef Dietl Boulevard", "de": "Józef-Dietl-Straße"}
        p['district'] = {"pl": "Stare Miasto / Kazimierz", "en": "Old Town / Kazimierz", "de": "Altstadt / Kazimierz"}
        p['category'] = {"pl": "Prezydenci i Medycyna", "en": "Mayors & Medicine", "de": "Bürgermeister & Medizin"}
        p['summary'] = {
            "pl": "Szeroka aleja plantowa powstała w latach 1878–1880 w miejscu zasypanego koryta Starej Wisły.",
            "en": "Broad green boulevard created between 1878 and 1880 on the filled-in bed of the Old Vistula river.",
            "de": "Breiter grüner Boulevard, angelegt 1878–1880 auf dem zugeschütteten Flussbett der Alten Weichsel."
        }
        p['etymology'] = {
            "pl": "Powstała po zasypaniu koryta Starej Wisły w latach 1878–1880. Nazwana na cześć prof. Józefa Dietla, wybitnego lekarza, rektora UJ i prezydenta Krakowa, który był głównym inicjatorem tej fundamentalnej dla higieny i rozwoju miasta inwestycji.",
            "en": "Created after filling in the stagnant Old Vistula riverbed in 1878–1880. Named in honor of Prof. Józef Dietl, distinguished physician, rector of Jagiellonian University, and Mayor of Kraków, who spearheaded this crucial public health reform.",
            "de": "Entstanden nach der Zuschüttung des Altarms der Weichsel 1878–1880. Benannt nach Prof. Józef Dietl, bedeutender Arzt, Rektor der Jagiellonen-Universität und Bürgermeister Krakaus, der Initiator dieses städtebaulichen Meilensteins war."
        }

with open('data/streets_sample.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Pomyślnie zaktualizowano wszystkie tłumaczenia w data/streets_sample.json!")
