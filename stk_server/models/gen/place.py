'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''

#import datetime
from sys import stderr
#import logging
from flask import g
#import models.dbutil


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
            desc = "Place {}: {} ({}) {}".format(self.id, self.pname, self.type, self.level)
        except:
            desc = "Place (undefined)"
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
    def get_place_path(locid):
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
        def retappend(p):
            """ Append a new Place to vector ret[], only if p is not a duplicate """
            if len(ret) > 0:
                if ret[-1].id == p.id:
                    return
            ret.append(p)

        query = """
MATCH (p:Place)-[r:HIERARCY*]->(i:Place) WHERE ID(p) = $locid
    RETURN SIZE(r) AS lv,
           ID(p) AS id1, p.type AS type1, p.pname AS name1,
           ID(i) AS id2, i.type AS type2, i.pname AS name2
    UNION
MATCH (p:Place) WHERE ID(p) = $locid
    RETURN 0 AS lv,
           ID(p) AS id1, p.type AS type1, p.pname AS name1,
           0 AS id2, "" AS type2, "" AS name2
    UNION
MATCH (p:Place)<-[r:HIERARCY*]-(i:Place) WHERE ID(p) = $locid
    RETURN SIZE(r)*-1 AS lv,
           ID(i) AS id1, i.type AS type1, i.pname AS name1,
           ID(p) AS id2, p.type AS type2, p.pname AS name2
"""
        result = g.driver.session().run(query, locid=int(locid))
        ret = []
        p0 = None

        for record in result:
            #│"lv"│"id1"│"type1"│"name1"│"id2"│"type2"│"name2"│
            level = record["lv"]
            id1 = int(record["id1"])
            id2 = int(record["id2"])
            if level > 0:
                if id1 == int(locid):
                    ptype =record["type2"]
                    name = record["name2"]
                    retappend(Place(id2, ptype, name, level))
                    p0 = Place(id1, record["type1"], record["name1"], 0)
            elif level == 0:
                retappend(Place(id1, record["type1"], record["name1"], level))
            else: # level < 0:
                if  p0:
                    retappend(p0)
                    p0 = None
                retappend(Place(id1, record["type1"], record["name1"], level))
        if  p0:
            retappend(p0)

        if len(ret) == 0:
            # Tällä paikalla ei ole hierarkiaa. 
            # Hae oman paikan tiedot ilman yhteyksiä
            query = """
MATCH (p:Place) WHERE ID(p) = $locid
  RETURN 0 AS lv, ID(p) AS id, p.type AS type, p.pname AS name
"""
            result = g.driver.session().run(query, locid=int(locid))
            record = result.single()
            p = Place(record["id"], record["type"], record["name"], record["lv"])
            ret = [p,]

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
        │       │ina","Justander"]]            │       │            │
        ├───────┼──────────────────────────────┼───────┼────────────┤
        │"23194"│[["Birth Name","Johanna Ulrika│"Death"│"1835-08-05"│
        │       │","Hedberg"],["Also Known As",│       │            │
        │       │"","Borg"]]                   │       │            │
        └───────┴──────────────────────────────┴───────┴────────────┘
        """
        
        query = """
MATCH (p:Person)-->(e:Event)-[:PLACE]->(l:Place)
  WHERE id(l) = {locid}
MATCH (p) --> (n:Name)
RETURN id(p) AS uid,
  COLLECT([n.type, n.firstname, n.surname]) AS names,
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
