'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''
from sys import stderr


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

    def __init__(self):
        """ Luo uuden place-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        self.type = ''
        self.pname = ''
        self.placeref_hlink = ''
    
    
    def get_place_data(self):
        """ Luetaan kaikki paikan tiedot """
        
        global session
                
        query = """
            MATCH (place:Place)
                WHERE place.gramps_handle='{}'
                RETURN place
            """.format(self.handle)
        place_result = session.run(query)
        
        for place_record in place_result:
            self.change = place_record["place"]["change"]
            self.id = place_record["place"]["id"]
            self.type = place_record["place"]["type"]
            self.pname = place_record["place"]["pname"]
            
        return True
        
    
    @staticmethod       
    def get_total():
        """ Tulostaa paikkojen määrän tietokannassa """
        
        global session
                
        query = """
            MATCH (p:Place) RETURN COUNT(p)
            """
        results =  session.run(query)
        
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


    def save(self):
        """ Tallettaa sen kantaan """

        global session
        
        if len(self.pname) >= 1:
            p_pname = self.pname
            if len(self.pname) > 1:
                print("Warning: More than one pname in a place, " + 
                      "handle: " + self.handle)
        else:
            p_pname = ''

        try:
            query = """
                CREATE (p:Place) 
                SET p.gramps_handle='{}', 
                    p.change='{}', 
                    p.id='{}', 
                    p.type='{}', 
                    p.pname='{}'
                """.format(self.handle, self.change, self.id, self.type, p_pname)
                
            session.run(query)
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
                                 
                session.run(query)
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
            
        return
