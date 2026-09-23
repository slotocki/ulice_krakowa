import json

def update_prl():
    fpath = 'data/sources/prl_1951_1955.json'
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for s in data['streets']:
        sid = s['id']
        if sid == 'prl1951_prl_18':
            s['district_id'] = 'IV'
            s['district_name'] = 'Krowodrza'
            s['former_description'] = 'ulica Grenadierów'
            s['official_name_1951'] = 'ulica Czerwonych Kosynierów'
            s['current_full_name'] = 'ulica Grenadierów'
            s['geojson_id'] = 'grenadierow'
            s['note'] = 'Nazwę tradycyjnej formacji wojskowej zastąpiono rewolucyjnymi kosynierami z 1848 i 1939 r.'
        elif sid == 'prl1951_prl_19':
            s['district_id'] = 'I'
            s['district_name'] = 'Kleparz'
            s['former_description'] = 'ulica Pędzichów'
            s['official_name_1951'] = 'ulica gen. Aleksandra Waszkiewicza'
            s['current_full_name'] = 'ulica Pędzichów'
            s['geojson_id'] = 'pedzichow'
            s['note'] = 'Średniowieczną nazwę jurydyki zastąpiono generałem Armii Radzieckiej i Wojska Polskiego poległym w 1945 r.'
        elif sid == 'prl1951_prl_21':
            s['district_id'] = 'I'
            s['district_name'] = 'Śródmieście'
            s['former_description'] = 'ulica Studencka'
            s['official_name_1951'] = 'ulica gen. Karola Świerczewskiego'
            s['current_full_name'] = 'ulica Studencka'
            s['geojson_id'] = 'studencka'
            s['note'] = 'Uniwersytecką nazwę zastąpiono generałem „Walterem” poległym pod Jabłonkami.'
        elif sid == 'prl1951_prl_22':
            s['district_id'] = 'I'
            s['district_name'] = 'Śródmieście'
            s['former_description'] = 'ulica Juliana Dunajewskiego'
            s['official_name_1951'] = 'ulica 1 Maja'
            s['current_full_name'] = 'ulica Juliana Dunajewskiego'
            s['geojson_id'] = 'juliana_dunajewskiego'
            s['note'] = 'Odcinek Plant miejskich przemianowano na cześć komunistycznego Święta Pracy.'
        elif sid == 'prl1951_prl_26':
            s['district_id'] = 'V'
            s['district_name'] = 'Krowodrza'
            s['former_description'] = 'ulica Kadrówki'
            s['official_name_1951'] = 'ulica Pawła Findera'
            s['current_full_name'] = 'ulica Kadrówki'
            s['geojson_id'] = 'kadrowki'
            s['note'] = 'Pamiątkę I Kompanii Kadrowej Józefa Piłsudskiego zastąpiono sekretarzem KC PPR.'
        elif sid == 'prl1951_prl_27':
            s['district_id'] = 'XIII'
            s['district_name'] = 'Podgórze'
            s['former_description'] = 'ulica Kalwaryjska'
            s['official_name_1951'] = 'ulica Wincentego Pstrowskiego'
            s['current_full_name'] = 'ulica Kalwaryjska'
            s['geojson_id'] = 'kalwaryjska'
            s['note'] = 'Główny historyczny trakt Podgórza przemianowano na cześć stachanowca i rębasa kopalni „Jadwiga”.'
        elif sid == 'prl1951_prl_28':
            s['district_id'] = 'II'
            s['district_name'] = 'Grzegórzki'
            s['former_description'] = 'aleja płk. Beliny-Prażmowskiego'
            s['official_name_1951'] = 'aleja Juliana Marchlewskiego'
            s['current_full_name'] = 'Aleja Pułkownika Władysława Beliny-Prażmowskiego'
            s['geojson_id'] = 'pulkownika_wladyslawa_beliny_prazmowskiego'
            s['note'] = 'Twórcę kawalerii legionowej zastąpiono działaczem Kominternu i SDKPiL.'
        elif sid == 'prl1951_prl_30':
            s['district_id'] = 'I'
            s['district_name'] = 'Kleparz'
            s['former_description'] = 'ulica Sereno Fenna'
            s['official_name_1951'] = 'ulica Stefana Jaracza'
            s['current_full_name'] = 'ulica Sereno Fenna'
            s['geojson_id'] = 'sereno_fenna'
            s['note'] = 'Amerykańskiego patrona i fundatora gmachu YMCA zastąpiono wybitnym polskim aktorem i reżyserem.'

    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print("Zaktualizowano prl_1951_1955.json")

def update_decom():
    fpath = 'data/sources/dekomunizacja_1991.json'
    with open(fpath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for s in data['streets']:
        sid = s['id']
        if sid == 'decom1991_decom_02':
            s['former_description'] = 'ulica Włodzimierza Majakowskiego'
            s['official_name_1991'] = 'ulica Karmelicka'
            s['current_full_name'] = 'ulica Karmelicka'
            s['geojson_id'] = 'karmelicka'
            s['note'] = 'Przywrócenie prastarej XIV-wiecznej nazwy od klasztoru Ojców Karmelitów (usunięto Majakowskiego).'
        elif sid == 'decom1991_decom_03':
            s['district_id'] = 'IV'
            s['district_name'] = 'IV Krowodrza / Prądnik Biały'
            s['former_description'] = 'ulica Aleksandra Zawadzkiego'
            s['official_name_1991'] = 'ulica gen. Augusta Fieldorfa „Nila”'
            s['current_full_name'] = 'ulica Generała Augusta Fieldorfa-Nila'
            s['geojson_id'] = 'generala_augusta_fieldorfa_nila'
            s['note'] = 'Usunięcie przewodniczącego Rady Państwa PRL; patronem gen. August Emil Fieldorf „Nil” – dowódca Kedywu AK.'
        elif sid == 'decom1991_decom_04':
            s['former_description'] = 'ulica 1 Maja'
            s['official_name_1991'] = 'ulica Juliana Dunajewskiego'
            s['current_full_name'] = 'ulica Juliana Dunajewskiego'
            s['geojson_id'] = 'juliana_dunajewskiego'
            s['note'] = 'Przywrócenie patronatu Juliana Dunajewskiego – rektora UJ i prezydenta Krakowa (usunięto 1 Maja).'
        elif sid == 'decom1991_decom_05':
            s['district_id'] = 'VI'
            s['district_name'] = 'VI Bronowice'
            s['former_description'] = 'ulica Obrońców Pokoju'
            s['official_name_1991'] = 'ulica Stanisława Balickiego'
            s['current_full_name'] = 'ulica Stanisława Balickiego'
            s['geojson_id'] = 'stanislawa_balickiego'
            s['note'] = 'Usunięcie propagandowej nazwy PRL; patron Stanisław Balicki (1863–1934) – działacz oświatowy i społeczny.'
        elif sid == 'decom1991_decom_07':
            s['former_description'] = 'ulica Ludwika Waryńskiego'
            s['official_name_1991'] = 'ulica św. Gertrudy'
            s['current_full_name'] = 'ulica św. Gertrudy'
            s['geojson_id'] = 'swietej_gertrudy'
            s['note'] = 'Przywrócenie historycznej nazwy od dawnego kościółka św. Gertrudy przy Plantach (usunięto Waryńskiego).'
        elif sid == 'decom1991_decom_08':
            s['district_id'] = 'VI'
            s['district_name'] = 'VI Bronowice'
            s['former_description'] = 'ulica Władysława Kniewskiego'
            s['official_name_1991'] = 'ulica Gustawa Daniłowskiego'
            s['current_full_name'] = 'ulica Gustawa Daniłowskiego'
            s['geojson_id'] = 'gustawa_danilowskiego'
            s['note'] = 'Usunięcie bojówkarza KPP; patron Gustaw Daniłowski – pisarz, działacz niepodległościowy i legionista.'
        elif sid == 'decom1991_decom_09':
            s['district_id'] = 'III'
            s['district_name'] = 'III Prądnik Czerwony'
            s['former_description'] = 'ulica Mariana Buczka'
            s['official_name_1991'] = 'ulica Nowogródzka'
            s['current_full_name'] = 'ulica Nowogródzka'
            s['geojson_id'] = 'nowogrodzka'
            s['note'] = 'Usunięcie działacza KPP; nadanie nazwy upamiętniającej polskie miasto kresowe Nowogródek.'
        elif sid == 'decom1991_decom_11':
            s['district_id'] = 'III'
            s['district_name'] = 'III Prądnik Czerwony'
            s['former_description'] = 'ulica Marcelego Nowotki'
            s['official_name_1991'] = 'ulica Jakuba Zachemskiego'
            s['current_full_name'] = 'ulica Jakuba Zachemskiego'
            s['geojson_id'] = 'jakuba_zachemskiego'
            s['note'] = 'Usunięcie I sekretarza PPR; patron Jakub Zachemski – podhalański pedagog, pisarz i folklorysta.'
        elif sid == 'decom1991_decom_12':
            s['district_id'] = 'XI'
            s['district_name'] = 'XI Podgórze Duchackie'
            s['former_description'] = 'ulica Franciszka Zubrzyckiego'
            s['official_name_1991'] = 'ulica Jana Sas-Zubrzyckiego'
            s['current_full_name'] = 'ulica Jana Sas-Zubrzyckiego'
            s['geojson_id'] = 'jana_sas_zubrzyckiego'
            s['note'] = 'Zastąpienie dowódcy GL wybitnym architektem, konserwatorem zabytków i profesorem Politechniki Lwowskiej.'
        elif sid == 'decom1991_decom_13':
            s['district_id'] = 'I'
            s['district_name'] = 'I Kazimierz'
            s['former_description'] = 'ulica Małgorzaty Fornalskiej'
            s['official_name_1991'] = 'ulica Hieronima Wietora'
            s['current_full_name'] = 'ulica Hieronima Wietora'
            s['geojson_id'] = 'hieronima_wietora'
            s['note'] = 'Usunięcie działaczki komunistycznej; patron Hieronim Wietor – wybitny renesansowy drukarz krakowski z XVI w.'
        elif sid == 'decom1991_decom_14':
            s['district_id'] = 'XI'
            s['district_name'] = 'XI Podgórze Duchackie'
            s['former_description'] = 'ulica Gwardii Ludowej'
            s['official_name_1991'] = 'ulica Walerego Sławka'
            s['current_full_name'] = 'ulica Walerego Sławka'
            s['geojson_id'] = 'walerego_slawka'
            s['note'] = 'Usunięcie formacji GL; patron Walery Sławek – trzykrotny premier II RP, marszałek Sejmu i bliski współpracownik Piłsudskiego.'
        elif sid == 'decom1991_decom_15':
            s['district_id'] = 'I'
            s['district_name'] = 'I Kleparz'
            s['former_description'] = 'ulica Marcina Borelowskiego'
            s['official_name_1991'] = 'ulica św. Filipa'
            s['current_full_name'] = 'ulica św. Filipa'
            s['geojson_id'] = 'swietego_filipa'
            s['note'] = 'Przywrócenie historycznej kleparskiej nazwy od kościoła św. Filipa i Jakuba.'
        elif sid == 'decom1991_decom_16':
            s['district_id'] = 'XVI'
            s['district_name'] = 'XVI Bieńczyce'
            s['former_description'] = 'ulica Karola Marksa'
            s['official_name_1991'] = 'ulica Ludźmierska'
            s['current_full_name'] = 'ulica Ludźmierska'
            s['geojson_id'] = 'ludzmierska'
            s['note'] = 'Usunięcie twórcy marksizmu; nadanie nazwy od sanktuarium Matki Boskiej Ludźmierskiej na Podhalu.'
        elif sid == 'decom1991_decom_17':
            s['district_id'] = 'VII'
            s['district_name'] = 'VII Zwierzyniec'
            s['former_description'] = 'ulica Georgija Dymitrowa'
            s['official_name_1991'] = 'ulica Klimka Bachledy'
            s['current_full_name'] = 'ulica Klimka Bachledy'
            s['geojson_id'] = 'klimka_bachledy'
            s['note'] = 'Usunięcie bułgarskiego działacza Kominternu; patron Klimek Bachleda – legendarny tatrzański przewodnik i ratownik TOPR.'
        elif sid == 'decom1991_decom_35':
            s['district_id'] = 'VI'
            s['district_name'] = 'VI Bronowice'
            s['former_description'] = 'ulica Róży Luksemburg'
            s['official_name_1991'] = 'ulica Księdza Ferdynanda Machaya'
            s['current_full_name'] = 'ulica Księdza Ferdynanda Machaya'
            s['geojson_id'] = 'ksiedza_ferdynanda_machaya'
            s['note'] = 'Usunięcie działaczki SDKPiL; patron ks. infułat Ferdynand Machay – działacz niepodległościowy na Orawie i proboszcz Kościoła Mariackiego.'

    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print("Zaktualizowano dekomunizacja_1991.json")

if __name__ == '__main__':
    update_prl()
    update_decom()
