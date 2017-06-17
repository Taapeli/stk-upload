'''

Created on 2.5.2017

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''
import datetime
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
        self.citations = []   # For creating display sets
    
    
    def get_citation_handle(self):
        """ Luetaan tapahtuman viittauksen handle """
        
        query = """
            MATCH (event:Event)-[r:CITATION]->(c:Citation) 
                WHERE event.gramps_handle='{}'
                RETURN c.gramps_handle AS citationref_hlink
            """.format(self.handle)
        return  g.driver.session().run(query)
    
    
    def get_citation_by_id(self):
        """ Luetaan tapahtuman viittauksen id """
        
        pid = int(self.uniq_id)
        query = """
MATCH (event:Event)-[r:CITATION]->(c:Citation) 
  WHERE ID(event)=$pid
RETURN ID(c) AS citationref_hlink"""
        return  g.driver.session().run(query, {"pid": pid})
    
    @staticmethod       
    def get_cite_sour_repo (uniq_id):
        """ Voidaan lukea läheitä viittauksineen kannasta
        """

        if uniq_id:
            where = "WHERE ID(event)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
 MATCH (event:Event)-[a]->(citation:Citation)-[b]->(source:Source)-[c]->(repo:Repository) {0}
 RETURN ID(event) AS id, event.type AS type, event.date AS date, 
  COLLECT([ID(citation), citation.dateval, citation.page, citation.confidence,
      ID(source), source.stitle, c.medium, ID(repo), repo.rname, repo.type] ) AS sources
 ORDER BY event.date""".format(where)
                
        return g.driver.session().run(query)


    def get_event_data(self):
        """ Luetaan tapahtuman tiedot """

        query = """
            MATCH (event:Event)
                WHERE event.gramps_handle='{}'
                RETURN event
            """.format(self.handle)
        event_result = g.driver.session().run(query)

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


    def get_event_data_by_id(self):
        """ Luetaan tapahtuman tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (event:Event)
  WHERE ID(event)=$pid
RETURN event"""
        event_result = g.driver.session().run(query, {"pid": pid})

        for event_record in event_result:
            self.id = event_record["event"]["id"]
            self.change = event_record["event"]["change"]
            self.type = event_record["event"]["type"]
            self.date = event_record["event"]["date"]
    
            event_place_result = self.get_place_by_id()
            for event_place_record in event_place_result:
                self.place_hlink = event_place_record["uniq_id"]
    
            event_citation_result = self.get_citation_by_id()
            for event_citation_record in event_citation_result:
                self.citationref_hlink = event_citation_record["citationref_hlink"]
                
        return True
    
    
    @staticmethod       
    def get_events_wo_citation():
        """ Voidaan lukea viittauksettomia tapahtumia kannasta
        """
        
        query = """
 MATCH (e:Event) WHERE NOT EXISTS((:Citation)<-[:CITATION]-(e:Event))
 RETURN ID(e) AS uniq_id, e
 ORDER BY e.type, e.date"""
                
        result = g.driver.session().run(query)
        
        titles = ['uniq_id', 'gramps_handle', 'change', 'id', 'type', 
                  'description', 'date', 'attr_type', 'attr_value']
        events = []
        
        for record in result:
            event_line = []
            if record['uniq_id']:
                event_line.append(record['uniq_id'])
            else:
                event_line.append('-')
            if record["e"]['gramps_handle']:
                event_line.append(record["e"]['gramps_handle'])
            else:
                event_line.append('-')
            if record["e"]['change']:
                event_line.append(record["e"]['change'])
            else:
                event_line.append('-')
            if record["e"]['id']:
                event_line.append(record["e"]['id'])
            else:
                event_line.append('-')
            if record["e"]['type']:
                event_line.append(record["e"]['type'])
            else:
                event_line.append('-')
            if record["e"]['description']:
                event_line.append(record["e"]['description'])
            else:
                event_line.append('-')
            if record["e"]['date']:
                event_line.append(record["e"]['date'])
            else:
                event_line.append('-')
            if record["e"]['attr_type']:
                event_line.append(record["e"]['attr_type'])
            else:
                event_line.append('-')
            if record["e"]['attr_value']:
                event_line.append(record["e"]['attr_value'])
            else:
                event_line.append('-')
                
            events.append(event_line)
        
        return (titles, events)
    
    
    def get_place_handle(self):
        """ Luetaan tapahtuman paikan handle """
        
        query = """
            MATCH (event:Event)-[r:PLACE]->(place:Place) 
                WHERE event.gramps_handle='{}'
                RETURN place.gramps_handle AS handle
            """.format(self.handle)
        return  g.driver.session().run(query)
    
    
        
    def get_place_by_id(self):
        """ Luetaan tapahtuman paikan uniq_id """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (event:Event)-[r:PLACE]->(place:Place) 
  WHERE ID(event)=$pid
RETURN ID(place) AS uniq_id"""
        return  g.driver.session().run(query, {"pid": pid})

        
    
    @staticmethod        
    def get_total():
        """ Tulostaa tapahtumien määrän tietokannassa """
        
        query = """
            MATCH (e:Event) RETURN COUNT(e)
            """
        results =  g.driver.session().run(query)
        
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


    def save(self, userid, tx):
        """ Tallettaa sen kantaan """

        today = str(datetime.date.today())
        handle = self.handle
        change = self.change
        eid = self.id
        etype = self.type
        description = self.description
        edate = self.date
        attr_type = self.attr_type
        attr_value = self.attr_value
        try:
            query = """
CREATE (e:Event) 
SET e.gramps_handle=$handle, 
    e.change=$change, 
    e.id=$id, 
    e.type=$type, 
    e.description=$description,
    e.date=$date,
    e.attr_type=$attr_type,
    e.attr_value=$attr_value"""
            tx.run(query, 
               {"handle": handle, "change": change, "id": eid, 
                "type": etype, "description": description, "date": edate, 
                "attr_type": attr_type, "attr_value": attr_value})
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            query = """
MATCH (u:User) WHERE u.userid=$userid  
MATCH (n:Event) WHERE n.gramps_handle=$handle
MERGE (u)-[r:REVISION]->(n)
SET r.date=$date"""
            tx.run(query, 
               {"userid": userid, "handle": handle, "date": today})
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Place node
            if self.place_hlink != '':
                place_hlink = self.place_hlink
                query = """
MATCH (n:Event) WHERE n.gramps_handle=$handle
MATCH (m:Place) WHERE m.gramps_handle=$place_hlink
MERGE (n)-[r:PLACE]->(m)"""  
                tx.run(query, 
               {"handle": handle, "place_hlink": place_hlink})
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Citation node
            if self.citationref_hlink != '':
                citationref_hlink = self.citationref_hlink
                query = """
MATCH (n:Event) WHERE n.gramps_handle=$handle
MATCH (m:Citation) WHERE m.gramps_handle=$citationref_hlink
MERGE (n)-[r:CITATION]->(m)"""                       
                tx.run(query, 
               {"handle": handle, "citationref_hlink": citationref_hlink})
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
        return




class Event_for_template(Event):
    """ Template-tapahtuma perii Tapahtuma-luokan
            
        Properties:
                place              str paikka
                
    """

    def __init__(self, eid='', desc='', handle=''):
        """ Luo uuden event-instanssin """
        self.handle = handle
        self.change = ''
        self.id = eid
        self.description = desc
        self.date = ''
        self.place = ''
        self.place_hlink = ''
        self.attr_type = ''
        self.attr_value = ''
        self.citationref_hlink = ''
