'''
Created on 30.1.2021

@author: jm
'''

from pe.neo4j.cypher.cy_person import CypherPerson
from bl.base import Status


class Neo4jReadServiceTx:
    ''' Methods for accessing Neo4j database.
    '''
    def __init__(self, driver):
        self.driver = driver
        self.tx = driver.session().begin_transaction()


    def tx_get_person_by_uuid(self, uuid:str, active_user:str):
        ''' Read a person from common data or user's own Batch.

        :param: uuid        str
        :param: active_user str if "": read from approved data
                                else:  read user's candidate data
         '''
        res = {}

        # 1. Get Person node by uuid, if that allowd for given user
        #    results: person, root

        try:
            record = self.tx.run(CypherPerson.get_person, uuid=uuid).single()
            # <Record 
            #    p=<Node id=25651 labels=frozenset({'Person'})
            #        properties={'sortname': 'Zakrevski#Arseni#Andreevits', 'death_high': 1865,
            #            'sex': 1, 'confidence': '', 'change': 1585409698, 'birth_low': 1783,
            #            'birth_high': 1783, 'id': 'I1135', 'uuid': 'dc6a05ca6b2249bfbdd9708c2ee6ef2b',
            #            'death_low': 1865}>
            #    root_type='PASSED'
            #    root=<Node id=31100 labels=frozenset({'Audit'})
            #        properties={'auditor': 'juha', 'id': '2020-07-28.001', 'user': 'juha',
            #            'timestamp': 1596463360673}>
            # >
            if record is None:
                print(f'dr_get_person_by_uuid: person={uuid} not found')
                res.update({'status': Status.NOT_FOUND, 'statustext': 'The person does not exist'})
                return res

            # Store original researcher data 
            #    root = dict {root_type, root_user, id}
            #    - root_type    which kind of owner link points to this object (PASSED / OWNER)
            #    - root_user    the (original) owner of this object
            #    - bid          Batch id
            root_type = record['root_type'] # OWNS / PASSED
            root_node = record['root']
            root_user = root_node.get('user', "")
            bid = root_node.get('id', "")
            if active_user is None:
                if root_type != "PASSED":
                    print(f'dr_get_person_by_uuid: person {uuid} is not in approved material')
                    res.update({'status': Status.NOT_FOUND, 'statustext': 'The person is not accessible'})
                    return res
            elif root_type != "OWNS":
                    print(f'dr_get_person_by_uuid: OWNS not allowed for person {uuid}')
                    res.update({'status': Status.NOT_FOUND, 'statustext': 'The person is not accessible'})
                    return res

            person_node = record['p']
            puid = person_node.id
            res['person_node'] = person_node
            res['root'] = {'root_type':root_type, 'root_user': root_user, 'batch_id':bid}

#                 # Add to list of all objects connected to this person
#                 self.objs[person.uniq_id] = person

        except Exception as e:
            msg = f'person={uuid} {e.__class__.name} {e}'
            print(f'dr_get_person_by_uuid: {msg}')
            res.update({'status': Status.ERROR, 'statustext': msg})
            return res

        # 2. Read person names and events
        #
        #    orig. def dr_get_person_names_events(self, puid:int)
        #    results: status,
        #    - name_nodes        node
        #    - event_node_roles  [node, role:str]
        #    - cause_of_death    event node

        name_nodes = []
        event_node_roles = []
        cause_of_death = None
        try:
            results = self.tx.run(CypherPerson.get_names_events, uid=puid)
            for record in results:
                # <Record
                #    rel_type='NAME'
                #    node=<Node id=21610 labels=frozenset({'Name'})
                #        properties={'firstname': 'Eva', 'surname': 'Sibelius', 'prefix': '', 
                #            'type': 'Birth Name', 'suffix': '', 'title': '', 'order': 0}>
                #    role=None
                # >
                person_rel = record['rel_type']     # NAME / EVENT
                node = record['node']
                role = record['role']               # Event: Primary ...
                label, = node.labels
                if label == 'Name':
                    name_nodes.append(node)
                    #self.objs[x.uniq_id] = x
                elif label == 'Event':
                    event_node_roles.append([node,role])
                    #self.objs[x.uniq_id] = x 
                    if node.get("type") == "Cause Of Death":
                        cause_of_death = node
                print(f"# 2  ({puid}) -[:{person_rel} {role}]-> ({node.id}:{label})")

                res['name_nodes'] = name_nodes
                res['event_node_roles'] = event_node_roles
                res['cause_of_death'] = cause_of_death

        except Exception as e:
            msg = f'person={puid} {e.__class__.__name__} {e}'
            print(f'dr_get_person_names_events: {msg}')
            res.update({'status': Status.ERROR, 'statustext': f"Could not read names and events: {msg}"})
            return res

        # 3. Read the families, where given Person is a member
        #
        #    orig. dr_get_person_families(self, puid:int)
        #
        #             (p:Person) <-- (f:Family)
        #                for f
        #                  (f) --> (fp:Person) -[*1]-> (fpn:Name)
        #                  (f) --> (fe:Event)
        #  Results
        #    - family_sets   list of dict {family, family_events, member_sets}
        #            - family_events = list of dict (node, relation_type, marriage_date)
        #                - the family events from families, where this person is a parent
        #            - member_sets   = list of dict {member_node, name_node, parental_role, birth_node}
        #                - the Family members with their birth event

        families = []
        try:
            results = self.tx.run(CypherPerson.get_families, uid=puid)
            for record in results:
                # <Record
                #  rel_type='CHILD'
                #  role=None  
                #  family=<Node id=432641 labels={'Family'} properties={...}> 
                #  events=[<Node id=269554 labels={'Event'} properties={'type': 'Marriage', ...}> ...]
                #  members=[[
                #    <Relationship ...  type='CHILD' ...>, 
                #    <Node ... labels={'Person'}...>, 
                #    <Node ... labels={'Name'}...>, 
                #    <Node ... labels={'Event'}...]
                #    ...]>

                # 3.1. What is the relation this Person to their Family

                family_rel = record['rel_type']     # CHILD / PARENT
                family_role = record['role']        # Member role as: father / mother / None (child)
                family_node = record['family']
                family_events = []                  # (node, relation_type, marriage_date)
                relation_type = None                # Marriage, other

                # 3.2. Family Events

                for event_node in record['events']:
#                         f_event = EventBl.from_node(event_node)
                    eid = event_node.get('id')
                    relation_type = event_node.get('type')
                    # Add family events to person events, too
                    if family_rel == "PARENT":
                        event_role = "Family"
                        print(f"#3.2 ({puid}) -[:EVENT {event_role}]-> (:Event {event_node.id} {eid})")
                        family_events.append(event_node)
#                             # Add Event to list of those events, who's Citation etc
#                             # references must be checked
#                             if not eid in self.objs.keys():
#                                 self.objs[eid] = event_node

                # 3.3. Family members and their birth events

                family_members = []
                for parental_role, member_node, name_node, event_node in record['members']:
                    # parental_role = 'father'
                    # member_node = <Node id=428883 labels={'Person'} properties={'sortname': 'Järnefelt##Caspar Woldemar', ... }>
                    # name_node = <Node id=428884 labels={'Name'} properties={'firstname': 'Caspar Woldemar' ...}>
                    # event_node = <Node id=267935 labels={'Event'} properties={'type': 'Birth', ... }>

                    member_set = {'parental_role':parental_role, 
                                  'member_node': member_node, 
                                  'name_node':name_node, 
                                  'birth_node': event_node}
                    family_members.append(member_set)

                # 3.4. The Family node

                family = {'family_rel': family_rel, 
                          'family_role': family_role,
                          'family_node': family_node,
                          'family_events': family_events,
                          'relation_type': relation_type,
                          'family_members': family_members
                          }
                print(f"#3.4 ({puid}) -[:{family_rel} {family_role}]-> (:Family {family_node.id} {family_node.get('id')})")
                families.append(family)

#                 return {'families_as_child':families_as_child,
#                         'families_as_parent': families_as_parent,
#                         'family_events': family_events,
#                         'status': Status.OK}

        except Exception as e:
            msg = f'person={puid} {e}' #{e.__class__.name} {e}'
            print(f'dr_get_person_families: {msg}')
            res.update({'status': Status.ERROR, 'statustext': f"Could not read families: {msg}"})
            return res

        res['families'] = families
        res['status'] = Status.OK
        return res


#     def dr_get_object_places(self, person):
#         ''' Read Place hierarchies for all Event objects in self.objs.
#         '''
#         uids = list(self.objs.keys())
# #         with self.driver.session(default_access_mode='READ') as session:
#         try:
#             results = self.tx.run(CypherPerson.get_objs_places, uid_list=uids)
#             for record in results:
#                 # <Record 
#                 #    label='Event' 
#                 #    uniq_id=17282 
#                 #    pl=<Node id=8888 labels=frozenset({'Place'}) 
#                 #        properties={'id': 'P1077', 'type': 'Parish', 'uuid': 'bc78df10a5fd47e88e11e6a80b51569d', 
#                 #            'pname': 'Loviisan srk', 'change': 1585562874}> 
#                 #    pnames=[
#                 #        <Node id=8889 labels=frozenset({'Place_name'}) 
#                 #            properties={'name': 'Loviisan srk', 'lang': ''}>]
#                 #    pi=<Node id=6889 labels=frozenset({'Place'}) 
#                 #        properties={'id': 'P1874', 'type': 'Organisaatio', 'uuid': 'de140aac2c8f4884a3a2422faea9a569', 
#                 #        'pname': 'Suomen ev.lut. kirkko', 'change': 1600105542}>
#                 #    pinames=[
#                 #        <Node id=10654 labels=frozenset({'Place_name'}) 
#                 #            properties={'name': 'Suomen ev.lut. kirkko', 'lang': ''}>, 
#                 #        <Node id=10655 labels=frozenset({'Place_name'}) 
#                 #            properties={'name': 'Evangelisk-lutherska kyrkan i Finland', 'lang': 'sv'}>]
#                 # >
#                 src_label = record['label']
#                 if src_label != "Event":
#                     raise TypeError(f'dr_get_object_places: An Event excepted, got {src_label}')
#                 src_uniq_id = record['uniq_id']
# 
#                 # Use the Event from Person events
#                 src = None
#                 for e in person.events:
#                     if e.uniq_id == src_uniq_id:
#                         src = e
#                         break
#                 if not src:
#                     raise LookupError(f"dr_get_object_places: Unknown Event {src_uniq_id}!?")
# 
#                 pl = PlaceBl.from_node(record['pl'])
#                 if not pl.uniq_id in self.objs.keys():
#                     # A new place
#                     self.objs[pl.uniq_id] = pl
#                     #print(f"# new place (x:{src_label} {src.uniq_id} {src}) --> (pl:Place {pl.uniq_id} type:{pl.type})")
#                     pl.names = place_names_from_nodes(record['pnames'])
#                     
#                 #else:
#                 #   print(f"# A known place (x:{src_label} {src.uniq_id} {src}) --> ({list(record['pl'].labels)[0]} {objs[pl.uniq_id]})")
#                 src.place_ref.append(pl.uniq_id)
# 
#                 # Surrounding places
#                 if record['pi']:
#                     pl_in = PlaceBl.from_node(record['pi'])
#                     ##print(f"# Hierarchy ({pl}) -[:IS_INSIDE]-> (pi:Place {pl_in})")
#                     if pl_in.uniq_id in self.objs:
#                         pl.uppers.append(self.objs[pl_in.uniq_id])
#                         ##print(f"# - Using a known place {objs[pl_in.uniq_id]}")
#                     else:
#                         pl.uppers.append(pl_in)
#                         self.objs[pl_in.uniq_id] = pl_in
#                         pl_in.names = place_names_from_nodes(record['pinames'])
#                         #print(f"#  ({pl_in} names {pl_in.names})")
#                 pass
# 
#         except Exception as e:
#             print(f"Could not read places for person {person.id} objects {self.objs}: {e}")
#             return {'status': Status.ERROR, 'statustext':f'{e.__class__.__name__}: {e}'}
# 
#         return {'status': Status.OK}
# 
# 
#     def tx_get_object_citation_note_media(self, person, active_objs=[]):
#         ''' Read Citations, Notes, Medias for list of objects.
# 
#                 (x) -[r:CITATION|NOTE|MEDIA]-> (y)
# 
#             First (when active_objs is empty) searches all Notes, Medias and
#             Citations of person or it's connected objects.
#             
#             Returns a list of created new objects, where this search should
#             be repeated.
#         '''
#         new_objs = []
# 
# #         with self.driver.session(default_access_mode='READ') as session:
#         try:
#             if active_objs and active_objs[0] > 0:
#                 # Search next level destinations x) -[r:CITATION|NOTE|MEDIA]-> (y)
#                 uids = active_objs
#             else:
#                 # Search all (x) -[r:CITATION|NOTE|MEDIA]-> (y)
#                 uids = list(self.objs.keys())
#             print(f'# Searching Citations, Notes, Medias for {len(uids)} nodes')
#             #print(f'# uniq_ids = {uids}')
# 
#             results = self.tx.run(CypherPerson.get_objs_citation_note_media,
#                                   uid_list=uids)
#             for record in results:
#                 # <Record
#                 #    label='Person'
#                 #    uniq_id=327766
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
#                 #                'url': 'https://nakoislehti.hs.fi/e7df520d-d47d-497d-a8a0-a6eb3c00d0b5/4', 'change': 0}>
#                 # >
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
#                     o = self.objs.get(y_uniq_id)
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
#                         x.note_ref = [o.uniq_id]
#                         print('NOTE Neo4jReadService.dr_get_object_citation_note_media: '
#                               f'Field {x_label}.{y_label.lower()}_ref created')            
# 
#                 elif y_label == "Media":
#                     o = self.objs.get(y_uniq_id, None)
#                     if not o:
#                         o = MediaBl.from_node(y_node)
#                         self.objs[o.uniq_id] = o
#                         new_objs.append(o.uniq_id)
#                     # Get relation properties
#                     order = rel.get('order')
# 
#                     # Media reference crop attributes
#                     left = rel.get('left')
#                     if left != None:
#                         upper = rel.get('upper')
#                         right = rel.get('right')
#                         lower = rel.get('lower')
#                         crop = (left, upper, right, lower)
#                     else:
#                         crop = None
#                     # Store reference to referee object
#                     if hasattr(x, 'media_ref'):
#                         x.media_ref.append((o.uniq_id, crop, order))
#                     else:
#                         x.media_ref = [(o.uniq_id, crop, order)]
#                         print('NOTE Neo4jReadService.dr_get_object_citation_note_media: '
#                               f'Field {x_label}.{y_label.lower()}_ref created')            
#                     print(f'#\tMedia ref {o.uniq_id} order={order}, crop={crop}')
#                     if len(x.media_ref) > 1 and x.media_ref[-2][2] > x.media_ref[-1][2]:
#                         x.media_ref.sort(key=lambda x: x[2])
#                         print("#\tMedia sort done")
#                     #print(f'# ({x_label}:{x.uniq_id} {x}) --> ({y_label}:{o.id})')
# 
#                 else:
#                     raise NotImplementedError(f'dr_get_object_citation_note_media: No rule for ({x_label}) --> ({y_label})')            
#                 #print(f'# ({x_label}:{x}) --> ({y_label}:{o.id})')
# 
#         except Exception as e:
#             print(f"dr_get_object_citation_note_media: Could not read 'Citations, Notes, Medias': {e}")
#             print(f"... for Person {person.uuid} objects {self.objs}: {e}")
#         return new_objs

