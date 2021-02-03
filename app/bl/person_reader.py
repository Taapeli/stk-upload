'''
Created on 30.1.2021

@author: jm
'''
from pe.db_reader import DbReader
from bl.base import Status
from bl.person import PersonBl
from bl.person_name import Name
from bl.event import EventBl
from bl.family import FamilyBl

import logging 
logger = logging.getLogger('stkserver')
#from models.source_citation_reader import get_citations_js


class PersonReaderTx(DbReader):
    '''
        Data reading class for Person objects with associated data.

        - Uses pe.db_reader.DbReader.__init__(self, readservice, u_context) 
          to define the database driver and user context

        - Returns a Result object.
    '''

    def get_person_data(self, uuid:str): #, args:dict):
        '''
        Get a Person with all connected nodes for display in Person page as object tree.
        '''
        """
        For Person data page we must have all business objects, which has connection
        to current Person. This is done in the following steps:
    
        1. (p:Person) --> (x:Name|Event)
        2. (p:Person) <-- (f:Family)
           for f
           (f) --> (fp:Person) -[*1]-> (fpn:Name)
           (f) --> (fe:Event)
        3. for z in p, x, fe, z, s, r
           (y) --> (z:Citation|Note|Media)
        4. for pl in z:Place, ph
           (pl) --> (pn:Place_name)
           (pl) --> (ph:Place)
        5. for c in z:Citation
           (c) --> (s:Source) --> (r:Repository)
        
            p:Person
              +-- x:Name
              |     +-- z:Citation (2)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
        (1)   +-- x:Event
              |     +-- z:Place
              |     |     +-- pn:Place_name
              |     |     +-- z:Place (hierarkia)
              |     |     +-- z:Citation (2)
              |     |     +-- z:Note (3)
              |     |     +-- z:Media (4)
              |     +-- z:Citation (2)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
              +-- f:Family
              |     +-- fp:Person
              |     |     +-- fpn:Name
              |     +-- fe:Event (1)
              |     +-- z:Citation (2)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
        (2)   +-- z:Citation
              |     +-- s:Source
              |     |     +-- r:Repository
              |     |     |     +-- z:Citation (2)
              |     |     |     +-- z:Note (3)
              |     |     |     +-- z:Media (4)
              |     |     +-- z:Citation (2)
              |     |     +-- z:Note (3)
              |     |     +-- z:Media (4)
              |     +-- z:Note (3)
              |     +-- z:Media (4)
        (3)    +-- z:Note
              |     +-- z:Citation (2)
              |     +-- z:Media (4)
        (4)   +-- z:Media
                    +-- z:Citation (2)
                    +-- z:Note (3)
          
        The objects are stored in PersonReader.person object p tree.
        - x and f: included objects (in p.names etc)
        - others: reference to "PersonReader.objs" dictionary (p.citation_ref[] etc)
    
        For ex. Sources may be referenced multiple times and we want to process them 
        once only.
        """

        # Objects by uniq_id, referred from current person
        self.readservice.objs = {}

        # 1. Read Person p, if not denied
        res = self.readservice.tx_get_person_by_uuid(uuid, active_user=self.use_user)
        if Status.has_failed(res):
            # Not found, not allowd (person.too_new) or error
            if res.get('status') == Status.NOT_FOUND:
                return {'status':Status.NOT_FOUND, 
                        'statustext': 'Requested person not found'}
            return res
        ''' 
        Got dictionary: Status and following objects:
            - person_node, root, name_nodes, event_node_roles, cause_of_death, families
            - - root = {root_type, root,user, batch_id}
            - - event_node_roles = [[Event node, role], ...]
            - - cause_of_death = Event node
            - - families = [{family_rel, family_role, family_node, 
                             family_events, relation_type, family_members}, ...]
            - - - family_events = [event_node]
            - - - family_members = [{member_node, name_node, parental_role, birth_node}, ...]
            - - - marriage_date = {datetype, date1, date2}
        '''
        person = PersonBl.from_node(res.get('person_node'))
        person.families_as_parent = []
        person.families_as_child = []

        # Info about linked Batch or Audit node
        root_dict = res.get('root')   # {root_type, root_user, batch_id}
        for name_node in res.get('name_nodes'):
            person.names.append(Name.from_node(name_node))
        for event_node, event_role in res.get('event_node_roles'):
            event = EventBl.from_node(event_node)
            event.role = event_role
            person.events.append(event)
        cause_node = res.get('cause_of_death')
        person.cause_of_death = EventBl.from_node(cause_node)

        for f in res.get('families'):
            family = FamilyBl.from_node(f['family_node'])
            family_role = f['family_role']          # Main person's role in family
            for event_node in f['family_events']:
                event = EventBl.from_node(event_node)
                if event.type == "Marriage":
                    family.marriage_dates = event.dates
                family.events.append(event)

            for m in f['family_members']:
                # Family member
                member = PersonBl.from_node(m['member_node'])
                name_node = m['name_node']
                if name_node:
                    name = Name.from_node(name_node)
                    member.names.append(name)
                event_node = m['birth_node']
                if event_node:
                    event = EventBl.from_node(event_node)
                    member.birth_date = event.dates
                # Add member to family
                parental_role = m['parental_role']  # Family member's role
                if parental_role == "father":
                    family.father = member
                elif parental_role == "mother":
                    family.mother = member
                else:       # chils
                    family.children.append(member)
                
            if family_role: # main person is a father or mother
                person.families_as_parent.append(family)
                person.events += family.events
            else:           # child
                person.families_as_child.append(family)

            if not self.user_context.use_common():
                family.remove_privacy_limits()

        #    Sort all Person and family Events by date
        person.events.sort()

#         # 3. (p:Person) <-- (f:Family)
#         #    for f
#         #      (f) --> (fp:Person) -[*1]-> (fpn:Name) # members
#         #      (fp)--> (me:Event{type:Birth})
#         #      (f) --> (fe:Event)
#         res = self.readservice.dr_get_person_families(person.uniq_id)
#         # res {'families_as_child', 'families_as_parent', 'family_events', 'status'}
#         if  Status.has_failed(res):
#             print(f'get_person_data: No families for person {uuid}')
# 
# 
# 
#         # 4. for pl in z:Place, ph
#         #      (pl) --> (pn:Place_name)
#         #      (pl) --> (pi:Place)
#         #      (pi) --> (pin:Place_name)
#         ret = self.readservice.dr_get_object_places(person)
#         if  Status.has_failed(res):
#             print(f'get_person_data: Event places read error: {ret.get("statustext")}')
#      
#         # 5. Read their connected nodes z: Citations, Notes, Medias
#         #    for y in p, x, fe, z, s, r
#         #        (y) --> (z:Citation|Note|Media)
#         new_objs = [-1]
#         self.readservice.citations = {}
#         while len(new_objs) > 0:
#             new_objs = self.readservice.dr_get_object_citation_note_media(person, new_objs)
# 
#         # Calculate the average confidence of the sources
#         if len(self.readservice.citations) > 0:
#             summa = 0
#             for cita in self.readservice.citations.values():
#                 summa += int(cita.confidence)
#                  
#             aver = summa / len(self.readservice.citations)
#             person.confidence = "%0.1f" % aver # string with one decimal
#      
#         # 6. Read Sources s and Repositories r for all Citations
#         #    for c in z:Citation
#         #        (c) --> (s:Source) --> (r:Repository)
#         self.readservice.dr_get_object_sources_repositories()
#     
#         # Create Javascript code to create source/citation list
#         jscode = get_citations_js(self.readservice.objs)
        jscode = "/* todo */"
    
        # Return Person with included objects,  and javascript code to create
        # Citations, Sources and Repositories with their Notes
        return {'person': person,
                'objs': self.readservice.objs,
                'jscode': jscode,
                'root': root_dict,
                'status': Status.OK}

