'''
    Event compound includes operations for accessing
    - Event
    - related Sources, Notes
    - related Person id

    1. kantaluokka gen.event.*Event*: 
       vain Event-noden parametrit (uniq_id, tyyppi, handle, päivämäärät)
    4. *Event_combo*:
       Event, lähteet, huomautukset, henkilön uniq_id
    2. *Event_w_person*: 
       Event ja ja siihen liittyvät Person-nodet ja roolit (ehkä myös nimet?)
    3. *Event_w_place*: 
       Event ja liittyvät paikat (pyydettäessä myös paikannimet?)

Created on 27.8.2018

@author: jm
'''
import shareds
from models.gen.dates import DateRange

from .event import Event


class Event_combo(Event):
    '''
        Tapahtumat, lähteet, huomautukset, henkilön uniq_id

        Event combo includes operations for accessing
        - Event
        - related Sources, Notes
        - related Person id    

    Lisäksi on kätevä olla metodi __str__(), joka antaa lyhyen sanalliseen muodon
    "syntynyt välillä 1.3.1840...31.3.1840 Hauho".
    '''

    def __init__(self, eid='', desc='', handle=''):
        '''
        Constructor Luo uuden Event_combo -instanssin
        '''
        Event.__init__(self, eid, desc, handle)
        self.note_ref = []      # Note uniq_ids (previous noteref_hlink had
                                # only the first one)
        self.citation_ref = []  # uniq_ids (previous citationref_hlink = '')
        self.place_hlink = ''
        self.objref_hlink = ''

        self.citations = []     # For creating display sets
        self.names = []         # For creating display sets
        self.notes = []         # For creating display sets
        self.place = ''     # TODO Change to places[]


#     def read(self, keys):
#         ''' Access a set of Event complexes using different search fields
#             like key = {'User_id': 1234}
#         '''
#         pass
#     
#     def get(self, uniq_id=None, handle=None):
#         ''' Access an Event complex using one of uniq_id or handle 
#         '''
#         pass
# 
#     def save(self):
#         ''' Store this Event and the included related objects
#         '''
#         pass

    # Entinen get_event_data_by_id()
    def get_event_combo(self):
        """ Read this event with uniq_id's of related Place, Note, and Citation
            nodes.

            Luetaan tapahtuman tiedot 
        """
        #TODO change name to get_w_relations()
              
#         query = """
# MATCH (event:Event) WHERE ID(event)=$pid
# RETURN event"""
        place_get_w_place_note_citation = '''
match (e:Event) where ID(e)=$pid
    optional match (e) -[:PLACE]-> (p:Place)
    optional match (e) -[:CITATION]-> (c:Citation)
    optional match (e) -[:NOTE]-> (n:Note)
return e as event, 
    collect(distinct id(p)) as place_ref, 
    collect(distinct id(c)) as citation_ref, 
    collect(distinct id(n)) as note_ref'''
        result = shareds.driver.session().run(place_get_w_place_note_citation, 
                                              pid=self.uniq_id)

        for record in result:
            # Event data
            event = record["event"]
            self.id = event["id"]
            self.change = event["change"]
            self.type = event["type"]
            if "datetype" in event:
                #TODO: Talletetaanko DateRange -objekti vai vain str?
                dates = DateRange(event["datetype"], event["date1"], event["date2"])
                self.dates = str(dates)
                self.date = dates.estimate()
            else:
                self.dates = ""
                self.date = ""                
            self.description = event["description"]
            # Related data
            for ref in record["note_ref"]:
                self.note_ref.append(ref) # List of uniq_ids # prev. noteref_hlink
            for ref in record["citation_ref"]:
                # uniq_ids of connected Citations
                self.citation_ref.append(ref)   # prev. citationref_hlink = ref
            for ref in record["place_ref"]:
                self.place_hlink = ref

#             # Place
#             place_result = self.get_place_by_id()
#             for place_record in place_result:
#                 self.place_hlink = place_record["uniq_id"]
#             # Note
#             note_result = self.get_note_by_id()
#             for note_record in note_result:
#                 self.noteref_hlink = note_record["noteref_hlink"]
#                 print("noteref_hlink: " + str(self.noteref_hlink))
#             # Citation
#             citation_result = self.get_citation_by_id()
#             for citation_record in citation_result:
#                 self.citationref_hlink = citation_record["citationref_hlink"]
                                
        return True
    
    

    def get_baptism_data(self):
        """ Read the persons related to this babtism Event.

            Luetaan kastetapahtuman henkilöt nimineen
        """

        query = """
MATCH (event:Event) <-[r:EVENT]- (p:Person) 
    WHERE ID(event)=$pid
OPTIONAL MATCH (p) -[:NAME]-> (n:Name)
RETURN  ID(event) AS id,    event.type AS type, 
        event.date AS date, event.dates AS dates,
        ID(p) AS person_id, r.role AS role, 
        COLLECT([n.firstname, n.surname]) AS person_names 
    ORDER BY r.role DESC"""
        return  shareds.driver.session().run(query, pid=self.uniq_id)


    @staticmethod       
    def get_cite_sour_repo (uniq_id):
        """ Get the Citations, Sources and Repositories related to this Event

            Voidaan lukea läheitä viittauksineen kannasta
        """
        #TODO Change name: get_citation_path ??

        if uniq_id:
            where = "WHERE ID(event)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
 MATCH (event:Event) -[a:CITATION]-> (citation:Citation)
        -[b:SOURCE]-> (source:Source)
        -[c:REPOSITORY]-> (repo:Repository) {0}
 RETURN ID(event) AS id, event.type AS type, 
        event.date AS date, event.dates AS dates, 
        COLLECT([ID(citation), citation.dateval, citation.page, 
                citation.confidence, ID(source), source.stitle, c.medium,
                ID(repo), repo.rname, repo.type] ) AS sources
 ORDER BY event.date""".format(where)
                
        return shareds.driver.session().run(query)


    @staticmethod       
    def get_event_cite (uniq_id):
        """ Get an Event with the connected Citations 

            Voidaan lukea tapahtuman tiedot lähdeviittauksineen kannasta
        """

        if uniq_id:
            where = "WHERE ID(event)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
MATCH (event:Event) -[a:CITATION]-> (citation:Citation) {0}
RETURN ID(event) AS id, event.type AS type, 
       event.date AS date, event.dates AS dates, 
       COLLECT( [ID(citation), citation.dateval, citation.page,
                 citation.confidence] ) AS sources
ORDER BY event.date""".format(where)

        return shareds.driver.session().run(query)
