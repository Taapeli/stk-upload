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
from bl.place import PlaceBl #, PlaceName
from bl.media import Media
from models.gen.note import Note
#TODO from bl.note import Note
from models.gen.citation import Citation
#TODO from bl.citation import Citation
# Pick a PlaceName by user language
from ui.place import place_names_from_nodes

import logging 
logger = logging.getLogger('stkserver')
from flask_babelex import _

#from models.source_citation_reader import get_citations_js


class PersonReaderTx(DbReader):
    '''
        Data reading class for Person objects with associated data.

        - Uses pe.db_reader.DbReader.__init__(self, readservice, u_context) 
          to define the database driver and user context

        - Returns a Result object.
    '''
    def __init__(self, readservice, u_context=None):
        DbReader.__init__(self, readservice, u_context)
        self.obj_catalog = {}          # {uniq_id: Connected_object}

    def _catalog(self, obj):
        ''' Collect list of objects connects to active node. '''
        if not obj is None:
            self.obj_catalog[obj.uniq_id] = obj


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

        res = self.readservice.tx_get_person_by_uuid(uuid, active_user=self.use_user)
        if Status.has_failed(res):
            # Not found, not allowd (person.too_new) or error
            if res.get('status') == Status.NOT_FOUND:
                return {'status':Status.NOT_FOUND, 
                        'statustext': _('Requested person not found')}
            return res

        # Got dictionary: Status and following objects:
        #     - person_node, root, name_nodes, event_node_roles, cause_of_death, families
        #     - - root = {root_type, root,user, batch_id}
        #     - - event_node_roles = [[Event node, role], ...]
        #     - - cause_of_death = Event node
        #     - - families = [{family_rel, family_role, family_node, 
        #                      family_events, relation_type, family_members}, ...]
        #     - - - family_events = [event_node]
        #     - - - family_members = [{member_node, name_node, parental_role, birth_node}, ...]
        #     - - - marriage_date = {datetype, date1, date2}


        # 1-2. Person, names and events

        person = PersonBl.from_node(res.get('person_node'))
        person.families_as_parent = []
        person.families_as_child = []
        person.citation_ref = []
        person.note_ref = []
        person.media_ref = []
        self._catalog(person)

        # Info about linked Batch or Audit node
        root_dict = res.get('root')   # {root_type, root_user, batch_id}
        for name_node in res.get('name_nodes'):
            name = Name.from_node(name_node)
            person.names.append(name)
            self._catalog(name)
        for event_node, event_role in res.get('event_node_roles'):
            event = EventBl.from_node(event_node)
            event.role = event_role
            person.events.append(event)
            self._catalog(event)
        obj = res.get('cause_of_death')
        if obj:
            person.cause_of_death = EventBl.from_node(obj)
            self._catalog(obj)

        # 3. Person's families as child or parent

        res = self.readservice.tx_get_person_families(person.uniq_id)
        if Status.has_failed(res):
            print('#bl.person_reader.PersonReaderTx.get_person_data - Can not read families:'\
                  f' {res.get("statustext")}')
            return res

        for f in res.get('families'):
            family = FamilyBl.from_node(f['family_node'])
            family_role = f['family_role']          # Main person's role in family
            self._catalog(family)
            for event_node in f['family_events']:
                event = EventBl.from_node(event_node)
                if event.type == "Marriage":
                    family.marriage_dates = event.dates
                family.events.append(event)
                self._catalog(event)
            for m in f['family_members']:
                # Family member
                member = PersonBl.from_node(m['member_node'])
                self._catalog(member)
                name_node = m['name_node']
                if name_node:
                    name = Name.from_node(name_node)
                    member.names.append(name)
                    self._catalog(name)
                event_node = m['birth_node']
                if event_node:
                    event = EventBl.from_node(event_node)
                    member.birth_date = event.dates
                    #self._catalog(event)
                # Add member to family
                parental_role = m['parental_role']  # Family member's role
                if parental_role == "father":
                    family.father = member
                elif parental_role == "mother":
                    family.mother = member
                else:       # children
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

        # 4. Places for person and each event

        res = self.readservice.tx_get_object_places(self.obj_catalog)
        # returns {status, place_references}
        place_references = res.get('place_references', {})
        # Got dictionary {object_id,  (place_node, (name_nodes))

        for e in person.events:
            #src = e.uniq_id
            if e.uniq_id in place_references.keys():
                place_node, name_nodes = place_references[e.uniq_id]
                if place_node:
                    # Place and name
                    place = PlaceBl.from_node(place_node)
                    place.names = place_names_from_nodes(name_nodes)
                    e.place_ref = [place.uniq_id]
                    self._catalog(place)
                    # Upper Place?
                    if place.uniq_id in place_references.keys():
                        up_place_node, up_name_nodes = place_references[place.uniq_id]
                        if up_place_node:
                            # Surrounding Place and name
                            up_place = PlaceBl.from_node(up_place_node)
                            up_place.names = place_names_from_nodes(up_name_nodes)
                            place.uppers = [up_place]


        # 5. Citations, Notes, Medias

        new_ids = [-1]
        while len(new_ids) > 0:
            # New objects
            citations = {}
            notes = {}
            medias = {}

            res = self.readservice.tx_get_object_citation_note_media(self.obj_catalog, new_ids)
            # returns {status, new_objects, references}
            # - new_objects    the objects, for which a new search shold be done
            # - references     {source id: [ReferenceObj(node, order, crop)]}
            if Status.has_failed(res): return res
            new_ids = res.get('new_objects', [])
            references = res.get('references')

            for src_id, source in self.obj_catalog.items():
                refs = references.get(src_id)
                if refs:
                    for current in refs:
                        node = current.node
                        order = current.order
                        crop = current.crop
                        label, = node.labels
                        #print (f'Link ({source.__class__.__name__} {src_id}:{source.id}) {current}')

                        target_obj = None
                        if label == "Citation":
                            # If id is in the dictionary, return its value.
                            # If not, insert id with a value of 2nd argument.
                            target_obj = citations.setdefault(node.id, Citation.from_node(node))
                            if hasattr(source, 'citation_ref'):
                                source.citation_ref.append(node.id)
                            else:
                                source.citation_ref = [node.id]
                        elif label == "Note":
                            target_obj = notes.setdefault(node.id, Note.from_node(node))
                            if hasattr(source, 'note_ref'):
                                source.note_ref.append(node.id)
                            else:
                                source.note_ref = [node.id]
                            target_obj.citation_ref = []
                        elif label == "Media":
                            target_obj = medias.setdefault(node.id, Media.from_node(node))
                            if hasattr(source, 'media_ref'):
                                source.media_ref.append((node.id, crop, order))
                            else:
                                source.media_ref = [(node.id, crop, order)]
                            target_obj.citation_ref = []
                        else:
                            raise NotImplementedError("Citation, Note or Media excepted, got {label}")

#             print(f'# - found {len(citations)} Citatons, {len(notes)} Notes, {len(medias)} Medias')
            self.obj_catalog.update(citations)
            self.obj_catalog.update(notes)
            self.obj_catalog.update(medias)

#         # Calculate the average confidence of the sources
#         if len(citations) > 0:
#             summa = 0
#             for cita in citations.values():
#                 summa += int(cita.confidence)
#                  
#             aver = summa / len(citations)
#             person.confidence = "%0.1f" % aver # string with one decimal

#         # 6. Read Sources s and Repositories r for all Citations
#         #    for c in z:Citation
#         #        (c) --> (s:Source) --> (r:Repository)
#         self.readservice.dr_get_object_sources_repositories()


#         # Create Javascript code to create source/citation list
#         jscode = get_citations_js(self.readservice.objs)
        jscode = "/* todo */"
    
        # Return Person with included objects,  and javascript code to create
        # Citations, Sources and Repositories with their Notes
        return {'person': person,
                'objs': self.obj_catalog,
                'jscode': jscode,
                'root': root_dict,
                'status': Status.OK}

