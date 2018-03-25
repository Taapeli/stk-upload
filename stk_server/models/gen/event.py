'''

Created on 2.5.2017

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''
import datetime
from sys import stderr
#from flask import g
from models.gen.dates import DateRange
import  shareds
from models.gen.cypher import Cypher
from models.gramps.cypher_gramps import Cypher_w_handle


class Event:
    """ Tapahtuma
            
        Properties:
                handle          
                change
                id                 esim. "E0001"
                type               esim. "Birth"
                description        esim. ammatin kuvaus
                date               str aika
                dates              DateRange date expression
                place_hlink        str paikan osoite
                attr_type          str lisätiedon tyyppi
                attr_value         str lisätiedon arvo
                noteref_hlink      str lisätiedon osoite
                citationref_hlink  str viittauksen osoite
                objref_hlink       str median osoite
     """

    def __init__(self, eid='', desc='', handle=''):
        """ Luo uuden event-instanssin """
        self.handle = handle
        self.change = ''
        self.id = eid
        self.description = desc
        self.date = ''
        self.dates = None
        self.place_hlink = ''
        self.attr_type = ''
        self.attr_value = ''
        self.noteref_hlink = ''
        self.citationref_hlink = ''
        self.objref_hlink = ''
        self.citations = []   # For creating display sets
        self.names = []   # For creating display sets
    
    
    def get_baptism_data(self):
        """ Luetaan kastetapahtuman henkilöt"""
        
        pid = int(self.uniq_id)
        query = """
MATCH (event:Event)<-[r:EVENT]-(p:Person) WHERE ID(event)=$pid
OPTIONAL MATCH (p)-[:NAME]->(n:Name)
RETURN ID(event) AS id, event.type AS type, event.date AS date, 
    event.dates AS dates, ID(p) AS person_id, r.role AS role, 
    COLLECT([n.firstname, n.surname]) AS person_names ORDER BY r.role DESC"""
        return  shareds.driver.session().run(query, {"pid": pid})
    
    
    def get_citation_by_id(self):
        """ Luetaan tapahtuman viittauksen id """
        
        pid = int(self.uniq_id)
        query = """
MATCH (event:Event)-[r:CITATION]->(c:Citation) 
  WHERE ID(event)=$pid
RETURN ID(c) AS citationref_hlink"""
        return  shareds.driver.session().run(query, {"pid": pid})

    
    @staticmethod       
    def get_cite_sour_repo (uniq_id):
        """ Voidaan lukea läheitä viittauksineen kannasta
        """

        if uniq_id:
            where = "WHERE ID(event)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
 MATCH (event:Event)-[a:CITATION]->(citation:Citation)
         -[b:SOURCE]->(source:Source)-[c:REPOSITORY]->(repo:Repository) {0}
 RETURN ID(event) AS id, event.type AS type, 
        event.date AS date, event.dates AS dates, 
        COLLECT([ID(citation), citation.dateval, citation.page, citation.confidence,
        ID(source), source.stitle, c.medium, ID(repo), repo.rname, repo.type] ) AS sources
 ORDER BY event.date""".format(where)
                
        return shareds.driver.session().run(query)

    
    @staticmethod       
    def get_event_cite (uniq_id):
        """ Voidaan lukea tapahtuman tiedot lähdeviittauksineen kannasta
        """

        if uniq_id:
            where = "WHERE ID(event)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
 MATCH (event:Event)-[a:CITATION]->(citation:Citation) {0}
 RETURN ID(event) AS id, event.type AS type, 
        event.date AS date, event.dates AS dates, 
        COLLECT([ID(citation), citation.dateval, citation.page,
                 citation.confidence] ) AS sources
 ORDER BY event.date""".format(where)
                
        return shareds.driver.session().run(query)


    def get_event_data_by_id(self):
        """ Luetaan tapahtuman tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (event:Event) WHERE ID(event)=$pid
RETURN event"""
        result = shareds.driver.session().run(query, {"pid": pid})

        for record in result:
            self.id = record["event"]["id"]
            self.change = record["event"]["change"]
            self.type = record["event"]["type"]
            dates = DateRange(record["event"]["dates"])
            self.date = dates.estimate()
            self.dates = str(dates)
            self.description = record["event"]["description"]
    
            place_result = self.get_place_by_id()
            for place_record in place_result:
                self.place_hlink = place_record["uniq_id"]
    
            note_result = self.get_note_by_id()
            for note_record in note_result:
                self.noteref_hlink = note_record["noteref_hlink"]
                print("noteref_hlink: " + str(self.noteref_hlink))
    
            citation_result = self.get_citation_by_id()
            for citation_record in citation_result:
                self.citationref_hlink = citation_record["citationref_hlink"]
                                
        return True
    
    
    @staticmethod       
    def get_events_wo_citation():
        """ Voidaan lukea viittauksettomia tapahtumia kannasta
        """
        
        query = """
 MATCH (e:Event) WHERE NOT EXISTS((:Citation)<-[:CITATION]-(e:Event))
 RETURN ID(e) AS uniq_id, e
 ORDER BY e.type, e.date"""
                
        result = shareds.driver.session().run(query)
        
        titles = ['uniq_id', 'gramps_handle', 'change', 'id', 'type', 
                  'description', 'date', 'dates', 
                  'attr_type', 'attr_value']
        lists = []
        
        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["e"]['gramps_handle']:
                data_line.append(record["e"]['gramps_handle'])
            else:
                data_line.append('-')
            if record["e"]['change']:
                data_line.append(record["e"]['change'])
            else:
                data_line.append('-')
            if record["e"]['id']:
                data_line.append(record["e"]['id'])
            else:
                data_line.append('-')
            if record["e"]['type']:
                data_line.append(record["e"]['type'])
            else:
                data_line.append('-')
            if record["e"]['description']:
                data_line.append(record["e"]['description'])
            else:
                data_line.append('-')
            if record["e"]['date']:
                data_line.append(record["e"]['date'])
            else:
                data_line.append('-')
            if record["e"]['dates']:
                data_line.append(str(DateRange(record["e"]['dates'])))
            else:
                data_line.append('-')
            if record["e"]['attr_type']:
                data_line.append(record["e"]['attr_type'])
            else:
                data_line.append('-')
            if record["e"]['attr_value']:
                data_line.append(record["e"]['attr_value'])
            else:
                data_line.append('-')
                
            lists.append(data_line)
        
        return (titles, lists)
    
    
    @staticmethod       
    def get_events_wo_place():
        """ Voidaan lukea paikattomia tapahtumia kannasta
        """
        
        query = """
 MATCH (e:Event) WHERE NOT EXISTS((:Place)<-[:PLACE]-(e:Event))
 RETURN ID(e) AS uniq_id, e
 ORDER BY e.type, e.date"""
                
        result = shareds.driver.session().run(query)
        
        titles = ['uniq_id', 'gramps_handle', 'change', 'id', 'type', 
                  'description', 'date', 'dates', 'attr_type', 'attr_value']
        lists = []
        
        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["e"]['gramps_handle']:
                data_line.append(record["e"]['gramps_handle'])
            else:
                data_line.append('-')
            if record["e"]['change']:
                data_line.append(record["e"]['change'])
            else:
                data_line.append('-')
            if record["e"]['id']:
                data_line.append(record["e"]['id'])
            else:
                data_line.append('-')
            if record["e"]['type']:
                data_line.append(record["e"]['type'])
            else:
                data_line.append('-')
            if record["e"]['description']:
                data_line.append(record["e"]['description'])
            else:
                data_line.append('-')
            if record["e"]['date']:
                data_line.append(record["e"]['date'])
            else:
                data_line.append('-')
            if record["e"]['dates']:
                data_line.append(str(DateRange(record["e"]['dates'])))
            else:
                data_line.append('-')
            if record["e"]['attr_type']:
                data_line.append(record["e"]['attr_type'])
            else:
                data_line.append('-')
            if record["e"]['attr_value']:
                data_line.append(record["e"]['attr_value'])
            else:
                data_line.append('-')
                
            lists.append(data_line)
        
        return (titles, lists)    
    
        
    def get_note_by_id(self):
        """ Luetaan tapahtuman lisätietojen uniq_id """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (event:Event)-[r:NOTE]->(note:Note) 
  WHERE ID(event)=$pid
RETURN ID(note) AS noteref_hlink"""
        return  shareds.driver.session().run(query, {"pid": pid})
    
        
    def get_place_by_id(self):
        """ Luetaan tapahtuman paikan uniq_id """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (event:Event)-[r:PLACE]->(place:Place) 
  WHERE ID(event)=$pid
RETURN ID(place) AS uniq_id"""
        return  shareds.driver.session().run(query, {"pid": pid})

        
    
    @staticmethod        
    def get_total():
        """ Tulostaa tapahtumien määrän tietokannassa """
        
        query = """
            MATCH (e:Event) RETURN COUNT(e)
            """
        results =  shareds.driver.session().run(query)
        
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
        print ("Dates: " + str(self.dates))
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
            print ("Dates: " + str(self.dates) + " # " + str(comp_event.dates))
            print ("Place: " + pname1 + " # " + pname2)
        # Give points if dates match
        if self.date == comp_event.date:
            points += 1
        return points


    def save(self, username, tx):
        """ Saves the Event to db including
            links from UserProfile, Person
        """

        today = str(datetime.date.today())
        if self.dates:
            dates = self.dates.for_db()
        else:
            dates = None
        e_attr = {
            "gramps_handle": self.handle,
            "change": self.change, 
            "id": self.id, 
            "type": self.type,
            "description": self.description, 
            "dates": dates,
            "attr_type": self.attr_type, 
            "attr_value": self.attr_value}
        try:
            tx.run(Cypher_w_handle.event_save, 
               {"username": username, "date": today, "e_attr": e_attr})
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Place node
            if self.place_hlink != '':
                place_hlink = self.place_hlink
                tx.run(Cypher_w_handle.event_link_place, 
                       {"handle": self.handle, "place_hlink": place_hlink})
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Note node
            if self.noteref_hlink != '':
                noteref_hlink = self.noteref_hlink
                tx.run(Cypher_w_handle.event_link_note, 
                       {"handle": self.handle, "noteref_hlink": noteref_hlink})
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Citation node
            if self.citationref_hlink != '':
                citationref_hlink = self.citationref_hlink
                tx.run(Cypher_w_handle.event_link_citation, 
                       {"handle": self.handle, "citationref_hlink": citationref_hlink})
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Media node
            if self.objref_hlink != '':
                objref_hlink = self.objref_hlink
                tx.run(Cypher_w_handle.event_link_media, 
                       {"handle": self.handle, "objref_hlink": objref_hlink})
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
        return



class Event_for_template(Event):
    """ Template-tapahtuma perii Tapahtuma-luokan
            
        Properties:
                place              str paikan nimi
    """

    def __init__(self, eid='', desc='', handle=''):
        """ Luo uuden event-instanssin """
        Event.__init__(self, eid, desc, handle)
        self.place = ''
