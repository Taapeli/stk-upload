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

    def _get_daterange(self, node):
        ''' Exctract DateRange as dictionary from Node object
        '''
        datetype = node.get('datetype')
        if datetype:
            return {'datetype':datetype, 
                    'date1': node.get('date1'), 
                    'date2': node.get('date2') }
        return {}


    def tx_get_person_by_uuid(self, uuid:str, active_user:str):
        ''' Read a person from common data or user's own Batch.

        :param: uuid        str
        :param: active_user str if "": read from approved data
                                else:  read user's candidate data
         '''
        res = {}
        with self.driver.session(default_access_mode='READ') as session:

            # 1. Get Person node by uuid, if that allowd for given user
            #    results: person, root

            try:
                record = session.run(CypherPerson.get_person, uuid=uuid).single()
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
                results = session.run(CypherPerson.get_names_events, uid=puid)
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
                results = session.run(CypherPerson.get_families, uid=puid)
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

                        member_set = {'member_node': member_node, 
                                      'name_node':name_node, 
                                      'parental_role':parental_role, 
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
