'''
Created on 24.10.2019

@author: jm
'''
import traceback
import shareds
#from flask_babelex import _
from bl.place import PlaceBl
from ui.place import place_names_from_nodes

from .gen.person_combo import Person_combo
from .gen.person_name import Name
from .gen.event_combo import Event_combo
from .gen.family_combo import Family_combo
#from .gen.place_combo import Place_combo
from .gen.note import Note
from .gen.media import Media
from .gen.citation import Citation
#from .gen.source import Source
#from .gen.repository import Repository
from .gen.cypher import Cypher_person


class PersonReader():
    '''
    Person reader is used for reading Person and all essential other nodes.

            Version 3 / 25.10.2019 / JMä
    '''


    def __init__(self, use_common):
        ''' Creates a Person from db node and essential connected nodes.

            if use_common = True, read from approved common data
            else from user's own batch
        '''
        self.session = shareds.driver.session()
        self.use_common = use_common

        # Person node with Names and Events included
        self.person = None
        # Referenced nodes, not directly saved in self.person
        self.objs = {}
        # Citations found
        self.citations = {}
        # Counters by Sources and Repositories source_citations[source_id][citation_id]
        self.source_citations = {}


    def get_person(self, uuid, owner):
        ''' Read Person p, if not denied.
 
            The Person must belong to user's Batch, if not using common data.
       '''
        self.person = Person_combo.get_my_person(self.session, uuid, owner, self.use_common)
        if not isinstance(self.person, Person_combo):
            traceback.print_exc()
            raise PermissionError(f"Person {uuid} is not available, got {self.person}")

        self.objs[self.person.uniq_id] = self.person


#     def read_person_names_events(self): # --> pe.neo4j.readservice.Neo4jReadService.dr_get_person_names_events()
#         ''' Read names and events to Person object p. '''

#     def read_person_families(self): # --> pe.neo4j.readservice.Neo4jReadService.dr_get_person_families
#         ''' Read the families, where this Person is a member. '''

#     def read_object_places(self): # --> pe.neo4j.readservice.Neo4jReadService.dr_get_object_places
#         ''' Read Place hierarchies for all objects in objs. '''

#     def read_object_citation_note_media(self, active_objs=[]):
#         ''' Read Citations, Notes, Medias for list of objects.
# 
#                 (x) -[r:CITATION|NOTE|MEDIA]-> (y)
# 
#             Returns a list of created new objects, where this search should
#             be repeated.
#         '''
#         new_objs = []
# 
#         try:
#             if active_objs and active_objs[0] > 0:
#                 # Search next level destinations x) -[r:CITATION|NOTE|MEDIA]-> (y)
#                 uids = active_objs
#             else:
#                 # Search all (x) -[r:CITATION|NOTE|MEDIA]-> (y)
#                 uids = list(self.objs.keys())
#             print(f'# --- Search Citations, Notes, Medias for {uids}')
# 
#             results = self.session.run(Cypher_person.get_citation_note_media,
#                                        uid_list=uids)
#             for record in results:
#                 # <Record label='Person' uniq_id=327766
#                 #    r=<Relationship id=426799
#                 #        nodes=(
#                 #            <Node id=327766 labels=set() properties={}>, 
#                 #            <Node id=327770 labels={'Note'}
#                 #                properties={'text': 'Nekrologi HS 4.7.1922 s. 4', 
#                 #                    'id': 'N2-I0033', 'type': 'Web Search', 'uuid': '14a26a62a6b446339b971c7a54941ed4', 
#                 #                    'url': 'https://nakoislehti.hs.fi/e7df520d-d47d-497d-a8a0-a6eb3c00d0b5/4', 'change': 0}>
#                 #        ) 
#                 #        type='NOTE' properties={}>
#                 #    y=<Node id=327770 labels={'Note'}
#                 #            properties={'text': 'Nekrologi HS 4.7.1922 s. 4', 'id': 'N2-I0033', 
#                 #                'type': 'Web Search', 'uuid': '14a26a62a6b446339b971c7a54941ed4', 
#                 #                'url': 'https://nakoislehti.hs.fi/e7df520d-d47d-497d-a8a0-a6eb3c00d0b5/4', 'change': 0}
#                 # >    >
# 
#                 # The existing object x
#                 x_label = record['label']
#                 x = self.objs[record['uniq_id']]
# 
#                 # Relation r between (x) --> (y)
#                 rel = record['r']
#                 #rel_type = rel.type
#                 #rel_properties = 
# 
#                 # Target y is a Citation, Note or Media
#                 y_node = record['y']    # 
#                 y_label = list(y_node.labels)[0]
#                 y_uniq_id = y_node.id
#                 #print(f'# Linking ({x.uniq_id}:{x_label} {x}) --> ({y_uniq_id}:{y_label})')
#                 #for k, v in rel._properties.items(): print(f"#\trel.{k}: {v}")
#                 if y_label == "Citation":
#                     o = self.objs.get(y_uniq_id, None)
#                     if not o:
#                         o = Citation.from_node(y_node)
#                         if not x.uniq_id in o.citators:
#                             # This citation is referenced by x
#                             o.citators.append(x.uniq_id)
#                         # The list of Citations, for further reference search
#                         self.citations[o.uniq_id] = o
#                         self.objs[o.uniq_id] = o
#                         new_objs.append(o.uniq_id)
#                     # Store reference to referee object
#                     if hasattr(x, 'citation_ref'):
#                         x.citation_ref.append(o.uniq_id)
#                     else:
#                         x.citation_ref = [o.uniq_id]
# #                         traceback.print_exc()
# #                         raise LookupError(f'Error: No field for {x_label}.{y_label.lower()}_ref')            
#                     #print(f'# ({x_label}:{x.uniq_id}) --> (Citation:{o.id})')
# 
#                 elif y_label == "Note":
#                     o = self.objs.get(y_uniq_id, None)
#                     if not o:
#                         o = Note.from_node(y_node)
#                         self.objs[o.uniq_id] = o
#                         new_objs.append(o.uniq_id)
#                     # Store reference to referee object
#                     if hasattr(x, 'note_ref'):
#                         x.note_ref.append(o.uniq_id)
#                     else:
#                         traceback.print_exc()
#                         raise LookupError(f'Error: No field for {x_label}.{y_label.lower()}_ref')            
# 
#                 elif y_label == "Media":
#                     o = self.objs.get(y_uniq_id, None)
#                     if not o:
#                         o = Media.from_node(y_node)
#                         self.objs[o.uniq_id] = o
#                         new_objs.append(o.uniq_id)
#                     # Get relation properties
#                     order = rel.get('order')
#                     # Store reference to referee object
#                     if hasattr(x, 'media_ref'):
#                         # Add media reference crop attributes
#                         left = rel.get('left')
#                         if left != None:
#                             upper = rel.get('upper')
#                             right = rel.get('right')
#                             lower = rel.get('lower')
#                             crop = (left, upper, right, lower)
#                         else:
#                             crop = None
#                         print(f'#\tMedia ref {o.uniq_id} order={order}, crop={crop}')
#                         x.media_ref.append((o.uniq_id,crop,order))
#                         if len(x.media_ref) > 1 and x.media_ref[-2][2] > x.media_ref[-1][2]:
#                             x.media_ref.sort(key=lambda x: x[2])
#                             print("#\tMedia sort done")
#                     else:
#                         print(f'Error: No field for {x_label}.{y_label.lower()}_ref')            
#                     #print(f'# ({x_label}:{x.uniq_id} {x}) --> ({y_label}:{o.id})')
# 
#                 else:
#                     traceback.print_exc()
#                     raise NotImplementedError(f'No rule for ({x_label}) --> ({y_label})')            
#                 #print(f'# ({x_label}:{x}) --> ({y_label}:{o.id})')
# 
#         except Exception as e:
#             traceback.print_exc()
#             print(f"Could not read 'Citations, Notes, Medias': {e}")
#             print(f"... for Person {self.person.uuid} objects {self.objs}: {e}")
#         return new_objs

    def remove_privacy_limit_from_family(self, family):
        ''' Clear privacy limitations from given family.
        
            Todo: should be in FamilyReader instead
        '''
        if family.father: family.father.too_new = False
        if family.mother: family.mother.too_new = False
        for c in family.children:
            c.too_new = False

#     def remove_privacy_limit_from_families(self): # --> bl.person.PersonBl.remove_privacy_limit_from_families()
#         ''' Clear privacy limitations from self.person's families.
#         '''
#         for family in self.person.families_as_child:
#             self.remove_privacy_limit_from_family(family)
#         for family in self.person.families_as_parent:
#             self.remove_privacy_limit_from_family(family)
            
    
    
    