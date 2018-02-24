'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''

from sys import stderr
#import logging
#from flask import g
from models.dbtree import DbTree
from models.gen.person import Weburl
from models.gen.note import Note
from models.gen.cypher import Cypher
import shareds

class Place:
    """ Paikka
            
        Properties:
                handle          
                change
                id                  esim. "P0001"
                type                str paikan tyyppi
                pname               str paikan nimi
                names[]:
                   name             str paikan nimi
                   lang             str kielikoodi
                   datetype         str aikavälin tyyppi
                   daterange_start  str aikavälin alku
                   daterange_stop   str aikavälin loppu
                coord_long          str paikan pituuspiiri
                coord_lat           str paikan leveyspiiri
                urls[]:
                    priv            str url salattu tieto
                    href            str url osoite
                    type            str url tyyppi
                    description     str url kuvaus
                placeref_hlink      str paikan osoite
                noteref_hlink       str huomautuksen osoite (tulostuksessa Note-olioita)
     """

    def __init__(self, locid="", ptype="", pname="", level=None):
        """ Luo uuden place-instanssin. 
            Argumenttina voidaan antaa valmiiksi paikan uniq_id, tyylin, nimen
            ja (tulossivua varten) mahdollisen hierarkiatason
        """
        self.id = locid
        self.type = ptype
        self.pname = pname
        if level != None:
            self.level = level
        # Gramps-tietoja
        self.handle = ''
        self.change = ''
        self.names = []
        self.coord_long = ''
        self.coord_lat = ''
        self.urls = []
        self.placeref_hlink = ''
        self.noteref_hlink = []
    
    
    def __str__(self):
        try:
            lv = self.level
        except:
            lv = ""
        desc = "Place {}: {} ({}) {}".format(self.id, self.pname, self.type, lv)
        return desc
    
    
    def get_place_data_by_id(self):
        """ Luetaan kaikki paikan tiedot ml. nimivariaatiot (tekstinä)
            Nimivariaatiot talletetaan kenttään pname, 
            esim. [["Svartholm", "sv"], ["Svartholma", None]]
            #TODO: Ei hieno, po. Place_name objects!
        """
        plid = self.uniq_id
        place_result = shareds.driver.session().run(Cypher.place_data_by_id,
                                                    place_id=plid)
        
        for place_record in place_result:
            self.change = place_record["place"]["change"]
            self.id = place_record["place"]["id"]
            self.type = place_record["place"]["type"]
            names = place_record["names"]
            self.pname = Place.namelist_w_lang(names)
            self.coord_long = place_record["place"]["coord_long"]
            self.coord_lat = place_record["place"]["coord_lat"]

            urls = place_record['urls']
            for url in urls:
                weburl = Weburl()
                weburl.priv = url["priv"]
                weburl.href = url["href"]
                weburl.type = url["type"]
                weburl.description = url["description"]
                self.urls.append(weburl)

            notes = place_record['notes']
            for note in notes:
                n = Note()
                n.priv = note["priv"]
                n.type = note["type"]
                n.text = note["text"]
                self.noteref_hlink.append(n)
            
        return True
    
    
    @staticmethod       
    def get_places():
        """ Luetaan kaikki paikat kannasta
        #TODO Eikö voisi palauttaa listan Place-olioita?
        """

        titles = ['uniq_id', 'gramps_handle', 'change', 'id', 'type', 'pname',
                  'coord_long', 'coord_lat']
        lists = []

        result = shareds.driver.session().run(Cypher.places_get)
        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["p"]['gramps_handle']:
                data_line.append(record["p"]['gramps_handle'])
            else:
                data_line.append('-')
            if record["p"]['change']:
                data_line.append(record["p"]['change'])
            else:
                data_line.append('-')
            if record["p"]['id']:
                data_line.append(record["p"]['id'])
            else:
                data_line.append('-')
            if record["p"]['type']:
                data_line.append(record["p"]['type'])
            else:
                data_line.append('-')
            if record["p"]['pname']:
                data_line.append(record["p"]['pname'])
            else:
                data_line.append('-')
            if record["p"]['coord_long']:
                data_line.append(record["p"]['coord_long'])
            else:
                data_line.append('-')
            if record["p"]['coord_lat']:
                data_line.append(record["p"]['coord_lat'])
            else:
                data_line.append('-')
                
            lists.append(data_line)
        
        return (titles, lists)


    @staticmethod       
    def get_place_names():
        """ Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat

            Esim.
╒═══════╤════════════╤══════════════════════════════╤════════════╤════════════╤═══════════════════════╤═══════════════════════╕
│"id"   │"type"      │"name"                        │"coord_long"│"coord_lat" │"upper"                │"lower"                │
╞═══════╪════════════╪══════════════════════════════╪════════════╪════════════╪═══════════════════════╪═══════════════════════╡
│"28427"│"Building"  │[["Ahlnäs",""]]               │""          │""          │[["28419","Farm",      │[[null,null,null,null]]│
│       │            │                              │            │            │"Labby 6 Smeds",""]]   │                       │
├───────┼────────────┼──────────────────────────────┼────────────┼────────────┼───────────────────────┼───────────────────────┤
│"28795"│"Hautausmaa"│[["Ahveniston hautausmaa",""]]│"24.4209"   │"60.9895"   │[[null,null,null,null]]│[[null,null,null,null]]│
├───────┼────────────┼──────────────────────────────┼────────────┼────────────┼───────────────────────┼───────────────────────┤
│"28118"│"Farm"      │[["Ainola",""]]               │"25.0873870"│"60.453655" │[[null,null,null,null]]│[[null,null,null,null]]│
├───────┼────────────┼──────────────────────────────┼────────────┼────────────┼───────────────────────┼───────────────────────┤
│"28865"│"City"      │[["Akaa",""],["Ackas","sv"]]  │"23.9481353"│"61.1881064"│[[null,null,null,null]]│[[null,null,null,null]]│
├───────┼────────────┼──────────────────────────────┼────────────┼────────────┼───────────────────────┼───────────────────────┤
│"28354"│"Building"  │[["Alnäs",""]]                │""          │""          │[["28325","Farm","Inger│[[null,null,null,null]]│
│       │            │                              │            │            │mansby 4 Sjökulla",""],│                       │
│       │            │                              │            │            │["28325","Farm", "Lappt│                       │
│       │            │                              │            │            │räsk Ladugård",""]]    │                       │
└───────┴────────────┴──────────────────────────────┴────────────┴────────────┴───────────────────────┴───────────────────────┘
"""

        def combine_places(field):
            """ Kenttä field sisältää Places-tietoja tuplena [[28101, "City", 
                "Lovisa", "sv"]].
                Jos sama Place esiintyy uudestaan, niiden nimet yhdistetään.
                Jos nimeen on liitetty kielikoodi, se laitetaan sulkuihin mukaan.
            """
            namedict = {}
            for near in field:
                if near[0]: # id of a lower place
                    if near[0] in namedict:
                        # Append name to existing Place
                        namedict[near[0]].pname.extend(Place.namelist_w_lang( (near[2:],) ))
                    else:
                        # Add a new Place
                        namedict[near[0]] = \
                            Place(near[0], near[1], Place.namelist_w_lang( (near[2:],) ))
            return list(namedict.values())

        ret = []
        result = shareds.driver.session().run(Cypher.places_get_names)
        for record in result:
            # Luodaan paikka ja siihen taulukko liittyvistä hierarkiassa lähinnä
            # alemmista paikoista
            p = Place(record['id'], record['type'], Place.namelist_w_lang(record['name']))
            p.coord_long = record['coord_long']
            p.coord_lat = record['coord_lat']
            p.uppers = combine_places(record['upper'])
            p.lowers = combine_places(record['lower'])
            ret.append(p)
        return ret

    @staticmethod       
    def namelist_w_lang(field):
        """ Muodostetaan nimien luettelo jossa on mahdolliset kielikoodit 
            mainittuna.
            Jos sarakkeessa field[1] on mainittu kielikoodi
            se lisätään kunkin nimen field[0] perään suluissa
        """
        names = []
        for n in field:
            if n[1]:
                # Name with langiage code
                names.append("{} ({})".format(n[0], n[1]))
            else:
                names.append(n[0])
        return names


    @staticmethod       
    def get_place_tree(locid):
        """ Haetaan koko paikkojen ketju paikan locid ympärillä
            Palauttaa listan paikka-olioita ylimmästä alimpaan. 
            Jos hierarkiaa ei ole, listalla on vain oma Place.
            
            Esim. Tuutarin hierarkia 
                  2 Venäjä -> 1 Inkeri -> 0 Tuutari -> -1 Nurkkala
                  tulee tietokannasta näin:
            ╒════╤═══════╤═════════╤══════════╤═══════╤═════════╤═════════╕
            │"lv"│"id1"  │"type1"  │"name1"   │"id2"  │"type2"  │"name2"  │
            ╞════╪═══════╪═════════╪══════════╪═══════╪═════════╪═════════╡
            │"2" │"21774"│"Region" │"Tuutari" │"21747"│"Country"│"Venäjä" │
            ├────┼───────┼─────────┼──────────┼───────┼─────────┼─────────┤
            │"1" │"21774"│"Region" │"Tuutari" │"21773"│"State"  │"Inkeri" │
            ├────┼───────┼─────────┼──────────┼───────┼─────────┼─────────┤
            │"-1"│"21775"│"Village"│"Nurkkala"│"21774"│"Region" │"Tuutari"│
            └────┴───────┴─────────┴──────────┴───────┴─────────┴─────────┘
            Metodi palauttaa siitä listan
                Place(result[0].id2) # Artjärvi City
                Place(result[0].id1) # Männistö Village
                Place(result[1].id1) # Pekkala Farm
            Muuttuja lv on taso: 
                >0 = ylemmät, 
                 0 = tämä, 
                <0 = alemmat
        """
        
        t = DbTree(shareds.driver, Cypher.place_hier_by_id, 'pname', 'type')
        t.load_to_tree_struct(locid)
        if t.tree.depth() == 0:
            # Vain ROOT-solmu: Tällä paikalla ei ole hierarkiaa. 
            # Hae oman paikan tiedot ilman yhteyksiä
            with shareds.driver.session() as session:
                result = session.run(Cypher.place_root_by_id, locid=int(locid))
                record = result.single()
                t.tree.create_node(record["name"], locid, parent=0, 
                                   data={'type': record["type"]})
        ret = []
        for node in t.tree.expand_tree(mode=t.tree.DEPTH):
            print ("{} {} {}".format(t.tree.depth(t.tree[node]), t.tree[node], 
                                     t.tree[node].bpointer))
            if node != 0:
                n = t.tree[node]

                # Get all names
                with shareds.driver.session() as session:
                    result = session.run(Cypher.place_name_by_id, locid=node)
                    record = result.single()
                    # Kysely palauttaa esim. [["Svartholm","sv"],["Svartholma",""]]
                    # josta tehdään ["Svartholm (sv)","Svartholma"]
                    names = Place.namelist_w_lang(record['names'])

                p = Place(locid=node, ptype=n.data['type'], \
                          pname=names, level=t.tree.depth(n))
                print ("# {}".format(p))
                p.parent = n.bpointer
                ret.append(p)
        return ret


    @staticmethod       
    def get_place_events(loc_id):
        """ Haetaan paikkaan liittyvät tapahtumat sekä
            osallisen henkilön nimitiedot.
            
        Palauttaa esimerkin mukaiset tiedot:
        ╒═══════╤═════════╤══════════════════════════════╤═════════╤════════════╕
        │"uid"  │"role"   │"names"                       │"etype"  │"edate"     │
        ╞═══════╪═════════╪══════════════════════════════╪═════════╪════════════╡
        │"36151"│"Primary"│[["Also Known As","Anna Katari│"Baptism"│"1738-01-17"│
        │       │         │na","Florin",""],["Birth Name"│         │            │
        │       │         │,"Anna Catharina","Florin",""]│         │            │
        │       │         │]                             │         │            │
        ├───────┼─────────┼──────────────────────────────┼─────────┼────────────┤
        │"36314"│"Kummi"  │[["Birth Name","Johan","Mennan│"Baptism"│"1738-01-17"│
        │       │         │der",""]]                     │         │            │
        └───────┴─────────┴──────────────────────────────┴─────────┴────────────┘
        """

        result = shareds.driver.session().run(Cypher.place_get_events, 
                                              locid=int(loc_id))
        ret = []
        for record in result:
            p = Place()
            p.uid = record["uid"]
            p.etype = record["etype"]
            p.edate = record["edate"]
            p.edatetype = record["edatetype"]
            p.edaterange_start = record["edaterange_start"]
            p.edaterange_stop = record["edaterange_stop"]
            if p.edaterange_start != '' and p.edaterange_stop != '':
                p.edaterange = p.edaterange_start + " - " + p.edaterange_stop
            elif p.edaterange_start != '':
                p.edaterange = p.edaterange_start + " - "
            elif p.edaterange_stop != '':
                p.edaterange = " - " + p.edaterange_stop
            p.role = record["role"]
            p.names = record["names"]   # tuples [name_type, given_name, surname]
            ret.append(p)
        return ret


    @staticmethod       
    def get_total():
        """ Tulostaa paikkojen määrän tietokannassa """

        results =  shareds.driver.session().run(Cypher.place_count)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Placeobj*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Type: " + self.type)
        if self.pname != '':
            print ("Pname: " + self.pname)
        if self.coord_long != '':
            print ("Coord_long: " + self.coord_long)
        if self.coord_lat != '':
            print ("Coord_lat: " + self.coord_lat)
        if self.placeref_hlink != '':
            print ("Placeref_hlink: " + self.placeref_hlink)
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                print ("Noteref_hlink: " + self.noteref_hlink[i])
        return True


    def save(self, tx):
        """ Save Place data in db """
        
        try:
            handle = self.handle
            change = self.change
            pid = self.id
            ptype = self.type
            pname = self.pname
            # Replace f.ex 26° 11\' 7,411"I with 26° 11' 7,411"I
            coord_long = self.coord_long.replace("\\\'", "\'")
            coord_lat = self.coord_lat.replace("\\\'", "\'")
            tx.run(Cypher.place_save, 
               {"handle": handle, "change": change, "id": pid, 
                "type": ptype, "pname": pname, 
                "coord_long": coord_long, "coord_lat": coord_lat})
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
        if len(self.names) >= 1:
            try:
                for i in range(len(self.names)):
                    name = self.names[i].name
                    lang = self.names[i].lang
                    datetype = self.names[i].datetype
                    daterange_start = self.names[i].daterange_start
                    daterange_stop = self.names[i].daterange_stop
                    tx.run(Cypher.place_save_name_by_handle, 
                           {"handle": handle, "name": name, "lang": lang, 
                            "datetype":datetype,
                            "daterange_start":daterange_start, 
                            "daterange_stop":daterange_stop})
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
            
        # Talleta Weburl nodet ja linkitä paikkaan
        if len(self.urls) > 0:
            for url in self.urls:
                url_priv = url.priv
                url_href = url.href
                url_type = url.type
                url_description = url.description
                try:
                    tx.run(Cypher.place_save_weburl_by_handle, 
                           {"handle": handle, "url_priv": url_priv, "url_href": url_href,
                            "url_type":url_type, "url_description":url_description})
                except Exception as err:
                    print("Virhe (Place.save:create Weburl): {0}".format(err), file=stderr)
                
        # Make hierarchy relations to the Place node
        if len(self.placeref_hlink) > 0:
            try:
                tx.run(Cypher.place_save_hier_by_handle, 
                       {"handle": self.handle, "hlink": self.placeref_hlink})
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
                
        # Make place note relations
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                try:
                    tx.run(Cypher.place_save_note_by_handle, 
                           {"handle": self.handle, "hlink": self.placeref_hlink[i]})
                except Exception as err:
                    print("Virhe: {0}".format(err), file=stderr)
            
        return
    

class Place_name:
    """ Paikan nimi
    
        Properties:
                name             str nimi
                lang             str kielikoodi
                datetype         str aikavälin tyyppi
                daterange_start  str aikavälin alku
                daterange_stop   str aikavälin loppu
    """
    
    def __init__(self):
        """ Luo uuden name-instanssin """
        self.name = ''
        self.lang = ''
        self.datetype = ''
        self.daterange_start = ''
        self.daterange_stop = ''

class Place_event:

    def __init__(self, uid):
        self.uid = uid
        self.etype = None
        self.edate = None
        self.edatetype = None
        self.edaterange_start = None
        self.edaterange_stop = None
        self.edaterange = None
        self.role = None
        self.names = None   # tuples [name_type, given_name, surname]
