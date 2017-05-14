'''

Created on 2.5.2017

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''
from datetime import date
from sys import stderr
from flask import g


class Event:
    """ Tapahtuma
            
        Properties:
                handle          
                change
                id                 esim. "E0001"
                type               esim. "Birth"
                description        esim. ammatin kuvaus
                date               str aika
                place_hlink        str paikan osoite
                attr_type          str lisätiedon tyyppi
                attr_value         str lisätiedon arvo
                citationref_hlink  str viittauksen osoite
     """

    def __init__(self, eid='', desc='', handle=''):
        """ Luo uuden event-instanssin """
        self.handle = handle
        self.change = ''
        self.id = eid
        self.description = desc
        self.date = ''
        self.place_hlink = ''
        self.attr_type = ''
        self.attr_value = ''
        self.citationref_hlink = ''
    
    
    def get_citation_handle(self):
        """ Luetaan tapahtuman viittauksen handle """
        
        query = """
            MATCH (event:Event)-[r:CITATION]->(c:Citation) 
                WHERE event.gramps_handle='{}'
                RETURN c.gramps_handle AS citationref_hlink
            """.format(self.handle)
        return  g.driver.session.run(query)


    def get_event_data(self):
        """ Luetaan tapahtuman tiedot """

        session = g.session
        query = """
            MATCH (event:Event)
                WHERE event.gramps_handle='{}'
                RETURN event
            """.format(self.handle)
        event_result = session.run(query)

        for event_record in event_result:
            self.id = event_record["event"]["id"]
            self.change = event_record["event"]["change"]
            self.type = event_record["event"]["type"]
            self.date = event_record["event"]["date"]
    
            event_place_result = self.get_place_handle()
            for event_place_record in event_place_result:
                self.place_hlink = event_place_record["handle"]
    
            event_citation_result = self.get_citation_handle()
            for event_citation_record in event_citation_result:
                self.citationref_hlink = event_citation_record["citationref_hlink"]
                
        return True
    
    
    def get_place_handle(self):
        """ Luetaan tapahtuman paikan handle """
        
        query = """
            MATCH (event:Event)-[r:PLACE]->(place:Place) 
                WHERE event.gramps_handle='{}'
                RETURN place.gramps_handle AS handle
            """.format(self.handle)
        return  g.driver.session.run(query)
        
    
    @staticmethod        
    def get_total():
        """ Tulostaa tapahtumien määrän tietokannassa """
        
        query = """
            MATCH (e:Event) RETURN COUNT(e)
            """
        results =  g.driver.session.run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Event*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Type: " + self.type)
        print ("Description: " + self.description)
        print ("Dateval: " + self.date)
        print ("Place_hlink: " + self.place_hlink)
        print ("Attr_type: " + self.attr_type)
        print ("Attr_value: " + self.attr_value)
        print ("Citationref_hlink: " + self.citationref_hlink)
        return True


    def print_compared_data(self, comp_event, pname1, pname2, print_out=True):
        points = 0
        """ Tulostaa pää- ja vertailtavan tapahtuman tiedot """
        print ("*****Events*****")
        if print_out:
            print ("Handle: " + self.handle + " # " + comp_event.handle)
            print ("Change: " + self.change + " # " + comp_event.change)
            print ("Id: " + self.id + " # " + comp_event.id)
            print ("Type: " + self.type + " # " + comp_event.type)
            print ("Description: " + self.description + " # " + comp_event.description)
            print ("Dateval: " + self.date + " # " + comp_event.date)
            print ("Place: " + pname1 + " # " + pname2)
        # Give points if dates match
        if self.date == comp_event.date:
            points += 1
        return points


    def save(self, userid):
        """ Tallettaa sen kantaan """

        today = date.today()
        session = g.driver.session
        try:
            query = """
                CREATE (e:Event) 
                SET e.gramps_handle='{}', 
                    e.change='{}', 
                    e.id='{}', 
                    e.type='{}', 
                    e.description='{}',
                    e.date='{}',
                    e.attr_type='{}',
                    e.attr_value='{}'
                """.format(self.handle, self.change, self.id, self.type, 
                           self.description, self.date, self.attr_type, 
                           self.attr_value)
                
            session.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            query = """
                MATCH (u:User) WHERE u.userid='{}'  
                MATCH (n:Event) WHERE n.gramps_handle='{}'
                MERGE (u)-[r:REVISION]->(n)
                SET r.date='{}'
                """.format(userid, self.handle, today)
                
            session.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Place node
            if self.place_hlink != '':
                query = """
                    MATCH (n:Event) WHERE n.gramps_handle='{}'
                    MATCH (m:Place) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:PLACE]->(m)
                     """.format(self.handle, self.place_hlink)
                                 
                session.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Citation node
            if self.citationref_hlink != '':
                query = """
                    MATCH (n:Event) WHERE n.gramps_handle='{}'
                    MATCH (m:Citation) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:CITATION]->(m)
                     """.format(self.handle, self.citationref_hlink)
                                 
                session.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
        return

