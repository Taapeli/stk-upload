'''

    Event hierarkiasuunnitelma 31.8.2018/JMä

    class gen.event.Event(NodeObject): 
       vain Event-noden parametrit (uniq_id, tyyppi, handle, päivämäärät)

    class gen.event.Event_combo(Event): 
        - __init__()
        - get_event_combo()
        - get_baptism_data()
        - get_event_cite()
       Event, lähteet, huomautukset, henkilön uniq_id

    class bp.gramps.models.event_gramps.Event_gramps(Event)
        - __init__()
        - save() # with relations to UserProfile, Person, Place, Note, Citation, Media

    ? *Event_w_person*: 
       Event ja ja siihen liittyvät Person-nodet ja roolit (ehkä myös nimet?)
    ? *Event_w_place*: 
       Event ja liittyvät paikat (pyydettäessä myös paikannimet?)

    Nämä Event-luokasta periytyvät luokat sisältävät tarpeen mukaan 
    tietokantametodit _read(), get()_ ja _save()_ (_read_ hakukenttien avulla, 
    _get_ uniq_id:n avulla). 
    
    Lisäksi on kätevä olla metodi __str__(), joka antaa lyhyen sanalliseen muodon
    "syntynyt välillä 1.3.1840...31.3.1840 Hauho".
    
    Ehkä _save()_-metodi koskee vain Event-nodea, ei liittyvä nodeja? 
    Ehkä yhteydet myös?
    
    Prosessointiin ja näyttöihin voidaan tehdä tarpeen mukaan bisnes-luokkia, 
    jotka sisältävät esim. poiminta-, yhdistely- ja muokkaussääntöjä ja 
    siellä ehkä hoidetaan isompien kokonaisuuksien talletus 
    (kuten henkilö + nimet ja lähteet).

Created on 2.5.2017
@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from bl.base import NodeObject
from .dates import DateRange
import  shareds
import traceback


class Event(NodeObject):
    """ Person or Family Event object.
    
        Tapahtuma
            
        Properties:
                handle             Unique constant handle (mostly from Gramps)
                change             Original timestamp like 1502552858
                id                 esim. "E0001"
                type               esim. "Birth"
                description        esim. ammatin kuvaus
                date               str aika
                dates              DateRange date expression
                attr[]             dict lisätiedot {attr_type: attr_value}
#                 attr_type          str lisätiedon tyyppi
#                 attr_value         str lisätiedon arvo
            For gramps_loader:
                note_handles[]     str lisätiedon handle (ent. noteref_hlink)
            Planned from gramps_loader:
                place_handles[]    str paikan handle (ent. place_hlink)
                citation_handles[] str viittauksen handle (ent. citationref_hlink)
                #place_hlink       str paikan handle
                #citation_ref      str viittauksen handle
                #objref_hlink      str median handle
        Event_combo properties:
                citations = []     Citations attached
                names = []         Names attached
     """

    def __init__(self):     #, eid='', desc='', handle=''):
        """ Luo uuden event-instanssin """
        NodeObject.__init__(self)
# #         print(f'KUTSUTTU VANHENTUVAA METODIA Event.__init__()')
# #         for line in traceback.format_stack():
# #             if not ( '/venv/' in line or 'python' in line or '/gen/event' in line):
# #                 print(line.strip())

#         self.uuid = None        # UUID
#         self.uniq_id = None     # Neo4j object id
#         self.change = 0         # Object change time
#         self.id = ''            # Gedcom object id like "I1234"
#         self.handle = ''       # Gramps handle (?)
        self.type = ''
        self.description = ''
        self.dates = None
        self.attr = dict()         # prev. attr_type, attr_value
        # Only in Event_combo
        #    self.note_ref = []    # prev. noteref_hlink
        #    self.place_hlink = ''
        #    self.citationref_hlink = ''
        #    self.objref_hlink = ''
        #    self.citations = []   # For creating display sets
        #    self.names = []   # For creating display sets


    def __str__(self):
        return "{} {}".format(self.type, self.dates or "No date")

    @classmethod
    def from_node(cls, node, obj=None):
        '''
        Transforms a node from db node to an object of type Event or Event_combo
        
        <Node id=88532 labels={'Event'} 
            properties={'type': 'Birth', 'change': 1500907890, 
                'handle': '_da692d0fb975c8e8ae9c4986d23', 'attr_value': '', 
                'id': 'E0161', 'attr_type': '', 'description': ''
                'datetype': 0, 'date1': 1754183, 'date2': 1754183}>
        '''
        if not obj:
            obj = cls()
        obj.uniq_id = node.id
        obj.id = node['id']
        obj.uuid = node['uuid']
        obj.type = node['type']
        obj.handle = node['handle']
        obj.change = node['change']
        if "datetype" in node:
            obj.dates = DateRange(node["datetype"], node["date1"], node["date2"])
#             obj.date = obj.dates.estimate()
        else:
            obj.dates = DateRange()
#             obj.date = ""
        obj.description = node['description'] or ''
        obj.attr = node['attr'] or dict()
#         obj.attr_type = node['attr_type'] or ''
#         obj.attr_value = node['attr_value'] or ''
        return obj

    @staticmethod       
    def get_events_wo_citation():
        """ Voidaan lukea viittauksettomia tapahtumia kannasta
        """
        query = """
 MATCH (e:Event) WHERE NOT EXISTS((:Citation)<-[:CITATION]-(e:Event))
 RETURN ID(e) AS uniq_id, e
 ORDER BY e.type, e.date1"""
                
        result = shareds.driver.session().run(query)
        
        titles = ['uniq_id', 'handle', 'change', 'id', 'type', 
                  'description', 'dates', 'attr']
        lists = []
        
        for record in result:
            lists.append(Event._event_listing(record))
        
        return (titles, lists)

    @staticmethod       
    def get_events_wo_place():
        """ Voidaan lukea paikattomia tapahtumia kannasta
        """
        
        query = """
 MATCH (e:Event) WHERE NOT EXISTS((:Place)<-[:PLACE]-(e:Event))
 RETURN ID(e) AS uniq_id, e
 ORDER BY e.type, e.date1"""
                
        result = shareds.driver.session().run(query)
        
        titles = ['uniq_id', 'handle', 'change', 'id', 'type', 
                  'description', 'dates', 'attr']
        lists = []
        
        for record in result:
            lists.append(Event._event_listing(record))

        return (titles, lists)    
    
    @staticmethod       
    def _event_listing(record):
        ''' Forms a list of data field values as strings 
        '''
        data_line = []
        if record['uniq_id']:
            data_line.append(record['uniq_id'])
        else:
            data_line.append('-')
        ev = record["e"]
        if ev['handle']:
            data_line.append(ev['handle'])
        else:
            data_line.append('-')
        if ev['change']:
            data_line.append(ev['change'])
        else:
            data_line.append('-')
        if ev['id']:
            data_line.append(ev['id'])
        else:
            data_line.append('-')
        if ev['type']:
            data_line.append(ev['type'])
        else:
            data_line.append('-')
        if ev['description']:
            data_line.append(ev['description'])
        else:
            data_line.append('-')
#         if ev['date']:
#             data_line.append(ev['date'])
#         else:
#             data_line.append('-')
        if ev['dates']:
            data_line.append(str(DateRange(ev['dates'])))
        else:
            data_line.append('-')
        if 'attr' in record['e']:
            attr_list = ev['attr']
            if attr_list != None and attr_list.__len__() >= 2:
                data_line.append("{}: {}".format(attr_list[0], attr_list[1]))
        elif 'attr_value' in ev and len(ev['attr_value']) > 0: #Todo remove Obsolete variable
            data_line.append("({})".format(ev['attr_value'])[1:-1])
        else:
            data_line.append('-')
        return data_line

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
        print ("Change: {}".format(self.change))
        print ("Id: " + self.id)
        print ("Type: " + self.type)
        print ("Description: " + self.description)
        print ("Dateval: " + self.dates)
        print ("Dates: " + str(self.dates))
        #print ("Place_hlink: " + self.place_hlink)
        print ("Attr: " + str(self.attr))
        #print ("Citationref_hlink: " + self.citationref_hlink)
        return True


    def print_compared_data(self, comp_event, pname1, pname2, print_out=True):
        points = 0
        """ Tulostaa pää- ja vertailtavan tapahtuman tiedot """
        print ("*****Events*****")
        if print_out:
            print ("Handle: " + self.handle + " # " + comp_event.handle)
            print ("Change: {} # {}".format(self.change, comp_event.change))
            print ("Id: " + self.id + " # " + comp_event.id)
            print ("Type: " + self.type + " # " + comp_event.type)
            print ("Description: " + self.description + " # " + comp_event.description)
            print ("Dateval: " + self.dates + " # " + comp_event.dates)
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
