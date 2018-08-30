'''

    Event hierarkiasuunnitelma 23.8.2018/JMä

    class gen.event.*Event*(): 
       vain Event-noden parametrit (uniq_id, tyyppi, handle, päivämäärät)

    class *Event_compound*(Event): 
        - __init__()
        - get_event_combo()
        - get_baptism_data()
        - get_cite_sour_repo() static <-- get_citation_path()?
        - get_event_cite()
       Event, lähteet, huomautukset, henkilön uniq_id

    class *Event_gramps*()
        - save() # with relations to UserProfile, Person, Place, Note, Citation, Media

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
# import datetime
# from sys import stderr
#from flask import g
from models.gen.dates import DateRange
import  shareds


class Event():
    """ Tapahtuma
            
        Properties:
                handle             Unique constant handle (mostly from Gramps)
                change             Original timestamp like 1502552858
                id                 esim. "E0001"
                type               esim. "Birth"
                description        esim. ammatin kuvaus
                date               str aika
                dates              DateRange date expression
                attr_type          str lisätiedon tyyppi
                attr_value         str lisätiedon arvo
            For gramps_loader:
                note_handles[]     str lisätiedon handle (ent. noteref_hlink)
            Planned from gramps_loader:
                place_handles[]    str paikan handle (ent. place_hlink)
                citation_handles[] str viittauksen handle (ent. citationref_hlink)
                media_handles[]    str median handle (ent. objref_hlink)
                #place_hlink       str paikan handle
                #citationref_hlink str viittauksen handle
                #objref_hlink      str median handle
        Event_combo properties:
                citations = []     Citations attached
                names = []         Names attached
     """

    def __init__(self, eid='', desc='', handle=''):
        """ Luo uuden event-instanssin """
        self.handle = handle
        self.change = ''
        self.id = eid
        self.type = ''
        self.description = desc
        self.date = ''
        self.dates = None
        # Only in Event_gramps
        #    self.attr_type = ''
        #    self.attr_value = ''
        # Only in Event_combo
        #    self.note_ref = []    # prev. noteref_hlink
        #    self.place_hlink = ''
        #    self.citationref_hlink = ''
        #    self.objref_hlink = ''
        #    self.citations = []   # For creating display sets
        #    self.names = []   # For creating display sets
    
    


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

#     def get_note_by_id(self):
#         """ Luetaan tapahtuman lisätietojen uniq_id """

#     def get_place_by_id(self):
#         """ Luetaan tapahtuman paikan uniq_id """
    
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
        #print ("Place_hlink: " + self.place_hlink)
        print ("Attr_type: " + self.attr_type)
        print ("Attr_value: " + self.attr_value)
        #print ("Citationref_hlink: " + self.citationref_hlink)
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

''' Method now Event_gramps.save() '''
#     def save(self, username, tx):
#         """ Saves the Event to db including
#             links from UserProfile, Person
#         """

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
