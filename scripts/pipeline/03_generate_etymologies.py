# -*- coding: utf-8 -*-
"""
Pipeline Tłumaczeń i Dosłownych Znaczeń (i18n) dla portalu Ulice Krakowa.
Generuje plik data/cache_etymologies.json zawierający dosłowne znaczenia (literal_meaning)
oraz trójjęzyczne etymologie (etymology w PL, EN, DE) dla wszystkich ulic nieosobowych.
"""
import json
import os
import re

CLASSIFIED_FILE = 'data/streets_classified.json'
OUTPUT_FILE = 'data/cache_etymologies.json'
LEXICON_FILE = 'data/street_translations_lexicon.json'

EXTENDED_LEXICON = {}
if os.path.exists(LEXICON_FILE):
    try:
        with open(LEXICON_FILE, 'r', encoding='utf-8') as f:
            EXTENDED_LEXICON = json.load(f)
    except Exception as e:
        print(f"Uwaga: Nie można wczytać {LEXICON_FILE}: {e}")

# --- 1. SŁOWNIK DOSŁOWNYCH ZNACZEŃ (LITERAL_DICTIONARY) ---
LITERAL_DICTIONARY = {
    # 1.1 Rzemiosło dawne i cechy (Medieval Crafts & Guilds)
    'szewska': ("Shoemakers' Street", "Schustergasse"),
    'grodzka': ("Castle / Citadel Road", "Burgstraße"),
    'garbarska': ("Tanners' Street", "Gerbergasse"),
    'stolarska': ("Carpenters' Street", "Tischlergasse"),
    'poselska': ("Envoys' / Legates' Street", "Gesandtengasse"),
    'kanonicza': ("Canons' Street", "Kanonikergasse"),
    'szeroka': ("Broad / Wide Street", "Breite Gasse"),
    'miodowa': ("Honey Street", "Honiggasse"),
    'piwna': ("Beer Street", "Biergasse"),
    'floriańska': ("St. Florian's Street", "Floriansgasse"),
    'sławkowska': ("Sławków Road", "Slawkauer Straße"),
    'bracka': ("Brothers' / Friars' Street", "Brüdergasse"),
    'sienna': ("Hay Street", "Heugasse"),
    'gołębia': ("Pigeon / Dove Street", "Taubengasse"),
    'młyńska': ("Mill Street", "Mühlstraße"),
    'młynarska': ("Millers' Street", "Müllerstraße"),
    'rybna': ("Fish Street", "Fischgasse"),
    'rzeźnicza': ("Butchers' Street", "Fleischergasse"),
    'masarska': ("Butchers' / Pork Butchers' Street", "Fleischerstraße"),
    'piekarska': ("Bakers' Street", "Bäckergasse"),
    'złotników': ("Goldsmiths' Street", "Goldschmiedgasse"),
    'kotlarska': ("Coppersmiths' Street", "Kesselschmiedstraße"),
    'kowalska': ("Blacksmiths' Street", "Schmiedgasse"),
    'krawiecka': ("Tailors' Street", "Schneidergasse"),
    'sukiennicza': ("Cloth Hall Street", "Tuchmacherstraße"),
    'sukiennice': ("Cloth Hall", "Tuchhallen"),
    'bednarska': ("Coopers' Street", "Böttchergasse"),
    'ciesielska': ("Carpenters' Street", "Zimmererstraße"),
    'blacharska': ("Tinsmiths' Street", "Flaschnerstraße"),
    'ceglarska': ("Brickmakers' Street", "Zieglergasse"),
    'garncarska': ("Potters' Street", "Töpfergasse"),
    'górników': ("Miners' Street", "Bergmannstraße"),
    'kolejarzy': ("Railwaymen's Street", "Eisenbahnerstraße"),
    'kołodziejska': ("Wheelwrights' Street", "Wagnerstraße"),
    'koszykarska': ("Basketmakers' Street", "Korbmachergasse"),
    'kuźnicka': ("Smithy / Forge Street", "Schmiedewerkstraße"),
    'monterska': ("Assemblers' / Fitters' Street", "Monteurstraße"),
    'murarska': ("Masons' Street", "Maurerstraße"),
    'pocztowa': ("Postal / Post Office Street", "Poststraße"),
    'puszkarska': ("Gunsmiths' Street", "Büchsenmacherstraße"),
    'rolnicza': ("Agricultural / Farmers' Street", "Bauernstraße"),
    'rycerska': ("Knights' Street", "Rittergasse"),
    'rymarzy': ("Harness Makers' / Saddlers' Street", "Riemergasse"),
    'serowarska': ("Cheesemakers' Street", "Käsergasse"),
    'snycerska': ("Woodcarvers' Street", "Bildschnitzergasse"),
    'spółdzielców': ("Cooperatives' Street", "Genossenschaftlerstraße"),
    'stelmachów': ("Cartwrights' Street", "Stellmacherstraße"),
    'szkutników': ("Boatbuilders' Street", "Bootbauerstraße"),
    'szlifierzy': ("Grinders' / Polishers' Street", "Schleifergasse"),
    'ślusarska': ("Locksmiths' Street", "Schlossergasse"),
    'tkacka': ("Weavers' Street", "Webergasse"),
    'tokarska': ("Turners' / Lathe Operators' Street", "Drechslergasse"),
    'włókniarzy': ("Textile Workers' Street", "Textilarbeiterstraße"),
    'zdunów': ("Stove Fitters' Street", "Hafnergasse"),
    'żeglarska': ("Sailors' / Mariners' Street", "Seglerstraße"),
    'marynarska': ("Seafarers' Street", "Matrosenstraße"),
    'drukarzy': ("Printers' Street", "Buchdruckerstraße"),
    'introligatorska': ("Bookbinders' Street", "Buchbindergasse"),
    'apteczna': ("Apothecary / Pharmacy Street", "Apothekergasse"),
    'lekarska': ("Physicians' Street", "Ärztestraße"),
    'aktorów': ("Actors' Street", "Schauspielerstraße"),
    'architektów': ("Architects' Street", "Architektenstraße"),
    'artystów': ("Artists' Street", "Künstlerstraße"),
    'muzyków': ("Musicians' Street", "Musikerstraße"),
    'literacka': ("Literary Street", "Literaturstraße"),
    'pisarzy': ("Writers' Street", "Schriftstellerstraße"),
    'bakałarzy': ("Schoolmasters' Street", "Bakkalaureusstraße"),
    'brązownicza': ("Bronzeworkers' Street", "Bronzegießerstraße"),
    'hutnicza': ("Foundry / Metallurgists' Street", "Hüttenstraße"),
    'kominiarska': ("Chimney Sweeps' Street", "Schornsteinfegergasse"),
    'koronkarska': ("Lacemakers' Street", "Spitzenmacherstraße"),
    'malarska': ("Painters' Street", "Malerstraße"),
    'naftowa': ("Petroleum / Oil Street", "Erdölstraße"),
    'folwarczna': ("Manorial Estate Street", "Vorwerkstraße"),
    'drwali': ("Lumberjacks' Street", "Holzfällerstraße"),
    'brukarzy': ("Pavers' Street", "Pflastererstraße"),
    'cukrowników': ("Sugar Refinery Workers' Street", "Zuckerarbeiterstraße"),
    'dekarska': ("Roofers' Street", "Dachdeckerstraße"),

    # 1.2 Drzewa i Krzewy (Trees & Shrubs)
    'lipowa': ("Linden / Lime Tree Street", "Lindenstraße"),
    'dębowa': ("Oak Tree Street", "Eichenstraße"),
    'brzozowa': ("Birch Tree Street", "Birkenstraße"),
    'sosnowa': ("Pine Tree Street", "Kiefernstraße"),
    'świerkowa': ("Spruce Street", "Fichtenstraße"),
    'jodłowa': ("Fir Tree Street", "Tannenstraße"),
    'modrzewiowa': ("Larch Street", "Lärchenstraße"),
    'cisowa': ("Yew Tree Street", "Eibenstraße"),
    'klonowa': ("Maple Street", "Ahornstraße"),
    'topolowa': ("Poplar Street", "Pappelstraße"),
    'kasztanowa': ("Chestnut Street", "Kastanienstraße"),
    'wierzbowa': ("Willow Street", "Weidenstraße"),
    'jaworowa': ("Sycamore Maple Street", "Bergahornstraße"),
    'jesionowa': ("Ash Tree Street", "Eschenstraße"),
    'wiązowa': ("Elm Street", "Ulmenstraße"),
    'grabowa': ("Hornbeam Street", "Hainbuchenstraße"),
    'bukowa': ("Beech Street", "Buchenstraße"),
    'olchowa': ("Alder Street", "Erlenstraße"),
    'olszowa': ("Alder Grove Street", "Erlenbuschstraße"),
    'cedrowa': ("Cedar Street", "Zedernstraße"),
    'cyprysowa': ("Cypress Street", "Zypressenstraße"),
    'palmowa': ("Palm Tree Street", "Palmenstraße"),
    'bambusowa': ("Bamboo Street", "Bambusstraße"),
    'hebanowa': ("Ebony Street", "Ebenholzstraße"),
    'akacjowa': ("Acacia Street", "Akazienstraße"),
    'jarzębinowa': ("Rowan / Mountain Ash Street", "Vogelbeerstraße"),
    'leszczynowa': ("Hazel Tree Street", "Haselnussstraße"),
    'głogowa': ("Hawthorn Street", "Weißdornstraße"),
    'dereniowa': ("Dogwood Street", "Kornelkirschenstraße"),
    'berberysowa': ("Barberry Street", "Berberitzenstraße"),
    'tarninowa': ("Blackthorn Street", "Schlehenstraße"),
    'osikowa': ("Aspen Street", "Espenstraße"),
    'bukszpanowa': ("Boxwood Street", "Buchsbaumstraße"),
    'krzewowa': ("Shrub / Bush Street", "Buschstraße"),
    'liściasta': ("Deciduous / Foliage Street", "Laubstraße"),
    'drzewna': ("Woodland Street", "Baumstraße"),
    'aleja modrzewiowa': ("Larch Avenue", "Lärchenallee"),
    'aleja dębowa': ("Oak Avenue", "Eichenallee"),
    'aleja kasztanowa': ("Chestnut Avenue", "Kastanienallee"),
    'aleja lipowa': ("Linden Avenue", "Lindenallee"),

    # 1.3 Kwiaty i Rośliny Ozdobne (Flowers & Ornamental Plants)
    'kwiatowa': ("Flower Street", "Blumenstraße"),
    'różana': ("Rose Street", "Rosenstraße"),
    'aleja róż': ("Avenue of Roses", "Rosenallee"),
    'tulipanowa': ("Tulip Street", "Tulpenstraße"),
    'konwaliowa': ("Lily of the Valley Street", "Maiglöckchenstraße"),
    'fiołkowa': ("Violet Street", "Veilchenstraße"),
    'krokusowa': ("Crocus Street", "Krokusstraße"),
    'irysowa': ("Iris Street", "Schwertlilienstraße"),
    'bratkowa': ("Pansy Street", "Stiefmütterchenstraße"),
    'chabrowa': ("Cornflower Street", "Kornblumenstraße"),
    'makowa': ("Poppy Street", "Mohnstraße"),
    'goździkowa': ("Carnation Street", "Nelkenstraße"),
    'lawendowa': ("Lavender Street", "Lavendelstraße"),
    'jaśminowa': ("Jasmine Street", "Jasminstraße"),
    'słonecznikowa': ("Sunflower Street", "Sonnenblumenstraße"),
    'storczykowa': ("Orchid Street", "Orchideenstraße"),
    'narcyzowa': ("Narcissus / Daffodil Street", "Narzissenstraße"),
    'żonkilowa': ("Jonquil Street", "Jonquillenstraße"),
    'stokrotek': ("Daisy Street", "Gänseblümchenstraße"),
    'niezapominajek': ("Forget-Me-Not Street", "Vergissmeinnichtstraße"),
    'azaliowa': ("Azalea Street", "Azaleenstraße"),
    'magnoliowa': ("Magnolia Street", "Magnolienstraße"),
    'astrowa': ("Aster Street", "Asternstraße"),
    'chryzantemowa': ("Chrysanthemum Street", "Chrysanthemenstraße"),
    'frezjowa': ("Freesia Street", "Freesienstraße"),
    'gerberowa': ("Gerbera Street", "Gerberastraße"),
    'hiacyntowa': ("Hyacinth Street", "Hyazinthenstraße"),
    'kameliowa': ("Camellia Street", "Kamelienstraße"),
    'liliowa': ("Lily Street", "Lilienstraße"),
    'malwowa': ("Mallow Street", "Malvenstraße"),
    'nagietkowa': ("Marigold Street", "Ringelblumenstraße"),
    'piwoniowa': ("Peony Street", "Pfingstrosenstraße"),
    'sasankowa': ("Pasque Flower Street", "Küchenschellenstraße"),
    'zawilcowa': ("Anemone Street", "Windröschenstraße"),
    'złocieniowa': ("Chrysanthemum / Marigold Street", "Goldlackstraße"),
    'begonii': ("Begonia Street", "Begonienstraße"),
    'dalii': ("Dahlia Street", "Dahlienstraße"),
    'kaktusowa': ("Cactus Street", "Kaktusstraße"),
    'agawy': ("Agave Street", "Agavenstraße"),
    'aloesowa': ("Aloe Street", "Aloestraße"),
    'bluszczowa': ("Ivy Street", "Efeustraße"),
    'paprociowa': ("Fern Street", "Farnstraße"),
    'wrzosowa': ("Heather Street", "Heidestraße"),
    'bukietowa': ("Bouquet Street", "Blumenstrauß-Straße"),

    # 1.4 Zioła, Owoce, Warzywa i Zboża (Herbs, Fruits, Vegetables & Grains)
    'rozmarynowa': ("Rosemary Street", "Rosmarinstraße"),
    'miętowa': ("Mint Street", "Minzstraße"),
    'bazyliowa': ("Basil Street", "Basilikumstraße"),
    'tymiankowa': ("Thyme Street", "Thymianstraße"),
    'szałwiowa': ("Sage Street", "Salbeistraße"),
    'rumiankowa': ("Chamomile Street", "Kamillenstraße"),
    'zielna': ("Herbal Street", "Kräuterstraße"),
    'chmielna': ("Hop Street", "Hopfengasse"),
    'macierzankowa': ("Wild Thyme Street", "Feldthymianstraße"),
    'agrestowa': ("Gooseberry Street", "Stachelbeerstraße"),
    'jagodowa': ("Berry / Blueberry Street", "Heidelbeerstraße"),
    'malinowa': ("Raspberry Street", "Himbeerstraße"),
    'truskawkowa': ("Strawberry Street", "Erdbeerstraße"),
    'poziomkowa': ("Wild Strawberry Street", "Walderdbeerstraße"),
    'borówkowa': ("Bilberry Street", "Heidelbeerstraße"),
    'borówczana': ("Bilberry Lane", "Preiselbeerweg"),
    'jeżynowa': ("Blackberry Street", "Brombeerstraße"),
    'porzeczkowa': ("Currant Street", "Johannisbeerstraße"),
    'winogronowa': ("Grapevine Street", "Weinrebenstraße"),
    'wiśniowa': ("Sour Cherry Street", "Kirschenstraße"),
    'czereśniowa': ("Sweet Cherry Street", "Kirschbaumstraße"),
    'jabłoniowa': ("Apple Tree Street", "Apfelbaumstraße"),
    'gruszkowa': ("Pear Tree Street", "Birnenstraße"),
    'śliwkowa': ("Plum Street", "Pflaumenstraße"),
    'morelowa': ("Apricot Street", "Aprikosenstraße"),
    'brzoskwiniowa': ("Peach Street", "Pfirsichstraße"),
    'orzechowa': ("Walnut Street", "Walnussstraße"),
    'migdałowa': ("Almond Street", "Mandelstraße"),
    'cytrynowa': ("Lemon Street", "Zitronenstraße"),
    'pomarańczowa': ("Orange Street", "Orangenstraße"),
    'oliwkowa': ("Olive Street", "Olivenstraße"),
    'figowa': ("Fig Tree Street", "Feigenstraße"),
    'grochowa': ("Pea Street", "Erbsenstraße"),
    'fasolowa': ("Bean Street", "Bohnenstraße"),
    'buraczana': ("Beetroot Street", "Rübenstraße"),
    'rzepakowa': ("Rapeseed Street", "Rapsstraße"),
    'pszenna': ("Wheat Street", "Weizenstraße"),
    'żytnia': ("Rye Street", "Roggenstraße"),
    'owsiana': ("Oat Street", "Haferstraße"),
    'jęczmienna': ("Barley Street", "Gerstenstraße"),
    'kłosowa': ("Ear of Grain Street", "Ährenstraße"),
    'chlebowa': ("Bread Street", "Brotstraße"),
    'mączna': ("Flour Street", "Mehlstraße"),
    'lniana': ("Linen / Flax Street", "Leinstraße"),
    'sadowa': ("Orchard Street", "Obstgartenstraße"),
    'ogrodowa': ("Garden Street", "Gartenstraße"),
    'sadownicza': ("Fruit Growers' Street", "Obstzüchterstraße"),
    'owocowa': ("Fruit Street", "Obststraße"),

    # 1.5 Grzyby (Mushrooms)
    'grzybowa': ("Mushroom Street", "Pilzstraße"),
    'borowikowa': ("Porcini / King Bolete Street", "Steinpilzstraße"),
    'maślaków': ("Slippery Jack Mushrooms Street", "Butterpilzstraße"),
    'rydzowa': ("Saffron Milk Cap Street", "Reizkerstraße"),
    'pieczarkowa': ("Champignon Street", "Champignonstraße"),

    # 1.6 Ptaki (Birds)
    'orla': ("Eagle Street", "Adlergasse"),
    'sokoła': ("Falcon Street", "Falkengasse"),
    'jastrzębia': ("Hawk Street", "Habichtstraße"),
    'sowia': ("Owl Street", "Eulenstraße"),
    'bociana': ("Stork Street", "Storchenstraße"),
    'bociania': ("Stork Lane", "Storchenweg"),
    'bocianów': ("Storks' Street", "Storchenstraße"),
    'żurawia': ("Crane Street", "Kranichstraße"),
    'łabędzia': ("Swan Street", "Schwanenstraße"),
    'gęsia': ("Goose Street", "Gänsegasse"),
    'kacza': ("Duck Street", "Entenstraße"),
    'kogucia': ("Rooster Street", "Hahnengasse"),
    'kurza': ("Hen Street", "Hühnergasse"),
    'gołębia': ("Pigeon / Dove Street", "Taubengasse"),
    'jaskółcza': ("Swallow Street", "Schwalbenstraße"),
    'wróbla': ("Sparrow Street", "Spatzenstraße"),
    'słowicza': ("Nightingale Street", "Nachtigallengasse"),
    'szpakowa': ("Starling Street", "Starenweg"),
    'kosów': ("Blackbirds' Street", "Amselstraße"),
    'drozdowa': ("Thrush Street", "Drosselweg"),
    'czyżyków': ("Siskins' Street", "Zeisigstraße"),
    'szczygla': ("Goldfinch Street", "Stieglitzstraße"),
    'dzięcioła': ("Woodpecker Street", "Spechtstraße"),
    'kukułcza': ("Cuckoo Street", "Kuckuckstraße"),
    'krucza': ("Raven Street", "Rabengasse"),
    'wronia': ("Crow Street", "Krähenstraße"),
    'srocza': ("Magpie Street", "Elsterstraße"),
    'sójki': ("Jay Street", "Eichelhäherstraße"),
    'pawia': ("Peacock Street", "Pfauengasse"),
    'bażancia': ("Pheasant Street", "Fasanenstraße"),
    'bażantowa': ("Pheasant Lane", "Fasanenweg"),
    'albatrosów': ("Albatross Street", "Albatrosstraße"),
    'rybitwy': ("Terns' Street", "Seeschwalbenstraße"),
    'kormoranów': ("Cormorants' Street", "Kormoranstraße"),
    'pelikana': ("Pelican Street", "Pelikanstraße"),
    'ptasia': ("Bird Street", "Vogelstraße"),
    'turkawkowa': ("Turtle Dove Street", "Turteltaubenstraße"),
    'czajcza': ("Lapwing Street", "Kiebitzstraße"),

    # 1.7 Ssaki (Mammals)
    'wilcza': ("Wolf Street", "Wolfsstraße"),
    'niedźwiedzia': ("Bear Street", "Bärenstraße"),
    'rysiowa': ("Lynx Street", "Luchsstraße"),
    'żubrowa': ("Bison Street", "Wisentstraße"),
    'aleja żubrowa': ("Bison Avenue", "Wisent-Allee"),
    'łosia': ("Elk / Moose Street", "Elchstraße"),
    'jelenia': ("Deer / Stag Street", "Hirschstraße"),
    'sarnia': ("Roe Deer Street", "Rehstraße"),
    'dzika': ("Wild Boar Street", "Wildschweinstraße"),
    'lisia': ("Fox Street", "Fuchsgasse"),
    'borsucza': ("Badger Street", "Dachsstraße"),
    'bobrowa': ("Beaver Street", "Biberstraße"),
    'wydrza': ("Otter Street", "Otterstraße"),
    'łasicza': ("Weasel Street", "Wieselstraße"),
    'jeżowa': ("Hedgehog Street", "Igelstraße"),
    'kretowa': ("Mole Street", "Maulwurfstraße"),
    'ryjówki': ("Shrew Street", "Spitzmausstraße"),
    'wiewiórcza': ("Squirrel Street", "Eichhörnchenweg"),
    'zająca': ("Hare Street", "Hasenstraße"),
    'królika': ("Rabbit Street", "Kaninchenstraße"),
    'koniowa': ("Horse Street", "Pferdestraße"),
    'bawół': ("Buffalo Street", "Büffelstraße"),
    'sobóli': ("Sable Street", "Zobelstraße"),

    # 1.8 Ryby, Owady i Płazy (Fish, Insects & Amphibians)
    'rybna': ("Fish Street", "Fischgasse"),
    'stróża rybna': ("Fish Watchers' Street", "Fischhütergasse"),
    'rakowa': ("Crayfish Street", "Krebsgasse"),
    'żabia': ("Frog Street", "Froschgasse"),
    'jaszczurcza': ("Lizard Street", "Eidechsenstraße"),
    'pszczela': ("Bee Street", "Bienenstraße"),
    'motyli': ("Butterflies' Street", "Schmetterlingsstraße"),
    'mrówcza': ("Ant Street", "Ameisenstraße"),
    'chrabąszcza': ("Cockchafer Street", "Maikäferstraße"),
    'szerszenia': ("Hornet Street", "Hornissenstraße"),
    'koralowa': ("Coral Street", "Korallenstraße"),

    # 1.9 Minerały, Skały i Metale (Minerals, Stones & Metals)
    'bursztynowa': ("Amber Street", "Bernsteinstraße"),
    'agatowa': ("Agate Street", "Achatstraße"),
    'ametystowa': ("Amethyst Street", "Amethyststraße"),
    'diamentowa': ("Diamond Street", "Diamantstraße"),
    'rubinowa': ("Ruby Street", "Rubinstraße"),
    'szmaragdowa': ("Emerald Street", "Smaragdstraße"),
    'szafirowa': ("Sapphire Street", "Saphirstraße"),
    'opalowa': ("Opal Street", "Opalstraße"),
    'topazowa': ("Topaz Street", "Topasstraße"),
    'turkusowa': ("Turquoise Street", "Türkisstraße"),
    'perłowa': ("Pearl Street", "Perlenstraße"),
    'kryształowa': ("Crystal Street", "Kristallstraße"),
    'granitowa': ("Granite Street", "Granitstraße"),
    'marmurowa': ("Marble Street", "Marmorstraße"),
    'bazaltowa': ("Basalt Street", "Basaltstraße"),
    'wapienna': ("Limestone Street", "Kalksteinstraße"),
    'gipsowa': ("Gypsum Street", "Gipsstraße"),
    'krzemionkowa': ("Flint / Silica Street", "Kieselerde-Straße"),
    'złota': ("Gold Street", "Goldene Gasse"),
    'srebrna': ("Silver Street", "Silbergasse"),
    'miedziana': ("Copper Street", "Kupfergasse"),
    'żelazna': ("Iron Street", "Eisengasse"),
    'stalowa': ("Steel Street", "Stahlstraße"),
    'cynkowa': ("Zinc Street", "Zinkstraße"),
    'ołowiana': ("Lead Street", "Bleistraße"),
    'solna': ("Salt Street", "Salzgasse"),
    'kamienna': ("Stone Street", "Steinstraße"),
    'piaskowa': ("Sand Street", "Sandgasse"),
    'żwirowa': ("Gravel Street", "Kiesstraße"),
    'betonowa': ("Concrete Street", "Betonstraße"),

    # 1.10 Krajobraz, Woda i Teren (Landscape, Water & Terrain)
    'polna': ("Field Road", "Feldstraße"),
    'leśna': ("Forest Road", "Waldstraße"),
    'łąkowa': ("Meadow Street", "Wiesenstraße"),
    'borowa': ("Pine Woods Street", "Kiefernwaldstraße"),
    'bór': ("Pine Forest Street", "Nadelwaldstraße"),
    'gajowa': ("Grove Street", "Hainstraße"),
    'górska': ("Mountain Street", "Bergstraße"),
    'pagórkowa': ("Hilly Street", "Hügelstraße"),
    'wzgórze': ("Hill Street", "Hügelstraße"),
    'białe wzgórze': ("White Hill Street", "Weißer-Hügel-Straße"),
    'dolinna': ("Valley Street", "Talstraße"),
    'wąwozowa': ("Gorge / Ravine Street", "Schluchtstraße"),
    'skalista': ("Rocky Street", "Felsenstraße"),
    'wodna': ("Water Street", "Wasserstraße"),
    'rzeczna': ("River Street", "Flussstraße"),
    'potokowa': ("Brook / Stream Street", "Bachstraße"),
    'źródlana': ("Spring Street", "Quellenstraße"),
    'zdrojowa': ("Spa / Mineral Spring Street", "Brunnenstraße"),
    'stawowa': ("Pond Street", "Teichstraße"),
    'jeziorna': ("Lake Street", "Seestraße"),
    'zalewowa': ("Floodplain Street", "Auestraße"),
    'bagienna': ("Marsh / Swamp Street", "Moorstraße"),
    'błotna': ("Muddy Street", "Schlammstraße"),
    'błotniska': ("Wetlands Street", "Moorlandstraße"),
    'brzegowa': ("Riverside / Shoreline Street", "Uferstraße"),
    'nadbrzeżna': ("Waterfront Street", "Uferpromenade"),
    'mostowa': ("Bridge Street", "Brückengasse"),
    'portowa': ("Harbor / Port Street", "Hafenstraße"),
    'przystaniowa': ("Pier / Marina Street", "Anlegestelle-Straße"),
    'bulwarowa': ("Boulevard Street", "Boulevardstraße"),
    'wałowa': ("Rampart / Embankment Street", "Wallstraße"),
    'grobla': ("Dike / Causeway", "Deichweg"),
    'plażowa': ("Beach Street", "Strandstraße"),
    'bliska': ("Nearby Street", "Nahe Straße"),
    'widokowa': ("Scenic View Street", "Aussichtsstraße"),

    # 1.11 Niebo, Zjawiska, Pory Roku (Sky, Weather & Seasons)
    'słoneczna': ("Sunny Street", "Sonnige Straße"),
    'jasna': ("Bright Street", "Helle Gasse"),
    'ciemna': ("Dark Lane", "Dunkle Gasse"),
    'błękitna': ("Azure / Sky Blue Street", "Himmelblaue Straße"),
    'księżycowa': ("Moon / Lunar Street", "Mondstraße"),
    'gwiaździsta': ("Starry Street", "Sternenstraße"),
    'gwiezdna': ("Stellar Street", "Sternstraße"),
    'tęczowa': ("Rainbow Street", "Regenbogenstraße"),
    'promienista': ("Radiant Street", "Strahlenstraße"),
    'świt': ("Daybreak / Dawn Street", "Morgendämmerung-Straße"),
    'brzask': ("Dawn / First Light Street", "Tagesanbruch-Straße"),
    'poranna': ("Morning Street", "Morgenstraße"),
    'południowa': ("Southern / Noon Street", "Südstraße"),
    'wieczorna': ("Evening Street", "Abendstraße"),
    'północna': ("Northern Street", "Nordstraße"),
    'wiosenna': ("Spring Street", "Frühlingsstraße"),
    'letnia': ("Summer Street", "Sommerstraße"),
    'jesienna': ("Autumn Street", "Herbststraße"),
    'zimowa': ("Winter Street", "Winterstraße"),
    'mroźna': ("Frosty Street", "Froststraße"),
    'mrozowa': ("Frost Street", "Froststraße"),
    'śnieżna': ("Snowy Street", "Schneestraße"),
    'wietrzna': ("Windy Street", "Windige Straße"),
    'burzowa': ("Stormy Street", "Stürmische Straße"),
    'chmurna': ("Cloudy Street", "Wolkige Straße"),
    'pogodna': ("Fair / Serene Street", "Heitere Straße"),
    'czysta': ("Clean / Pure Street", "Reine Straße"),
    'babiego lata': ("Indian Summer Street", "Altweibersommerstraße"),
    'astronautów': ("Astronauts' Street", "Astronautenstraße"),
    'kosmiczna': ("Cosmic Street", "Kosmische Straße"),

    # 1.12 Cechy Fizyczne, Kształt i Układ (Physical, Geometry & Layout)
    'długa': ("Long Street", "Lange Straße"),
    'krótka': ("Short Street", "Kurze Gasse"),
    'szeroka': ("Broad / Wide Street", "Breite Gasse"),
    'wąska': ("Narrow Street", "Enge Gasse"),
    'prosta': ("Straight Street", "Gerade Straße"),
    'krzywa': ("Crooked Street", "Krumme Gasse"),
    'cicha': ("Quiet Street", "Stille Straße"),
    'spokojna': ("Peaceful Street", "Ruhige Straße"),
    'zielona': ("Green Street", "Grüne Straße"),
    'biała': ("White Street", "Weiße Straße"),
    'biała droga': ("White Road", "Weißer Weg"),
    'czarna': ("Black Street", "Schwarze Straße"),
    'czerwona': ("Red Street", "Rote Straße"),
    'żółta': ("Yellow Street", "Gelbe Straße"),
    'barwna': ("Colorful Street", "Bunte Straße"),
    'amarantowa': ("Amaranth Street", "Amarantstraße"),
    'nowa': ("New Street", "Neue Straße"),
    'stara': ("Old Street", "Alte Straße"),
    'główna': ("Main Street", "Hauptstraße"),
    'aleja główna': ("Main Avenue", "Hauptallee"),
    'boczna': ("Side Street / Lane", "Seitengasse"),
    'bocznica': ("Railway Siding Street", "Gleisanschluss-Straße"),
    'poprzeczna': ("Cross / Transverse Street", "Querstraße"),
    'kręta': ("Winding Street", "Kurvenreiche Straße"),
    'stroma': ("Steep Street", "Steile Gasse"),
    'zaciszna': ("Secluded / Cozy Street", "Gemütliche Gasse"),
    'okrężna': ("Circular / Ring Street", "Ringstraße"),
    'ślepa': ("Blind / Dead-End Alley", "Sackgasse"),
    'zaułek': ("Alley / Nook", "Gässchen"),
    'blokowa': ("Apartment Blocks Street", "Blockstraße"),
    'bystra': ("Rapid / Swift Street", "Schnelle Straße"),
    'bruzdowa': ("Furrow Street", "Furchenstraße"),

    # 1.13 Wartości, Nastrój i Społeczeństwo (Virtues, Mood & Society)
    'przyjaźni': ("Friendship Avenue", "Allee der Freundschaft"),
    'aleja przyjaźni': ("Friendship Avenue", "Allee der Freundschaft"),
    'pokoju': ("Peace Avenue", "Friedensallee"),
    'aleja pokoju': ("Peace Avenue", "Friedensallee"),
    'zgody': ("Harmony / Concord Square", "Platz der Eintracht"),
    'solidarności': ("Solidarity Avenue", "Solidarność-Allee"),
    'aleja solidarności': ("Solidarity Avenue", "Solidarność-Allee"),
    'wolności': ("Freedom / Liberty Street", "Freiheitsstraße"),
    'braterstwa broni': ("Brotherhood in Arms Street", "Waffenbrüderschaft-Straße"),
    'braterska': ("Fraternal Street", "Brüderliche Straße"),
    'bohaterska': ("Heroic Street", "Heldenhafte Straße"),
    'zwycięstwa': ("Victory Street", "Siegesstraße"),
    'bajeczna': ("Fairytale Street", "Märchenstraße"),
    'wesoła': ("Cheerful / Merry Street", "Fröhliche Straße"),
    'radosna': ("Joyful Street", "Freudige Straße"),
    'urocza': ("Charming Street", "Liebliche Straße"),
    'biesiadna': ("Feast / Banquet Street", "Festmahlsstraße"),
    'biwakowa': ("Camp / Bivouac Street", "Biwakstraße"),
    'wędrowników': ("Wanderers' / Hikers' Avenue", "Wandererallee"),
    'zasłużonych': ("Meritorious Avenue", "Verdienstvollenallee"),
    'amazonek': ("Amazons' Street", "Amazonenstraße"),
    'bagatela': ("Bagatelle / Trifle Street", "Bagatellestraße"),

    # 1.14 Architektura, Obronność i Miasto (Fortifications, City & Architecture)
    'basztowa': ("Turret / Bastion Tower Street", "Basteistraße"),
    'bastionowa': ("Bastion Street", "Bastionstraße"),
    'arsenał': ("Arsenal Street", "Zeughausstraße"),
    'podzamcze': ("Castle Suburb / Under Castle Street", "Am Schlossgrund"),
    'wawelska': ("Wawel Hill Road", "Wawel-Straße"),
    'aleja wawelska': ("Wawel Avenue", "Wawel-Allee"),
    'smocza': ("Wawel Dragon Street", "Drachengasse"),
    'rynek główny': ("Main Market Square", "Hauptmarkt"),
    'mały rynek': ("Little Market Square", "Kleiner Ring"),
    'plac mariacki': ("St. Mary's Church Square", "Marienplatz"),
    'plac nowy': ("New Square (Jewish Quarter)", "Neuer Platz"),
    'plac wolnica': ("Wolnica Square (Kazimierz Town Hall)", "Wolnica-Platz"),
    'planty': ("Planty Garden Ring", "Planty-Grüngürtel"),
    'altanowa': ("Gazebo / Arbour Street", "Lusthausstraße"),
    'amfiteatr': ("Amphitheater Street", "Amphitheaterstraße"),
    'armatury': ("Fittings / Valves Street", "Armaturenstraße"),
    'browarniana': ("Brewery Street", "Brauereistraße"),
    'bularnia': ("River Sandbank Street", "Buhnenstraße"),
    'cegielniana': ("Brickyard Street", "Ziegeleistraße"),
    'fabryczna': ("Factory Street", "Fabrikstraße"),
    'dworcowa': ("Railway Station Street", "Bahnhofstraße"),
    'kolejowa': ("Railway Street", "Eisenbahnstraße"),
    'torowa': ("Track Street", "Gleisstraße"),
    'tramwajowa': ("Tramway Street", "Straßenbahnstraße"),
    'zajezdnia': ("Depot Street", "Depotstraße"),
    'lotnicza': ("Aviation Street", "Luftfahrtstraße"),
    'szybowcowa': ("Glider Street", "Segelflugzeugstraße"),
    'balonowa': ("Balloon Street", "Ballonstraße"),
    'sportowa': ("Sports Street", "Sportstraße"),
    'stadionowa': ("Stadium Street", "Stadionstraße"),
    'parkowa': ("Park Street", "Parkstraße"),
    'teatralna': ("Theater Street", "Theaterstraße"),
    'muzealna': ("Museum Street", "Museumsstraße"),
    'szkolna': ("School Street", "Schulstraße"),
    'akademicka': ("Academic Street", "Akademiestraße"),
    'profesorska': ("Professors' Street", "Professorengasse"),
    'studencka': ("Students' Street", "Studentengasse"),
    'uniwersytecka': ("University Street", "Universitätsstraße"),
    'botaniczna': ("Botanical Gardens Street", "Botanische Straße"),
    'biskupia': ("Bishops' Street", "Bischofsgasse"),
    'kanonicza': ("Canons' Street", "Kanonikergasse"),
    'klasztorna': ("Monastery Street", "Klosterstraße"),
    'kościelna': ("Church Street", "Kirchgasse"),
    'cmentarna': ("Cemetery Street", "Friedhofstraße"),
    'bożego ciała': ("Corpus Christi Street", "Fronleichnamsgasse"),
    'bożego miłosierdzia': ("Divine Mercy Street", "Göttliche-Barmherzigkeit-Straße"),
    'augustiańska': ("Augustinian Friars' Street", "Augustinergasse"),
    'benedyktyńska': ("Benedictine Friars' Street", "Benediktinergasse"),
    'bernardyńska': ("Bernardine Friars' Street", "Bernhardinergasse"),
    'bonifraterska': ("Brothers Hospitallers Street", "Barmherzige-Brüder-Gasse"),
    'bosacka': ("Discalced Friars' Street", "Unbeschuhte-Karmeliter-Gasse"),
    'ariańska': ("Polish Brethren / Arian Street", "Arianerstraße"),
    'braci polskich': ("Polish Brethren Street", "Polnische-Brüder-Straße"),
    'blich': ("Bleaching Ground Lane", "Bleichgasse"),
    'do kopca': ("Mound Path", "Hügelweg"),
    'pod kopcem': ("Under the Mound Street", "Am Hügelfuß"),
    'aleja do kopca': ("Mound Avenue", "Hügelallee"),
    'aleja pod kopcem': ("Under the Mound Avenue", "Am-Hügelfuß-Allee"),
    'aleja panieńskich skał': ("Maiden Rocks Avenue", "Jungfrauenfelsen-Allee"),
    'panieńskich skał': ("Maiden Rocks Avenue", "Jungfrauenfelsen-Allee"),
    'pustelnika': ("Hermit Avenue", "Einsiedlerallee"),
    'aleja pustelnika': ("Hermit Avenue", "Einsiedlerallee"),

    # 1.15 Daty, Wydarzenia i Wojsko (Dates, Events & Military)
    '3 maja': ("May 3rd Constitution Avenue", "3.-Mai-Verfassungsallee"),
    'aleja 3 maja': ("May 3rd Constitution Avenue", "3.-Mai-Verfassungsallee"),
    '11 listopada': ("November 11th Independence Street", "11.-November-Straße"),
    '29 listopada': ("November 29th Uprising Avenue", "29.-November-Aufstand-Allee"),
    'aleja 29 listopada': ("November 29th Uprising Avenue", "29.-November-Aufstand-Allee"),
    '1 maja': ("May 1st Labor Day Street", "1.-Mai-Straße"),
    '28 lipca 1943': ("July 28, 1943 Commemorative Street", "28.-Juli-1943-Gedenkstraße"),
    '8 pułku ułanów': ("8th Uhlan Regiment Street", "8.-Ulanen-Regiment-Straße"),
    '308 dywizjonu': ("308th Polish Fighter Squadron Street", "308.-Staffel-Straße"),
    'armii krajowej': ("Home Army (Armia Krajowa) Avenue", "Heimatarmee-Allee"),
    'armii «kraków»': ("Kraków Army Avenue", "Krakau-Armee-Allee"),
    'batalionów chłopskich': ("Peasants' Battalions Street", "Bauernbataillone-Straße"),
    'batalionu „parasol”': ("Parasol Battalion Street", "Bataillon-Parasol-Straße"),
    'batalionu „skała” ak': ("Skała AK Battalion Street", "Bataillon-Skała-Straße"),
    'batalionu „zośka”': ("Zośka Battalion Street", "Bataillon-Zośka-Straße"),
    'bohaterów getta': ("Ghetto Heroes Square", "Platz der Helden des Ghettos"),
    'plac bohaterów getta': ("Ghetto Heroes Square", "Platz der Helden des Ghettos"),
    'bohaterów monte cassino': ("Heroes of Monte Cassino Street", "Helden-von-Monte-Cassino-Straße"),
    'monte cassino': ("Battle of Monte Cassino Street", "Monte-Cassino-Straße"),
    'bohaterów wietnamu': ("Heroes of Vietnam Street", "Helden-von-Vietnam-Straße"),
    'bohaterów września': ("Heroes of September 1939 Street", "Helden-vom-September-1939-Straße"),
    'czerwonych maków': ("Red Poppies of Monte Cassino Street", "Rote-Mohnblumen-Straße"),
    'estakada obrońców lwowa': ("Defenders of Lwów Overpass", "Verteidiger-von-Lemberg-Überführung"),
    'grunwaldzka': ("Battle of Grunwald Road", "Grunwald- / Tannenbergstraße"),
    'legionów piłsudskiego': ("Piłsudski Legions Street", "Piłsudski-Legionen-Straße"),
    'obrońców helu': ("Defenders of Hel Peninsula Street", "Verteidiger-von-Hel-Straße"),
    'obrońców krzyża': ("Defenders of the Cross (Nowa Huta) Street", "Verteidiger-des-Kreuzes-Straße"),
    'obrońców modlina': ("Defenders of Modlin Fortress Street", "Verteidiger-von-Modlin-Straße"),
    'obrońców poczty gdańskiej': ("Defenders of the Polish Post in Danzig Street", "Verteidiger-der-Danziger-Post-Straße"),
    'obrońców tobruku': ("Defenders of Tobruk Street", "Verteidiger-von-Tobruk-Straße"),
    'obrońców warszawy': ("Defenders of Warsaw Street", "Verteidiger-von-Warschau-Straße"),
    'obrońców westerplatte': ("Defenders of Westerplatte Street", "Verteidiger-von-Westerplatte-Straße"),
    'obrońców tomaszowa': ("Defenders of Tomaszów Street", "Verteidiger-von-Tomaszów-Straße"),
    'orląt lwowskich': ("Eaglets of Lwów Street", "Lemberger-Adlerjungen-Straße"),
    'powstania kościuszkowskiego': ("Kościuszko Uprising Street", "Kościuszko-Aufstand-Straße"),
    'powstania listopadowego': ("November Uprising Street", "Novemberaufstand-Straße"),
    'powstania styczniowego': ("January Uprising Street", "Januaraufstand-Straße"),
    'powstania warszawskiego': ("Warsaw Uprising Avenue", "Warschauer-Aufstand-Allee"),
    'aleja powstania warszawskiego': ("Warsaw Uprising Avenue", "Warschauer-Aufstand-Allee"),
    'powstańców śląskich': ("Silesian Insurgents Avenue", "Schlesische-Aufständische-Allee"),
    'aleja powstańców śląskich': ("Silesian Insurgents Avenue", "Schlesische-Aufständische-Allee"),
    'powstańców wielkopolskich': ("Greater Poland Insurgents Avenue", "Großpolnische-Aufständische-Allee"),
    'belwederczyków': ("Belvedere Cadets Insurgents Street", "Belvedere-Aufständische-Straße"),
    'bitwy nad bzurą': ("Battle of the Bzura Street", "Schlacht-an-der-Bzura-Straße"),
    'warszawianka': ("Warszawianka Anthem Street", "Warszawianka-Straße"),
    'niepodległości': ("Independence Avenue", "Unabhängigkeitsallee"),
    'zwycięzców': ("Victors' Street", "Siegerstraße")
}

# --- 2. TRAKTY KIERUNKOWE I TOPONIMY (DIRECTIONAL_TOWNS) ---
DIRECTIONAL_TOWNS = {
    # Miasta Małopolski i okolic Krakowa
    'wielicka': ('Wieliczka', 'Wieliczka Road', 'Wieliczka-Straße'),
    'skawińska': ('Skawina', 'Skawina Road', 'Skawina-Straße'),
    'bocheńska': ('Bochnia', 'Bochnia Road', 'Bochner Straße'),
    'tarnowska': ('Tarnów', 'Tarnów Road', 'Tarnower Straße'),
    'myślenicka': ('Myślenice', 'Myślenice Road', 'Myślenicer Straße'),
    'wadowicka': ('Wadowice', 'Wadowice Road', 'Wadowicer Straße'),
    'zakopiańska': ('Zakopane', 'Zakopane Highway', 'Zakopane-Straße'),
    'nowotarska': ('Nowy Targ', 'Nowy Targ Road', 'Neumarkter Straße'),
    'nowosądecka': ('Nowy Sącz', 'Nowy Sącz Road', 'Neu-Sandezer Straße'),
    'limanowska': ('Limanowa', 'Limanowa Road', 'Limanowa-Straße'),
    'gorlicka': ('Gorlice', 'Gorlice Road', 'Gorlice-Straße'),
    'chrzanowska': ('Chrzanów', 'Chrzanów Road', 'Chrzanower Straße'),
    'olkuska': ('Olkusz', 'Olkusz Road', 'Olkuscher Straße'),
    'krzeszowicka': ('Krzeszowice', 'Krzeszowice Road', 'Krzeszowicer Straße'),
    'trzebińska': ('Trzebinia', 'Trzebinia Road', 'Trzebinia-Straße'),
    'zatorska': ('Zator', 'Zator Road', 'Zatorer Straße'),
    'alwernijska': ('Alwernia', 'Alwernia Road', 'Alwernia-Straße'),
    'oświęcimska': ('Oświęcim', 'Oświęcim Road', 'Auschwitzer Straße'),
    'kęcka': ('Kęty', 'Kęty Road', 'Kęty-Straße'),
    'żywiecka': ('Żywiec', 'Żywiec Road', 'Saybuscher Straße'),
    'andrychowska': ('Andrychów', 'Andrychów Road', 'Andrychauer Straße'),
    'słomnicka': ('Słomniki', 'Słomniki Road', 'Słomniki-Straße'),
    'miechowska': ('Miechów', 'Miechów Road', 'Miechower Straße'),
    'proszowicka': ('Proszowice', 'Proszowice Road', 'Proszowicer Straße'),
    'niepołomicka': ('Niepołomice', 'Niepołomice Road', 'Niepołomice-Straße'),
    'gdowska': ('Gdów', 'Gdów Road', 'Gdówer Straße'),
    'dobczycka': ('Dobczyce', 'Dobczyce Road', 'Dobczycer Straße'),
    'kalwaryjska': ('Kalwaria Zebrzydowska', 'Kalwaria Road', 'Kalwaria-Straße'),

    # Dawne przedmieścia i toponimy krakowskie
    'balicka': ('Balice', 'Balice Road', 'Balicer Straße'),
    'zabierzowska': ('Zabierzów', 'Zabierzów Road', 'Zabierzower Straße'),
    'tyniecka': ('Tyniec', 'Tyniec Abbey Road', 'Tyniec-Straße'),
    'mogilska': ('Mogiła', 'Mogiła Abbey Road', 'Mogiła-Straße'),
    'krowoderska': ('Krowodrza', 'Krowodrza Road', 'Krowodrza-Straße'),
    'bieżanowska': ('Bieżanów', 'Bieżanów Road', 'Bieżanower Straße'),
    'borecka': ('Borek Fałęcki', 'Borek Fałęcki Road', 'Borkower Straße'),
    'borkowska': ('Borek Fałęcki', 'Borek Road', 'Borkower Straße'),
    'czarnowiejska': ('Czarna Wieś', 'Czarna Wieś Road', 'Schwarzdorfer Straße'),
    'zwierzyniecka': ('Zwierzyniec', 'Zwierzyniec Road', 'Zwierzyniec-Straße'),
    'prądnicka': ('Prądnik', 'Prądnik Road', 'Prądnik-Straße'),
    'białoprądnicka': ('Prądnik Biały', 'Prądnik Biały Road', 'Weiß-Prądnik-Straße'),
    'kobierzyńska': ('Kobierzyn', 'Kobierzyn Road', 'Kobierzyner Straße'),
    'olszanicka': ('Olszanica', 'Olszanica Road', 'Olszanica-Straße'),
    'łagiewnicka': ('Łagiewniki', 'Łagiewniki Sanctuary Road', 'Łagiewniki-Straße'),
    'prokocimska': ('Prokocim', 'Prokocim Road', 'Prokocimer Straße'),
    'płaszowska': ('Płaszów', 'Płaszów Road', 'Płaszower Straße'),
    'bronowicka': ('Bronowice', 'Bronowice Road', 'Bronowicer Straße'),
    'zielonecka': ('Zielonki', 'Zielonki Road', 'Zielonki-Straße'),
    'bibicka': ('Bibice', 'Bibice Road', 'Bibicer Straße'),
    'batowicka': ('Batowice', 'Batowice Road', 'Batowicer Straße'),
    'bielańska': ('Bielany', 'Bielany Road', 'Bielany-Straße'),
    'bieńczycka': ('Bieńczyce', 'Bieńczyce Road', 'Bieńczycer Straße'),
    'bodzowska': ('Bodzów', 'Bodzów Road', 'Bodzówer Straße'),
    'bogucicka': ('Bogucice', 'Bogucice Road', 'Bogucicer Straße'),
    'branicka': ('Branice', 'Branice Road', 'Branicer Straße'),
    'krakowska': ('Kazimierz / Kraków', 'Kraków Gate Thoroughfare', 'Krakauer Straße'),
    'starowiślna': ('Stara Wisła', 'Old Vistula Riverbed Boulevard', 'Alte-Weichsel-Straße'),
    'stradomska': ('Stradom', 'Stradom Royal Route', 'Stradom-Straße'),

    # Główne miasta Polski
    'warszawska': ('Warszawa', 'Warsaw Highway', 'Warschauer Straße'),
    'wrocławska': ('Wrocław', 'Wrocław Road', 'Breslauer Straße'),
    'poznańska': ('Poznań', 'Poznań Road', 'Posener Straße'),
    'gdańska': ('Gdańsk', 'Gdańsk Road', 'Danziger Straße'),
    'szczecińska': ('Szczecin', 'Szczecin Road', 'Stettiner Straße'),
    'lubelska': ('Lublin', 'Lublin Road', 'Lubliner Straße'),
    'kielecka': ('Kielce', 'Kielce Road', 'Kielcer Straße'),
    'radomska': ('Radom', 'Radom Road', 'Radomer Straße'),
    'rzeszowska': ('Rzeszów', 'Rzeszów Road', 'Rzeszower Straße'),
    'sandomierska': ('Sandomierz', 'Sandomierz Road', 'Sandomirer Straße'),
    'zamojska': ('Zamość', 'Zamość Road', 'Zamość-Straße'),
    'katowicka': ('Katowice', 'Katowice Road', 'Kattowitzer Straße'),
    'bytomska': ('Bytom', 'Bytom Road', 'Beuthener Straße'),
    'gliwicka': ('Gliwice', 'Gliwice Road', 'Gleiwitzer Straße'),
    'zabrzańska': ('Zabrze', 'Zabrze Road', 'Zabrzer Straße'),
    'chorzowska': ('Chorzów', 'Chorzów Road', 'Königshütter Straße'),
    'sosnowiecka': ('Sosnowiec', 'Sosnowiec Road', 'Sosnowitzer Straße'),
    'dąbrowska': ('Dąbrowa Górnicza', 'Dąbrowa Road', 'Dombrowaer Straße'),
    'jaworznicka': ('Jaworzno', 'Jaworzno Road', 'Jaworzno-Straße'),
    'bielska': ('Bielsko-Biała', 'Bielsko Road', 'Bielitzer Straße'),
    'cieszyńska': ('Cieszyn', 'Cieszyn Road', 'Teschner Straße'),
    'opolska': ('Opole', 'Opole Road', 'Oppelner Straße'),
    'nyska': ('Nysa', 'Nysa Road', 'Neißer Straße'),
    'raciborska': ('Racibórz', 'Racibórz Road', 'Ratiborer Straße'),
    'legnicka': ('Legnica', 'Legnica Road', 'Liegnitzer Straße'),
    'wałbrzyska': ('Wałbrzych', 'Wałbrzych Road', 'Waldenburger Straße'),
    'świdnicka': ('Świdnica', 'Świdnica Road', 'Schweidnitzer Straße'),
    'kłodzka': ('Kłodzko', 'Kłodzko Road', 'Glatzer Straße'),
    'jeleniogórska': ('Jelenia Góra', 'Jelenia Góra Road', 'Hirschberger Straße'),
    'zielonogórska': ('Zielona Góra', 'Zielona Góra Road', 'Grünberger Straße'),
    'gorzowska': ('Gorzów Wielkopolski', 'Gorzów Road', 'Landsberger Straße'),
    'bydgoska': ('Bydgoszcz', 'Bydgoszcz Road', 'Bromberger Straße'),
    'toruńska': ('Toruń', 'Toruń Road', 'Thorner Straße'),
    'włocławska': ('Włocławek', 'Włocławek Road', 'Leslauer Straße'),
    'płocka': ('Płock', 'Płock Road', 'Plotzker Straße'),
    'kaliska': ('Kalisz', 'Kalisz Road', 'Kalisch-Straße'),
    'konińska': ('Konin', 'Konin Road', 'Koniner Straße'),
    'gnieźnieńska': ('Gniezno', 'Gniezno Road', 'Gnesener Straße'),
    'białostocka': ('Białystok', 'Białystok Road', 'Białystoker Straße'),
    'suwalska': ('Suwałki', 'Suwałki Road', 'Suwałki-Straße'),
    'łomżyńska': ('Łomża', 'Łomża Road', 'Lomschaer Straße'),
    'siedlecka': ('Siedlce', 'Siedlce Road', 'Siedlcer Straße'),
    'chełmska': ('Chełm', 'Chełm Road', 'Cholmer Straße'),
    'piotrkowska': ('Piotrków Trybunalski', 'Piotrków Road', 'Petrikauer Straße'),
    'częstochowska': ('Częstochowa', 'Częstochowa Road', 'Tschenstochauer Straße'),
    'olsztyńska': ('Olsztyn', 'Olsztyn Road', 'Allensteiner Straße'),
    'elbląska': ('Elbląg', 'Elbląg Road', 'Elbinger Straße'),
    'gdyńska': ('Gdynia', 'Gdynia Road', 'Gdinger Straße'),
    'sopocka': ('Sopot', 'Sopot Road', 'Zoppoter Straße'),
    'słupska': ('Słupsk', 'Słupsk Road', 'Stolper Straße'),
    'koszalińska': ('Koszalin', 'Koszalin Road', 'Kösliner Straße'),
    'będzińska': ('Będzin', 'Będzin Road', 'Bendlauer Straße'),
    'brzeska': ('Brzesko', 'Brzesko Road', 'Brzesko-Straße'),

    # Miasta Kresów i Stolice Międzynarodowe
    'kijowska': ('Kijów (Kyiv)', 'Kyiv Road', 'Kiewer Straße'),
    'aleja kijowska': ('Kijów (Kyiv)', 'Kyiv Avenue', 'Kiewer Allee'),
    'lwowska': ('Lwów (Lviv)', 'Lwów Road', 'Lemberger Straße'),
    'wileńska': ('Wilno (Vilnius)', 'Vilnius Road', 'Wilnaer Straße'),
    'grodzieńska': ('Grodno', 'Grodno Road', 'Grodnoer Straße'),
    'bratysławska': ('Bratysława', 'Bratislava Road', 'Pressburger Straße'),
    'budapesztańska': ('Budapeszt', 'Budapest Road', 'Budapester Straße'),
    'praska': ('Praga', 'Prague Street', 'Prager Straße'),
    'wiedeńska': ('Wiedeń', 'Vienna Road', 'Wiener Straße'),
    'berdyczowska': ('Berdyczów', 'Berdychiv Road', 'Berditschewer Straße'),
    'budziszyńska': ('Budziszyn (Bautzen)', 'Bautzen Road', 'Bautzener Straße'),

    # Regiony i Krainy Geograficzne
    'śląska': ('Śląsk (Silesia)', 'Silesia Road', 'Schlesische Straße'),
    'pomorska': ('Pomorze (Pomerania)', 'Pomerania Road', 'Pommersche Straße'),
    'mazowiecka': ('Mazowsze (Mazovia)', 'Mazovia Road', 'Masowische Straße'),
    'kujawska': ('Kujawy', 'Kuyavia Road', 'Kujawische Straße'),
    'podhalańska': ('Podhale', 'Podhale Highlands Road', 'Podhale-Straße'),
    'tatrzańska': ('Tatry', 'Tatra Mountains Road', 'Tatra-Straße'),
    'beskidzka': ('Beskidy', 'Beskid Mountains Road', 'Beskidenstraße'),
    'bieszczadzka': ('Bieszczady', 'Bieszczady Mountains Road', 'Bieszczady-Straße'),
    'karpacka': ('Karpaty', 'Carpathian Mountains Road', 'Karpatenstraße'),
    'orawska': ('Orawa', 'Orava Road', 'Arwa-Straße'),
    'spiska': ('Spisz', 'Spiš Road', 'Zips-Straße'),
    'kurpiowska': ('Kurpie', 'Kurpie Region Road', 'Kurpie-Straße'),
    'bałtycka': ('Morze Bałtyckie', 'Baltic Sea Street', 'Ostseestraße'),
    'burgundzka': ('Burgundia', 'Burgundy Street', 'Burgunderstraße'),
    'albańska': ('Albania', 'Albanian Street', 'Albanische Straße'),
    'algierska': ('Algier', 'Algiers Street', 'Algierstraße'),
    'białoruska': ('Białoruś', 'Belarusian Street', 'Weißrussische Straße'),
    'bułgarska': ('Bułgaria', 'Bulgarian Street', 'Bulgarische Straße')
}

# --- 3. SPECJALNE OPISY HISTORYCZNE DLA KLUCZOWYCH ULIC KRAKOWA ---
HISTORICAL_DESCRIPTIONS = {
    'szewska': {
        'pl': 'Jedna z najstarszych ulic lokacyjnego Krakowa (1257 r.), łącząca Rynek Główny z dawną Bramą Szewską i traktem śląskim. Historyczna siedziba krakowskiego cechu szewców i garbarzy.',
        'en': 'One of the oldest streets of chartered Kraków (1257), connecting the Main Square to the historic Silesian trade route. Medieval home of the shoemakers and tanners guilds.',
        'de': 'Eine der ältesten Straßen des Krakauer Gründungsplans von 1257. Historisches Zentrum der Schuhmacher- und Gerberzunft, das den Hauptmarkt mit der schlesischen Handelsroute verband.'
    },
    'grodzka': {
        'pl': 'Najstarszy trakt Krakowa, fragment starożytnego szlaku handlowego z północy na południe (bursztynowy szlak), wiodący z Rynku Głównego prosto ku Zamkowi Królewskiemu na Wawelu.',
        'en': 'The most ancient thoroughfare in Kraków and part of the historic amber trade route, leading directly from the Main Market Square to the Royal Castle on Wawel Hill.',
        'de': 'Der älteste Straßenzug Krakaus und Teil der historischen Bernsteinstraße, der vom Hauptmarkt direkt zur königlichen Wawel-Burg führt.'
    },
    'floriańska': {
        'pl': 'Reprezentacyjna arteria Drogi Królewskiej (Via Regia), wytyczona w 1257 r., wiodąca od Rynku ku gotyckiej Bramie Floriańskiej i Barbakanowi.',
        'en': 'Prestigious artery of the Royal Road (Via Regia), laid out in 1257, leading from the Main Square towards the medieval St. Florian Gate and Barbican.',
        'de': 'Prachtstraße des königlichen Krönungswegs (Via Regia), angelegt 1257, die vom Hauptmarkt zum gotischen Florianstor und Barbakan führt.'
    },
    'kanonicza': {
        'pl': 'Zabytkowa, najlepiej zachowana renesansowa ulica Krakowa, dawna rezydencja kanoników kapituły katedralnej Wawelu.',
        'en': 'The finest and best-preserved Renaissance street in Kraków, historically housing the senior canons of Wawel Cathedral.',
        'de': 'Die am besten erhaltene historische Renaissancestraße Krakaus, ehemalige Residenz der Domherren des Wawels.'
    },
    'szeroka': {
        'pl': 'Główny plac i serce dawnego żydowskiego miasta Kazimierz, ośrodek życia religijnego i kulturalnego ze Starą Synagogą z XV wieku.',
        'en': 'The historic main square and beating heart of Jewish Kazimierz, featuring the 15th-century Old Synagogue and historic synagogues.',
        'de': 'Der historische Hauptplatz und das Herz des jüdischen Viertels Kazimierz, Zentrum religiöser Kultur mit der Alten Synagoge aus dem 15. Jahrhundert.'
    },
    'sławkowska': {
        'pl': 'Średniowieczna ulica wylotowa z Rynku ku Sławkowowi i kopalniom srebra oraz ołowiu w Olkuszu, zwieńczona niegdyś obronną Bramą Sławkowską.',
        'en': 'Medieval commercial route leading from the Market Square towards the historic lead and silver mining town of Sławków and Olkusz.',
        'de': 'Mittelalterliche Handelsstraße vom Hauptmarkt in Richtung der Silber- und Bleiminenstädte Sławków und Olkusz.'
    },
    'bracka': {
        'pl': 'Jedna z ulic lokacyjnych z 1257 r. Nazwa wywodzi się od braci franciszkanów, których klasztor zamyka jej południowy wylot.',
        'en': 'Laid out in the 1257 charter. Named after the Franciscan friars (Brothers) whose historic monastery anchors its southern end.',
        'de': 'Eine Gründungsstraße von 1257, benannt nach den Franziskanerbrüdern, deren gotisches Kloster das südliche Straßenende markiert.'
    },
    'sienna': {
        'pl': 'Dawny trakt handlowy wiodący z Rynku ku Wieliczce i Rusi, gdzie historycznie handlowano sianem i bydłem.',
        'en': 'Historic commercial route leading east towards the Wieliczka salt mines, historically the venue of the medieval hay market.',
        'de': 'Historische Handelsstraße in Richtung Wieliczka, auf der im Mittelalter der Heu- und Viehmarkt abgehalten wurde.'
    },
    'stolarska': {
        'pl': 'Ulica lokacyjna biegnąca wzdłuż zespołu klasztornego dominikanów, dawne skupisko warsztatów stolarskich i rzemieślników drewnianych.',
        'en': 'Charter street running alongside the Dominican Monastery, historically the quarter of the carpenters guild and fine woodworkers.',
        'de': 'Historische Handwerkerstraße entlang des Dominikanerklosters, historischer Sitz der Krakauer Tischler- und Holzkunsthandwerker.'
    },
    'poselska': {
        'pl': 'Elegancka ulica dawnego patrycjatu i szlachty, gdzie rezydowali posłowie zagraniczni zmierzający na dwór królewski na Wawelu.',
        'en': 'Historic aristocratic street where foreign envoys, ambassadors, and parliamentary deputies lodged on their way to the royal court.',
        'de': 'Aristokratische Straße, in der ausländische Gesandte und königliche Abgeordnete auf ihrem Weg zum Wawel-Schloss residierten.'
    },
    'garbarska': {
        'pl': 'Średniowieczna ulica rzemieślnicza na dawnym Piasku, zlokalizowana nad odnogą rzeki Rudawy, gdzie działały krakowskie garbarnie.',
        'en': 'Historic artisans street on former Piasek suburb, situated by the Rudawa river channel where tanners soaked and treated leather.',
        'de': 'Mittelalterliche Handwerkerstraße am Fluss Rudawa, an der die Krakauer Gerber ihre Werkstätten und Wasserbecken betrieben.'
    },
    'gołębia': {
        'pl': 'Serce dzielnicy uniwersyteckiej z najstarszym budynkiem Uniwersytetu Jagiellońskiego – Collegium Maius (XV w.).',
        'en': 'The academic heart of Kraków, home to the Gothic Collegium Maius (15th c.), the oldest surviving building of Jagiellonian University.',
        'de': 'Das akademische Herz Krakaus mit dem Collegium Maius aus dem 15. Jahrhundert, dem ältesten Gebäude der Jagiellonen-Universität.'
    },
    'jagiellońska': {
        'pl': 'Ulica kwartału uniwersyteckiego, nazwana na cześć dynastii Jagiellonów – odnowicieli Akademii Krakowskiej.',
        'en': 'University quarter street honoring the Jagiellonian Dynasty, who refounded and endowed the Kraków Academy in 1400.',
        'de': 'Prägende Straße des Universitätsviertels, benannt nach der Jagiellonen-Dynastie, den Stiftern der Krakauer Universität.'
    },
    'wiślna': {
        'pl': 'Wytyczona w 1257 r. ulica prowadząca z narożnika Rynku Głównego ku brzegom Wisły i dawnej Bramie Wiślnej.',
        'en': 'Laid out in 1257, leading from the southwest corner of the Main Square towards the Vistula River and medieval river gate.',
        'de': '1257 angelegt, führte sie von der Ecke des Hauptmarkts direkt zum Weichselufer und zum ehemaligen Weichseltor.'
    },
    'basztowa': {
        'pl': 'Reprezentacyjna aleja obwodowa wytyczona wzdłuż dawnych północnych murów obronnych z zachowaną Basztą Pasamoników i Barbakanem.',
        'en': 'Grand boulevard laid out along the dismantled medieval northern ramparts, running past the Barbican and surviving bastion towers.',
        'de': 'Prächtige Ringstraße entlang der ehemaligen nördlichen Stadtmauer, vorbei am Barbakan und den erhaltenen Basteitürmen.'
    },
    'planty': {
        'pl': 'Unikalny park miejski o obwodzie 4 km, utworzony w latach 1822–1830 w miejscu zburzonych średniowiecznych murów obronnych i fosy.',
        'en': 'Famous 4-kilometer green belt park created in 1822–1830 encircling the Old Town where medieval fortifications once stood.',
        'de': 'Weltberühmter 4 km langer Grüngürtelpark, der 1822–1830 anstelle der geschleiften Stadtmauern und Gräben angelegt wurde.'
    },
    'rynek główny': {
        'pl': 'Największy średniowieczny rynek Europy (200 x 200 m), wytyczony podczas lokacji miasta w 1257 r., z Sukiennicami i Kościołem Mariackim.',
        'en': "Europe's largest medieval market square (200 x 200 m), laid out in 1257, featuring the Cloth Hall and St. Mary's Basilica.",
        'de': 'Europas größter mittelalterlicher Marktplatz (200 x 200 m), angelegt 1257, mit den Tuchhallen und der Marienkirche.'
    },
    'sukiennice': {
        'pl': 'Zabytkowe sukiennice na Rynku Głównym, historyczne centrum międzynarodowego handlu suknem, przyprawami i solą od XIII wieku.',
        'en': 'Iconic medieval Cloth Hall at the center of the Main Square, the historic hub of international trade in textiles, salt, and spices.',
        'de': 'Historische Krakauer Tuchhallen im Zentrum des Hauptmarkts, Drehscheibe des mittelalterlichen Tuch- und Salzhandels seit dem 13. Jh.'
    },
    'plac bohaterów getta': {
        'pl': 'Historyczny plac w Podgórzu, centralne miejsce pamięci getta krakowskiego z pomnikiem 70 metalowych krzeseł i Apteką pod Orłem.',
        'en': 'Historic memorial square in Podgórze, epicenter of the wartime Kraków Ghetto with 70 bronze chair monuments and Eagle Pharmacy.',
        'de': 'Historischer Gedenkplatz in Podgórze, Zentrum des ehemaligen Krakauer Ghettos mit dem Mahnmal der 70 Stühle und der Adler-Apotheke.'
    },
    'aleja róż': {
        'pl': 'Reprezentacyjna aleja Nowej Huty, serce socrealistycznego założenia urbanistycznego, słynąca niegdyś z tysięcy krzewów różanych.',
        'en': 'Prestigious central boulevard of Nowa Huta, the core of the socialist-realist architectural ensemble, historically lined with thousands of roses.',
        'de': 'Zentraler Prachtboulevard von Nowa Huta, das städtebauliche Herz der sozialistischen Planstadt, einst berühmt für tausende Rosensträucher.'
    }
}

def clean_prefix(raw_name):
    """Usuwa prefiksy miejskie dla ujednolicenia dopasowania."""
    s = raw_name.lower().strip()
    s = re.sub(r'^(ulica|ul\.|aleja|al\.|plac|pl\.|osiedle|os\.|rondo|skwer|bulwar|droga|grobla|park|zaułek|rynek|estakada|most)\s+', '', s)
    return s.strip()

def match_literal_meaning(clean_n, cat, target_town=None):
    """Zwraca słownik {en, de} z dosłownym znaczeniem lub formą zlokalizowaną."""
    lower = clean_n.lower().strip()
    no_pref = clean_prefix(clean_n)

    # 1. Dokładne dopasowanie w słownikach
    if lower in LITERAL_DICTIONARY:
        en_t, de_t = LITERAL_DICTIONARY[lower]
        return {'en': en_t, 'de': de_t}
    if no_pref in LITERAL_DICTIONARY:
        en_t, de_t = LITERAL_DICTIONARY[no_pref]
        return {'en': en_t, 'de': de_t}

    if lower in EXTENDED_LEXICON:
        en_t, de_t = EXTENDED_LEXICON[lower]
        return {'en': en_t, 'de': de_t}
    if no_pref in EXTENDED_LEXICON:
        en_t, de_t = EXTENDED_LEXICON[no_pref]
        return {'en': en_t, 'de': de_t}

    # 2. Dopasowanie ulic kierunkowych (miasta i krainy)
    for k, info in DIRECTIONAL_TOWNS.items():
        if k == lower or k == no_pref or lower.startswith(k) or no_pref.startswith(k):
            town_pl, en_name, de_name = info
            return {'en': en_name, 'de': de_name}

    # 3. Dopasowanie toponimiczne z pola target_town
    if target_town:
        return {
            'en': f'{target_town} Road',
            'de': f'{target_town}er Straße'
        }

    # 4. Przymiotniki toponimiczne i regionalne kończące się na -ska, -cka, -zka
    if lower.endswith(('ska', 'cka', 'zka')) or no_pref.endswith(('ska', 'cka', 'zka')):
        return {
            'en': f'{clean_n} Road',
            'de': f'{clean_n}-Straße'
        }

    # 5. Zwroty przyimkowe (np. Na Błoniach, Pod Kopcem, Do Fortu, Za Górą)
    prep_m = re.match(r'^(na|nad|do|pod|za|przy|ku|od|w|u)\s+(.*)', lower)
    if prep_m:
        prep = prep_m.group(1)
        rest_title = prep_m.group(2).title()
        prep_en_map = {'na': 'On', 'nad': 'By the', 'do': 'To', 'pod': 'Under', 'za': 'Behind', 'przy': 'By', 'ku': 'Towards', 'od': 'From', 'w': 'In', 'u': 'At'}
        prep_de_map = {'na': 'Auf dem', 'nad': 'Am', 'do': 'Zum', 'pod': 'Unter dem', 'za': 'Hinter dem', 'przy': 'Beim', 'ku': 'Nach', 'od': 'Von', 'w': 'In', 'u': 'Bei'}
        p_en = prep_en_map.get(prep, prep.title())
        p_de = prep_de_map.get(prep, prep.title())
        return {
            'en': f'{p_en} {rest_title} Lane',
            'de': f'{p_de}-{rest_title}-Weg'
        }

    # 6. Prefiksy obiektów miejskich (Plac, Rondo, Park, Osiedle, Most, Bulwar, Aleja, Skwer, Estakada)
    pref_m = re.match(r'^(plac|rondo|park|osiedle|most|bulwar|aleja|skwer|estakada)\s+(.*)', lower)
    if pref_m:
        p_type = pref_m.group(1)
        rest_title = pref_m.group(2).title()
        en_suf = {'plac': 'Square', 'rondo': 'Roundabout', 'park': 'Park', 'osiedle': 'Estate', 'most': 'Bridge', 'bulwar': 'Boulevard', 'aleja': 'Avenue', 'skwer': 'Square', 'estakada': 'Overpass'}.get(p_type, 'Street')
        de_suf = {'plac': 'Platz', 'rondo': 'Kreisverkehr', 'park': 'Park', 'osiedle': 'Siedlung', 'most': 'Brücke', 'bulwar': 'Boulevard', 'aleja': 'Allee', 'skwer': 'Platz', 'estakada': 'Überführung'}.get(p_type, 'Straße')
        return {
            'en': f'{rest_title} {en_suf}',
            'de': f'{rest_title}-{de_suf}'
        }

    # 7. Postacie z imionami (np. Stanisława Barei -> Stanisław Bareja Street)
    if lower.startswith(('stanisława ', 'edmunda ', 'jana ', 'piotra ')):
        nom = clean_n
        for gen, nominative in [('Stanisława ', 'Stanisław '), ('Edmunda ', 'Edmund '), ('Jana ', 'Jan '), ('Piotra ', 'Piotr ')]:
            if nom.startswith(gen):
                nom = nominative + nom[len(gen):]
                break
        return {
            'en': f'{nom} Street',
            'de': f'{nom}-Straße'
        }

    # 8. Regularne formy przymiotnikowe (-owa, -na, -a) i rzeczownikowe (-ów, -arzy, -ek)
    if lower.endswith('owa'):
        return {
            'en': f'{clean_n} Street',
            'de': f'{clean_n}-Straße'
        }

    if lower.endswith('na') and not lower.endswith(('ana', 'ena')):
        return {
            'en': f'{clean_n} Street',
            'de': f'{clean_n}-Straße'
        }

    if lower.endswith(('ów', 'arzy', 'ek')):
        return {
            'en': f'{clean_n} Street',
            'de': f'{clean_n}-Straße'
        }

    # 9. Domyślny fallback dla pozostałych nazw
    return {
        'en': f'{clean_n} Street',
        'de': f'{clean_n}-Straße'
    }

def build_etymology(clean_n, cat, literal_m, target_town=None):
    """Generuje trójjęzyczną etymologię w formatach PL, EN, DE."""
    lower = clean_n.lower().strip()
    no_pref = clean_prefix(clean_n)

    # 1. Dedykowany opis historyczny dla kluczowych ulic
    if lower in HISTORICAL_DESCRIPTIONS:
        return HISTORICAL_DESCRIPTIONS[lower]
    if no_pref in HISTORICAL_DESCRIPTIONS:
        return HISTORICAL_DESCRIPTIONS[no_pref]

    # 2. Flora
    if cat == 'nature_flora':
        flower = literal_m['en'].replace(' Street', '').replace(' Road', '') if literal_m else clean_n
        return {
            'pl': f'Nazwa o motywacji florystycznej (przyrodniczej), nadana podczas rozbudowy i parcelacji dawnych ogrodów oraz terenów zielonych Krakowa.',
            'en': f'Nature-inspired street name ({flower}), established during the suburban development of former orchards and green spaces of Kraków.',
            'de': f'Naturbezogener Straßenname ({flower}), vergeben während der städtebaulichen Erschließung historischer Garten- und Grünflächen Krakaus.'
        }

    # 3. Fauna
    if cat == 'nature_fauna':
        animal = literal_m['en'].replace(' Street', '').replace(' Road', '') if literal_m else clean_n
        return {
            'pl': f'Nazwa o motywacji zoologicznej (fauna), wywodząca się z tradycji nadawania spójnych tematycznie nazw w osiedlach mieszkaniowych Krakowa.',
            'en': f'Fauna-inspired street name ({animal}), typical of thematic residential developments and nature-related street naming in Kraków.',
            'de': f'Tierbezogener Straßenname ({animal}), charakteristisch für thematische Wohnsiedlungen und naturverbundene Straßennamen in Krakau.'
        }

    # 4. Trakty kierunkowe
    if cat == 'directional':
        town = target_town or clean_n
        return {
            'pl': f'Historyczny trakt kierunkowy (toponimiczny), wiodący z Krakowa w stronę miejscowości {town}.',
            'en': f'Historical directional thoroughfare leading from Kraków towards the town of {town}.',
            'de': f'Historische Ausfallstraße, die von Krakau in Richtung der Ortschaft {town} führte.'
        }

    # 5. Trakty regionalne
    if cat == 'directional_regional':
        region_desc = literal_m['en'].replace(' Road', '') if literal_m else clean_n
        return {
            'pl': f'Ulica o nazwie toponimicznej ({clean_n}), nawiązująca do historycznego traktu handlowego, osady podkrakowskiej lub regionu Polski.',
            'en': f'Toponymic street name ({region_desc}), commemorating a historic trade route, suburban settlement, or Polish geographical region.',
            'de': f'Toponymischer Straßenname ({region_desc}), der an einen historischen Handelsweg, eine Vorortsiedlung oder eine polnische Region erinnert.'
        }

    # 6. Rzemiosło dawne
    if cat == 'historical_craft':
        craft_en = literal_m['en'].replace(' Street', '') if literal_m else clean_n
        return {
            'pl': f'Historyczna nazwa o motywacji rzemieślniczej lub cechowej, wywodząca się z dawnych tradycji kupieckich i warsztatów rzemieślniczych Krakowa.',
            'en': f'Historic street name derived from traditional craft guilds ({craft_en}) and medieval artisan workshops of Kraków.',
            'de': f'Historischer Straßenname, der auf die Traditionen der alten Handwerkszünfte ({craft_en}) und Werkstätten Krakaus zurückgeht.'
        }

    # 7. Wydarzenia i rocznice
    if cat == 'event_date':
        return {
            'pl': f'Nazwa pamiątkowa upamiętniająca doniosłe wydarzenie historyczne, formację zbrojną lub datę w dziejach oręża i państwowości polskiej.',
            'en': f'Commemorative street name honoring a significant milestone, military formation, or date in Polish history.',
            'de': f'Gedenkstraßenname zur Erinnerung an ein bedeutendes historisches Datum oder eine militärische Formation der polnischen Geschichte.'
        }

    # 8. Ogólne toponimy miejskie
    return {
        'pl': f'Oficjalna ulica m. Krakowa ({clean_n}). Nazwa o motywacji toponimicznej lub topograficznej, trwale utrwalona w tradycji miejskiej.',
        'en': f'Official street in Kraków ({clean_n}) with a historical toponymic background established in municipal tradition.',
        'de': f'Offizielle Straße in Krakau ({clean_n}) mit toponymischem Hintergrund, fest verankert in der städtischen Tradition.'
    }

def generate_etymologies():
    if not os.path.exists(CLASSIFIED_FILE):
        print(f'Błąd: Brak pliku {CLASSIFIED_FILE}!')
        return

    print('Wczytuję sklasyfikowane ulice Krakowa...')
    with open(CLASSIFIED_FILE, 'r', encoding='utf-8') as f:
        classified = json.load(f)

    etymologies = {}
    literal_count = 0

    for item in classified:
        raw_name = item['raw_name']
        clean_name = item['clean_name']
        cat = item['category']
        target_town = item.get('target_town')

        # Zgodnie ze specyfikacją (Filar 2): ulice osobowe są obsługiwane w cache_patrons.json
        if cat == 'person':
            continue

        literal_meaning = match_literal_meaning(clean_name, cat, target_town)
        if literal_meaning:
            literal_count += 1

        etymology = build_etymology(clean_name, cat, literal_meaning, target_town)

        etymologies[raw_name] = {
            'category': cat,
            'clean_name': clean_name,
            'literal_meaning': literal_meaning,
            'etymology': etymology
        }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(etymologies, f, ensure_ascii=False, indent=2)

    total = len(etymologies)
    pct = (literal_count / total * 100) if total else 0
    print(f'=== ZAKOŃCZONO GENEROWANIE ETYMOLOGII I ZNACZEŃ DOSŁOWNYCH ===')
    print(f' - Wszystkich ulic nieosobowych w bazie: {total}')
    print(f' - Wzbogaconych o dosłowne znaczenie (literal_meaning EN/DE): {literal_count} ({pct:.1f}%)')
    print(f' - Wszystkie ulice posiadają pełne trójjęzyczne etymologie (PL, EN, DE).')
    print(f' - Wyniki zapisano pomyślnie do {OUTPUT_FILE}.')

if __name__ == '__main__':
    generate_etymologies()
