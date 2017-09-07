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

    def __init__(self, locid = ""):
        """ Luo uuden place-instanssin. 
            Argumenttina voidaan antaa paikan uniq_id 
        """
        self.handle = ''            # Gramps-handle
        self.change = ''
        self.id = locid
        self.type = ''
        self.pname = ''
        self.placeref_hlink = ''    # ?
    
    
    def get_place_data(self):
        """ Luetaan kaikki paikan tiedot """
                
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
            Palauttaa listan paikka-olioita sisemmästä uloimpaan. 
            Jos hierarkiaa ei ole, listalla on vain oma Place.
            
            Esim. Männistön hierarkia Pekkala (talo) > Männistö (kylä) > Artjärvi (kunta)
                  tulee tietokannasta:
            ╒═══════╤═════════╤══════════╤═══════╤═════════╤══════════╤════╕
            │"id1"  │"type1"  │"name1"   │"id2"  │"type2"  │"name2"   │"lv"│
            ╞═══════╪═════════╪══════════╪═══════╪═════════╪══════════╪════╡
            │"21992"│"Village"│"Männistö"│"21729"│"City"   │"Artjärvi"│  0 │
            ├───────┼─────────┼──────────┼───────┼─────────┼──────────┼────┤
            │"22022"│"Farm"   │"Pekkala" │"21992"│"Village"│"Männistö"│  2 │
            └───────┴─────────┴──────────┴───────┴─────────┴──────────┴────┘
            Metodi palauttaa siitä listan
                Place(result[0].id2) # Artjärvi City
                Place(result[0].id1) # Männistö Village
                Place(result[1].id1) # Pekkala Farm
            Muuttuja lv on taso: 
                0 = ylemmät, 
                1 = tämä, 
                2 = seuraava alempi
        """

        query = """
MATCH x= (p:Place)-[r:HIERARCY*]->(i:Place) WHERE ID(p) = $locid
    RETURN ID(p) AS id1, p.type AS type1, p.pname AS name1,
           ID(i) AS id2, i.type AS type2, i.pname AS name2, 
           0 AS lv
    UNION
MATCH x= (p:Place)<-[r:HIERARCY]-(i:Place) WHERE ID(p) = $locid
    RETURN ID(i) AS id1, i.type AS type1, i.pname AS name1,
           ID(p) AS id2, p.type AS type2, p.pname AS name2,
           2 AS lv
"""
        result = g.driver.session().run(query, locid=int(locid))
        ret = []

        for record in result:
            if len(ret) == 0:       # Ensimmäinen rivi
                if record["lv"] == 0:
                    levels = [0,1]
                else:
                    levels = [1,2]
                p = Place()         # 1. rivin oikeanpuoleinen paikka
                p.id = record["id2"]
                p.type = record["type2"]
                p.pname = record["name2"]
                p.level = levels[0]
                ret.append(p)
                p = Place()          # 1. rivin vasemmanpuoleinen paikka
                p.id = record["id1"]
                p.type = record["type1"]
                p.pname = record["name1"]
                p.level = levels[1]      # Kysytty paikka
                ret.append(p)
            else:
                p = Place()          # Tulosrivin vasemmanpuoleinen paikka
                p.id = record["id1"]
                p.type = record["type1"]
                p.pname = record["name1"]
                #p.handle = ''
                #p.change = ''
                #p.placeref_hlink = ''
                p.level = record["lv"]
                ret.append(p)

        if len(ret) == 0:
            # Tällä paikalla ei ole hierarkiaa. 
            # Hae oman paikan tiedot ilman yhteyksiä
            query = """
MATCH (p:Place) WHERE ID(p) = $locid
  RETURN ID(p) AS id, p.type AS type, p.pname AS name, 1 AS lv
"""
            result = g.driver.session().run(query, locid=int(locid))
            record = result.single()
            p = Place()         # Ainoan rivin paikka
            p.id = record["id"]
            p.type = record["type"]
            p.pname = record["name"]
            p.level = record["lv"]
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
