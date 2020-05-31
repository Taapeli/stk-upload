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
from sys import stderr

from .event import Event
from models.gen.cypher import Cypher_event


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

    def __init__(self):         #, eid='', desc='', handle=''):
        '''
        Constructor Luo uuden Event_combo -instanssin
        '''
        Event.__init__(self)
        #TODO Remove:  Event_combo.clearnames is not set or in use
        self.clearnames = []    # filled by models.gen.place.Place.show_names_list
                                # to show names list 
        self.role = ''          # role of event from EVENT relation, if available
        self.note_ref = []      # Note uniq_ids (previous noteref_hlink had
                                # only the first one)
        self.citation_ref = []  # uniq_ids (previous citationref_hlink = '')
        self.place_ref = []     # uniq_ids (previous placeref_hlink = '')
        self.place = None       # Place node, if included
        self.media_ref = []     # uniq_ids (preovious self.objref_hlink had gramps handles)
        self.note_ref = []      # uniq_ids (previously note[])
        
        self.citations = []     # For creating display sets
        self.person = None        # Persons names connected; for creating display
        #self.notes = []         # For creating display sets
        #self.places = []        # Places of the event (for person list)


# @classmethod from_node(cls, node): see event.from_node


    # Entinen get_event_data_by_id()
    def get_event_combo(self):
        """ Read this event with uniq_id's of related Place, Note, and Citation
            nodes.
            #TODO: Tulisi lukea Notes ja Citations vasta get_persondata_by_id() lopuksi

            Luetaan tapahtuman tiedot 
        """
        with shareds.driver.session() as session:
            try:
                result = session.run(Cypher_event.get_w_place_note_citation, 
                                     pid=self.uniq_id)
    
                for record in result:
                    # <Record 
                    #    event=<Node id=84467 labels={'Event'} 
                    #    properties={'datetype': 0, 'change': 1522422810, 'description': '', 
                    #        'handle': '_dd8aab5481c7c18befdd4baa628', 'attr_type': '', 
                    #        'id': 'E2965', 'date2': 1829189, 'type': 'Baptism', 
                    #        'date1': 1829189, 'attr_value': ''}> 
                    #        place_ref=[78213] 
                    #    citation_ref=[] 
                    #    note_ref=[]>
                    node = record["event"]
                    # Marshall self from the Node from db
                    self.from_node(node, self)
        
                    # Related data
                    for ref in record["note_ref"]:
                        self.note_ref.append(ref) # List of uniq_ids
                    for ref in record["citation_ref"]:
                        # uniq_ids of connected Citations
                        self.citation_ref.append(ref)
                    for ref in record["place_ref"]:
                        self.place_ref.append(ref)
            except Exception as err:
                print("iError get_event_combo: {1} {0}".format(err, self.uniq_id), file=stderr)

    @staticmethod       
    def get_connected_events_w_links(uniq_id):
        """ Read all Events referred from given node (Person or Family)
            with links to connected Places, Notes, Citations, Media
            Luetaan henkilön tapahtumat

            Korvaamaan models.gen.person_combo.Person_combo.get_event_data_by_id etc

╒═════════╤═══════════════════════════════════════════════════╤═══════╤══════════╤═══════╕
│"role"   │"event"                                            │"x_uid"│"label"   │"x_id" │
╞═════════╪═══════════════════════════════════════════════════╪═══════╪══════════╪═══════╡
│"Primary"│{"datetype":0,"change":1500907890,"description":"",│null   │null      │null   │
│         │"handle":"_da692d0fb975c8e8ae9c4986d23","attr_type"│       │          │       │
│         │:"","id":"E0161","date2":1754183,"type":"Birth","da│       │          │       │
│         │te1":1754183,"attr_value":""}                      │       │          │       │
├─────────┼───────────────────────────────────────────────────┼───────┼──────────┼───────┤
│"Kummi"  │{"datetype":0,"change":1504295227,"description":"An│90106  │"Citation"│"C0046"│
│         │na Florinin kaste","handle":"_da68e18032c6cbd294a41│       │          │       │
│         │be46ff","attr_type":"","id":"E0076","date2":1779729│       │          │       │
│         │,"type":"Baptism","date1":1779729,"attr_value":""} │       │          │       │
├─────────┼───────────────────────────────────────────────────┼───────┼──────────┼───────┤
│"Kummi"  │{"datetype":0,"change":1504295227,"description":"An│78279  │"Place"   │"P0002"│
│         │na Florinin kaste","handle":"_da68e18032c6cbd294a41│       │          │       │
│         │be46ff","attr_type":"","id":"E0076","date2":1779729│       │          │       │
│         │,"type":"Baptism","date1":1779729,"attr_value":""} │       │          │       │
├─────────┼───────────────────────────────────────────────────┼───────┼──────────┼───────┤
│"Primary"│{"datetype":0,"change":1507204555,"description":"",│90343  │"Citation"│"C0462"│
│         │"handle":"_da692d5233a6fc0d5bc142579ce","attr_type"│       │          │       │
│         │:"","id":"E0166","date2":1789257,"type":"Death","da│       │          │       │
│         │te1":1789257,"attr_value":""}                      │       │          │       │
└─────────┴───────────────────────────────────────────────────┴───────┴──────────┴───────┘
        """

        get_events_w_links = """
match (root) -[r:EVENT]-> (e:Event) where id(root)=$root
optional match (e) -[rx]-> (x)
return r.role as role, e as event, 
       id(x) as x_uid, labels(x)[0] as label, x.id as x_id"""
        result = shareds.driver.session().run(get_events_w_links, root=uniq_id)
        events = []
        for record in result:
            node = record['event']
            e = Event_combo.from_node(node)
            e.role = record['role']
            # Links
            linked = record['label']
            if linked == 'Citation':
                e.citation_ref.append(record['x_uid'])
            elif linked == 'Place':
                e.place_hlink = record['x_uid']
            elif linked:
                print ("*** Ohitettu linkki {}".format(linked))
                    
            events.append(e)
        return events


    def get_participants(self):
        """ Read the persons related to this Event.

            Luetaan [kaste]tapahtuman henkilöt nimineen
        """
        return  shareds.driver.session().run(Cypher_event.get_participants_uniq_id, 
                                             pid=self.uniq_id)


    def get_baptism_data(self):
        """ Read the persons related to this babtism Event.

            Luetaan kastetapahtuman henkilöt nimineen.
            
            Called from event.html link
        """

        query = """
MATCH (event:Event) <-[r:EVENT]- (p:Person) 
    WHERE ID(event)=$pid
OPTIONAL MATCH (p) -[:NAME]-> (n:Name)
RETURN  //ID(event) AS id,    event.type AS type,
        //[event.datetype, event.date1, event.date2] AS dates,
        ID(p) AS person_id, r.role AS role, 
        COLLECT([n.firstname, n.surname]) AS person_names 
    ORDER BY r.role DESC"""
        return  shareds.driver.session().run(query, pid=self.uniq_id)


#     @staticmethod       
#     def get_cite_sour_repo (uniq_id):
#         """ Get the Citations, Sources and Repositories related to this Event.
# 
#             Voidaan lukea läheitä viittauksineen kannasta  --  NOT IN USE
#         """
#         #Change name: get_citation_path ??
# 
#         if uniq_id:
#             where = "WHERE ID(event)={} ".format(uniq_id)
#         else:
#             where = ''
#         
#         query = """
#  MATCH (event:Event) -[a:CITATION]-> (citation:Citation)
#         -[b:SOURCE]-> (source:Source)
#         -[c:REPOSITORY]-> (repo:Repository) {0}
#  RETURN ID(event) AS id, event.type AS type, // event.date AS date,
#         event.datetype AS datetype, event.date1 AS date1, event.date2 AS date2,
#         COLLECT([ID(citation), citation.dateval, citation.page, 
#                 citation.confidence, ID(source), source.stitle, c.medium,
#                 ID(repo), repo.rname, repo.type] ) AS sources
#  ORDER BY event.date1""".format(where)
                
        return shareds.driver.session().run(query)


    @staticmethod       
    def get_event_cite (uniq_id):
        """ Get an Event with the connected Citations.  - NOT IN USE

            Voidaan lukea tapahtuman tiedot lähdeviittauksineen kannasta
        """

        if uniq_id:
            where = "WHERE ID(event)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
MATCH (event:Event) -[a:CITATION]-> (citation:Citation) {0}
RETURN ID(event) AS id, event.type AS type, // event.date AS date, event.dates AS dates, 
       [event.datetype, event.date1, event.date2] AS dates,
       COLLECT( [ID(citation), citation.dateval, citation.page,
                 citation.confidence] ) AS sources
ORDER BY event.date1""".format(where)

        return shareds.driver.session().run(query)
