'''

    Event hierarkiasuunnitelma 23.8.2018/JMä

    class gen.event.*Event*(): 
       vain Event-noden parametrit (uniq_id, tyyppi, handle, päivämäärät)

    class *Event_compound*(Event): 
        - __init__()
        - get_person_events()
        - get_baptism_data()
        - get_cite_sour_repo() static <-- get_citation_path()?
        - get_event_cite()
       Event, lähteet, huomautukset, henkilön uniq_id

    2. *Event_w_person*: 
       Event ja ja siihen liittyvät Person-nodet ja roolit (ehkä myös nimet?)
    3. *Event_w_place*: 
       Event ja liittyvät paikat (pyydettäessä myös paikannimet?)

    Nämä siis periytyvät Event-luokasta ja sisältävät tarpeen mukaan 
    tietokantametodit _read(), get()_ ja _save()_ (_read_ hakukenttien avulla, 
    _get_ uniq_id:n avulla). L
    
    isäksi on kätevä olla metodi __str__(), joka antaa lyhyen sanalliseen muodon
    "syntynyt välillä 1.3.1840...31.3.1840 Hauho".
    
    Ehkä _save()_-metodi koskee vain Event-nodea, ei liittyvä nodeja? 
    Ehkä yhteydet myös?
    
    Prosessointiin ja näyttöihin tehdään tarpeen mukaan bisnes-luokkia, 
    jotka sisältävät esim. poiminta-, yhdistely- ja muokkaussääntöjä ja 
    siellä ehkä hoidetaan isompien kokonaisuuksien talletus 
    (kuten henkilö + nimet ja lähteet).

Created on 2.5.2017
@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''
import datetime
from sys import stderr
#from flask import g
from models.gen.dates import DateRange
import  shareds
from models.cypher_gramps import Cypher_event_w_handle

#-------------------------------------------------------------------------------

class Event():
    """ Tapahtuma
            
        Properties:
                handle             Gramps handle
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
    
    


    @staticmethod       
    def get_events_wo_citation():
        """ Voidaan lukea viittauksettomia tapahtumia kannasta
        """
        
        query = """
 MATCH (e:Event) WHERE NOT EXISTS((:Citation)<-[:CITATION]-(e:Event))
 RETURN ID(e) AS uniq_id, e
 ORDER BY e.type, e.date"""
                
        result = shareds.driver.session().run(query)
        
        titles = ['uniq_id', 'handle', 'change', 'id', 'type', 
                  'description', 'date', 'dates', 
                  'attr_type', 'attr_value']
        lists = []
        
        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["e"]['handle']:
                data_line.append(record["e"]['handle'])
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
        
        titles = ['uniq_id', 'handle', 'change', 'id', 'type', 
                  'description', 'date', 'dates', 'attr_type', 'attr_value']
        lists = []
        
        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["e"]['handle']:
                data_line.append(record["e"]['handle'])
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
        e_attr = {
            "handle": self.handle,
            "change": self.change, 
            "id": self.id, 
            "type": self.type,
            "description": self.description, 
            "attr_type": self.attr_type, 
            "attr_value": self.attr_value}
        if self.dates:
            e_attr.update(self.dates.for_db())
        try:
            tx.run(Cypher_event_w_handle.create, 
               username=username, date=today, e_attr=e_attr)
        except Exception as err:
            print("Virhe.event_save: {0}".format(err), file=stderr)

        try:
            # Make relation to the Place node
            if self.place_hlink != '':
                tx.run(Cypher_event_w_handle.link_place, 
                       handle=self.handle, place_hlink=self.place_hlink)
        except Exception as err:
            print("Virhe.event_link_place: {0}".format(err), file=stderr)

        try:
            # Make relation to the Note node
            if self.noteref_hlink != '':
                tx.run(Cypher_event_w_handle.link_note,
                       handle=self.handle, noteref_hlink=self.noteref_hlink)
        except Exception as err:
            print("Virhe.event_link_note: {0}".format(err), file=stderr)

        try:
            # Make relation to the Citation node
            if self.citationref_hlink != '':
                tx.run(Cypher_event_w_handle.link_citation,
                       handle=self.handle, citationref_hlink=self.citationref_hlink)
        except Exception as err:
            print("Virhe.event_link_citation: {0}".format(err), file=stderr)

        try:
            # Make relation to the Media node
            if self.objref_hlink != '':
                tx.run(Cypher_event_w_handle.link_media, 
                       handle=self.handle, objref_hlink=self.objref_hlink)
        except Exception as err:
            print("Virhe.event_link_media: {0}".format(err), file=stderr)
            
        return

# class Event_for_template(Event):
''' Tämä on korvattu luokalla Event_combo'''
#     """ Template-tapahtuma perii Tapahtuma-luokan
#             
#         Properties:
#                 place              str paikan nimi
#     """
# 
#     def __init__(self, eid='', desc='', handle=''):
#         """ Luo uuden event-instanssin """
#         Event.__init__(self, eid, desc, handle)
#         self.place = ''
