'''
Created on 30.1.2021

@author: jm
'''
import logging
import traceback

import shareds
#from bl.person_name import Name
from bl.dates import DateRange
from bl.base import Status
from bl.material import Material
from bl.place import PlaceBl, PlaceName

from ui.place import place_names_local_from_nodes

from pe.dataservice import ConcreteService
from pe.neo4j.util import run_cypher
from pe.neo4j.util import run_cypher_batch
from pe.neo4j.nodereaders import Citation_from_node
from pe.neo4j.nodereaders import Comment_from_node
from pe.neo4j.nodereaders import DateRange_from_node
from pe.neo4j.nodereaders import EventBl_from_node
from pe.neo4j.nodereaders import FamilyBl_from_node
from pe.neo4j.nodereaders import MediaBl_from_node
from pe.neo4j.nodereaders import Note_from_node
from pe.neo4j.nodereaders import Name_from_node
from pe.neo4j.nodereaders import PersonBl_from_node
from pe.neo4j.nodereaders import PlaceBl_from_node
from pe.neo4j.nodereaders import PlaceName_from_node
from pe.neo4j.nodereaders import Repository_from_node
from pe.neo4j.nodereaders import SourceBl_from_node
from pe.neo4j.cypher.cy_person import CypherPerson
from pe.neo4j.cypher.cy_place import CypherPlace
from pe.neo4j.cypher.cy_place import CypherPlaceStats
from pe.neo4j.cypher.cy_source import CypherSource

from models.dbtree import DbTree

logger = logging.getLogger("stkserver")

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
        self.source_obj = None
        self.repository_obj = None
        self.medium = ""

    def __str__(self):
        if self.source_obj:
            label = self.source_obj.__class__.__name__
            source_str = f'{label} {self.source_obj.uniq_id}:{self.source_obj.id}'
        else:
            source_str = ""
        if self.repository_obj:
            label = self.repository_obj.__class__.__name__
            repo_str = f'{label} {self.repository_obj.uniq_id}:{self.repository_obj.id}'
        else:
            repo_str = ""
        return f'({source_str}) -[{self.medium}]-> ({repo_str})'



class Neo4jReadServiceTx(ConcreteService):
    ''' 
    Methods for accessing Neo4j database.

    Referenced as shareds.dataservices["read_tx"] class.
    
    The DataService class enables use as Context Manager.
    @See: https://www.integralist.co.uk/posts/python-context-managers/
    '''
    def __init__(self, driver=None):
        
        logger.debug(f'#~~~~{self.__class__.__name__} init')
        self.driver = driver if driver else shareds.driver


    # ------ Persons -----

    def tx_get_person_list(self, args):
        """ Read Person data from given fw_from.
        
            args = dict {use_user, fw, limit, rule, key, years}
        """
        material = args.get('material')
        state = args.get('state')
        username = args.get('use_user')
        rule = args.get('rule')
        key = args.get('key')
        fw_from = args.get('fw','')
        years= args.get('years',[-9999,9999])
        limit = args.get('limit', 100)
        restart = (rule == 'start')

        # Select cypher clause by arguments

        #if not username: username = ""

        cypher_prefix = ""
        if restart:
            # Show search form only
            return {'items': [], 'status': Status.NOT_STARTED }
        elif args.get('pg') == 'all':
            # Show persons, no search form
            cypher = CypherPerson.get_person_list
            print(f"tx_get_person_list: Show '{state}' '{material}' @{username} fw={fw_from}")
        elif rule == 'freetext':
            cypher_prefix = CypherPerson.read_persons_w_events_by_name1
            cypher = CypherPerson.read_persons_w_events_by_name2
        elif rule in ['surname', 'firstname', 'patronyme']:
            # Search persons matching <rule> field to <key> value
            cypher = CypherPerson.read_persons_w_events_by_refname
            print(f"tx_get_person_list: Show '{state}' '{material}' data @{username}, {rule} ~ \"{key}*\"")
        elif rule == 'years':
            # Search persons matching <years>
            cypher = CypherPerson.read_persons_w_events_by_years
            print(f"tx_get_person_list: Show '{state}' '{material}', years {years}")
        elif rule == 'ref':
            #TODO: Search persons where a reference name = <key> value
            return {'items': [], 'status': Status.ERROR, 'statustext': 
                        f'tx_get_person_list: TODO: Show approved common data {rule}={key}'}
            #return session.run(Cypher_person.get_events_by_refname, name=key)
            # if show_approved:
            #     print(f'tx_get_person_list: TODO: Show approved common data {rule}={key}')
            #     #return session.run(Cypher_person.get_events_by_refname, name=key)
            # else:
            #     print(f'tx_get_person_list: TODO: Show candidate data {rule}={key}')
            #     #return session.run(Cypher_person.get_events_by_refname, name=key)
        else:
            return {'persons': [], 'status': Status.ERROR,
                    'statustext': 'tx_get_person_list: Invalid rule'}
 
        persons = []
        #logger.debug(f"tx_get_person_list: cypher: {cypher}")
        result = run_cypher_batch(self.tx, cypher, username, 
                            material=material,
                            cypher_prefix=cypher_prefix,
                            use=rule, name=key,
                            years=years,
                            start_name=fw_from, 
                            limit=limit)
        # result: person, names, events
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
            prec = PersonRecord()
            prec.person_node = record.get('person')
            prec.names = record.get('names')           # list(name_nodes)
            prec.events_w_role = record.get('events')  # list of tuples (event_node, place_name, role)
            prec.owners = record.get('owners')

        # got {'items': [PersonRecord], 'status': Status.OK}
        #    - PersonRecord = object with fields person_node, names, events_w_role, owners
        #    -    events_w_role = list of tuples (event_node, place_name, role)

            # print(p_record)
            node = prec.person_node
            person = PersonBl_from_node(node)

            # if take_refnames and record['refnames']:
            #     refnlist = sorted(record['refnames'])
            #     p.refnames = ", ".join(refnlist)

            for node in prec.names:
                pname = Name_from_node(node)
                pname.initial = pname.surname[0] if pname.surname else ""
                person.names.append(pname)

            # Events
            for node, pname, role in prec.events_w_role:
                if not node is None:
                    e = EventBl_from_node(node)
                    e.place = pname or ""
                    if role and role != "Primary":
                        e.role = role
                    person.events.append(e)

            persons.append(person)

        if len(persons) == 0:
            return {'persons': [], 'status': Status.NOT_FOUND,
                    'statustext': f'No persons found by "{args}"'}
        return {'persons': persons, 'status': Status.OK}


    def tx_get_person_by_uuid(self, uuid:str, material:Material, active_user:str):
        ''' Read a person from common data or user's own Batch.

        :param: uuid        str
        :param: active_user str         if "": read from approved data
                                        else:  read user's candidate data
        :param: material    Material    defines the material 
                                        (state,  material_type, batch_id)
         '''
        res = {'status':Status.OK}

        # 1. Get Person node by uuid, if that allowed for given user
        #    results: person, root

        try:
            record = run_cypher_batch(self.tx, CypherPerson.get_person,
                                      active_user, material, uuid=uuid).single()
            # <Record 
            #    p=<Node id=25651 labels=frozenset({'Person'})
            #        properties={'sortname': 'Zakrevski#Arseni#Andreevits', 'death_high': 1865,
            #            'sex': 1, 'confidence': '', 'change': 1585409698, 'birth_low': 1783,
            #            'birth_high': 1783, 'id': 'I1135', 'uuid': 'dc6a05ca6b2249bfbdd9708c2ee6ef2b',
            #            'death_low': 1865}>
            #    root=<Node id=31100 labels=frozenset({'Audit'})
            #        properties={'id': '2020-07-28.001', ... 'timestamp': 1596463360673}>
            # >
            if record is None:
                print(f'dx_get_person_by_uuid: person={uuid} not found')
                res.update({'status': Status.NOT_FOUND, 'statustext': 'The person does not exist'})
                return res

            # Store original researcher data 
            #    root = dict {material_type, root_user, id}
            #    - material_type root material type
            #    - root_user    the (original) owner of this object
            #    - bid          Batch id
            node = record['root']
            material_type = node.get('material', "")
            root_state = node.get('state', "")
            root_user = node.get('user', "")
            bid = node.get('id', "")

            person_node = record['p']
            puid = person_node.id
            #res['person_node'] = person_node
            res['root'] = {'material':material_type, 'root_state':root_state, 'root_user': root_user, 'batch_id':bid}

#                 # Add to list of all objects connected to this person
#                 self.objs[person.uniq_id] = person

        except Exception as e:
            raise
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

                #person_rel = record['rel_type']     # NAME / EVENT
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

        person = PersonBl_from_node(person_node)
        person.families_as_parent = []
        person.families_as_child = []
        person.citation_ref = []
        person.note_ref = []
        person.media_ref = []
        #self._catalog(person)

        # Info about linked Root node
        for name_node in res.get("name_nodes"):
            name = Name_from_node(name_node)
            person.names.append(name)
            #self._catalog(name)
        # Events
        for event_node, event_role in res.get("event_node_roles"):
            event = EventBl_from_node(event_node)
            event.role = event_role
            event.citation_ref = []
            person.events.append(event)
            #self._catalog(event)
        node = res.get("cause_of_death")
        if node:
            person.cause_of_death = EventBl_from_node(node)
            #self._catalog(person.cause_of_death)
        else:
            person.cause_of_death = None
            
        res['person'] = person
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
#                         f_event = EventBl_from_node(event_node)
                    relation_type = event_node.get('type')
                    # Add family events to person events, too
                    if family_rel == "PARENT":
                        #eid = event_node.get('id')
                        #event_role = "Family"
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

                family = FamilyBl_from_node(family_node)
                family.members = []
                #self._catalog(family)
                for event_node in family_events:
                    event = EventBl_from_node(event_node)
                    if event.type == "Marriage":
                        family.marriage_dates = event.dates
                    family.events.append(event)
                    #self._catalog(event)
                for m in family_members:
                    # Family member
                    member = PersonBl_from_node(m["member_node"])
                    #self._catalog(member)
                    name_node = m["name_node"]
                    if name_node:
                        name = Name_from_node(name_node)
                        member.names.append(name)
                        #self._catalog(name)
                    event_node = m["birth_node"]
                    if event_node:
                        event = EventBl_from_node(event_node)
                        member.birth_date = event.dates
                        member.dates = event.dates
                    else:
                        member.dates = DateRange()
                        # self._catalog(event)
                    # Add member to family
                    family.members.append(member)
                    parental_role = m["parental_role"]  # Family member's role
                    if parental_role == "father":
                        family.father = member
                    elif parental_role == "mother":
                        family.mother = member
                    else:  # child
                        family.children.append(member)

                family.family_role = family_role
                families.append(family)


        except Exception as e:
            msg = f'person={puid} {e}' #{e.__class__.name} {e}'
            print(f'dx_get_person_families: {msg}')
            res.update({'status': Status.ERROR, 'statustext': f"Could not read families: {msg}"})
            return res

        res['families'] = families
        return res

    # ------ Places -----

    def tx_get_placename_list(self, username, material, count=50):
        """List most referenced Places by name. 
        
        If username is defined, filter by user. 
        """
        result_list = []
        with self.driver.session(default_access_mode="READ") as session:
            # Select Batches by user, if defined
            if material.m_type == "Place Data":
                cypher = CypherPlaceStats.get_place_list_for_place_data
            else:
                cypher = CypherPlaceStats.get_place_list
            # logger.debug(f"#  Neo4jReadService.tx_get_placename_list: cypher \n{cypher}\n")
            result = run_cypher_batch(session, cypher, username, material, count=count)
            for record in result:
                place = record["place"]
                placename = place["pname"]
                iid = place["iid"]
                count = record["count"]
                result_list.append(
                    {"placename": placename, "count": count, "iid": iid}
                )
        return result_list

    def tx_get_place_list_fw(self, user, fw_from, limit, lang, material):
        """Read place list from given start point"""
        ret = []
        if lang not in ["fi", "sv"]:
            lang = "fi"
        with self.driver.session(default_access_mode="READ") as session:
            print("Neo4jReadService.tx_get_place_list_fw")
            result = run_cypher_batch(
                session,
                CypherPlace.get_name_hierarchies,
                user,
                material,
                fw=fw_from,
                limit=limit,
                lang=lang,
            )
            for record in result:
                # <Record
                #    place=<Node id=514341 labels={'Place'}
                #        properties={'coord': [61.49, 23.76],
                #            'id': 'P0300', 'type': 'City', 'uuid': '8fbe632144584d30aa75701b49f15484',
                #            'pname': 'Tampere', 'change': 1585409704}>
                #    name=<Node id=514342 labels={'Place_name'}
                #        properties={'name': 'Tampere', 'lang': ''}>
                #    names=[<Node id=514344 labels={'Place_name'}
                #            properties={'name': 'Tampereen kaupunki', 'lang': ''}>,
                #        <Node id=514343 ...>]
                #    uses=4
                #    upper=[[514289, 'b16a6ee2c7a24e399d45554faa8fb094', 'Country', 'Finnland', 'de'],
                #        [514289, 'b16a6ee2c7a24e399d45554faa8fb094', 'Country', 'Finland', 'sv'],
                #        [514289, 'b16a6ee2c7a24e399d45554faa8fb094', 'Country', 'Suomi', '']
                #    ]
                #    lower=[[None, None, None, None, None]]>
                node = record["place"]
                p = PlaceBl_from_node(node)
                p.ref_cnt = record["uses"]

                # Set place names and default display name pname
                # 1. default name
                p.names.append(PlaceName_from_node(record["name"]))
                # 2. other names arranged by language
                lst = place_names_local_from_nodes(record["names"])
                p.names += lst
                p.pname = p.names[0].name
                
                # Combined names for upper and lower places
                p.uppers = PlaceBl.combine_places(record["upper"], lang)
                p.lowers = PlaceBl.combine_places(record["lower"], lang)
                ret.append(p)

        # Return sorted by first name in the list p.names -> p.pname
        return sorted(ret, key=lambda x: x.pname)

    def tx_get_place_w_names_citations_notes_medias(self, user, iid, lang, material):
        """
        Returns the PlaceBl with PlaceNames, Notes, Medias and Citations.

        The connected Notes for Citations are saved in Citation.notes[]
        for accessing citation urls.
        """
        pl = None
        citations = [] # Citation objects referenced from this Place
        cita_dict = {}
        node_ids = []  # List of uniq_is for place, name, note and media nodes
        with self.driver.session(default_access_mode="READ") as session:

            # 1. Get names, notes, medias and citations

            result = run_cypher(
                session,
                CypherPlace.get_w_citas_names_notes,
                user,
                material,
                iid=iid,
                lang=lang,
            )
            for record in result:
                # <Record
                #    place=<Node id=514286 labels={'Place'}
                #        properties={'coord': [60.45138888888889, 22.266666666666666],
                #            'id': 'P0007', 'type': 'City', 'uuid': '494a748a2730417ca02ccaa11685e21a',
                #            'pname': 'Turku', 'change': 1585409704}>
                #    name=<Node id=514288 labels={'Place_name'}
                #        properties={'name': 'Åbo', 'lang': 'sv'}>
                #    names=[<Node id=514287 labels={'Place_name'}
                #                properties={'name': 'Turku', 'lang': ''}>]
                #    notes=[<Node id=582777 labels=frozenset({'Note'}) properties=...>]
                #    medias=[]
                #    citas=[]
                # >

                node = record["place"]
                pl = PlaceBl_from_node(node)
                node_ids.append(pl.uniq_id)
                # Default language name
                node = record["name"]
                if node:
                    pl.names.append(PlaceName_from_node(node))
                # Other name versions
                for node in record["names"]:
                    pl.names.append(PlaceName_from_node(node))
                    node_ids.append(pl.names[-1].uniq_id)

                for node in record["notes"]:
                    n = Note_from_node(node)
                    pl.notes.append(n)
                    node_ids.append(n.uniq_id)

                for node in record["medias"]:
                    m = MediaBl_from_node(node)
                    # Todo: should replace pl.media_ref[] <-- pl.medias[]
                    pl.media_ref.append(m)
                    node_ids.append(m.uniq_id)

                for node in record["citas"]:
                    c = Citation_from_node(node)
                    c.notes = [] # To be set below
                    citations.append(c)
                    cita_dict[c.uniq_id] = c
                    node_ids.append(c.uniq_id)

            # 2. Get Notes for Citations

            result = run_cypher(
                session, 
                CypherPlace.get_notes_for_citas,
                user,
                material,
                citas=list(cita_dict.keys()),
            )
            for record in result:
                # Set Note to active Citation
                cita_uid = record["cid"]
                cita_obj = cita_dict[cita_uid]
                note_obj = Note_from_node(record["note"])
                cita_obj.notes.append(note_obj)

        return {"place": pl, "uniq_ids": node_ids, "citas": citations}

    def tx_get_place_tree(self, locid, lang="fi"):
        """Read upper and lower places around this place.

        Haetaan koko paikkojen ketju paikan locid ympärillä
        Palauttaa listan paikka-olioita ylimmästä alimpaan.
        Jos hierarkiaa ei ole, listalla on vain oma Place_combo.

        Esim. Tuutarin hierarkia
              2 Venäjä -> 1 Inkeri -> 0 Tuutari -> -1 Nurkkala
              tulee tietokannasta näin:
        ╒════╤═══════╤═════════╤══════════╤═══════╤═════════╤═════════╕
        │"lv"│"id1"  │"type1"  │"name1"   │"id2"  │"type2"  │"name2"  │
        ╞════╪═══════╪═════════╪══════════╪═══════╪═════════╪═════════╡
        │"2" │"21774"│"Region" │"Tuutari" │"21747"│"Country"│"Venäjä" │
        ├────┼───────┼─────────┼──────────┼───────┼─────────┼─────────┤
        │"1" │"21774"│"Region" │"Tuutari" │"21773"│"State"  │"Inkeri" │
        ├────┼───────┼─────────┼──────────┼───────┼─────────┼─────────┤
        │"-1"│"21775"│"Village"│"Nurkkala"│"21774"│"Region" │"Tuutari"│
        └────┴───────┴─────────┴──────────┴───────┴─────────┴─────────┘
        Metodi palauttaa siitä listan
            Place(result[0].id2) # Artjärvi City
            Place(result[0].id1) # Männistö Village
            Place(result[1].id1) # Pekkala Farm
        Muuttuja lv on taso:
            >0 = ylemmät,
             0 = tämä,
            <0 = alemmat
        """
        t = DbTree(self.driver, CypherPlace.read_pl_hierarchy, "pname", "type")
        t.load_to_tree_struct(locid)
        if t.tree.depth() == 0:
            # Vain ROOT-solmu: Tällä paikalla ei ole hierarkiaa.
            # Hae oman paikan tiedot ilman yhteyksiä
            with self.driver.session(default_access_mode="READ") as session:
                result = session.run(CypherPlace.root_query, locid=int(locid))
                record = result.single()
                t.tree.create_node(
                    record["name"],
                    locid,
                    parent=0,
                    data={"type": record["type"], "uuid": record["uuid"]},
                )
        ret = []
        for tnode in t.tree.expand_tree(mode=t.tree.DEPTH):
            logger.debug(
                f"{t.tree.depth(t.tree[tnode])} {t.tree[tnode]} {t.tree[tnode].bpointer}"
            )
            if tnode != 0:
                n = t.tree[tnode]

                # Get all names: default lang: 'name' and others: 'names'
                with self.driver.session(default_access_mode="READ") as session:
                    result = session.run(
                        CypherPlace.read_pl_names, locid=tnode, lang=lang
                    )
                    record = result.single()
                    # <Record
                    #    name=<Node id=514413 labels={'Place_name'}
                    #        properties={'name': 'Suomi', 'lang': ''}>
                    #    names=[<Node id=514415 labels={'Place_name'}
                    #            properties={'name': 'Finnland', 'lang': 'de'}>,
                    #        <Node id=514414 labels={'Place_name'} ...}>
                    #    ]
                    # >
                lv = t.tree.depth(n)
                p = PlaceBl(uniq_id=tnode, ptype=n.data["type"], level=lv)
                p.iid = n.data["iid"]
                node = record["name"]
                if node:
                    p.names.append(PlaceName_from_node(node))
                oth_names = []
                for node in record["names"]:
                    oth_names.append(PlaceName_from_node(node))
                # Arrage names by local language first
                lst = PlaceName.arrange_names(oth_names)
                p.names += lst

                p.pname = p.names[0].name
                # logger.info("# {}".format(p))
                p.parent = n.bpointer
                ret.append(p)
        return ret

    def tx_get_place_events(self, uniq_id, privacy):
        """Find events and persons associated to given Place.

            :param: uniq_id    current place uniq_id
            :param: privacy    True, if not showing live people
        """
        result = self.driver.session(default_access_mode="READ").run(
            CypherPlace.get_person_family_events, locid=uniq_id
        )
        ret = []
        for record in result:
            # <Record
            #    indi=<Node id=523974 labels={'Person'}
            #        properties={'sortname': 'Borg#Maria Charlotta#', 'death_high': 1897,
            #            'confidence': '', 'sex': 2, 'change': 1585409709, 'birth_low': 1841,
            #            'birth_high': 1841, 'id': 'I0029', 'uuid': 'e9bc18f7e9b34f1e8291de96002689cd',
            #            'death_low': 1897}>
            #    role='Primary'
            #    names=[<Node id=523975 labels={'Name'}
            #            properties={'firstname': 'Maria Charlotta', 'type': 'Birth Name',
            #                'suffix': '', 'surname': 'Borg', 'prefix': '', 'order': 0}>,
            #        <Node id=523976 labels={'Name'} properties={...}>]
            #    event=<Node id=523891 labels={'Event'}
            #            properties={'datetype': 0, 'change': 1585409700, 'description': '',
            #                'id': 'E0080', 'date2': 1885458, 'type': 'Birth', 'date1': 1885458,
            #                'uuid': '160a0c75659145a4ac09809823fca5f9'}>
            # >
            e = EventBl_from_node(record["event"])
            # Fields uid (person uniq_id) and names are on standard in EventBl
            e.role = record["role"]
            indi_label = list(record["indi"].labels)[0]
            if "Person" == indi_label:
                e.indi_label = "Person"
                e.indi = PersonBl_from_node(record["indi"])
                # Reading confidential person data which is available to this user?
                if not privacy:
                    e.indi.too_new = False
                elif e.indi.too_new:  # Check privacy
                    continue
                for node in record["names"]:
                    e.indi.names.append(Name_from_node(node))
                ##ret.append({'event':e, 'indi':e.indi, 'label':'Person'})
                ret.append(e)
            elif "Family" == indi_label:
                e.indi_label = "Family"
                e.indi = FamilyBl_from_node(record["indi"])
                ##ret.append({'event':e, 'indi':e.indi, 'label':'Family'})
                ret.append(e)
        return {"items": ret, "status": Status.OK}

    # ------ Other -----

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
                placenames = [PlaceName_from_node(node) for node in pn_nodes]
                references[event_uniq_id] = (place_node, placenames)

                # Upper Place node and names linked to this Place
                upper_place_node = record['pi']
                if upper_place_node:
                    pn_nodes = record['pinames']
                    placenames = [PlaceName_from_node(node) for node in pn_nodes]
                    references[place_uniq_id] = (upper_place_node, placenames)
                pass

            # Convert nodes and store them as PlaceBl objects with PlaceNames included
            places = []
            for pl_node, placenames in references.values():
                place = PlaceBl_from_node(pl_node)
                place.names = placenames
                #self._catalog(place)
                places.append(place)
 
        except Exception as e:
            traceback.print_exc()
            print(f"Could not read places for {len(base_objs)} objects: {e.__class__.__name__} {e}")
            return {'status': Status.ERROR, 'statustext':f'{e.__class__.__name__}: {e}'}

        #print(f'#+tx_get_object_places: Got {len(references)} place references') 
        return {'status': Status.OK, 'place_references': references, 'places':places}

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
                #    - r        relation CITATION|NOTE|MEDIA properties
                #    - target   target object Citation|Note|Media

                # Create a reference to target object including node, order and crop
                ref = MediaReference()

                # The existing object src
                src_node = record['src']
                src_uniq_id = src_node.id
                #src_label, = src_node.labels
                #src = obj_catalog[record['uniq_id']]

                rel = record['r']
                ref.order = rel.get('order')
                # Target is a Citation, Note or Media
                target_node = record['target']
                target_uniq_id = target_node.id
                target_label, = target_node.labels
                #ref.node = target_node
                if target_label == 'Citation':
                    ref.obj = Citation_from_node(target_node)
                if target_label == 'Note':
                    ref.obj = Note_from_node(target_node)
                if target_label == 'Media':
                    ref.obj = MediaBl_from_node(target_node)
                    # Media crop attributes used in this relation
                    left = rel.get('left')
                    if left != None:
                        upper = rel.get('upper')
                        right = rel.get('right')
                        lower = rel.get('lower')
                        ref.crop = (left, upper, right, lower)
                ref.label = target_label
                # Relation r between (src_node) --> (target)
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
            traceback.print_exc()
            msg = f"Could not read 'Citations, Notes, Medias': {e.__class__.__name__} {e}"
            print(f"dx_get_object_citation_note_media: {msg}")
            return {'status': Status.ERROR, 'statustext': msg}

        return {'status': Status.OK,
                'new_objects': new_obj_ids, 
                'references': coll}

    def tx_get_citation_sources_repositories(self, citations:list):
        ''' Get Sources and Repositories for given Citations.
        
            Read Source -> Repository hierarchies for given list of citations
                            
            - session       neo4j.session   for database access
            - citations[]   list Citation   list of Citation objects
            
            On return res['sources'] gives references as a dict 
            {uniq_id: SourceReference}
        '''
        if len(citations) == 0:
            return {'status':Status.NOT_FOUND}
        references = {} # {Citation.unid_id: SourceReference}

        citation_uids = [cita.uniq_id for cita in citations]
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
                # 1. Current Citation
                uniq_id = record['uniq_id']
                ref = SourceReference()

                # 2. The Source node
                source_node = record['source']
                ref.source_obj = SourceBl_from_node(source_node)
                repository_node = record['repo']
                if repository_node:
                    ref.repository_obj = Repository_from_node(repository_node)
                    ref.medium = record['rel'].get('medium', "")
                else:
                    ref.repository_obj = None
                references[uniq_id] = ref

        return {'status': Status.OK, 'sources': references}


    def tx_note_search(self, args):
        """Free text search in Notes"""
        print("Neo4jReadServiceTx.tx_note_search: TODO - MUST limit by material_type !!")
#TODO tx_note_search() - Should limit by material_type 
        material = args.get('material')
        batch_id = material.batch_id
        material_type = material.m_type
        #state = args.get('state')
        username = args.get('use_user')
        searchtext = args.get('key')
        limit = args.get('limit', 100)

        cypher_prefix = """
            CALL db.index.fulltext.queryNodes("notetext",$searchtext) 
                YIELD node as note, score
            with note,score
            order by score desc
        """
        #cypher_prefix = ""
        cypher = """
            match (root) --> (note) 
            match (x) --> (note)
                where not "Root" in labels(x)
            optional match (x:Person) --> (n:Name{order:0})
            return distinct note, collect([x,labels(x),n]) as referrers, score
            limit $limit
            """
        result = run_cypher_batch(self.tx, cypher, username, material,
                                  cypher_prefix=cypher_prefix,
                                  searchtext=searchtext,
                                  limit=limit)
        rsp = []
        for record in result:
            #item = record.get('item')
            #note = item[0]
            #x = item[1]
            note = record.get('note')
            #x = record.get('x')
            referrers = record.get('referrers')
            score = record.get('score')
            referrerlist = []
            for r in referrers:
                refdata = dict(r[0])
                url = ""
                label = r[1][0]
                name = r[2]
                if name:
                    fullname = f"{name['firstname']} {name['suffix']} {name['surname']}"
                    refdata['pname'] = fullname 
                uuid = refdata["uuid"]
                iid = refdata["iid"]
                if label in ["Person","Family","Source","Media"]:
                    url = f"/scene/{label.lower()}?uuid={uuid}"
                if label == "Event":
                    url = f"/scene/event/uuid={uuid}"
                if label == "Place":
                    url = f"/place/{iid}"
                refdata['url'] = url 
                referrerlist.append(refdata)
            d = dict(
                note=dict(note),
                #x=dict(x),
                referrers=referrerlist,
                score=score)
            rsp.append(d) 
        return {'items': rsp, 'status': Status.OK}

