'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

Components moved 15.5.2020 from 
    - models.gen.family.Family -> Family
    - models.gen.family_combo.Family_combo -> FamilyBl
    - models.gen.family_combo.Family_combo -> FamilyBl, FamilyReader

@author: jm 
'''
#from sys import stderr
import  shareds
from .base import NodeObject
from pe.db_reader import DBreader, FamilyResult

from bl.place import PlaceBl
from bl.source import SourceBl
from ui.place import place_names_from_nodes

#TODO remove this
from pe.neo4j.cypher_family import CypherFamily

from models.gen.dates import DateRange
from models.gen.cypher import Cypher_person #, Cypher_family
from models.gen.event_combo import Event_combo
#from models.gen.person import Person
from models.gen.person_name import Name
from models.gen.citation import Citation
from models.gen.repository import Repository
from models.gen.note import Note
#from .source import Source
#from .place_combo import Place_combo
#from ui.user_context import UserContext
#from models.gen import family

# Import these later to handle circular dependencies where referencing from Person classes! 
#from .person_combo import Person_combo
#from .person_combo import Person_as_member

class Family(NodeObject):
    """ Family Node object.
    
        Properties:
                change
                id              esim. "F0001"
                uniq_id         int database key
                uuid            str UUID key
                rel_type        str suhteen tyyppi
                priv            str private if exists
                father_sortname str search key
                mother_sortname str search key
     """

    def __init__(self, uniq_id=None):
        """ Creates a new Family instance representing a database Family node.
        
        """
        """ Luo uuden family-instanssin """
        NodeObject.__init__(self, uniq_id)
        self.priv = None
        self.rel_type = ''
        self.dates = None       #TODO DateRange marriage .. divorce
        # Sorting name of family's father and mother
        self.father_sortname = ''
        self.mother_sortname = ''

    def __str__(self):
        if self.rel_type:   rel = self.rel_type.lower()
        else:               rel = _('undefined relation')
        return "{} {}".format(self.id, rel, self.dates)
    
    @classmethod
    def from_node(cls, node):
        '''
        Transforms a db node to an object of type Family.
        
        You can create a Family or Family_combo instance. (cls is the class 
        where we are, either Family or Family_combo)
        
        <Node id=99991 labels={'Family'} 
            properties={'rel_type': 'Married', 'handle': '_da692e4ca604cf37ac7973d7778', 
            'id': 'F0031', 'change': 1507492602}>
        '''
        n = cls()
        n.uniq_id = node.id
        n.id = node['id'] or ''
        n.uuid = node['uuid']
        n.handle = node['handle']
        n.change = node['change']
        n.rel_type = node['rel_type'] or ''
        n.father_sortname = node['father_sortname']
        n.mother_sortname = node['mother_sortname']
        if "datetype" in node:
            n.dates = DateRange(node["datetype"], node["date1"], node["date2"])
        return n


class FamilyBl(Family):
    """ Family business logic object carries the family and connected data.
            
        Properties from Family:
                change
                id              esim. "F0001"
                uniq_id         int database key
                uuid            str UUID key
                rel_type        str "marriage" etc.
                father_sortname str search key
                mother_sortname str search key
#             #TODO: Obsolete properties?
#                 eventref_hlink      str tapahtuman osoite
#                 eventref_role       str tapahtuman rooli
#                 childref_hlink      str lapsen osoite
#                 noteref_hlink       str lisätiedon osoite
#                 citationref_hlink   str lisätiedon osoite
     """

    def __init__(self, uniq_id=None):
        """ Creates a Family instance for carrying whole family information. 
        """
        Family.__init__(self, uniq_id)

        self.father = None
        self.mother = None
        self.children = []          # Child object
        self.events = []            # Event objects
        self.notes = []
        self.sources = []
        self.marriage_dates = None
        self.note_ref = []          # For a page, where same note may be referenced
                                    # from multiple events and other objects

#         #TODO Obsolete parameters???
#         self.eventref_hlink = []
#         self.eventref_role = []
#         self.childref_hlink = []    # handles
#         self.noteref_hlink = []
#         self.citationref_hlink = []


class FamilyReader(DBreader):
    '''
        Data reading class for Family objects with associated data.

        - Use pe.db_reader.DBreader.__init__(self, dbdriver, u_context) 
          to define the database driver and user context

        - Returns a Result object which includes the tems and eventuel error object.
    '''

#     @staticmethod
#     def get_family_paths_apoc(uniq_id):
#         ''' Read a person and paths for all connected nodes.
#             Experimental!
#         '''


    def get_children_by_id(self):
        """ Luetaan perheen lasten tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)-[r:CHILD]->(person:Person)
  WHERE ID(family)=$pid
RETURN ID(person) AS children"""
        return  shareds.driver.session().run(query, {"pid": pid})


    def get_family_events(self):
        """ Luetaan perheen tapahtumien tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)-[r:EVENT]->(event:Event)
  WHERE ID(family)=$pid
RETURN r.role AS eventref_role, event.handle AS eventref_hlink"""
        return  shareds.driver.session().run(query, {"pid": pid})

    @staticmethod
    def find_family_for_event(event_uniq_id):
        """ Returns Family instance which has given Event.

            NOT IN USE. For models.datareader.get_source_with_events
        """                
        query = """
MATCH (family:Family)-[r:EVENT]->(event)
  WHERE ID(event)=$pid
RETURN family"""
        result = shareds.driver.session().run(query, pid=event_uniq_id)
        for record in result:
            f = FamilyBl.from_node(record[0])
            return f
        raise LookupError(f"Family {event_uniq_id} not found")


#     def get_family_data_by_id(self): #see models.gen.family_combo.Family_combo.get_family_data_by_id
#         """ Luetaan perheen tiedot. 
#             Called from models.datareader.get_families_data_by_id 
#                    from bp.tools.routes.show_family_data
    
    
    def get_family_data(self, uuid:str):
        """ Read Family information including Events, Children, Notes and Sources.
        
            1) read 
                (f:Family) --> (e:Event)
                (f:Family) -[:PARENT]-> (pp:Person) -> (np:Name)
                (f:Family) -[:CHILD]->  (pc:Person) -> (nc:Name)
                (f:Family) --> (fn:Note)
                (e:Event) --> (en:Note)
                (f:Family) --> (fac:Citation) --> (fas:Source) --> (far:Repository)
                (e:Event) --> (evc:Citation) --> (evs:Source) --> (evr:Repository)
 
            2) read
                (pp:Person) --> (ppe:Event) --> (:Place)
                (pc:Person) --> (pce:Event) --> (:Place)

            3) build
                Family_combo.mother, .names, event_birth, event_death
                Family_combo.father, .names, event_birth, event_death
                Family_combo.events
                Family_combo.notes
                Family_combo.sources / citation -> source -> repocitory ?
                Family_combo.children, .names, event_birth, event_death
            Returns a Family object with other objects included
        """

        # Import here to handle circular dependency
        from models.gen.person_combo import Person_combo
        results = FamilyResult()
        """
            1. Get Family node by user/common
        """
        # res is dict {item, status, statustext}
        res = self.dbdriver.dr_get_family_uuid(self.use_user, uuid)
        family = res.get('item')
        results.error = res.get('statustext')
        if not family:
            return results
        results.items = family

        """
            2. Get Parent nodes
               optionally with default Name
        """
        # res is dict {items, status, statustext}
        res = self.dbdriver.dr_get_family_parents(family.uniq_id, with_name=True)
        for p in res.get('items'):
            # For User's own data, no hiding for too new persons
            if self.use_user:           p.too_new = False
            if p.role == 'father':      family.father = p
            elif p.role == 'mother':    family.mother = p

        """
            3. Get Child nodes
               optionally with Birth and Death nodes
        """
        res = self.dbdriver.\
              dr_get_family_children(family.uniq_id, with_events=True, with_names=True)
        num_hidden_children = 0
        for p in res.get('items'):
            # For User's own data, no hiding for too new persons
            if self.use_user:   p.too_new = False
            if p.too_new:       num_hidden_children += 1
            family.children.append(p)

        """
            4. Get family Events node with Places
        """
        events = self.dbdriver.dr_get_family_events(family.uniq_id, with_places=True)
        for e in events:
            family.events.append(e)
        """
            5 Get family event Sources Citations and Repositories
              optionally with Notes
        """
        sources = self.dbdriver.dr_get_family_sources(family.uniq_id, with_notes=True)
        for c in sources:
            family.sources.append(c)



        with shareds.driver.session() as session:
            try:
                result = session.run(CypherFamily.get_family_data, 
                                     id_list=[family.uniq_id])
                for record in result:
                    """
                        2. Get Events node [with Place?]
                    """
                    for event_node, place_node in record['family_event']:
                        if event_node:
                            # event_node:
                            # <Node id=242570 labels={'Event'} 
                            #    properties={'datetype': 0, 'change': 1528183878, 'description': '', 
                            #        'handle': '_dcf94f35ea262b7e1a0a0066d6e', 'id': 'E1692', 
                            #        'date2': 1875043, 'type': 'Marriage', 'date1': 1875043}>
                            e = Event_combo.from_node(event_node)
                            if place_node:
                                # place_node: <Node id=73479 labels={'Place'} properties={'coord':
                                # [60.5625, 21.609722222222224], 'id': 'P0468', 'type': 'City', 'uuid':
                                # 'd1d0693de1714a47acf6442d64246a50', 'pname': 'Taivassalo', 'change':
                                # 1556953682}>
                                e.place = PlaceBl.from_node(place_node)

                                # Look for surrounding place:
                                res = session.run(Cypher_person.get_places, uid_list=[e.uniq_id])
                                for rec in res:
                                    e.place.names = place_names_from_nodes(rec['pnames'])
                                    if rec['pi']:
                                        pl_in = PlaceBl.from_node(rec['pi'])
                                        pl_in.names = place_names_from_nodes(rec['pinames'])
                                        e.place.uppers.append(pl_in)

                            family.events.append(e)
                    """
                        3. Get Parent nodes [with default Name?]
                    """
#                     for role, person_node, name_node, birth_node, death_node in record['parent']

                    """
                        4. Get Child nodes [with Birth and Death nodes?]
                    """
#                     family.no_of_children = 0
#                     family.num_hidden_children = 0
#                     for person_node, name_node, birth_node, death_node in record['child']:
#                         # record['child'][0]:
#                         # [<Node id=235176 labels={'Person'} 
#                         #    properties={'sortname': '#Andersdotter#Maria Christina', 
#                         #        'datetype': 19, 'confidence': '2.0', 'sex': 2, 'change': 1532009600, 
#                         #        'handle': '_dd2a65b2f8c7e05bc664bd49d54', 'id': 'I0781', 'date2': 1877226, 'date1': 1877219}>, 
#                         #  <Node id=235177 labels={'Name'} 
#                         #    properties={'firstname': 'Maria Christina', 'type': 'Birth Name', 'suffix': 'Andersdotter', 
#                         #        'prefix': '', 'surname': '', 'order': 0}>, 
#                         #  <Node id=242697 labels={'Event'} 
#                         #    properties={'datetype': 0, 'change': 1532009545, 'description': '', 'handle': '_dd2a65b218a14e81692d77955d2', 
#                         #        'id': 'E1886', 'date2': 1877219, 'type': 'Birth', 'date1': 1877219}>, 
#                         #  <Node id=242702 labels={'Event'} 
#                         #    properties={'datetype': 0, 'change': 1519916327, 'description': '', 'handle': '_dd2a65b218a4e85ab141faeab48', 
#                         #        'id': 'E1887', 'date2': 1877226, 'type': 'Death', 'date1': 1877226}>
#                         # ]
#                         if person_node:
#                             family.no_of_children += 1
#                             p = Person_combo.from_node(person_node)
#                             if name_node:
#                                 p.names.append(Name.from_node(name_node))
#                             set_birth_death(p, birth_node, death_node)
#                             if not self.use_user:
#                                 # Common data
#                                 if p.too_new:
#                                     family.num_hidden_children += 1
#                                     continue
#                             else: 
#                                 p.too_new = False
#                             family.children.append(p)
                    """
                        5. Get Citation, Source, Repository nodes
                    """
                    for repository_node, source_node, citation_node in record['sources']:
                        # record['sources'][0]:
                        # [<Node id=253027 labels={'Repository'} 
                        #    properties={'handle': '_dcad22f5914b34fe61c341dad0', 'id': 'R0068', 'rname': 'Taivassalon seurakunnan arkisto', 
                        #        'type': 'Archive', 'change': '1546265916'}>, 
                        #  <Node id=247578 labels={'Source'} 
                        #    properties={'handle': '_e085cd6d68d256a94afecd2162d', 'id': 'S1418', 
                        #        'stitle': 'Taivassalon seurakunnan syntyneiden ja kastettujen luettelot 1790-1850 (I C:4)', 
                        #        'change': '1543186596'}>, 
                        #  <Node id=246371 labels={'Citation'} 
                        #    properties={'handle': '_dd12b0b88d5741ee11d8bef1ca5', 'id': 'C0854', 'page': 'Vigde år 1831 April 4', 
                        #        /* dates missing here */, 'change': 1543186596, 'confidence': '2'}>
                        # ]
                        if repository_node:
                            source = SourceBl.from_node(source_node)
                            cita = Citation.from_node(citation_node)
                            repo = Repository.from_node(repository_node)
                            source.repositories.append(repo)
                            source.citations.append(cita)
                            family.sources.append(source)
                        
                    for node in record['note']:
                        note = Note.from_node(node)
                        family.notes.append(note)

            
            except Exception as e:
                results.error = 'Error get_family_data: {} {}'.format(e.__class__.__name__, e)          
                raise      
    
        return results

    
#     @staticmethod           
#     def get_dates_parents(tx, uniq_id): #see models.gen.family_combo.Family_combo
#         return tx.run(Cypher_family.get_dates_parents,id=uniq_id)

#     @staticmethod           
#     def set_dates_sortnames(tx, uniq_id, dates, father_sortname, mother_sortname): #see models.gen.family_combo.Family_combo
#         ''' Update Family dates and parents' sortnames.

#     @staticmethod       
#     def hide_privacy_protected_families(families): #see models.gen.family_combo.Family_combo

#     @staticmethod       
#     def get_families(o_context, opt='father', limit=100): #see models.gen.family_combo.Family_combo
#         """ Find families from the database """
    
#     @staticmethod       
#     def get_all_families(): #see models.gen.family_combo.Family_combo
#         """ Find all families from the database - not in use!
    
#     @staticmethod       
#     def get_own_families(user=None): #see models.gen.family_combo.Family_combo
#         """ Find all families from the database - not in use!

#     @staticmethod       
#     def get_marriage_parent_names(event_uniq_id): #see models.gen.family_combo.Family_combo

#     def get_parent_by_id(self, role='father'): #see models.gen.family_combo.Family_combo
#         """ Luetaan perheen isän (tai äidin) tiedot """
