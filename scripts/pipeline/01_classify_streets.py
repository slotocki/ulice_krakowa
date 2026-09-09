# -*- coding: utf-8 -*-
import json
import re

INPUT_FILE = 'data/krakow_street_names.json'
OUTPUT_FILE = 'data/streets_classified.json'

PREFIXES_MAP = {
    'aleja ': 'aleja', 'al. ': 'aleja', 'plac ': 'plac', 'pl. ': 'plac',
    'osiedle ': 'osiedle', 'os. ': 'osiedle', 'rondo ': 'rondo',
    'skwer ': 'skwer', 'bulwar ': 'bulwar', 'ulica ': 'ulica', 'ul. ': 'ulica',
    'droga ': 'droga', 'zaułek ': 'zaułek', 'rynek ': 'rynek', 'park ': 'park'
}

TITLE_PREFIXES = {
    'św.': 'Święty', 'sw.': 'Święty', 'świętego': 'Święty', 'świętej': 'Święta',
    'bł.': 'Błogosławiony', 'błogosławionego': 'Błogosławiony', 'błogosławionej': 'Błogosławiona',
    'gen.': 'Generał', 'generała': 'Generał', 'marsz.': 'Marszałek', 'marszałka': 'Marszałek',
    'płk.': 'Pułkownik', 'płk': 'Pułkownik', 'pułkownika': 'Pułkownik',
    'ppłk.': 'Podpułkownik', 'podpułkownika': 'Podpułkownik',
    'mjr.': 'Major', 'mjr': 'Major', 'majora': 'Major',
    'por.': 'Porucznik', 'por': 'Porucznik', 'porucznika': 'Porucznik',
    'kpt.': 'Kapitan', 'kpt': 'Kapitan', 'kapitana': 'Kapitan',
    'prof.': 'Profesor', 'profesora': 'Profesor',
    'dr.': 'Doktor', 'dr': 'Doktor', 'doktora': 'Doktor', 'dra': 'Doktor', 'doc.': 'Docent',
    'inż.': 'Inżynier', 'inżyniera': 'Inżynier',
    'króla': 'Król', 'królowej': 'Królowa', 'księcia': 'Książę', 'księżnej': 'Księżna',
    'ks.': 'Ksiądz', 'księdza': 'Ksiądz', 'bpa': 'Biskup', 'biskupa': 'Biskup',
    'abpa': 'Arcybiskup', 'arcybiskupa': 'Arcybiskup', 'kard.': 'Kardynał', 'kardynała': 'Kardynał',
    'o.': 'Ojciec', 'ojca': 'Ojciec', 'brata': 'Brat', 'siostry': 'Siostra',
    'hetm.': 'Hetman', 'hetmana': 'Hetman', 'prezydenta': 'Prezydent', 'senatora': 'Senator',
    'admiralska': 'Admirał', 'admirała': 'Admirał', 'rotmistrza': 'Rotmistrz', 'rtm.': 'Rotmistrz',
    'redaktora': 'Redaktor', 'red.': 'Redaktor', 'mecenasa': 'Mecenas', 'mec.': 'Mecenas',
    'mistrza': 'Mistrz', 'artysty': 'Artysta', 'poety': 'Poeta', 'pisarza': 'Pisarz'
}

FIRST_NAMES_GENITIVE_TO_NOMINATIVE = {
    'adama': 'Adam', 'adolfa': 'Adolf', 'adriana': 'Adrian', 'alberta': 'Albert',
    'albina': 'Albin', 'aleksandra': 'Aleksander', 'aleksandry': 'Aleksandra',
    'alfonsa': 'Alfons', 'alfreda': 'Alfred', 'aliny': 'Alina', 'alojzego': 'Alojzy',
    'ambrożego': 'Ambroży', 'anastazego': 'Anastazy', 'anatola': 'Anatol',
    'andrzeja': 'Andrzej', 'andrieja': 'Andriej', 'anieli': 'Aniela',
    'ani': 'Ania', 'anusi': 'Anusia', 'anny': 'Anna', 'antoniego': 'Antoni',
    'apolinarego': 'Apolinary', 'arkadiusza': 'Arkadiusz',
    'artura': 'Artur', 'augusta': 'August', 'augustyna': 'Augustyn',
    'baltazara': 'Baltazar', 'barbary': 'Barbara', 'bartosza': 'Bartosz',
    'bartłomieja': 'Bartłomiej', 'bazylego': 'Bazyli', 'beaty': 'Beata',
    'benedykta': 'Benedykt', 'bernarda': 'Bernard', 'błażeja': 'Błażej',
    'bogdana': 'Bogdan', 'bogumiła': 'Bogumił', 'bogusława': 'Bogusław',
    'bohdan': 'Bohdan', 'bohdana': 'Bohdan', 'bolesława': 'Bolesław',
    'bonifacego': 'Bonifacy', 'borysa': 'Borys', 'bronislawa': 'Bronisław',
    'bronisława': 'Bronisław', 'bronisławy': 'Bronisława', 'brunona': 'Brunon',
    'cecylii': 'Cecylia', 'cezarego': 'Cezary', 'chaima': 'Chaim',
    'cypriana': 'Cyprian', 'cyryla': 'Cyryl', 'czesława': 'Czesław',
    'damiana': 'Damian', 'daniela': 'Daniel', 'danuty': 'Danuta',
    'dariusza': 'Dariusz', 'dawida': 'Dawid', 'dionizego': 'Dionizy',
    'dobrosława': 'Dobrosław', 'dominika': 'Dominik', 'doroty': 'Dorota',
    'edwarda': 'Edward', 'edwina': 'Edwin', 'eleonory': 'Eleonora',
    'eliasza': 'Eliasz', 'elżbiety': 'Elżbieta', 'emila': 'Emil',
    'emilii': 'Emilia', 'erazma': 'Erazm', 'ernesta': 'Ernest',
    'eugeniusza': 'Eugeniusz', 'eustachego': 'Eustachy', 'ewy': 'Ewa',
    'faustyny': 'Faustyna', 'felicjana': 'Felicjan', 'feliksa': 'Feliks',
    'ferdynanda': 'Ferdynand', 'filipa': 'Filip', 'flora': 'Florian',
    'floriana': 'Florian', 'franciszka': 'Franciszek', 'franciszki': 'Franciszka',
    'fryderyka': 'Fryderyk', 'gabriela': 'Gabriel', 'gabrieli': 'Gabriela',
    'galla': 'Gall Anonim', 'gaspara': 'Gaspar', 'gerarda': 'Gerard',
    'gertrudy': 'Gertruda', 'gotfryda': 'Gotfryd', 'grażyny': 'Grażyna',
    'grzegorza': 'Grzegorz', 'gustawa': 'Gustaw', 'gwalberta': 'Gwalbert',
    'haliny': 'Halina', 'hanki': 'Hanka', 'hanny': 'Hanna', 'heleny': 'Helena',
    'henryka': 'Henryk', 'herberta': 'Zbigniew Herbert', 'hieronima': 'Hieronim',
    'hilarego': 'Hilary', 'hipolita': 'Hipolit', 'huberta': 'Hubert',
    'hugona': 'Hugo', 'idziego': 'Idzi', 'ignacego': 'Ignacy',
    'igor': 'Igor', 'igora': 'Igor', 'ireny': 'Irena',
    'iwona': 'Iwon', 'izaaka': 'Izaak', 'izabeli': 'Izabela', 'izydora': 'Izydor',
    'jacka': 'Jacek', 'jadwigi': 'Jadwiga', 'jakuba': 'Jakub',
    'jana': 'Jan', 'janiny': 'Janina', 'janusza': 'Janusz', 'jaremy': 'Jarema',
    'jarosława': 'Jarosław', 'jerzego': 'Jerzy', 'joachima': 'Joachim',
    'joanny': 'Joanna', 'jonatana': 'Jonatan', 'jordana': 'Henryk Jordan',
    'josela': 'Josel', 'juliana': 'Julian', 'juliusza': 'Juliusz',
    'justyna': 'Justyn', 'józefa': 'Józef', 'józefata': 'Józefat',
    'józefy': 'Józefa', 'kajetana': 'Kajetan', 'kamila': 'Kamil',
    'karola': 'Karol', 'karoliny': 'Karolina', 'kaspra': 'Kasper',
    'katarzyny': 'Katarzyna', 'kazimierza': 'Kazimierz', 'kazimiery': 'Kazimiera',
    'klaudyny': 'Klaudyna', 'klemensa': 'Klemens', 'konrada': 'Konrad',
    'konstantego': 'Konstanty', 'kordiana': 'Kordian', 'kornela': 'Kornel',
    'kosmy': 'Kosma', 'krystyna': 'Krystyn', 'krystyny': 'Krystyna',
    'krzysztofa': 'Krzysztof', 'ksawerego': 'Ksawery', 'lecha': 'Lech',
    'leona': 'Leon', 'leonarda': 'Leonard', 'leopolda': 'Leopold',
    'leszka': 'Leszek', 'lucjana': 'Lucjan', 'ludwika': 'Ludwik',
    'ludwiki': 'Ludwika', 'łazarza': 'Łazarz',
    'łukasza': 'Łukasz', 'macieja': 'Maciej', 'magdaleny': 'Magdalena',
    'maksymiliana': 'Maksymilian', 'malwiny': 'Malwina', 'manfreda': 'Manfred',
    'marcelego': 'Marceli', 'marcina': 'Marcin', 'marconiego': 'Henryk Marconi',
    'marka': 'Marek', 'marii': 'Maria', 'mariana': 'Marian', 'marianny': 'Marianna',
    'marty': 'Marta', 'mateusza': 'Mateusz', 'maurycego': 'Maurycy',
    'medarda': 'Medard', 'meiselsa': 'Dov Ber Meisels', 'melchiora': 'Melchior',
    'michała': 'Michał', 'mieczysława': 'Mieczysław', 'mikołaja': 'Mikołaj',
    'mirona': 'Miron', 'mirosława': 'Mirosław', 'mordechaja': 'Mordechaj',
    'narcyza': 'Narcyz', 'natalii': 'Natalia', 'nikodema': 'Nikodem',
    'norberta': 'Norbert', 'olgi': 'Olga', 'oliwiera': 'Oliwier',
    'onufrego': 'Onufry', 'oskara': 'Oskar', 'otylii': 'Otylia',
    'pankracego': 'Pankracy', 'paschalisa': 'Paschalis', 'patryka': 'Patryk',
    'paula': 'Paul', 'pauliny': 'Paulina', 'pawła': 'Paweł',
    'piotra': 'Piotr', 'polikarpa': 'Polikarp', 'protazego': 'Protazy',
    'przemysława': 'Przemysław', 'radomiła': 'Radomił', 'radosława': 'Radosław',
    'radziwiłłów': 'Radziwiłłowie', 'rafała': 'Rafał', 'rajmunda': 'Rajmund',
    'remigiusza': 'Remigiusz', 'renarda': 'Renard', 'roberta': 'Robert',
    'rocha': 'Roch', 'romana': 'Roman', 'romualda': 'Romuald',
    'róży': 'Róża', 'rudolfa': 'Rudolf', 'ryszarda': 'Ryszard',
    'sabiny': 'Sabina', 'salwatora': 'Salwator', 'samuela': 'Samuel',
    'sebastiana': 'Sebastian', 'sergiusza': 'Sergiusz', 'sereno': 'Sereno Fenn',
    'seweryna': 'Seweryn', 'sławomira': 'Sławomir', 'sobiepana': 'Sobiepan',
    'sobiesława': 'Sobiesław', 'stefana': 'Stefan', 'stelli': 'Izydor Stella-Sawicki',
    'sylwestra': 'Sylwester', 'szczepana': 'Szczepan', 'szczęsnego': 'Szczęsny',
    'szymona': 'Szymon', 'tadeusza': 'Tadeusz', 'tarsycjusza': 'Tarsycjusz',
    'teodora': 'Teodor', 'teodozji': 'Teodozja', 'teofila': 'Teofil',
    'teresy': 'Teresa', 'tobiasza': 'Tobiasz', 'tomasza': 'Tomasz',
    'tymoteusza': 'Tymoteusz', 'tytusa': 'Tytus', 'urszuli': 'Urszula',
    'wacława': 'Wacław', 'waldemara': 'Waldemar', 'walentego': 'Walenty',
    'waleriana': 'Walerian', 'walerego': 'Walery', 'wandy': 'Wanda',
    'wawrzyńca': 'Wawrzyniec', 'weroniki': 'Weronika', 'wespazjana': 'Wespazjan',
    'wiesława': 'Wiesław', 'wiktora': 'Wiktor', 'wiktorii': 'Wiktoria',
    'wilhelma': 'Wilhelm', 'wincentego': 'Wincenty', 'wirgiliusza': 'Wirgilusz',
    'wisławy': 'Wisława', 'wita': 'Wit', 'witolda': 'Witold',
    'władysława': 'Władysław', 'włodzimierza': 'Włodzimierz',
    'wojciecha': 'Wojciech', 'zachariasza': 'Zachariasz', 'zbigniewa': 'Zbigniew',
    'zdzisława': 'Zdzisław', 'zenona': 'Zenon', 'ziemowita': 'Ziemowit',
    'zygmunt': 'Zygmunt', 'zygmunta': 'Zygmunt'
}

FAMOUS_SINGLE_SURNAME_PATRONS = {
    'mickiewicza': ('Adam Mickiewicz', 'polski poeta i wieszcz narodowy'),
    'słowackiego': ('Juliusz Słowacki', 'polski poeta epoki romantyzmu'),
    'kościuszki': ('Tadeusz Kościuszko', 'polski i amerykański generał, inżynier wojskowy'),
    'kopernika': ('Mikołaj Kopernik', 'polski astronom, matematyk, lekarz i prawnik'),
    'matejki': ('Jan Matejko', 'wybitny polski malarz historyczny'),
    'sienkiewicza': ('Henryk Sienkiewicz', 'polski nowelista, powieściopisarz, noblista'),
    'reymonta': ('Władysław Reymont', 'polski pisarz i noblista'),
    'prusa': ('Bolesław Prus', 'polski pisarz, prozaik i publicysta'),
    'żeromskiego': ('Stefan Żeromski', 'polski pisarz, publicysta i dramaturg'),
    'wyspiańskiego': ('Stanisław Wyspiański', 'polski dramaturg, poeta, malarz i grafik'),
    'chopina': ('Fryderyk Chopin', 'wybitny polski kompozytor i pianista'),
    'moniuszki': ('Stanisław Moniuszko', 'polski kompozytor, dyrygent i pedagog'),
    'curie-skłodowskiej': ('Maria Skłodowska-Curie', 'polska fizyczka i chemiczka, dwukrotna noblistka'),
    'skłodowskiej-curie': ('Maria Skłodowska-Curie', 'polska fizyczka i chemiczka, dwukrotna noblistka'),
    'piłsudskiego': ('Józef Piłsudski', 'polski działacz niepodległościowy, marszałek Polski'),
    'asnyka': ('Adam Asnyk', 'polski poeta i dramaturg'),
    'fredry': ('Aleksander Fredro', 'polski hrabia, komediopisarz i pamiętnikarz'),
    'norwida': ('Cyprian Kamil Norwid', 'polski poeta, dramatopisarz i malarz'),
    'konopnickiej': ('Maria Konopnicka', 'polska poetka, nowelistka i publicystka'),
    'długosza': ('Jan Długosz', 'polski historyk, kronikarz, kanonik krakowski'),
    'kraszewskiego': ('Józef Ignacy Kraszewski', 'polski pisarz, publicysta i historyk'),
    'orzeszkowej': ('Eliza Orzeszkowa', 'polska pisarka epoki pozytywizmu'),
    'reja': ('Mikołaj Rej', 'polski poeta, prozaik renesansowy, ojciec piśmiennictwa polskiego'),
    'kochanowskiego': ('Jan Kochanowski', 'najwybitniejszy polski poeta renesansowy'),
    'modrzejewskiej': ('Helena Modrzejewska', 'wybitna polska aktorka teatralna'),
    'stryjeńskiego': ('Aleksander Stryjeński', 'polski inżynier wojskowy i kartograf'),
    'tetmajera': ('Kazimierz Przerwa-Tetmajer', 'polski poeta, nowelista i dramaturg'),
    'rydla': ('Lucjan Rydel', 'polski poeta i dramatopisarz Młodej Polski'),
    'wernyhory': ('Wernyhora', 'legendarny wieszcz ukraiński i kozacki'),
    'dietla': ('Józef Dietl', 'lekarz balneolog, profesor i prezydent Krakowa'),
    'lema': ('Stanisław Lem', 'światowej sławy polski pisarz science-fiction'),
    'szymborskiej': ('Wisława Szymborska', 'polska poetka, eseistka, laureatka Nagrody Nobla'),
    'kasprowicza': ('Jan Kasprowicz', 'polski poeta, dramaturg i tłumacz Młodej Polski'),
    'lelewela': ('Joachim Lelewel', 'polski historyk, numizmatyk i działacz polityczny'),
    'bema': ('Józef Bem', 'polski i węgierski generał, inżynier wojskowy'),
    'czarnieckiego': ('Stefan Czarniecki', 'hetman polny koronny, dowódca wojskowy'),
    'traugutta': ('Romuald Traugutt', 'dyktator powstania styczniowego'),
    'narutowicza': ('Gabriel Narutowicz', 'pierwszy prezydent Rzeczypospolitej Polskiej'),
    'mościckiego': ('Ignacy Mościcki', 'polski chemik, naukowiec, prezydent RP'),
    'paderewskiego': ('Ignacy Jan Paderewski', 'polski pianista, kompozytor, premier RP'),
    'karłowicza': ('Mieczysław Karłowicz', 'polski kompozytor i dyrygent, taternik'),
    'wieniawskiego': ('Henryk Wieniawski', 'polski skrzypek i kompozytor wirtuoz'),
    'szymanowskiego': ('Karol Szymanowski', 'wybitny polski kompozytor i pianista'),
    'lutosławskiego': ('Witold Lutosławski', 'jeden z najwybitniejszych polskich kompozytorów XX w.'),
    'pendereckiego': ('Krzysztof Penderecki', 'światowej sławy polski kompozytor i dyrygent')
}

NATURE_FLORA_WORDS = {
    'akacjowa', 'agrestowa', 'agawy', 'aloesowa', 'anyżowa', 'araliowa', 'astrowa', 'azaliowa',
    'bakaliowa', 'bambusowa', 'bananowa', 'barszcza', 'bazyliowa', 'begonii', 'berberysowa',
    'bluszczowa', 'bławatkowa', 'borowikowa', 'borówkowa', 'bratkowa', 'brzoskwiniowa',
    'brzozowa', 'bukowa', 'cedrowa', 'chabrowa', 'chmielna', 'chryzantemowa', 'cisowa', 'cytrynowa',
    'czereśniowa', 'cyprysowa', 'daktylowa', 'dębowa', 'dereniowa', 'fasolowa', 'fiołkowa', 'forsycji',
    'frezjowa', 'gerberowa', 'głogowa', 'goździkowa', 'grabowa', 'grochowa', 'gronowa', 'gruszkowa',
    'grzybowa', 'hebanowa', 'hiacyntowa', 'irysowa', 'jabłoniowa', 'jagodowa', 'jara', 'jarzębinowa',
    'jasminowa', 'jaśminowa', 'jaworowa', 'jedlicza', 'jodłowa', 'kaktusowa', 'kalinowa', 'kameliowa',
    'kasztanowa', 'kielkowa', 'kłosowa', 'koniczynowa', 'konwaliowa', 'koperkowa', 'krokusowa',
    'krzewowa', 'kwiatowa', 'lawendowa', 'leszczynowa', 'leśna', 'lipowa', 'liściasta', 'lobeliowa',
    'lucerny', 'liliowa', 'makowa', 'malinowa', 'maślana', 'maślaków', 'miętowa', 'migdałowa',
    'mikołajkowa', 'modrzewiowa', 'morelowa', 'mrozowa', 'narcyzowa', 'nasturcjowa', 'niezapominajek',
    'ogrodowa', 'ogrodników', 'olchowa', 'oliwkowa', 'orzechowa', 'osikowa', 'owocowa', 'palmowa',
    'paprociowa', 'pieczarkowa', 'pigwowa', 'piwoniowa', 'płomykowa', 'poziomkowa', 'porzeczkowa',
    'pszenna', 'różana', 'rumiankowa', 'rzepakowa', 'sadownicza', 'sadowa', 'sasankowa', 'słonecznikowa',
    'sosnowa', 'stokrotek', 'storczykowa', 'świerkowa', 'tatarczana', 'topolowa', 'truskawkowa',
    'tulipanowa', 'warzywna', 'wierzbowa', 'winogronowa', 'wiśniowa', 'wrzosowa', 'zawilcowa', 'zielna',
    'zielona', 'złocieniowa', 'żonkilowa', 'żytnia', 'lawendowa', 'nagietkowa', 'macierzankowa', 'rozmarynowa'
}

NATURE_FAUNA_WORDS = {
    'albatrosów', 'bażancie', 'bażantowa', 'bociania', 'bociana', 'bobrowa', 'bocianów', 'chrabąszcza',
    'czajcza', 'czyżyków', 'delfina', 'dorsza', 'drozdowa', 'dzięcioła', 'gołębia', 'gęsia',
    'indycza', 'jaskółcza', 'jastrzębia', 'jaszczurcza', 'jelenia', 'jeżowa', 'kacza', 'kogucia',
    'kormoranów', 'kosów', 'koniowa', 'koralowa', 'kozacka', 'koziorożca', 'kretowa', 'królika',
    'kukułcza', 'kurza', 'łabędzia', 'łasicza', 'łosia', 'motyli', 'mrówcza', 'mysia', 'niedźwiedzia',
    'orla', 'pawia', 'pelikana', 'perlicza', 'pszczela', 'ptasia', 'rakowa', 'renifera', 'robacza',
    'rybia', 'rybna', 'rybitwy', 'ryjówki', 'sarnia', 'słowicza', 'sobóli', 'sokoła', 'somowa',
    'sowia', 'strusia', 'szarańczy', 'szerszenia', 'szpakowa', 'tchórzowa', 'turkawkowa', 'wiewiórcza',
    'wilcza', 'wróbla', 'wronia', 'wydrza', 'zająca', 'żabie', 'żabia', 'żubrza', 'żurawia', 'żubrowa'
}

EVENT_DATE_WORDS = {
    '28 lipca 1943', '8 pułku ułanów', '3 maja', 'aleja 3 maja', '29 listopada', 'aleja 29 listopada',
    'aleja pokoju', 'aleja powstania warszawskiego', 'monte cassino', 'obrońców modlina',
    'obrońców poczty gdańskiej', 'obrońców tomaszowa', 'obrońców warszawy', 'obrońców westerplatte',
    'orląt lwowskich', 'powstania kościuszkowskiego', 'powstania styczniowego', 'powstańców śląskich',
    'powstańców wielkopolskich', 'armii krajowej', 'armii «kraków»', 'batalionów chłopskich',
    'bohaterów getta', 'bohaterów monte cassino', 'bohaterów września', 'czerwonych maków',
    'grunwaldzka', 'legionów piłsudskiego', 'solidarności', 'zwycięstwa', '11 listopada', '1 maja',
    'warszawianka', 'niepodległości', 'pokoju', 'zwycięzców', 'braterstwa broni'
}

HISTORICAL_CRAFT_WORDS = {
    'szewska', 'grodzka', 'garbarska', 'stolarska', 'poselska', 'kanonicza', 'józefa', 'szeroka',
    'miodowa', 'piwna', 'św. anny', 'floriańska', 'sukiennice', 'rynek główny', 'rynek podgórski',
    'mały rynek', 'bednarska', 'blacharska', 'brukarzy', 'ceglarska', 'cieśla', 'ciesielska',
    'cukrowników', 'dekarska', 'drukarzy', 'drwali', 'folwarczna', 'garncarska', 'górników',
    'hafciarska', 'hutnicza', 'kolejarzy', 'kołodziejska', 'kominiarska', 'koronkarska', 'koszykarska',
    'kotlarska', 'kowalska', 'krawiecka', 'kuźnicka', 'malarska', 'marynarska', 'masarska', 'młynarska',
    'monterska', 'murarska', 'naftowa', 'piekarska', 'pocztowa', 'puszkarska', 'rolnicza', 'rzeźnicza',
    'rycerska', 'rymarzy', 'serowarska', 'snycerska', 'spółdzielców', 'stelmachów', 'sukiennicza',
    'szkutników', 'szlifierzy', 'ślusarska', 'tkacka', 'tokarska', 'włókniarzy', 'zdunów', 'złotników',
    'żeglarska', 'św. krzyża', 'św. tomasza', 'św. marka', 'św. jana', 'św. sebastiana', 'sienna',
    'bracka', 'sławkowska', 'gołębia', 'św. ducha', 'kościuszkowców'
}

DIRECTIONAL_TOWNS = {
    'wielicka': 'Wieliczka', 'skawińska': 'Skawina', 'mogilska': 'Mogiła', 'tyniecka': 'Tyniec',
    'krowoderska': 'Krowodrza', 'bieżanowska': 'Bieżanów', 'borecka': 'Borek Fałęcki',
    'wrocławska': 'Wrocław', 'warszawska': 'Warszawa', 'czarnowiejska': 'Czarna Wieś',
    'zwierzyniecka': 'Zwierzyniec', 'prądnicka': 'Prądnik', 'kobierzyńska': 'Kobierzyn',
    'olszanicka': 'Olszanica', 'wadowicka': 'Wadowice', 'zakopiańska': 'Zakopane',
    'myślenicka': 'Myślenice', 'sandomierska': 'Sandomierz', 'lubelska': 'Lublin',
    'poznańska': 'Poznań', 'radomska': 'Radom', 'kielecka': 'Kielce', 'bocheńska': 'Bochnia',
    'tarnowska': 'Tarnów', 'rzeszowska': 'Rzeszów', 'zamojska': 'Zamość', 'lwowska': 'Lwów',
    'wileńska': 'Wilno', 'łagiewnicka': 'Łagiewniki', 'prokocimska': 'Prokocim',
    'płaszowska': 'Płaszów', 'bronowicka': 'Bronowice', 'zielonecka': 'Zielonki',
    'balicka': 'Balice', 'zabierzowska': 'Zabierzów', 'krzeszowicka': 'Krzeszowice',
    'chrzanowska': 'Chrzanów', 'olkuska': 'Olkusz', 'miechowska': 'Miechów',
    'słomnicka': 'Słomniki', 'niepołomicka': 'Niepołomice', 'gdowska': 'Gdów',
    'dobczycka': 'Dobczyce', 'limanowska': 'Limanowa', 'nowosądecka': 'Nowy Sącz',
    'żywiecka': 'Żywiec', 'oświęcimska': 'Oświęcim', 'śląska': 'Śląsk', 'pomorska': 'Pomorze',
    'mazowiecka': 'Mazowsze', 'kujawska': 'Kujawy', 'podhalańska': 'Podhale', 'orawska': 'Orawa',
    'spiska': 'Spisz', 'kurpiowska': 'Kurpie', 'kalwaryjska': 'Kalwaria Zebrzydowska',
    'starowiślna': 'Stara Wisła', 'stradomska': 'Stradom'
}

def clean_prefix(name):
    lower = name.lower().strip()
    for pref in PREFIXES_MAP:
        if lower.startswith(pref):
            return name[len(pref):].strip()
    return name.strip()

def fix_surname(last):
    lower = last.lower()
    if lower.endswith('skiego'):
        return last[:-6] + 'ski'
    if lower.endswith('ckiego'):
        return last[:-6] + 'cki'
    if lower.endswith('zkiego'):
        return last[:-6] + 'zki'
    if lower.endswith('ego'):
        return last[:-3] + 'i'
    if lower.endswith(('ejki', 'uszki', 'yszki', 'aszki', 'oszki')):
        return last[:-1] + 'o'
    if lower.endswith(('łły', 'lly')):
        return last[:-1] + 'o'
    if lower.endswith(('icza', 'ycza', 'owicza', 'ewicza')):
        return last[:-1]
    if lower.endswith('dry'):
        return last[:-1] + 'o'
    if lower.endswith('enka'):
        return last[:-4] + 'enek'
    if lower.endswith('ka') and not lower.endswith('ska'):
        return last[:-1]
    if lower.endswith('owa') and not lower.endswith(('kowa', 'lowa')):
        return last[:-1]
    if lower.endswith(('ta', 'da', 'ra', 'na', 'sa', 'ba', 'fa', 'wa')) and len(lower) > 4:
        return last[:-1]
    return last

def lemmatize_person_name(clean_n):
    words = clean_n.split()
    if not words:
        return clean_n
    
    title = ''
    first_w_lower = words[0].lower().rstrip('.')
    if first_w_lower in TITLE_PREFIXES:
        title = TITLE_PREFIXES[first_w_lower]
        words = words[1:]
    
    if not words:
        return clean_n
        
    first_name_gen = words[0].lower()
    if first_name_gen in FIRST_NAMES_GENITIVE_TO_NOMINATIVE:
        words[0] = FIRST_NAMES_GENITIVE_TO_NOMINATIVE[first_name_gen]
        
    if len(words) >= 2:
        words[-1] = fix_surname(words[-1])

    nominative = ' '.join(words)
    if title and not nominative.lower().startswith(title.lower()):
        return f'{title} {nominative}'.strip()
    return nominative.strip()

def classify_street(raw_name):
    clean_n = clean_prefix(raw_name)
    lower_clean = clean_n.lower()
    raw_lower = raw_name.lower()
    words = lower_clean.split()
    first_w = words[0] if words else ''
    first_clean = first_w.rstrip('.')

    # 1. Wydarzenie / Data
    if raw_lower in EVENT_DATE_WORDS or lower_clean in EVENT_DATE_WORDS or any(d in lower_clean for d in ['powstania', 'obrońców', 'armii krajowej', 'bohaterów', 'monte cassino', '3 maja', '29 listopada']):
        return {
            'category': 'event_date',
            'raw_name': raw_name,
            'clean_name': clean_n,
            'nominative': clean_n
        }

    # 2. Słynne pojedyncze nazwiska
    if lower_clean in FAMOUS_SINGLE_SURNAME_PATRONS:
        nom, role_hint = FAMOUS_SINGLE_SURNAME_PATRONS[lower_clean]
        return {
            'category': 'person',
            'raw_name': raw_name,
            'clean_name': clean_n,
            'nominative': nom,
            'role_hint': role_hint
        }

    # 3. Postać z imieniem lub tytułem
    is_person = False
    if first_clean in TITLE_PREFIXES:
        is_person = True
    elif first_clean in FIRST_NAMES_GENITIVE_TO_NOMINATIVE and FIRST_NAMES_GENITIVE_TO_NOMINATIVE[first_clean]:
        is_person = True
    elif len(words) >= 2 and words[1].rstrip('.') in FIRST_NAMES_GENITIVE_TO_NOMINATIVE and FIRST_NAMES_GENITIVE_TO_NOMINATIVE[words[1].rstrip('.')]:
        is_person = True

    if is_person:
        nom = lemmatize_person_name(clean_n)
        return {
            'category': 'person',
            'raw_name': raw_name,
            'clean_name': clean_n,
            'nominative': nom
        }

    # 4. Dawne rzemiosło / trakt lokacyjny
    if lower_clean in HISTORICAL_CRAFT_WORDS or any(craft in lower_clean for craft in ['szewska', 'grodzka', 'garbarska', 'stolarska', 'poselska', 'kanonicza', 'sukiennice', 'rynek']):
        return {
            'category': 'historical_craft',
            'raw_name': raw_name,
            'clean_name': clean_n,
            'nominative': clean_n
        }

    # 5. Przyroda (Flora / Fauna)
    if lower_clean in NATURE_FLORA_WORDS or any(w in NATURE_FLORA_WORDS for w in words):
        return {
            'category': 'nature_flora',
            'raw_name': raw_name,
            'clean_name': clean_n,
            'nominative': clean_n
        }
    if lower_clean in NATURE_FAUNA_WORDS or any(w in NATURE_FAUNA_WORDS for w in words):
        return {
            'category': 'nature_fauna',
            'raw_name': raw_name,
            'clean_name': clean_n,
            'nominative': clean_n
        }

    # 6. Ulica kierunkowa
    for town_key, town_name in DIRECTIONAL_TOWNS.items():
        if town_key in lower_clean or lower_clean.startswith(town_key):
            return {
                'category': 'directional',
                'raw_name': raw_name,
                'clean_name': clean_n,
                'nominative': clean_n,
                'target_town': town_name
            }

    # 7. Regionalna ulica kierunkowa (-ska, -cka)
    if lower_clean.endswith(('ska', 'cka', 'zka')) and not lower_clean.endswith(('ogrodowa', 'krótka', 'wąska')):
        return {
            'category': 'directional_regional',
            'raw_name': raw_name,
            'clean_name': clean_n,
            'nominative': clean_n
        }

    return {
        'category': 'toponymic_general',
        'raw_name': raw_name,
        'clean_name': clean_n,
        'nominative': clean_n
    }

def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        names = json.load(f)

    results = []
    stats = {}

    for name in names:
        classified = classify_street(name)
        results.append(classified)
        cat = classified['category']
        stats[cat] = stats.get(cat, 0) + 1

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print('\n=== WYNIKI KLASYFIKACJI 2 763 ULIC KRAKOWA (v3 z ulepszoną lematyzacją) ===')
    for cat, cnt in sorted(stats.items(), key=lambda x: -x[1]):
        print(f' - {cat:<24}: {cnt:>4} ulic ({cnt/len(names)*100:>5.1f}%)')
    print(f'Zapisano wyniki do {OUTPUT_FILE}.')

if __name__ == '__main__':
    main()
