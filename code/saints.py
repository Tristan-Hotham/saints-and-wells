"""Saint name normalisation and church-label parser for 'Whose Church Is It?'.

Everything here works at the level of the NAME a church is dedicated to
(the 'key'), not the individual historical person: 'John' covers John the
Baptist and John the Evangelist, 'James' covers James the Greater and the
Less, 'Anthony' covers Anthony of Padua and Anthony the Great, and so on,
because a label such as 'St John's Church' or 'Johanniskirche' cannot tell
them apart. All Marian titles (Our Lady of X, the Assumption, Notre-Dame,
Mariä Himmelfahrt, Nuestra Señora, Madonna ...) are one key, 'Mary'.
Dedications to Christ, the Trinity, the Holy Cross, the Holy Spirit and the
Holy Family are kept as their own keys and typed 'dominical'.

Rules, in order (documented in README and on the page):
 1. Find every saint mention in the label with its position:
    a. a saint prefix (St, St., Ste, Saint, Saints, Sankt, Hl., Heilige(r),
       Sint, San, Santa, Santo, Santi, Santos, Sant, Sant', São, SS., Santes,
       Naomh, Santissimo/a ...) followed by a name;
    b. French hyphenated forms (Saint-Martin, Sainte-Anne, Saints-Côme-et-
       Damien), ignored when they directly follow 'de', 'd'', 'du' or 'à'
       (then they are a place name, as in 'église de Saint-Rémy');
    c. fixed phrases: Marian titles, dominical titles, All Saints, Santiago;
    d. German and Dutch compound words ending in -kirche, -kapelle, -kerk,
       -kapel, -dom, -münster (Martinskirche, Nikolaikirche, Marienkirche),
       accepted only when the stem is a known name form.
 2. Each mention's name text is looked up (longest match first, up to four
    words, accents and case ignored) in a table of name forms. The table is
    a hand-written core (below) plus forms generated from the English,
    French, German, Spanish, Italian and Latin Wikidata labels of every P825
    dedication item in the data. A name not in the table becomes its own
    key (as written) if it starts with a capital letter.
 3. The first mention is the primary dedication; all are kept.
"""
import re, unicodedata, collections, json

def norm(s):
    s = s.replace("’", "'").replace("ʼ", "'").replace("`", "'")
    s = s.replace("œ", "oe").replace("Œ", "Oe").replace("æ", "ae").replace("ß", "ss")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower().strip()

# --- key types -------------------------------------------------------------
DOMINICAL = ["Christ", "Holy Trinity", "Holy Cross", "Holy Spirit", "Holy Family"]
def key_type(k):
    if k == "Mary": return "marian"
    if k in DOMINICAL: return "dominical"
    if k == "All Saints": return "all_saints"
    return "saint"

# --- hand-written core of name forms (normalised, lower case) ---------------
CORE = {
 "Mary": ["mary", "maria", "marie", "marien", "mariae", "mariä", "mariakerk", "maryam", "mair", "fair", "muire", "liebfrauen", "frauen",
          "unserer lieben frau", "unsere liebe frau", "lieben frau", "muttergottes", "gottesmutter", "mariahilf", "maria hilf", "lourdes", "fatima", "loreto",
          "notre dame", "our lady", "onze lieve vrouw", "o l vrouw", "olv", "lieve vrouw", "nuestra senora", "nossa senhora", "senhora", "madonna",
          "beata vergine", "vergine", "virgen", "vierge", "virgin", "mare de deu", "annunziata", "assunta", "immacolata", "addolorata", "maggiore",
          "asuncion", "inmaculada", "purisima", "concepcion", "concezione", "conceicao", "assuncao", "anunciacion", "assomption", "immaculee",
          "annonciation", "visitation", "visitacion", "natividad", "nativite", "pilar", "rosario", "rosaire", "carmen", "carmine", "carmo", "carmel",
          "dolores", "soledad", "merce", "merced", "mercedes", "remedios", "angustias", "piedad", "socorro", "candelaria", "consolata", "maddona",
          "marija", "mariana", "santa maria", "himmelfahrt", "heimsuchung", "maagd", "maagd der armen", "theotokos", "salute", "grazie",
          "nostra signora", "madre di dio", "vergine maria", "virgem", "mae de deus", "ermita de la virgen", "lady"],
 "Mary Magdalene": ["mary magdalene", "mary magdalen", "magdalene", "magdalen", "maria maddalena", "maddalena", "marie madeleine", "madeleine",
                    "maria magdalena", "magdalena", "magdalenen", "madalena", "maria madalena", "marie magdeleine", "magdeleine"],
 "Christ": ["christ", "christus", "christi", "cristo", "crist", "jesus", "jesu", "gesu", "jezus", "sauveur", "salvator", "salvatore", "salvador", "salvatorkirche",
            "saviour", "savior", "redeemer", "redentore", "redentor", "erloser", "heiland", "heilands", "sacre coeur", "sacred heart", "herz jesu",
            "sacro cuore", "sagrado corazon", "sagrado coracao", "sagrat cor", "heilig hart", "christ roi", "cristo re", "cristo rey", "christkonig",
            "sacrement", "sacramento", "corpus christi", "fronleichnam", "sepulcre", "sepolcro", "sepulcro", "grab", "heilig grab", "crocifisso",
            "crucifixo", "crucifix", "auferstehung", "auferstehungs", "resurrezione", "resurreccion", "resurrection", "ascension", "ascensione",
            "ascensao", "transfiguration", "trasfigurazione", "transfiguracion", "verklarung", "immanuel", "emmanuel", "olberg", "kalvarienberg",
            "calvaire", "calvario", "nome di gesu", "nom de jesus", "nombre de jesus", "bom jesus", "buon pastore", "bon pasteur", "good shepherd",
            "guter hirte", "goede herder", "cristo rei", "santissimo", "sanctissimo", "hart", "heilig hart"],
 "Holy Trinity": ["trinity", "trinite", "trinita", "trinidad", "trindade", "trinitat", "trinitatis", "dreifaltigkeit", "dreifaltigkeits",
                  "dreieinigkeit", "dreieinigkeits", "drievuldigheid", "drie-eenheid", "holy trinity"],
 "Holy Cross": ["cross", "holy cross", "holy rood", "rood", "croix", "croce", "cruz", "creu", "kreuz", "heiligkreuz", "heilig kreuz", "kruis",
                "heilig kruis", "vera cruz", "santa cruz", "santa croce", "sainte croix", "exaltation de la sainte croix"],
 "Holy Spirit": ["holy spirit", "holy ghost", "esprit", "spirito", "espiritu", "espirito", "esperit", "geist", "heilig geist", "heiligen geist",
                 "heilige geest", "geest", "santo spirito", "espiritu santo", "espirito santo"],
 "Holy Family": ["holy family", "famille", "famiglia", "familia", "familie", "heilige familie", "sacra famiglia", "sagrada familia", "sainte famille"],
 "All Saints": ["all saints", "all hallows", "toussaint", "tous les saints", "ognissanti", "tutti i santi", "todos los santos", "todos os santos",
                "allerheiligen", "alle heiligen", "tots sants", "alle heiligen"],
 "John": ["john", "jean", "johannes", "johann", "johannis", "jan", "jans", "giovanni", "juan", "joao", "joan", "ioan", "iohannes", "joannes", "jehan",
          "john the baptist", "john the evangelist", "jean baptiste", "giovanni battista", "juan bautista", "joao baptista", "joao batista",
          "johannes der taufer", "johannes baptist", "johannes de doper", "jan de doper", "jean l'evangeliste", "giovanni evangelista", "ieuan", "sion", "eoin", "seain"],
 "John of Nepomuk": ["nepomuk", "johannes nepomuk", "johann nepomuk", "giovanni nepomuceno", "juan nepomuceno", "jean nepomucene", "nepomucene", "nepomuceno"],
 "James": ["james", "jacques", "jakob", "jakobus", "jacobus", "jakobs", "jakobi", "jacobi", "giacomo", "santiago", "iago", "tiago", "jaume", "jaime", "jacob",
           "jacobs", "jacobuskerk", "diego", "jaco", "xacobe", "james the great", "james the less"],
 "Peter": ["peter", "pierre", "petrus", "piero", "petri", "pieter", "pieters", "pietro", "pedro", "pere", "pere", "pedr", "peadar", "pieter", "pietersbanden",
           "pierre aux liens", "peter ad vincula", "pietro in vincoli", "petrus in ketten", "petri ketten", "peters"],
 "Paul": ["paul", "paulus", "pauli", "paolo", "pablo", "paulo", "pau", "pol"],
 "Andrew": ["andrew", "andre", "andreas", "andrea", "andres", "andreu", "andries", "andrei", "aindrias"],
 "Michael": ["michael", "michel", "michaels", "michaelis", "michele", "miguel", "miquel", "michiel", "mihangel", "micheal", "michel archange",
             "angelo", "michael and all angels", "michele arcangelo", "miguel arcangel", "mikael"],
 "Martin": ["martin", "martins", "martini", "martinus", "maarten", "martino", "marti", "martinho", "mairtin", "martinikerk"],
 "Nicholas": ["nicholas", "nicolas", "nikolaus", "nikolai", "nicolai", "nicolaas", "nicola", "nicolo", "niccolo", "nicolau", "niklaas", "niklaus",
              "nicolaus", "klaas", "nikola", "nicolao", "nicolo", "nicholas of myra"],
 "Stephen": ["stephen", "etienne", "stephan", "stephanus", "stefanus", "stephanuskerk", "stefan", "stefano", "esteban", "estevao", "esteve", "steven", "stevens", "stephanie"],
 "Lawrence": ["lawrence", "laurence", "laurent", "laurentius", "lorenz", "lorenzo", "lourenco", "llorenc", "laurens", "lorenzen"],
 "George": ["george", "georges", "georg", "georgs", "giorgio", "jorge", "jordi", "joris", "georgius", "siors"],
 "Bartholomew": ["bartholomew", "barthelemy", "bartholomaus", "bartolomeo", "bartolome", "bartomeu", "bartolomeu", "bartholomeus"],
 "Matthew": ["matthew", "matthieu", "matthaus", "matteo", "mateo", "mateu", "mateus", "mattheus"],
 "Thomas": ["thomas", "tommaso", "tomas", "tome", "tomaso", "tomas"],
 "Anne": ["anne", "anna", "annen", "ana", "ann", "anna selbdritt"],
 "Joseph": ["joseph", "josef", "josefs", "jozef", "giuseppe", "jose", "josep", "iosif"],
 "Anthony": ["anthony", "antony", "antoine", "antonius", "antonio", "antoni", "antao", "anton"],
 "Catherine": ["catherine", "katharina", "katharinen", "caterina", "catalina", "catarina", "catharina", "katherine", "catrin", "katrien"],
 "Margaret": ["margaret", "marguerite", "margareta", "margaretha", "margherita", "margarita", "margarida", "margriet", "marina"],
 "Sebastian": ["sebastian", "sebastien", "sebastiano", "sebastiao", "sebastians", "sebastiaan", "bastian"],
 "Roch": ["roch", "rochus", "rocco", "roque", "roc", "rok"],
 "Giles": ["giles", "gilles", "aegidius", "agidius", "egidio", "gil", "gilg", "egidius"],
 "Leonard": ["leonard", "leonhard", "leonhards", "leonardo", "lienhard", "linhart"],
 "Vitus": ["vitus", "veit", "vito", "guy", "vit", "veits"],
 "Vincent": ["vincent", "vincenzo", "vicente", "vicenc", "vinzenz", "vincentius"],
 "Blaise": ["blaise", "blasius", "biagio", "blas", "bras", "blasi"],
 "Hubert": ["hubert", "hubertus", "uberto"],
 "Christopher": ["christopher", "christophe", "christophorus", "cristoforo", "cristobal", "cristovao", "cristofol", "kristoffel", "christoffel"],
 "Boniface": ["boniface", "bonifatius", "bonifacius", "bonifacio", "bonifaz"],
 "Kilian": ["kilian", "killian", "cillian", "chilian"],
 "Ambrose": ["ambrose", "ambroise", "ambrosius", "ambrogio", "ambrosio"],
 "Florian": ["florian", "floriani", "floriano"],
 "Ulrich": ["ulrich", "ulrichs", "udalricus", "udalrico", "ulderico", "ulric"],
 "Wolfgang": ["wolfgang"],
 "Rupert": ["rupert", "ruprecht", "rupertus"],
 "Gall": ["gall", "gallus", "gallo", "gal"],
 "Remigius": ["remi", "remy", "remigius", "remigio", "remacle"],
 "Lambert": ["lambert", "lambertus", "lamberto"],
 "Servatius": ["servatius", "servaas", "servais", "servazio"],
 "Willibrord": ["willibrord", "willibrordus"],
 "Bavo": ["bavo", "bavon", "baaf"],
 "Amand": ["amand", "amandus", "amando"],
 "Quentin": ["quentin", "quintinus", "quinten", "quintino"],
 "Denis": ["denis", "denys", "dionysius", "dionigi", "dionisio", "denijs"],
 "Germanus": ["germain", "germanus", "germano", "german", "garmon"],
 "Hilary": ["hilaire", "hilary", "hilarius", "ilario", "hilario"],
 "Eligius": ["eloi", "eligius", "eligio", "elooi", "loy"],
 "Mark": ["mark", "marc", "markus", "marco", "marcos", "marcus", "marc evangeliste"],
 "Luke": ["luke", "luc", "lukas", "luca", "lucas"],
 "Francis": ["francis", "francois", "franziskus", "francesco", "francisco", "francesc", "franciscus", "franz"],
 "Joan of Arc": ["joan of arc", "jeanne d'arc", "jeanne"],
 "Patrick": ["patrick", "patrice", "patricio", "patrizio", "patricius", "padraig", "patraic", "padrig"],
 "Brigid": ["brigid", "bridget", "brigit", "bride", "brigida", "brigitte", "brid", "ffraid", "bregida", "brigide"],
 "Columba": ["columba", "colmcille", "columcille", "colum cille", "colum", "colm"],
 "Colombe": ["colombe", "colomba"],
 "David": ["david", "dewi", "divy", "davy"],
 "Teilo": ["teilo", "theleau", "thelo", "eliud"],
 "Cadoc": ["cadoc", "cadog", "cado", "cattwg"],
 "Piran": ["piran", "perran", "pirin"],
 "Petroc": ["petroc", "petrock", "pedrog"],
 "Samson": ["samson", "sampson"],
 "Brioc": ["brioc", "brieuc", "briog"],
 "Ronan": ["ronan", "renan"],
 "Malo": ["malo", "maclou", "machutus"],
 "Winwaloe": ["winwaloe", "guenole", "gwenole", "winnoc", "winwalloe", "gunwalloe", "wynwallow"],
 "Corentin": ["corentin", "corentinus"],
 "Tugdual": ["tugdual", "tudwal", "tudual", "pabu"],
 "Gildas": ["gildas"],
 "Kentigern": ["kentigern", "mungo"],
 "Ninian": ["ninian", "ringan", "trinian"],
 "Aidan": ["aidan", "aedan", "aodhan"],
 "Ciaran": ["ciaran", "kieran", "piran of saighir"],
 "Kevin": ["kevin", "caoimhin"],
 "Brendan": ["brendan", "brandan", "brandon", "breandan"],
 "Finbarr": ["finbarr", "finbar", "fionnbarra", "barr"],
 "Declan": ["declan", "deaglan"],
 "Illtud": ["illtud", "illtyd", "eltut"],
 "Beuno": ["beuno"],
 "Tysilio": ["tysilio", "suliau"],
 "Deiniol": ["deiniol", "daniel of bangor"],
 "Cybi": ["cybi"],
 "Padarn": ["padarn", "paternus", "patern", "pern"],
 "Dyfrig": ["dyfrig", "dubricius"],
 "Asaph": ["asaph", "asa"],
 "Non": ["non", "nonna"],
 "Hervé": ["herve", "houarne"],
 "Méen": ["meen", "mewan", "mevenn"],
 "Melaine": ["melaine", "melanius"],
 "Efflam": ["efflam"],
 "Elizabeth": ["elizabeth", "elisabeth", "elisabetta", "isabel", "elisabet", "elsbeth"],
 "Barbara": ["barbara", "barbe", "barbora"],
 "Gertrude": ["gertrude", "gertrud", "gertrudis", "geertruida", "gertruda"],
 "Walburga": ["walburga", "walpurga", "walpurgis", "walburgis", "waldburga"],
 "Agatha": ["agatha", "agathe", "agata", "agueda", "agada"],
 "Lucy": ["lucy", "lucie", "lucia", "luzia", "llucia"],
 "Agnes": ["agnes", "agnese", "ines"],
 "Ursula": ["ursula", "ursule", "orsola"],
 "Cecilia": ["cecilia", "cecile", "cacilia", "cecilie"],
 "Helen": ["helen", "helena", "helene", "elena", "elena imperatrice"],
 "Radegund": ["radegonde", "radegund", "radegunde", "radegundis"],
 "Odile": ["odile", "ottilia", "odilia", "ottilie"],
 "Maurice": ["maurice", "mauritius", "maurizio", "mauricio", "moritz", "mauritz"],
 "Pancras": ["pancras", "pancrace", "pankratius", "pancratius", "pancrazio", "pancracio"],
 "Cyriacus": ["cyriacus", "cyriakus", "ciriaco", "cyriaque"],
 "Cyricus": ["cyr", "cyricus", "quirico", "quirze", "cirico", "cyrique", "ciro"],
 "Benedict": ["benedict", "benoit", "benedikt", "benedetto", "benito", "bento", "benet", "benedictus"],
 "Bernard": ["bernard", "bernhard", "bernardo", "bernat"],
 "Dominic": ["dominic", "dominique", "domenico", "domingo", "dominikus", "domingos"],
 "Gregory": ["gregory", "gregoire", "gregor", "gregorio", "gregorius"],
 "Clement": ["clement", "clemens", "clemente"],
 "Gervasius": ["gervasius", "gervais", "gervasio", "gervaso", "gervase"],
 "Cosmas": ["cosmas", "come", "cosma", "cosme", "kosmas"],
 "Julian": ["julian", "julien", "giuliano", "julia", "juliao", "julia"],
 "Felix": ["felix", "felice", "feliu"],
 "Saturninus": ["saturnin", "saturninus", "saturnino", "sernin", "sadurni", "cernin"],
 "Mammes": ["mammes", "mames", "mamede", "mamas", "mamete", "mamert"],
 "Pelagius": ["pelagius", "pelayo", "paio", "pelagio"],
 "Eulalia": ["eulalia", "eulalie", "olalla", "aulaire"],
 "Isidore": ["isidore", "isidro", "isidoro"],
 "Cuthbert": ["cuthbert"],
 "Chad": ["chad", "ceadda"],
 "Oswald": ["oswald", "osvaldo"],
 "Wilfrid": ["wilfrid", "wilfred"],
 "Edmund": ["edmund", "edmond"],
 "Alban": ["alban", "albans", "albano"],
 "Swithun": ["swithun", "swithin"],
 "Botolph": ["botolph", "botwulf", "botulph"],
 "Augustine": ["augustine", "augustin", "augustinus", "agostino", "agustin", "austin"],
 "Dunstan": ["dunstan"],
 "Thomas Becket": ["thomas becket", "thomas a becket", "thomas of canterbury"],
 "Faith": ["faith", "foy", "fides", "fe"],
 "Philip": ["philip", "philippe", "philippus", "filippo", "felipe", "filipe"],
 "Jude": ["jude", "judas", "judas thaddaus", "giuda"],
 "Simon": ["simon", "simone", "simao"],
 "Matthias": ["matthias", "mattia", "matias", "mathias"],
 "Barnabas": ["barnabas", "barnabe", "barnaba", "bernabe"],
 "Sylvester": ["sylvester", "silvestre", "silvestro", "sylvestre"],
 "Valentine": ["valentine", "valentin", "valentino", "valentijn"],
 "Wendelin": ["wendelin", "wendelinus"],
 "Severinus": ["severin", "severinus", "severino"],
 "Quirinus": ["quirin", "quirinus", "quirino"],
 "Emmeram": ["emmeram"],
 "Korbinian": ["korbinian", "corbinian"],
 "Liudger": ["liudger", "ludger", "ludgerus", "liudgerus"],
 "Ansgar": ["ansgar", "anskar"],
 "Gotthard": ["gotthard", "gothard", "gottardo"],
 "Zeno": ["zeno", "zenone", "zenon"],
 "Vigilius": ["vigilius", "vigilio", "vigile"],
 "Charles Borromeo": ["carlo", "carlo borromeo", "charles borromee", "karl borromaus", "carlos borromeo"],
 "Bernardino": ["bernardino"],
 "Rita": ["rita"],
 "Teresa": ["teresa", "therese", "theresia", "tereza"],
 "Clare": ["clare", "claire", "chiara", "clara"],
 "Martha": ["martha", "marthe", "marta"],
 "Ignatius": ["ignatius", "ignace", "ignazio", "ignacio"],
 "Louis": ["louis", "luigi", "ludwig", "luis", "lluis"],
 "Pantaleon": ["pantaleon", "pantaleone", "pantaleo"],
 "Medard": ["medard", "medardus"],
 "Apollinaris": ["apollinaris", "apollinare", "apollinaire"],
 "Innocents": ["innocents", "innocenti", "inocentes", "unschuldige kinder"],
 "Fourteen Holy Helpers": ["nothelfer", "vierzehn nothelfer", "quatorze saints auxiliaires"],
 "Angels": ["angels", "anges", "angeli", "angeles", "engel", "schutzengel", "angeli custodi"],
}
# early medieval saints of Ireland, Scotland, Wales, Cornwall and Brittany not already above (the 'Insular Celtic' group)
CELTIC_EXTRA = {
 "Senan": ["senan"], "Mel": ["mel"], "Adomnan": ["adomnan", "eunan", "adamnan"], "Fechin": ["fechin"], "Colman": ["colman"], "Canice": ["canice", "cainnech", "kenneth"],
 "Ita": ["ita", "ide"], "Moling": ["moling"], "Ailbe": ["ailbe"], "Enda": ["enda"], "Finnian": ["finnian", "finian"], "Comgall": ["comgall"],
 "Carthage": ["carthage", "mochuda"], "Flannan": ["flannan"], "Munchin": ["munchin"], "Manchan": ["manchan"], "Attracta": ["attracta"], "Molaise": ["molaise", "laserian"],
 "Fillan": ["fillan"], "Serf": ["serf", "serf's"], "Moluag": ["moluag"], "Maelrubha": ["maelrubha", "maree"], "Machar": ["machar"], "Drostan": ["drostan"],
 "Kessog": ["kessog"], "Ternan": ["ternan"], "Blane": ["blane"], "Devenick": ["devenick"],
 "Tudno": ["tudno"], "Seiriol": ["seiriol"], "Brynach": ["brynach"], "Gwynllyw": ["gwynllyw", "woolos"], "Dogmael": ["dogmael", "dogfael"], "Cadfan": ["cadfan"],
 "Cynog": ["cynog"], "Tydfil": ["tydfil"], "Gwladys": ["gwladys"], "Winefride": ["winefride", "gwenffrewi", "winifred"], "Dwynwen": ["dwynwen"], "Elian": ["elian"],
 "Mawgan": ["mawgan", "meugan"], "Keyne": ["keyne", "ceinwen"], "Euny": ["euny"], "Ia": ["ia", "ives"], "Breage": ["breage"], "Gwinear": ["gwinear"], "Austell": ["austell"],
 "Germoe": ["germoe"], "Sennen": ["sennen"], "Buryan": ["buryan"], "Endellion": ["endellion"], "Neot": ["neot"], "Nectan": ["nectan"], "Carantoc": ["carantoc", "carannog"],
 "Kea": ["kea", "ke"], "Mabyn": ["mabyn"], "Minver": ["minver"], "Tudy": ["tudy"], "Enodoc": ["enodoc"], "Madron": ["madron"], "Gulval": ["gulval"], "Ludgvan": ["ludgvan"],
 "Mylor": ["mylor"], "Feock": ["feock"], "Clether": ["clether"], "Gerrans": ["gerrans"], "Goran": ["goran", "gorran"], "Maudez": ["maudez", "mawes", "maudet"],
 "Guirec": ["guirec"], "Envel": ["envel"], "Herbot": ["herbot"], "Jaoua": ["jaoua"], "Gonéry": ["gonery"], "Thégonnec": ["thegonnec"], "Briac": ["briac"], "Jacut": ["jacut"],
 "Mélar": ["melar"], "Conogan": ["conogan"], "Goustan": ["goustan"], "Meriadoc": ["meriadec", "meriadoc"], "Kentigern": ["kentigern", "mungo"],
}
CORE.update({k: v for k, v in CELTIC_EXTRA.items() if k not in CORE})
CORE.update({"Fabian": ["fabian", "fabiano", "fabien"], "Romanus": ["romanus", "romain", "romano", "roma", "roman"], "Cyprian": ["cyprian", "cyprien", "cipriano", "cebria"],
             "Wenceslas": ["wenceslas", "wenzel", "wenzeslaus", "venceslao", "wenceslaus"], "Pol": ["pol"]})
CORE["Paul"] = [f for f in CORE["Paul"] if f != "pol"]
for k, fs in {"Sebastian": ["sebastia"], "Matthew": ["mathieu"], "Colombe": ["coloma"], "Clement": ["climent"], "Margaret": ["margarethen", "margareth"],
              "George": ["jurgen", "jorgen", "joris"], "Isidore": ["isidre"], "Holy Cross": ["crucis", "sanctae crucis"], "Andrew": ["andra", "andrae"], "Christ": ["crocefisso"],
              "Giles": ["agydius", "aegidien", "agidien", "aegydius"], "James": ["iacopo", "jacopo"], "Marina": ["marinha"], "Augustine": ["agusti"], "Mary": ["pieta"]}.items():
    CORE[k] = CORE.get(k, []) + fs
# names that would otherwise be read as words: never accept as raw fallback keys
STOP = set("""church chapel kirche kapelle kerk kapel eglise chapelle chiesa cappella iglesia capilla igreja capela ermita ermida esglesia capella
cathedral cathedrale catedral cattedrale dom munster basilica basilique basilika parish parochial pfarrkirche abbey abbaye abbazia monastery
the of and und et e y en de di da do du des del della dei degli la le les l il el lo los las a im am in an zu zum zur van der die das den
road street lane rue via calle rua strasse place square well wells school college hospital hall house mission catholic roman methodist
baptist evangelische reformierte protestant protestantische katholische kath orthodox orthodoxe old new nouvelle neue alte vieille casa misericordia""".split())
MARIAN_RE = re.compile(r"\b(mary|our lady|virgin|notre[- ]dame|madonna|assumption|annunciation|immaculate|visitation|nativity of mary|queen of heaven|"
                       r"hodegetria|theotokos|rosary|loreto|lourdes|fatima|fátima|carmel|sorrows|pillar|help of christians|perpetual help|good counsel|"
                       r"star of the sea|holy name of mary|holy house|presentation of mary|dormition|purification|mercy|graces|snows|consolation|peace|"
                       r"good help|good health|guardia|caravaggio|remedios|angels|nostra signora|vierge|marie|maria|virgen)\b", re.I)
NOT_MARY = re.compile(r"margaret mary|mary magdalen|mary of egypt|mary of bethany|maria goretti|mary of the cross|mary mackillop|magdal|guardian angel|marina|mariana", re.I)
DOM_RULES = [("Holy Trinity", r"\btrinity\b"), ("Holy Cross", r"\b(cross|rood|crucifix)\b"), ("Holy Spirit", r"\b(holy spirit|holy ghost|pentecost)\b"),
             ("Holy Family", r"\bholy family\b"), ("All Saints", r"\ball saints|all hallows"),
             ("Christ", r"\b(jesus|christ|salvator|saviour|savior|redeemer|sacred heart|holy name|good shepherd|ascension|resurrection|transfiguration|"
                        r"corpus christi|eucharist|blessed sacrament|holy sepulchre|holy face|infant jesus|nativity of jesus|epiphany|holy blood|divine mercy|"
                        r"christ the king|sacrament)\b")]
QID_OVERRIDE = {"Q448171": "Colombe", "Q550505": "Germanus", "Q442516": "Germanus", "Q221522": "John of Nepomuk", "Q192236": "Thomas Becket",
                "Q159834": "Hubert", "Q212850": "Vitus", "Q236326": "Columba", "Q331697": "David", "Q80979": "Brigid", "Q165479": "Patrick",
                "Q7226": "Joan of Arc", "Q2664456": "Marina", "Q894757": "Botolph", "Q1515920": "Gervasius", "Q76486": "Cosmas",
                "Q11841156": "Cosmas", "Q514765": "Cyricus", "Q63070": "Mary Magdalene", "Q216946": "Charles Borromeo", "Q558148": "Leonard",
                "Q1065053": "Mary", "Q728388": "Angels", "Q81989": "Gabriel", "Q51625": "Christ", "Q20460": "Christ"}
# Marina of Aguas Santas is a Galician martyr; keep her apart from Margaret (whom Italy also calls Marina)
CORE["Margaret"] = [f for f in CORE["Margaret"] if f != "marina"]
CORE["Marina"] = ["marina", "mariña", "marinha"]

def clean_name(s):
    """Strip saint prefixes and qualifiers from a dedication label; return (full, first) normalised."""
    s = norm(s)
    s = re.sub(r"^(?:(saints?|sainte?s?|st\.?|ste\.?|sts\.?|ss\.?|san|santa|santo|santi|santos|santas|sankt|hl\.?|heiliger?|heilige|sant|sao|sint|s\.|beata|beato|blessed|archange|archangel|apostle)\s*[- ]\s*|sant'\s*)", "", s)
    s = re.sub(r"^(saints?|sainte?|st\.?|san|santa|santo|santi|sankt|archange)\s+", "", s)
    full = re.split(r"[,(]", s)[0].strip()
    first = re.split(r"\s+(?:of|de|di|d'|von|van|da|do|du|des|del|della|dei|le|la|il|el|the|der|die|y|e|et|und|and|en|&|from|aus|von)\s+|\s+(?:i|ii|iii|iv|v|vi|vii|viii|ix|x|xi|xii|xiii|xxiii)$|[ -]", full)[0]
    first = re.sub(r"^d'", "", first).strip(" '.")
    return full, first

EVENT_RE = re.compile(r"^(?:feast of (?:the )?|the )?(?:nativity|birth|decollation|beheading|conversion|martyrdom|translation|presentation|dedication|"
                      r"apparition|vision|chair|exaltation|invention|finding|stigmata|transitus|death|assumption|coronation|holy name|heart|patronage) of (?:the )?(.+)$", re.I)

def key_for_ded(q, lab):
    """Name-level key for a P825 dedication item from its labels."""
    if q in QID_OVERRIDE: return QID_OVERRIDE[q]
    en = lab.get("en") or lab.get("fr") or lab.get("it") or lab.get("de") or lab.get("es") or lab.get("la") or ""
    en = en.split("/")[0].strip()
    if re.search(r"^candlemas$", en, re.I): return "Mary"
    m = EVENT_RE.match(en)
    if m and not re.search(r"\b(mary|our lady|virgin|jesus|christ|lord)\b", m.group(1), re.I) and not re.search(r"cross", m.group(1), re.I):
        en = m.group(1)              # e.g. 'Decollation of Saint John the Baptist' -> John
    if not NOT_MARY.search(en) and re.search(r"\b(mary|our lady|virgin mary|blessed virgin|holy virgin|virgin of|notre[- ]dame|madonna|assumption|annunciation|immaculate|"
                     r"visitation|queen of heaven|hodegetria|theotokos|rosary|loreto|lourdes|f[a\u00e1]tima|mount carmel|sorrows|pillar|help of christians|perpetual help|"
                     r"good counsel|star of the sea|holy house|dormition|purification|nostra signora|vierge|virgen|our mother|of the virgin)\b|^virgin\b", en, re.I):
        return "Mary"
    for k, pat in DOM_RULES:
        if re.search(pat, en, re.I) and not re.search(r"christopher|christina|christine|christian\b(?! cross)", en, re.I):
            return k
    full, first = clean_name(en)
    f = FORM.get(full) or FORM.get(first)
    if f: return f
    return first[:1].upper() + first[1:] if first else None

FORM = {}
def build_forms(ded_labels, freq):
    """FORM: normalised name form -> key. CORE first; then forms from every dedication's labels."""
    for k, fs in CORE.items():
        for f in fs: FORM.setdefault(norm(f), k)
    auto = collections.defaultdict(collections.Counter)
    dkey = {}
    for d in ded_labels:
        q = d["d"]; k = key_for_ded(q, d)
        if not k: continue
        dkey[q] = k
        for lang in ("en", "fr", "de", "es", "it", "la"):
            if d.get(lang):
                full, first = clean_name(d[lang])
                for f in {full, first}:
                    if f and len(f) >= 3 and f not in STOP: auto[f][k] += freq.get(q, 0) + 1
    for f, c in auto.items():
        if f not in FORM: FORM[f] = c.most_common(1)[0][0]
    return dkey

# --- label parser ------------------------------------------------------------
UP = "A-ZÀ-ÖØ-ÞŒÆ"
# longest alternatives first; a prefix must be followed by a space or hyphen unless it ends in '.' or an apostrophe
PREFIX = (r"(?<![\w'’.-])(?:(?:Santissim[oa]|Sant[íi]ssim[oa]|Sant[íi]sim[oa]|Santos|Santas|Santes|Santa|Santo|Santi|Sankt|Sant|San|São|Sao|"
          r"Saints|Saint|SAINT|Sinte|Sint|Heiligen|Heiliger|Heilige|Naomh|Sts|Ste|St|ST|SS|Ss)(?:\s+|\s*-\s*|\.\s*-?\s*)|"
          r"(?:Sant['’]|Hll\.|hll\.|Hlg\.|Hl\.|hl\.|H\.\s?H\.|HH\.|H\.|S\.)\s*-?\s*)")
RX_PREFIX = re.compile(PREFIX + r"(?=[" + UP + r"a-z])")
RX_FR = re.compile(r"(?<![\w'’-])(Saintes|Saints|Sainte|Saint|Ste|St)-(?=[" + UP + r"])")
PHRASES = [(k, re.compile(p, re.I)) for k, p in [
    ("Mary", r"notre[- ]dame|our lady|blessed virgin|virgin mary|unser(?:er)? lieben frau|liebfrauen|frauenkirche|marien(?:kirche|kapelle|dom|m[üu]nster|kirchlein)|"
             r"\bmari[aä][- ]?(?:hilf|himmelfahrt|geburt|heimsuchung|empf[äa]ngnis|verk[üu]ndigung|schnee|trost|rosenkranz|k[öo]nigin|lichtmess|namen|opferung|reinigung|schmerzen)|"
             r"\bmari[äa]\b|onze[- ]lieve[- ]vrouw|o\.\s?l\.\s?vrouw|\bolv\b|nuestra se[ñn]ora|ntra\.? sra|nossa senhora|n\.?ª\s?s\.?ª|\bsenhora\b|\bmadonna\b|beata vergine|"
             r"\bvergine\b|\bvirgen\b|mare de d[ée]u|\bannunziata\b|\bassunta\b|\bimmacolata\b|\baddolorata\b|\basunci[óo]n\b|\binmaculada\b|\bpur[íi]sima\b|"
             r"\bconcepci[óo]n\b|\bconcezione\b|\bconcei[çc][ãa]o\b|\bassun[çc][ãa]o\b|\bassomption\b|\bimmacul[ée]e\b|\bannonciation\b|\bvisitation\b|\bvisitaci[óo]n\b|"
             r"\bnatividad\b|\bnativit[ée] de (?:la vierge|marie|notre)|\bpilar\b|\brosario\b|\bcarmen\b|\bcarmine\b|\bcarmo\b|\bdolores\b|\bsoledad\b|\bremedios\b|"
             r"\bangustias\b|\bcandelaria\b|\bmuttergottes|\bgottesmutter|\blourdes|\bf[áa]tima\b|\bloreto\b|\bmaagd\b|\bmariakerk|\bnostra signora|\bvierge\b|"
             r"\bvirgem\b|\bmariahilf|\bmercè\b|\bmerced\b|\bpiedad\b|\bsocorro\b|\bconsolata\b|\blady chapel\b"),
    ("Christ", r"sacr[ée][- ]c(?:œ|oe)ur|sacred heart|herz[- ]jesu|heilig[- ]hart|sacro cuore|sagrado coraz[óo]n|sagrado cora[çc][ãa]o|sagrat cor|christ church|christchurch|"
               r"christuskirche|christ the king|christ[- ]roi|cristo re\b|cristo rey|christk[öo]nig|salvatorkirche|erl[öo]ser|heilands|\bredentore\b|\bredeemer\b|"
               r"corpus christi|fronleichnam|heilig[- ]grab|\bgesù\b|bom jesus|santo cristo|crocifisso|crucifixo|auferstehung|\bimmanuel|\bemmanuel\b|"
               r"[öo]lberg|kalvarienberg|\bcalvaire\b|\bcalvario\b|buon pastore|bon[- ]pasteur|good shepherd|guten? hirten?|goede herder|transfiguration|trasfigurazione|"
               r"saint[- ]sacrement|sant[íi]simo sacramento|santissimo sacramento|santissimo salvatore|\bsalvador\b|\bsalvatore\b|\bsalvator\b|saint[- ]sauveur|"
               r"\bascension\b|\bascensione\b|\bascensi[óo]n\b|\bchristus\b|\bjezus\b|\bjes[úu]s\b"),
    ("Holy Trinity", r"trinity|trinit[ée]|trinit[àa]|trinidad|trindade|trinitat|trinitatis|dreifaltigkeit|dreieinigkeit|drievuldigheid"),
    ("Holy Cross", r"holy cross|holy rood|sainte[- ]croix|santa croce|santa cruz|santa creu|heilig[- ]?kreuz|kreuzkirche|kreuzkapelle|heilig[- ]kruis|kruiskerk|vera cruz|\bst\.? cross\b"),
    ("Holy Spirit", r"holy spirit|holy ghost|saint[- ]esprit|santo spirito|esp[íi]ritu santo|esp[íi]rito santo|heilig[- ]?geist|heiligen[- ]geist|heilige[- ]geest|sant esperit"),
    ("Holy Family", r"holy family|sainte[- ]famille|sacra famiglia|sagrada fam[íi]lia|heilige[- ]familie|heilig[- ]familie"),
    ("All Saints", r"all saints|all hallows|toussaint|tous[- ]les[- ]saints|ognissanti|tutti i santi|todos los santos|todos os santos|allerheiligen|alle heiligen|tots sants"),
    ("James", r"\bsantiago\b"),
]]
SUFFIX = r"(?i:kirche|kapelle|kirchlein|dom|m[üu]nster|kathedrale|basilika|kerk|kapel|kerkje|kathedraal|basiliek)"
RX_COMP = re.compile(r"(?<![\w])([" + UP + r"][a-zäöüßë]+)-?" + SUFFIX + r"\b")
RX_SUFFIX_TOKEN = re.compile(r"(?:kirche|kapelle|kirchlein|dom|munster|kathedrale|basilika|kerk|kapel|kerkje|kathedraal|basiliek)$")
CONNECT = {"and", "und", "e", "y", "et", "en", "&", "i", "ed"}
BREAK = set("""church chapel kirche kapelle kerk kapel eglise chapelle chiesa cappella iglesia capilla igreja capela ermita ermida esglesia capella
cathedral cathedrale catedral cattedrale dom munster basilica basilique basilika parish pfarrkirche abbey abbaye abbazia monastery priory
road street lane rue via calle rua strasse place square well wells school college hospital hall house mission catholic roman methodist
baptist evangelische reformierte protestant katholische kath orthodox orthodoxe old new kerkje kirchlein oratorio oratory pieve parrocchiale
convento convent kloster klooster stift tower toren ruins ruin""".split())
TOKEN_RX = re.compile(r"[\w'’]+|[-,()/;:\[\]]")

def lookup(tokens):
    """Longest match of up to four tokens; returns (key, n_tokens_used) or (None, 0)."""
    for n in (4, 3, 2, 1):
        if len(tokens) < n: continue
        t = " ".join(norm(x) for x in tokens[:n])
        t = re.sub(r"'s$|'$", "", t)
        cands = [t]
        if n == 1:
            s = RX_SUFFIX_TOKEN.sub("", t)
            cands += [s, re.sub(r"s$", "", s), re.sub(r"(i|is)$", "", s), re.sub(r"i$", "us", s), re.sub(r"is$", "es", s), re.sub(r"en$", "", s), re.sub(r"s$", "", t)]
        for c in cands:
            if len(c) >= 2 and c in FORM: return FORM[c], n
    return None, 0

def name_tokens(text):
    """Word tokens after a prefix (with the end offset of each), stopping at punctuation or a church word."""
    out, ends = [], []
    for m in TOKEN_RX.finditer(text):
        w = m.group(0)
        if w in ",()/;:[]": break
        if w == "-": continue
        nw = norm(w)
        if nw in BREAK or RX_SUFFIX_TOKEN.fullmatch(nw): break
        out.append(w); ends.append(m.end())
        if len(out) >= 6: break
    return out, ends

def _fallback(tok):
    w = re.sub(r"['’]s?$", "", tok)
    w2 = RX_SUFFIX_TOKEN.sub("", norm(w))
    if w2 != norm(w) and len(w2) >= 3: w = w[:len(w2)]
    if w[:1].isupper() and len(w) >= 3 and norm(w) not in STOP and not w.isupper(): return w
    return None

def _prefix_mention(label, start, end, res, spans):
    toks, ends = name_tokens(label[end:])
    k, n = lookup(toks)
    if not k and toks: k = _fallback(toks[0]); n = 1 if k else 0
    if not k: return
    res.append((start, k, "prefix")); spans.append((start, end + ends[max(n, 1) - 1]))
    rest = toks[max(n, 1):]
    if len(rest) >= 2 and norm(rest[0]) in CONNECT:
        nxt = rest[1:]
        if nxt and norm(nxt[0]).rstrip(".") in ("st", "saint", "sainte", "san", "sant", "santa", "santo", "sankt", "hl", "sint"): nxt = nxt[1:]
        k2, _ = lookup(nxt)
        if k2: res.append((start + 1, k2, "second"))

def mentions(label):
    """All (position, key, how) mentions in one label, primary first."""
    res, spans = [], []
    if not label: return res
    for m in RX_FR.finditer(label):
        pre = label[max(0, m.start() - 4):m.start()].lower()
        if re.search(r"(?:\bde |\bd'|\bd’|\bdu |\bà )$", pre): continue   # a place name such as 'église de Saint-Rémy'
        _prefix_mention(label.replace("-", " "), m.start(), m.end(), res, spans)
    for m in RX_PREFIX.finditer(label):
        if any(a <= m.start() < b for a, b in spans) or RX_FR.match(label, m.start()): continue
        _prefix_mention(label, m.start(), m.end(), res, spans)
    for m in RX_COMP.finditer(label):
        if any(a <= m.start() < b for a, b in spans): continue
        k, _ = lookup([m.group(1)])
        if k and norm(m.group(1)) not in STOP: res.append((m.start(), k, "compound")); spans.append((m.start(), m.end()))
    for k, rx in PHRASES:
        for m in rx.finditer(label):
            if any(a <= m.start() < b for a, b in spans): continue
            res.append((m.start(), k, "phrase"))
    res.sort(key=lambda r: r[0])
    seen, out = set(), []
    for pos, k, how in res:
        if k in seen: continue
        seen.add(k); out.append((pos, k, how))
    return out

def parse(label):
    """Keys (primary first) for a church label. Uses the part before the first comma or bracket when that part names a saint."""
    if not label: return []
    head = re.split(r"[,(]", label)[0]
    r = mentions(head)
    if not r and head != label: r = mentions(label)
    return [k for _, k, _ in r]
