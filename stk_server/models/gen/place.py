'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''

from sys import stderr
#import logging
from flask import g
from models.dbtree import DbTree


class Place:
    """ Paikka
            
        Properties:
                handle          
                change
                id              esim. "P0001"
                type            str paikan tyyppi
                pname           str paikan nimi
                placeref_hlink  str paikan osoite
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
        self.placeref_hlink = ''
    
    
    def __str__(self):
        try:
            lv = self.level
        except:
            lv = ""
        desc = "Place {}: {} ({}) {}".format(self.id, self.pname, self.type, lv)
        return desc

    
    def get_place_data(self):
        """ Luetaan kannasta kaikki paikan tiedot """
                
        query = """
            MATCH (place:Place)
                WHERE place.gramps_handle='{}'
                RETURN place
            """.format(self.handle)
        place_result = g.driver.session().run(query)
        
        for place_record in place_result:
            self.change = place_record["place"]["change"]
            self.id = place_record["place"]["id"]
            self.type = place_record["place"]["type"]
            self.pname = place_record["place"]["pname"]
            
        return True
        self.placeref_hlink = ''
    
    
    def get_place_data_by_id(self):
        """ Luetaan kaikki paikan tiedot """
        
        plid = self.uniq_id
        query = """
            MATCH (place:Place)
                WHERE ID(place)=$place_id
                RETURN place
            """.format(self.uniq_id)
        place_result = g.driver.session().run(query, {"place_id": plid})
        
        for place_record in place_result:
            self.change = place_record["place"]["change"]
            self.id = place_record["place"]["id"]
            self.type = place_record["place"]["type"]
            self.pname = place_record["place"]["pname"]
            
        return True
    
    
    @staticmethod       
    def get_places():
        """ Luetaan kaikki paikat kannasta
        #TODO Eikö voisi palauttaa listan Place-olioita?
        """
        
        query = """
 MATCH (p:Place)
 RETURN ID(p) AS uniq_id, p
 ORDER BY p.pname, p.type"""
                
        result = g.driver.session().run(query)
        
        titles = ['uniq_id', 'gramps_handle', 'change', 'id', 'type', 'pname']
        lists = []
        
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
                
            lists.append(data_line)
        
        return (titles, lists)


    @staticmethod       
    def get_place_names():
        """ Haetaan paikkaluettelo ml. hierarkiassa ylemmät ja alemmat
            
            Esim.
╒═══════╤═══════════╤══════════╤════════════════════╤══════════════════════╕
│"id"   │"name"     │"type"    │"upper"             │"lower"               │
╞═══════╪═══════════╪══════════╪════════════════════╪══════════════════════╡
│"30358"│"Alnäs"    │"Building"│[["30344","Lappträsk│[[null,null,null]]    │
│       │           │          │ Ladugård","Farm"]] │                      │
├───────┼───────────┼──────────┼────────────────────┼──────────────────────┤
│"30256"│"Artjärvi" │"City"    │[[null,null,null],  │[["30257","Rastula",  │
│       │           │          │[null,null,null]]   │"Village"],["30515",  │
│       │           │          │                    │"Männistö","Village"]]│                            │
├───────┼───────────┼──────────┼────────────────────┼──────────────────────┤
│"30341"│"Backas"   │"Building"│[[null,null,null]]  │[[null,null,null]]    │
└───────┴───────────┴──────────┴────────────────────┴──────────────────────┘
"""
        
        query = """
MATCH (a:Place) 
OPTIONAL MATCH (a:Place)-->(up:Place) 
OPTIONAL MATCH (a:Place)<--(do:Place) 
RETURN ID(a) AS id, a.type AS type, a.pname AS name,
       COLLECT([ID(up), up.type, up.pname]) AS upper, 
       COLLECT([ID(do), do.type, do.pname]) AS lower
  ORDER BY name
"""
        ret = []
        result = g.driver.session().run(query)
        for record in result:
            # Luodaan paikka ja siihen taulukko liittyvistä hierarkiassa lähinnä
            # alemmista paikoista
            p = Place(record['id'], record['type'], record['name'])
            p.uppers = []
            for near in record['upper']:
                if near[0]:
                    p.uppers.append(Place(near[0], near[1], near[2]))
            p.lowers = []
            for near in record['lower']:
                if near[0]:
                    p.lowers.append(Place(near[0], near[1], near[2]))
            ret.append(p)
        return ret


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
        
        query = """
MATCH x= (p:Place)<-[r:HIERARCY*]-(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r) AS lv, r
    UNION
MATCH x= (p:Place)-[r:HIERARCY*]->(i:Place) WHERE ID(p) = $locid
    RETURN NODES(x) AS nodes, SIZE(r)*-1 AS lv, r
"""
        t = DbTree(g.driver, query, 'pname', 'type')
        t.load_to_tree_struct(locid)
        if t.tree.depth() == 0:
            # Vain ROOT-solmu: Tällä paikalla ei ole hierarkiaa. 
            # Hae oman paikan tiedot ilman yhteyksiä
            query = """
MATCH (p:Place) WHERE ID(p) = $locid
RETURN p.type AS type, p.pname AS name
"""
            with g.driver.session() as session:
                result = session.run(query, locid=int(locid))
                record = result.single()
                t.tree.create_node(record["name"], locid, parent=0, 
                                   data={'type': record["type"]})
# locid="", ptype="", pname="", level=None
        ret = []
        for node in t.tree.expand_tree(mode=t.tree.DEPTH):
#             print ("{} {} {}".format(t.tree.depth(t.tree[node]), t.tree[node], 
#                                      t.tree[node].bpointer))
            if node != 0:
                n = t.tree[node]
                p = Place(locid=node, ptype=n.data['type'], 
                          pname=n.tag, level=t.tree.depth(n))
                p.parent = n.bpointer
                ret.append(p)
        return ret


    @staticmethod       
    def get_place_events(loc_id):
        """ Haetaan paikkaan liittyvät tapahtumat sekä
            osallisen henkilön nimitiedot.
            
        Palauttaa esimerkin mukaiset tiedot:
        ╒═══════╤══════════════════════════════╤═══════╤════════════╕
        │"uid"  │"names"                       │"etype"│"edate"     │
        ╞═══════╪══════════════════════════════╪═══════╪════════════╡
        │"23063"│[["Birth Name","Justina Cathar│"Death"│"1789-12-26"│
        │       │ina","Justander",""]]         │       │            │
        ├───────┼──────────────────────────────┼───────┼────────────┤
        │"23194"│[["Birth Name","Johanna Ulrika│"Death"│"1835-08-05"│
        │       │","Hedberg",""],              │       │            │
        │       │["Also Known As","","Borg"]]  │       │            │
        └───────┴──────────────────────────────┴───────┴────────────┘
        """

        query = """
MATCH (p:Person)-[r:EVENT]->(e:Event)-[:PLACE]->(l:Place)
  WHERE id(l) = {locid}
MATCH (p) --> (n:Name)
RETURN id(p) AS uid, r.role AS role,
  COLLECT([n.type, n.firstname, n.surname, n.suffix]) AS names,
  e.type AS etype,
  e.date AS edate
ORDER BY edate"""
                
        result = g.driver.session().run(query, locid=int(loc_id))
        ret = []
        for record in result:
            p = Place()
            p.uid = record["uid"]
            p.etype = record["etype"]
            p.edate = record["edate"]
            p.role = record["role"]
            p.names = record["names"]   # tuples [name_type, given_name, surname]
            ret.append(p)
        return ret
    
    @staticmethod       
    def get_total():
        """ Tulostaa paikkojen määrän tietokannassa """
        
                
        query = """
            MATCH (p:Place) RETURN COUNT(p)
            """
        results =  g.driver.session().run(query)
        
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
        if self.placeref_hlink != '':
            print ("Placeref_hlink: " + self.placeref_hlink)
        return True


    def save(self, tx):
        """ Tallettaa sen kantaan """
        
        try:
            if len(self.pname) >= 1:
                p_pname = self.pname
                if len(self.pname) > 1:
                    print("Warning: More than one pname in a place, " + 
                          "handle: " + self.handle)
            else:
                p_pname = ''

            query = """
                CREATE (p:Place) 
                SET p.gramps_handle='{}', 
                    p.change='{}', 
                    p.id='{}', 
                    p.type='{}', 
                    p.pname='{}'
                """.format(self.handle, self.change, self.id, self.type, p_pname)
                
            tx.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        # Make hierarchy relations to the Place node
        if len(self.placeref_hlink) > 0:
            try:
                query = """
                    MATCH (n:Place) WHERE n.gramps_handle='{}'
                    MATCH (m:Place) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:HIERARCY]->(m)
                     """.format(self.handle, self.placeref_hlink)
                                 
                tx.run(query)
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
            
        return
