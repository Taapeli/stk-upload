'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

Components moved 15.5.2020 from 
    - models.gen.family.Family -> Family
    - models.gen.family_combo.Family_combo -> FamilyBl
    - models.gen.family_combo.Family_combo -> FamilyBl, FamilyReader

@author: jm 
'''
import  shareds

from .base import NodeObject, Status
from pe.db_reader import DBreader

from models.gen.dates import DateRange


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
        
        You can create a Family or FamilyBl instance. (cls is the class 
        where we are, either Family or FamilyBl)
        
        <Node id=99991 labels={'Family'} 
            properties={'rel_type': 'Married', 'handle': '_da692e4ca604cf37ac7973d7778', 
            'id': 'F0031', 'change': 1507492602}>
        '''
        n = cls()
        n.uniq_id = node.id
        n.id = node.get('id','')
        n.uuid = node['uuid']
        n.handle = node['handle']
        n.change = node['change']
        n.rel_type = node.get('rel_type','')
        n.father_sortname = node.get('father_sortname','')
        n.mother_sortname = node.get('mother_sortname','')
        if "datetype" in node:
            n.dates = DateRange(node["datetype"], node["date1"], node["date2"])
        else:
            n.dates = DateRange()
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
    
    def get_family_data(self, uuid:str, wanted=[]):
        """ Read Family information including Events, Children, Notes and Sources.

            Returns a dict {item:Family, status=0, statustext:None}
            
            where status code is one of
                - Status.OK = 0
                - Status.NOT_FOUND = 1
                - Status.ERROR = 2
            
            Ther wanted parameter is a string of short keywords separated by ':'.
            
            Operations path
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
                FamilyBl.mother, .names, event_birth, event_death
                FamilyBl.father, .names, event_birth, event_death
                FamilyBl.events
                FamilyBl.notes
                FamilyBl.sources / citation -> source -> repocitory ?
                FamilyBl.children, .names, event_birth, event_death
        """

        # Select data by wanted parameter like 'pare:name:even:plac':
        
        # all - all data
        select_all = 'all' in wanted
        if not wanted:  select_all = True
        # pare - Parents (mother, father)
        select_parents  = select_all or 'pare' in wanted
        # chil - Children
        select_children = select_all or 'chil' in wanted
        # name - Person names (for parents, children)
        select_names    = select_all or 'name' in wanted
        # even - Events
        select_events   = select_all or 'even' in wanted
        # plac - Places (for events)
        select_places   = select_all or 'plac' in wanted
        # note - Notes
        select_notes    = select_all or 'note' in wanted
        # soour - Sources (Citations, Sources, Repositories)
        select_sources  = select_all or 'sour' in wanted
        ## medi - Media
        #select_media  = select_all or 'medi' in wanted
        """
            1. Get Family node by user/common
               res is dict {item, status, statustext}
        """
        res = self.dbdriver.dr_get_family_by_uuid(self.use_user, uuid)
        family = res.get('item')
        results = {'item': family, 
                   'status': res.get('status'),
                   'statustext':res.get('statustext')}
        if not family:
            return results
        # The Nodes for search of Sources and Notes (Family and Events)
        src_list = [family.uniq_id]
        """
            2. Get Parent nodes [optionally] with default Name
               res is dict {items, status, statustext}
        """
        if select_parents:
            res = self.dbdriver.dr_get_family_parents(family.uniq_id, 
                                                      with_name=select_names)
            for p in res.get('items'):
                # For User's own data, no hiding for too new persons
                if self.use_user:           p.too_new = False
                if p.role == 'father':      family.father = p
                elif p.role == 'mother':    family.mother = p
        """
            3. Get Child nodes [optionally] with Birth and Death nodes
               res is dict {items, status, statustext}
        """
        if select_children:
            res = self.dbdriver.dr_get_family_children(family.uniq_id,
                                                       with_events=select_events,
                                                       with_names=select_names)
            family.num_hidden_children = 0
            for p in res.get('items'):
                # For User's own data, no hiding for too new persons
                if self.use_user:   p.too_new = False
                if p.too_new:       family.num_hidden_children += 1
                family.children.append(p)
        """
            4. Get family Events node with Places
               res is dict {items, status, statustext}
        """
        if select_events:
            res = self.dbdriver.dr_get_family_events(family.uniq_id, 
                                                     with_places=select_places)
            for e in res.get('items'):
                family.events.append(e)
                src_list.append(e.uniq_id)
        """
            5 Get family and event Sources Citations and Repositories
              optionally with Notes
        """
        if select_sources:
            res = self.dbdriver.dr_get_family_sources(src_list)
            for s in res.get('items'):
                family.sources.append(s)
        """
            6 Get Notes for family and events
        """
        if select_notes:
            res = self.dbdriver.dr_get_family_notes(src_list)
            for s in res.get('items'):
                family.sources.append(s)

        return results


    def get_person_families(self, uuid:str):
        """ Get all families for given person in marriage date order.
        """
        res = self.dbdriver.dr_get_person_families(uuid)
        families = res.get('items')
        if families:
#             try:
            families.sort(key=lambda x: x.dates)
            return {"items":families, "status":Status.OK}
#             except TypeError:
#                 print(f'bl.family.FamilyReader.get_person_families: sort by date failed')
#                 return {"items":families, "status":Status.OK, 
#                     "statustext": 'Failed to sort families'}
        else:
            return {"items":[], "status":Status.NOT_FOUND, 
                    "statustext": 'This person has no families'}


    # The followind may be obsolete

    def get_children_by_id(self):
        raise("Obsolete bl.family.FamilyReader.get_children_by_id")


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
