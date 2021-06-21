'''
Created on 30.1.2021

@author: jm
'''
import shareds
import logging

logger = logging.getLogger("stkserver")

from pe.dataservice import ConcreteService
from pe.neo4j.cypher.cy_person import CypherPerson
from pe.neo4j.cypher.cy_source import CypherSource
from bl.base import Status

from .util import run_cypher

class PersonRecord:
    ''' Object to return person display data. '''
    def __init__(self):
        self.person_node = None
        self.names = []
        self.events_w_role = []    # tuples (event_node, place_name, role)

    def __str__(self):
        if self.person_node:
            label, = self.person_node.labels
            id_str = f'{label} {self.person_node.id}:{self.person_node["id"]}'
        else:
            id_str = ""
        return f'({id_str}) {len(self.names)} names,{len(self.events_w_role)} events'

class MediaReference:
    ''' Object to return media reference data. '''
    def __init__(self):
        self.node = None
        self.order = None
        self.crop = None

    def __str__(self):
        if self.node:
            label, = self.node.labels
            id_str = f'{label} {self.node.id}:{self.node["id"]}'
        else:
            id_str = ""
        if self.crop:
            crop_str = f'[{self.crop}]'
        else:
            crop_str = ""
        return f'-{crop_str}-> ({id_str})'

class SourceReference:
    ''' Object to return Source and Repository reference data. '''
    def __init__(self):
        self.source_node = None
        self.repository_node = None
        self.medium = ""

    def __str__(self):
        if self.source_node:
            label, = self.source_node.labels
            source_str = f'{label} {self.source_node.id}:{self.source_node["id"]}'
        else:
            source_str = ""
        if self.repository_node:
            label, = self.repository_node.labels
            repo_str = f'{label} {self.repository_node.id}:{self.repository_node["id"]}'
        else:
            repo_str = ""
        return f'{source_str}-{self.medium}->({repo_str})'

class Neo4jReadServiceTx(ConcreteService):
    ''' 
    Methods for accessing Neo4j database.

    Referenced as shareds.dataservices["read_tx"] class.
    
    The DataService class enables use as Context Manager.
    @See: https://www.integralist.co.uk/posts/python-context-managers/
    '''
    def __init__(self, driver=None):
        
        print(f'#~~~~{self.__class__.__name__} init')
        self.driver = driver if driver else shareds.driver


    def tx_get_person_list(self, args):
        """ Read Person data from given fw_from.
        
            args = dict {use_user, fw, limit, rule, key, years}
        """
        material = shareds.dservice.material
        state = shareds.dservice.state
        username = args.get('use_user')
        rule = args.get('rule')
        key = args.get('key')
        fw_from = args.get('fw','')
        years= args.get('years',[-9999,9999])
        limit = args.get('limit', 100)
        restart = (rule == 'start')

        # Select cypher clause by arguments

        #if not username: username = ""

        if restart:
            # Show search form only
            return {'items': [], 'status': Status.NOT_STARTED }
        elif args.get('pg') == 'all':
            # Show persons, no search form
            cypher = CypherPerson.get_person_list
            print(f"tx_get_person_list: Show '{state}' '{material}' @{username} fw={fw_from}")
        elif rule in ['surname', 'firstname', 'patronyme']:
            # Search persons matching <rule> field to <key> value
            cypher = CypherPerson.read_persons_w_events_by_refname
            print(f"tx_get_person_list: Show '{state}' '{material}' data @{username}, {rule} ~ \"{key}*\"")
        elif rule == 'years':
            # Search persons matching <years>
            cypher = CypherPerson.read_persons_w_events_by_years
            print(f"tx_get_person_list: Show '{state}' '{material}', years {years}")
            # if show_approved:
            #     print(f'tx_get_person_list: Show approved common data years {years}')
            #     result = self.tx.run(CypherPerson.get_common_events_by_years,
            #                          years=years)
            # else:
            #     print(f'tx_get_person_list: Show candidate data  years {years}')
            #     result = self.tx.run(CypherPerson.get_my_events_by_years,
            #                          years=years, user=user)
        elif rule == 'ref':
            #TODO: Search persons where a reference name = <key> value
            return {'items': [], 'status': Status.ERROR,
                    'statustext': f'tx_get_person_list: TODO: Show approved common data {rule}={key}'}
            #return session.run(Cypher_person.get_events_by_refname, name=key)
            # if show_approved:
            #     print(f'tx_get_person_list: TODO: Show approved common data {rule}={key}')
            #     #return session.run(Cypher_person.get_events_by_refname, name=key)
            # else:
            #     print(f'tx_get_person_list: TODO: Show candidate data {rule}={key}')
            #     #return session.run(Cypher_person.get_events_by_refname, name=key)
        else:
            return {'items': [], 'status': Status.ERROR,
                    'statustext': 'tx_get_person_list: Invalid rule'}
 
        persons = []
        logger.debug(f"tx_get_person_list: cypher: {cypher}")
        result = run_cypher(self.tx, cypher, username,
                            #material=material, state=state,
                            use=rule, name=key,
                            years=years,
                            start_name=fw_from, 
                            limit=limit)            # result: person, names, events
        for record in result:
            #  <Record 
            #     person=<Node id=163281 labels={'Person'} 
            #       properties={'sortname': 'Ahonius##Knut Hjalmar',  
            #         'sex': '1', 'confidence': '', 'change': 1540719036, 
            #         'handle': '_e04abcd5677326e0e132c9c8ad8', 'id': 'I1543', 
            #         'priv': 1,'datetype': 19, 'date2': 1910808, 'date1': 1910808}> 
            #     names=[<Node id=163282 labels={'Name'} 
            #       properties={'firstname': 'Knut Hjalmar', 'type': 'Birth Name', 
            #         'suffix': '', 'surname': 'Ahonius', 'order': 0}>] 
            #     events=[
            #        <Node id=18571 labels=frozenset({'Event'})
            #           properties={'datetype': 0, 'change': 1585409703, 'description': '', 
            #             'id': 'E5393', 'date2': 1839427, 'date1': 1839427, 'type': 'Birth',
            #             'uuid': 'f461f3b634dd488cbc47d9a6978d5247'}>, 
            #        'Voipala',
            #        'Primary']
            #  >
            p = PersonRecord()
            p.person_node = record.get('person')
            p.names = record.get('names')           # list(name_nodes)
            p.events_w_role = record.get('events')  # list of tuples (event_node, place_name, role)
            p.owners = record.get('owners')

            persons.append(p)   

        if len(persons) == 0:
            return {'items': [], 'status': Status.NOT_FOUND,
                    'statustext': f'No persons found by "{args}"'}
        return {'items': persons, 'status': Status.OK}


    def tx_get_person_by_uuid(self, uuid:str, active_user:str):
        ''' Read a person from common data or user's own Batch.

        :param: uuid        str
        :param: active_user str if "": read from approved data
                                else:  read user's candidate data
         '''
        res = {'status':Status.OK}

        # 1. Get Person node by uuid, if that allowed for given user
        #    results: person, root

        try:
            record = run_cypher(self.tx, CypherPerson.get_person, active_user, uuid=uuid).single()
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
                print(f'dx_get_person_by_uuid: person={uuid} not found')
                res.update({'status': Status.NOT_FOUND, 'statustext': 'The person does not exist'})
                return res

            # Store original researcher data 
            #    root = dict {root_type, root_user, id}
            #    - root_type    which kind of owner link points to this object (PASSED / OWNER)
            #    - root_user    the (original) owner of this object
            #    - bid          Batch id
            root_node = record['root']
            root_type = root_node.get('material', "")
            root_user = root_node.get('user', "")
            original_user = root_node.get('original_user', "")
            bid = root_node.get('id', "")

            person_node = record['p']
            puid = person_node.id
            res['person_node'] = person_node
            res['root'] = {'root_type':root_type, 'root_user': root_user, 'original_user': original_user, 'batch_id':bid}

#                 # Add to list of all objects connected to this person
#                 self.objs[person.uniq_id] = person

        except Exception as e:
            msg = f'person={uuid} {e.__class__.__name__} {e}'
            print(f'dx_get_person_by_uuid: {msg}')
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
                #print(f"#+ 2  ({puid}) -[:{person_rel} {role}]-> ({node.id}:{label})")

                res['name_nodes'] = name_nodes
                res['event_node_roles'] = event_node_roles
                res['cause_of_death'] = cause_of_death

        except Exception as e:
            msg = f'person={puid} {e.__class__.__name__} {e}'
            print(f'dx_get_person_names_events: {msg}')
            res.update({'status': Status.ERROR, 'statustext': f"Could not read names and events: {msg}"})
            return res

        return res

    def tx_get_person_families(self, puid:int):
        ''' Read the families, where given Person is a member.
            Returns
            - the Families, where this person is a parent or child
            - the Family members with their birth event
            - the family events from families, where this person is a parent
            (p:Person) <-- (f:Family)
               for f
                 (f) --> (fp:Person) -[*1]-> (fpn:Name)
                 (f) --> (fe:Event)
        '''
        # 3. Read the families, where given Person is a member
        #    orig. dr_get_person_families(self, puid:int)

        #             (p:Person) <-- (f:Family)
        #                for f
        #                  (f) --> (fp:Person) -[*1]-> (fpn:Name)
        #                  (f) --> (fe:Event)
        #  Results
        #    - family_sets   list of dict {family, family_events, member_sets}
        #      - family_events = list of dict (node, relation_type, marriage_date)
        #        - the family events from families, where this person is a parent
        #      - member_sets   = list of dict {member_node, name_node, parental_role, birth_node}
        #        - the Family members with their birth event

        res = {'status':Status.OK}
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
                        #print(f"#+3.2 ({puid}) -[:EVENT {event_role}]-> (:Event {event_node.id} {eid})")
                        family_events.append(event_node)

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
                #print(f"#+3.4 ({puid}) -[:{family_rel} {family_role}]-> (:Family {family_node.id} {family_node.get('id')})")
                families.append(family)

        except Exception as e:
            msg = f'person={puid} {e}' #{e.__class__.name} {e}'
            print(f'dx_get_person_families: {msg}')
            res.update({'status': Status.ERROR, 'statustext': f"Could not read families: {msg}"})
            return res

        res['families'] = families
        return res


    def tx_get_object_places(self, base_objs:dict):
        ''' Read Place hierarchies for given Event objects.
        
        :param:    base_objs    {uniq_id: bl.base.NodeObject}, updated!
        '''
        # Place references: {src: (place_node, [name_node, ...])}
        # - src                 Event (or Place) uniq_id
        # - place_node          connected place node
        # - [name_node, ...]    name nodes for this place
        references = {}

        try:
            uids = list(base_objs.keys())
            results = self.tx.run(CypherPerson.get_event_places, uid_list=uids)
            for record in results:
                # Returns 
                #    - label    'Event'
                #    - uniq_id  db id of current Event
                #    - pl       Place node
                #    - [pn]     its Place_name objects
                #    - pi       surrounding Place node
                #    - [pi]     its Place_name objects

                event_uniq_id = record['uniq_id']

                # Place node and names linked to this event
                place_node = record['pl']
                place_uniq_id = place_node.id
                pn_nodes = record['pnames']
                references[event_uniq_id] = (place_node, pn_nodes)

                # Upper Place node and names linked to this Place
                upper_place_node = record['pi']
                if upper_place_node:
                    pn_nodes = record['pinames']
                    references[place_uniq_id] = (upper_place_node, pn_nodes)
                pass
 
        except Exception as e:
            print(f"Could not read places for {len(base_objs)} objects: {e.__class__.__name__} {e}")
            return {'status': Status.ERROR, 'statustext':f'{e.__class__.__name__}: {e}'}

        #print(f'#+tx_get_object_places: Got {len(references)} place references') 
        return {'status': Status.OK, 'place_references': references}

    def tx_get_object_citation_note_media(self, obj_catalog:dict, active_objs=[]):
        ''' 
        Read Citations, Notes, Medias for list of active objects.
 
        :param:    obj_catalog    {uniq_id: NodeObject}, by uniq_id, updated!
        :param:    active_objs    The src uniq_ids to check for targets

                (src) -[r:CITATION|NOTE|MEDIA]-> (target)
 
        First (when active_objs is empty) searches all Notes, Medias and
        Citations of person or it's connected objects.
             
        Returns {status, new_objects, references}
        - references    Object by source with target_label, target_node, order
                        and crop fields
        - new_objects   list of created all new uniq_ids, where this search
                        should be repeated
        '''
        
        # Collections {src_id: [target_nodes]) - the object referred from each src node
        coll = {}
        # These new objects may have more Citations, Notes or Medias 
        new_obj_ids = []

        try:
            if active_objs and active_objs[0] > 0:
                # Search next level destinations (src) -[r:CITATION|NOTE|MEDIA]-> (target)
                uids = active_objs
            else:
                # Search all (src) -[r:CITATION|NOTE|MEDIA]-> (target)
                uids = list(obj_catalog.keys())
            #print(f'# Searching Citations, Notes, Medias for {len(uids)} nodes')

            results = self.tx.run(CypherPerson.get_objs_citations_notes_medias,
                                  uid_list=uids)
            for record in results:
                # Returns 
                #    - src      source node
                #    - r        relation: CITATION|NOTE|MEDIA
                #    - target   target object Citation|Note|Media

                # Create a reference to target object including node, order and crop
                ref = MediaReference()

                # The existing object src
                src_node = record['src']
                src_uniq_id = src_node.id
                src_label, = src_node.labels
                #src = obj_catalog[record['uniq_id']]

                # Target is a Citation, Note or Media
                target_node = record['target']
                target_uniq_id = target_node.id
                target_label, = target_node.labels
                ref.node = target_node

                # Relation r between (src_node) --> (target)
                rel = record['r']
                ref.order = rel.get('order')
                if target_label == "Media":
                    # Media crop attributes used in this relation
                    left = rel.get('left')
                    if left != None:
                        upper = rel.get('upper')
                        right = rel.get('right')
                        lower = rel.get('lower')
                        ref.crop = (left, upper, right, lower)
                #print(f'# Cita/Note/Media: ({src_uniq_id}:{src_label} {src_node["id"]}) {ref}')

                # Add current target reference to objects referred 
                # from this src object 
                ref_list = coll.get(src_uniq_id, None)
                if ref_list:
                    # There are already targets referred from src_node
                    if not ref in ref_list:
                        coll[src_uniq_id].append(ref)
                else:
                    coll[src_uniq_id] = [ref]

                if not ( target_uniq_id in new_obj_ids or \
                         target_uniq_id in active_objs):
                    new_obj_ids.append(target_uniq_id)

        except Exception as e:
            msg = f"Could not read 'Citations, Notes, Medias': {e.__class__.__name__} {e}"
            print(f"dx_get_object_citation_note_media: {msg}")
            return {'status': Status.ERROR, 'statustext': msg}

        return {'status': Status.OK,
                'new_objects': new_obj_ids, 
                'references': coll}

    def tx_get_object_sources_repositories(self, citation_uids:list):
        ''' Get Sources and Repositories udes by listed objects
        
            Read Source -> Repository hierarchies for given list of citations
                            
            - session       neo4j.session   for database access
            - citations[]   list int        list of citation.uniq_ids
            - objs{}        dict            objs[uniq_id] = NodeObject
            
            * The Citations mentioned must be in objs dictionary
            * On return, the new Sources and Repositories found are added to objs{} 
            
            --> Origin from models.obsolete_source_citation_reader.read_sources_repositories
        '''
        if len(citation_uids) == 0:
            return {'status':Status.NOT_FOUND}
        references = {} # {Citation.unid_id: SourceReference}

        with self.driver.session(default_access_mode='READ') as session:
            results = session.run(CypherSource.get_citation_sources_repositories, 
                                  uid_list=citation_uids)
            for record in results:
                # <Record 
                #    uniq_id=392761 
                #    source=<Node id=397146 labels={'Source'} 
                #        properties={'id': 'S1723', 'stitle': 'Hauhon seurakunnan rippikirja 1757-1764', 
                #            'uuid': 'f704b8b90c0640efbade4332e126a294', 'spubinfo': '', 'sauthor': '', 'change': 1563727817}>
                #    rel={'medium': 'Book'}
                #    repo=<Node id=316903 labels={'Repository'}
                #        properties={'id': 'R0157', 'rname': 'Hauhon seurakunnan arkisto', 'type': 'Archive', 
                #            'uuid': '7ac1615894ea4457ba634c644e8921d6', 'change': 1563727817}>
                # >
                ref = SourceReference()

                # 1. Citation
                uniq_id = record['uniq_id']

                # 2. The Source node
                ref.source_node = record['source']
                ref.repository_node = record['repo']
                if ref.repository_node:
                    ref.medium = record['rel'].get('medium', "")
                references[uniq_id] = ref

        return {'status': Status.OK, 'sources': references}
