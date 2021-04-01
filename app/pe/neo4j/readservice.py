#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on 17.3.2020

@author: jm
'''
import functools
import logging
#from models.gen.family_combo import Family_combo
from bl.dates import DateRange
logger = logging.getLogger('stkserver')

from bl.base import Status
from bl.person_name import Name
from bl.place import PlaceBl, PlaceName
from bl.source import SourceBl
from bl.family import FamilyBl
from bl.event import EventBl
from bl.person import PersonBl
from bl.media import MediaBl

from ui.place import place_names_local_from_nodes

from pe.neo4j.cypher.cy_place import CypherPlace, CypherPlaceStats
from pe.neo4j.cypher.cy_source import CypherSource
from pe.neo4j.cypher.cy_family import CypherFamily
from pe.neo4j.cypher.cy_event import CypherEvent
from pe.neo4j.cypher.cy_person import CypherPerson
from pe.neo4j.cypher.cy_media import CypherMedia

from bl.event import Event
#Todo: Change Old style includes to bl classes
from models.gen.note import Note
#from models.gen.media import Media
from models.gen.repository import Repository
from models.dbtree import DbTree
from models.gen.citation import Citation


class Neo4jReadService:
    ''' 
    Methods for accessing Neo4j database.

    Referenced as shareds.dataservices["read"] class.

    The DataService class enables use as Context Manager.
    @See: https://www.integralist.co.uk/posts/python-context-managers/
    '''
    def __init__(self, driver):
        self.driver = driver
        print(f'#{self.__class__.__name__} init')

    def _set_birth_death(self, person, birth_node, death_node):
        '''
        Set person.birth and person.death events from db nodes
        '''
        if birth_node:
            person.event_birth = EventBl.from_node(birth_node)
        if death_node:
            person.event_death = EventBl.from_node(death_node)


    def _obj_from_node(self, node, role=None):
        ''' Create Person or Family object from db node.
        '''
        if 'Person' in node.labels:
            obj = PersonBl.from_node(node)
        elif 'Family' in node.labels:
            obj = FamilyBl.from_node(node)
            obj.clearname = obj.father_sortname+' <> '+obj.mother_sortname
        else:
            #raise NotImplementedError(f'Person or Family expexted: {list(node.labels})')
            logger.warning(f'pe.neo4j.read_driver.Neo4jReadService._obj_from_node: Person or Family expexted: {list(node.labels)}')
            return None
        obj.role = role if role != 'Primary' else None
        return obj

# Obsolete:
#     def dr_get_person_by_uuid(self, uuid:str, user:str): #--> pe.neo4j.readservice_tx.Neo4jReadServiceTx.tx_get_person_by_uuid
#     def dr_get_person_names_events(self, puid:int): #--> included in pe.neo4j.readservice_tx.Neo4jReadServiceTx.tx_get_person_by_uuid
#     def dr_get_person_families(self, puid:int): #--> pe.neo4j.readservice_tx.Neo4jReadServiceTx.tx_get_person_families
#     def dr_get_object_sources_repositories(self): # --> pe.neo4j.readservice_tx.Neo4jReadServiceTx.tx_get_object_sources_repositories
#     def dr_get_object_places(self, person): # --> pe.neo4j.readservice_tx.Neo4jReadServiceTx.tx_get_object_places
#     def dr_get_object_citation_note_media(self, person, active_objs=[]): #--> pe.neo4j.readservice_tx.Neo4jReadServiceTx.tx_get_object_citation_note_media


    def dr_get_person_list(self, args):
        """ Read Person data from given fw_from.
        
            args = dict {use_user, fw, limit, rule, key, years}
        """
        user = args.get('use_user')
        show_approved = (user is None)
        rule = args.get('rule')
        key = args.get('key')
        fw_from = args.get('fw','')
        years= args.get('years',[-9999,9999])
        limit = args.get('limit', 100)
        restart = (rule == 'start')
        
        persons = []
        with self.driver.session(default_access_mode='READ') as session:
            try:
                if restart:
                    # Show search form only
                    return {'items': [], 'status': Status.NOT_STARTED }
                elif args.get('pg') == 'all':
                    # Show persons, no search form
                    if show_approved:
                        print(f'dr_get_person_list: Show approved, common data fw={fw_from}')
                        result = session.run(CypherPerson.read_approved_persons_w_events_fw_name,
                                             start_name=fw_from, limit=limit)
                    else:
                        print(f'dr_get_person_list: Show candidate data fw={fw_from}')
                        result = session.run(CypherPerson.read_my_persons_w_events_fw_name,
                                             user=user, start_name=fw_from, limit=limit)
                elif rule in ['surname', 'firstname', 'patronyme']:
                    # Search persons matching <rule> field to <key> value
                    if show_approved:
                        print(f'dr_get_person_list: Show approved common data {rule} ~ "{key}*"')
                        result = session.run(CypherPerson.get_common_events_by_refname_use,
                                             use=rule, name=key)
                    else:
                        print(f'dr_get_person_list: Show candidate data {rule} ~ "{key}*"')
                        result = session.run(CypherPerson.get_my_events_by_refname_use,
                                             use=rule, name=key, user=user)
                elif rule == 'years':
                    # Search persons matching <years>
                    if show_approved:
                        print(f'dr_get_person_list: Show approved common data years {years}')
                        result = session.run(CypherPerson.get_common_events_by_years,
                                             years=years)
                    else:
                        print(f'dr_get_person_list: Show candidate data  years {years}')
                        result = session.run(CypherPerson.get_my_events_by_years,
                                             years=years, user=user)
                elif rule == 'ref':
                    # Search persons where a reference name = <key> value
                    if show_approved:
                        print(f'dr_get_person_list: TODO: Show approved common data {rule}={key}')
                        #return session.run(Cypher_person.get_events_by_refname, name=key)
                    else:
                        print(f'dr_get_person_list: TODO: Show candidate data {rule}={key}')
                        #return session.run(Cypher_person.get_events_by_refname, name=key)
                else:
                    return {'items': [], 'status': Status.ERROR,
                            'statustext': 'dr_get_person_list: Invalid rule'}
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
                    #     events=[[
                    #         <Node id=169494 labels={'Event'} 
                    #             properties={'datetype': 0, 'change': 1540587380, 
                    #             'description': '', 'handle': '_e04abcd46811349c7b18f6321ed', 
                    #             'id': 'E5126', 'date2': 1910808, 'type': 'Birth', 'date1': 1910808}>,
                    #          None
                    #          ]] 
                    #     owners=['jpek']>
                    node = record['person']
                    #print(node.id, node.get('sortname'), node.get('death_high'))
                    p = PersonBl.from_node(node)
                    #if show_with_common and p.too_new: continue

                    # if take_refnames and record['refnames']:
                    #     refnlist = sorted(record['refnames'])
                    #     p.refnames = ", ".join(refnlist)
                    p.names = []
                    for node in record['names']:
                        pname = Name.from_node(node)
                        pname.initial = pname.surname[0] if pname.surname else ''
                        p.names.append(pname)
            
                    # Create a list with the mentioned user name, if present
                    if user:
                        p.owners = record.get('owners',[user])
                                                                                                                                        
                    # Events
                    for node, pname, role in record['events']:
                        if not node is None:
                            e = EventBl.from_node(node)
                            e.place = pname or ""
                            if role and role != "Primary":
                                e.role = role
                            p.events.append(e)
        
                    persons.append(p)   

            except Exception as e:
                return {'items':[], 'status':Status.ERROR,
                        'statustext': f'dr_get_person_list: {e.__class__.__name__} {e}'}

        if len(persons) == 0:
            return {'items': persons, 'status': Status.NOT_FOUND,
                    'statustext': f'No persons found by "{args}"'}
        return {'items': persons, 'status': Status.OK}


    def dr_get_event_by_uuid(self, user:str, uuid:str):
        '''
        Read an Event using uuid and username.
        
        Returns dict {item, status, statustext}
        '''
        event = None
        with self.driver.session(default_access_mode='READ') as session:
            try:
                if user: 
                    # Show my researcher data
                    result = session.run(CypherEvent.get_an_event_own,
                                         uuid=uuid, user=user)
                else:
                    print("dr_get_event_by_uuid: approved common only")
                    result = session.run(CypherEvent.get_an_event_common, 
                                         uuid=uuid)
                for record in result:
                    if record['e']:
                        # Record: <Record 
                        #    e=<Node id=16580 labels=frozenset({'Event'}) 
                        #        properties={'datetype': 0, 'change': 1585409701, 'description': '', 
                        #            'id': 'E1742', 'date2': 1815589, 'date1': 1815589, 
                        #            'type': 'Baptism', 'uuid': 'dc969e6831dc47d7b6719edd94fe6007'}>
                        #    root_type='PASSED'
                        #    root=<Node id=31100 labels=frozenset({'Audit'})
                        #        properties={'auditor': 'juha', 'id': '2020-07-28.001', 'user': 'juha',
                        #            'timestamp': 1596463360673}>
                        # >
                        node = record['e']
                        event = EventBl.from_node(node)
                if event:
                    return {"item":event, "status":Status.OK}

            except Exception as e:
                return {"item":None, "status":Status.ERROR, "statustext":str(e)}

        return {"item":event, "status":Status.NOT_FOUND, "statustext":"No Event found"}


    def dr_get_event_participants(self, uid):
        ''' Get people and families connected to this event. 

            Returns dict {items, status, statustext}
        '''
        try:
            with self.driver.session(default_access_mode='READ') as session:
                result = session.run(CypherEvent.get_event_participants, uid=uid)
                parts = []
                for record in result:
                        # <Record
                        #    role='Primary' 
                        #    p=<Node id=24571 labels=frozenset({'Person'})
                        #        properties={'sortname': 'Lekatt#Johan#', 'death_high': 1809, 
                        #            'sex': 1, 'change': 1585409698, 'confidence': '2.0', 
                        #            'birth_low': 1773, 'birth_high': 1773, 'id': 'I0718', 
                        #            'uuid': '80198ed21942468db2ecf777a3de88fa', 'death_low': 1807}>
                        #    name=<Node id=24572 labels=frozenset({'Name'}) 
                        #        properties={'firstname': 'Johan', 'surname': 'Lekatt', 'prefix': '', 
                        #            'suffix': '', 'type': 'Also Known As', 'order': 0}>
                        # >
                    node = record['p']
                    role = record['role']
                    name_node = record['name']
                    # Create Person or Family
                    referee = self._obj_from_node(node, role)
                    cls_name = referee.__class__.__name__
                    if cls_name == "PersonBl":
                        referee.label = "Person"
                    elif cls_name == "FamilyBl":
                        referee.label = "Family"
                    else:
                        raise TypeError('dr_get_event_participants: Invalid member class '+cls_name);
                    # Person may have Name
                    if name_node:
                        name = Name.from_node(name_node)
                        referee.names.append(name)
                    parts.append(referee)

        except Exception as e:
            return {"status":Status.ERROR, 
                    "statustext": f'Error dr_get_event_participants: {e}'}     

        return {"items":parts, "status":Status.OK}

    def dr_get_event_place(self, uid):
        ''' Get event place(s) of this event with surrounding place. 

            Returns dict {items, status, statustext}
        '''
        places = []
        try:
            with self.driver.session(default_access_mode='READ') as session:
                result = session.run(CypherEvent.get_event_place, uid=uid, lang="fi")
                for record in result:
                    # Returns place, name, COLLECT(DISTINCT [properties(r), upper,uname]) as upper_n
                    pl = PlaceBl.from_node(record['place'])
                    pl_name = PlaceName.from_node(record['name'])
                    pl.names.append(pl_name)
                    for _rel_prop, upper, uname in record['upper_n']:
                        pl_upper = PlaceBl.from_node(upper)
                        pl_upper.names.append(PlaceName.from_node(uname))
                        pl.uppers.append(pl_upper)
                    places.append(pl)

        except Exception as e:
            return {"status":Status.ERROR, 
                    "statustext": f'Error dr_get_event_participants: {e}'}     

        return {"items":places, "status":Status.OK}


    def dr_get_event_notes_medias(self, uid):
        ''' Get notes and media connected this event. 

            Returns dict {items, status, statustext}
        '''
        notes = []
        medias = []
        try:
            with self.driver.session(default_access_mode='READ') as session:
                result = session.run(CypherEvent.get_event_notes_medias, uid=uid)
                for record in result:
                    # Return COLLECT(DISTINCT [properties(rel_n), note]) AS notes, 
                    #        COLLECT(DISTINCT [properties(rel_m), media]) AS medias
                    for _rel_prop, node in record['notes']:
                        if node:
                            notes.append(Note.from_node(node))
                    for _rel_prop, node in record['medias']:
                        # _rel_prop may be {"order":0} (not used)
                        if node:
                            medias.append(MediaBl.from_node(node))

        except Exception as e:
            return {"status":Status.ERROR, 
                    "statustext": f'Error dr_get_event_notes_medias: {e}'}     

        return {"notes":notes, "medias":medias, "status":Status.OK}


    def dr_get_family_by_uuid(self, user:str, uuid:str):
        '''
        Read a Family using uuid and user info.
        
        Returns dict {item, status, statustext}
        '''
        family = None

        with self.driver.session(default_access_mode='READ') as session:
            try:
                if user: 
                    # Show my researcher data
                    result = session.run(CypherFamily.get_a_family_own, 
                                     f_uuid=uuid, user=user)
                else:
                    print("dr_get_family_by_uuid: approved common only")
                    result = session.run(CypherFamily.get_a_family_common, 
                                     f_uuid=uuid)
                for record in result:
                    if record['f']:
                        # <Record 
                        #    f=<Node id=590928 labels={'Family'}
                        #        properties={'datetype': 1, 'father_sortname': 'Gadd#Peter Olofsson#', 
                        #            'change': 1560931512, 'rel_type': 'Unknown', 'id': 'F0002', 
                        #            'date2': 1766592, 'date1': 1766592, 'uuid': '9488e3c76c6645f8b024902f2119e15a'}>
                        #    root_type='OWNS' 
                        #    root=<Node id=384349 labels={'Batch'} 
                        #        properties={'mediapath': '/home/rinminlij1l1j1/paikat_pirkanmaa_yhdistetty_06052020.gpkg.media', 
                        #            'file': 'uploads/juha/paikat_pirkanmaa_yhdistetty_6.5.2020_clean.gramps', 
                        #            'id': '2020-05-09.001', 'user': 'juha', 'timestamp': 1589022866282, 'status': 'completed'}>
                        # >
                        node = record['f']
                        family = FamilyBl.from_node(node)
                    return {"item":family, "status":Status.OK}
            except Exception as e:
                return {"item":None, "status":Status.ERROR, "statustext":str(e)}

        return {"item":None, "status":Status.NOT_FOUND, "statustext":"No families found"}


    def dr_get_family_parents(self, uniq_id:int, with_name=True):
        """
            Get Parent nodes, optionally with default Name
            
            returns dict {items, status, statustext}
        """
        parents = []
        with self.driver.session(default_access_mode='READ') as session:
            try:
                result = session.run(CypherFamily.get_family_parents, 
                                     fuid=uniq_id)
                for record in result:
                    # <Record 
                    #    role='father'
                    #    parent=<Node id=550536 labels={'Person'}
                    #        properties={'sortname': 'Linderoos#Johan Wilhelm#', 'death_high': 1844,
                    #            'confidence': '2.0', 'sex': 1, 'change': 1585409699, 'birth_low': 1788,
                    #            'birth_high': 1788, 'id': 'I1314', 'uuid': '8a4d49509d26434bb3bf63c4657af9e2',
                    #            'death_low': 1844}>
                    #    name=<Node id=550537 labels={'Name'}
                    #        properties={'firstname': 'Johan Wilhelm', 'type': 'Birth Name',
                    #            'suffix': '', 'prefix': '', 'surname': 'Linderoos', 'order': 0}>
                    #    birth=<Node id=543985 labels={'Event'}
                    #        properties={'datetype': 0, 'change': 1585409702, 'description': '',
                    #            'id': 'E4460', 'date2': 1831101, 'type': 'Birth', 'date1': 1831101,
                    #            'uuid': '5f9b78fe1a644834bc52715d58d61774'}>
                    #   death=<Node id=543986 labels={'Event'} properties={'id': 'E4461', ...}>
                    # >

                    role = record['role']
                    person_node = record['person']
                    if person_node:
                        if uniq_id != person_node.id:
                            # Skip person with double default name
                            p = PersonBl.from_node(person_node)
                            p.role = role
                            name_node = record['name']
                            if name_node:
                                p.names.append(Name.from_node(name_node))

                            birth_node = record['birth']
                            death_node = record['death']
                            self._set_birth_death(p, birth_node, death_node)

                            parents.append(p)

            except Exception as e:
                return {"status":Status.ERROR, 
                        "statustext": f'Error dr_get_family_parents: {e}'}     
    
        return {"items":parents, "status":Status.OK, "statustext":""}


    def dr_get_family_children(self, uniq_id, with_events=True, with_names=True):
        """ 
        Get Child nodes, optionally with Birth and Death nodes
            
            returns dict {items, status, statustext}
        """
        children = []
        with self.driver.session(default_access_mode='READ') as session:
            try:
                result = session.run(CypherFamily.get_family_children, 
                                     fuid=uniq_id)
                for record in result:
                    # <Record 
                    #    person=<Node id=550538 labels={'Person'}
                    #        properties={'sortname': 'Linderoos#Gustaf Mathias Israel#',...}> 
                    #    name=<Node id=550539 labels={'Name'}
                    #        properties={'firstname': 'Gustaf Mathias Israel', 'type': 'Birth Name',...'order': 0}>
                    #    birth=<Node id=543988 labels={'Event'}
                    #        properties={'id': 'E4463', 'type': 'Birth', ...}>
                    #    death=None
                    # >
                    person_node = record['person']
                    if person_node:
                        p = PersonBl.from_node(person_node)
                        name_node = record['name']
                        if name_node:
                            p.names.append(Name.from_node(name_node))
                        birth_node = record['birth']
                        death_node = record['death']
                        self._set_birth_death(p, birth_node, death_node)

                        children.append(p)

            except Exception as e:
                return {"status":Status.ERROR, 
                        "statustext": f'Error dr_get_family_children: {e}'}     

        return {"items":children, "status":Status.OK}


    def dr_get_family_events(self, uniq_id, with_places=True):
        """
            4. Get family Events node with Places

            returns dict {items, status, statustext}
        """
        events = []
        with self.driver.session(default_access_mode='READ') as session:
            try:
                result = session.run(CypherFamily.get_events_w_places, fuid=uniq_id)
                # RETURN event, place, names,
                #        COLLECT(DISTINCT [place_in, rel_in, COLLECT in_names]) AS inside
                for record in result:
                    event_node = record['event']
                    if event_node:
                        #    event=<Node id=543995 labels={'Event'}
                        #        properties={'datetype': 0, 'change': 1585409702, 'description': '', 
                        #            'id': 'E0170', 'date2': 1860684, 'type': 'Marriage', 'date1': 1860684, 
                        #            'uuid': '38c0d5bdc0f245c88bfb1083228db219'}>
                        e = EventBl.from_node(event_node)

                        place_node = record['place']
                        if place_node:
                            #    place=<Node id=531912 labels={'Place'} 
                            #        properties={'id': 'P1077', 'type': 'Parish', 'uuid': '55c069c9cee54092a88366a15b75d1a4', 
                            #            'pname': 'Loviisan srk', 'change': 1585562874}>
                            #    names=[ <Node id=531913 labels={'Place_name'} 
                            #                properties={'name': 'Loviisan srk', 'lang': ''}>
                            #        ] 
                            e.place = PlaceBl.from_node(place_node)
                            e.place.names = place_names_local_from_nodes(record['names'])
                            
                        for inside_node, inside_rel, inside_names in record['inside']:
                            if inside_node:
                                # <Node id=5494 labels=frozenset({'Place'})
                                #     properties={'id': 'P0024', 'type': 'Country', 'uuid': '199338cdcd754760acfe3d2165c2805c', 
                                #         'pname': 'Venäjä', 'change': 1585409705}>
                                # <Relationship id=6192
                                #     nodes=(
                                #         <Node id=5788 labels=frozenset({'Place'})
                                #             properties={'coord': [60.70911111111111, 28.745330555555558],
                                #                 'pname': 'Viipuri', 'change': 1585409704, 'id': 'P0011',
                                #                 'type': 'City', 'uuid': '4bea93a25e7841cfb2160f00dccbfcf5'}>,
                                #         <Node id=5494 labels=frozenset({'Place'})
                                #             properties={'id': 'P0024', 'type': 'Country', 'uuid': '199338cdcd754760acfe3d2165c2805c',
                                #                 'pname': 'Venäjä', 'change': 1585409705}>
                                #     )
                                #     type='IS_INSIDE'
                                #     properties={'datetype': 2, 'date2': 2040000, 'date1': 2040000}
                                # >
                                # [
                                #     <Node id=5496 labels=frozenset({'Place_name'}) properties={'name': 'Ryssland', 'lang': 'sv'}>
                                #     <Node id=5495 labels=frozenset({'Place_name'}) properties={'name': 'Venäjä', 'lang': ''}>
                                # ]
                                pl_in = PlaceBl.from_node(inside_node)
                                if len(inside_rel._properties):
                                    pl_in.dates = DateRange.from_node(inside_rel._properties)
    
                                pl_in.names = place_names_local_from_nodes(inside_names)
                                e.place.uppers.append(pl_in)

                        events.append(e)

            except Exception as e:
                return {"status":Status.ERROR, 
                        "statustext": f'Error dr_get_family_events: {e}'}     

        return {"items":events, "status":Status.OK}


    def dr_get_family_sources(self, id_list, with_notes=True):
        """
            Get Sources Citations and Repositories for given families and events.

            The id_list should include the uniq_ids for Family and events Events

            returns dict {items, status, statustext}
        """
        sources = []
        with self.driver.session(default_access_mode='READ') as session:
            try:
                result = session.run(CypherFamily.get_family_sources, 
                                     id_list=id_list)
                for record in result:
                    # <Record 
                    #    src_id=543995
                    #    repository=<Node id=529693 labels={'Repository'}
                    #        properties={'id': 'R0179', 'rname': 'Loviisan seurakunnan arkisto', 'type': 'Archive', 'uuid': 'ef2369ac6e67450abc9ed8c0bd04ce45', 'change': 1585409708}> 
                    #    source=<Node id=534511 labels={'Source'}
                    #        properties={'id': 'S0876', 'stitle': 'Loviisan srk - vihityt 1794-1837', 'uuid': '8b29ab449849434c984dcf4885b5882b',
                    #            'spubinfo': 'MKO131-133', 'change': 1585409705, 'sauthor': ''}>
                    #    citation=<Node id=537795 labels={'Citation'}
                    #        properties={'id': 'C2598', 'page': '1817 Mars 13', 'uuid': 'e0841eb28d8143ce92bbb2c9a43f4d23',
                    #            'change': 1585409707, 'confidence': '2'}>
                    # >
                    repository_node = record['repository']
                    if repository_node:
                        source_node = record['source']
                        citation_node = record['citation']
                        src_id = record['src_id']

                        source = SourceBl.from_node(source_node)
                        cita = Citation.from_node(citation_node)
                        repo = Repository.from_node(repository_node)
                        source.repositories.append(repo)
                        source.citations.append(cita)
                        source.referrer = src_id
                        sources.append(source)
                        
#                     for node in record['note']:
#                         note = Note.from_node(node)
#                         family.notes.append(note)

            except Exception as e:
                return {"status":Status.ERROR, 
                        "statustext": f'Error dr_get_family_sources: {e}'}     

        return {"items":sources, "status":Status.OK}


    def dr_get_family_notes(self, id_list:list):
        """
            Get Notes for family and events
            The id_list should include the uniq_ids for Family and events Events

            returns dict {items, status, statustext}
        """
        notes = []
        with self.driver.session(default_access_mode='READ') as session:
            try:
                result = session.run(CypherFamily.get_family_notes, 
                                     id_list=id_list)
                for record in result:
                    # <Record 
                    #    src_id=543995
                    #    repository=<Node id=529693 labels={'Repository'}
                    #        properties={'id': 'R0179', 'rname': 'Loviisan seurakunnan arkisto', 'type': 'Archive', 'uuid': 'ef2369ac6e67450abc9ed8c0bd04ce45', 'change': 1585409708}> 
                    #    source=<Node id=534511 labels={'Source'}
                    #        properties={'id': 'S0876', 'stitle': 'Loviisan srk - vihityt 1794-1837', 'uuid': '8b29ab449849434c984dcf4885b5882b',
                    #            'spubinfo': 'MKO131-133', 'change': 1585409705, 'sauthor': ''}>
                    #    citation=<Node id=537795 labels={'Citation'}
                    #        properties={'id': 'C2598', 'page': '1817 Mars 13', 'uuid': 'e0841eb28d8143ce92bbb2c9a43f4d23',
                    #            'change': 1585409707, 'confidence': '2'}>
                    # >
                    note_node = record['note']
                    if note_node:
                        src_id = record['src_id']
                        note = Note.from_node(note_node)
                        note.referrer = src_id
                        notes.append(note)
                        
            except Exception as e:
                return {"status":Status.ERROR, 
                        "statustext": f'Error dr_get_family_notes: {e}'}     

        return {"items":notes, "status":Status.OK}


    def dr_get_person_families_uuid(self, uuid):
        """
            Get the Families where Person is a member (parent or child).

            Returns dict {items, status, statustext}
            
            Family.parents[] has mother and father Person objects with 
            corresponding .role (the fields .father and .mother are not used).
        """
        families = {}
        with self.driver.session(default_access_mode='READ') as session:
            try:
                result = session.run(CypherFamily.get_person_families, 
                                     p_uuid=uuid)
                for record in result:
                    #<Record 
                    #    family=<Node id=552768 labels={'Family'}
                    #        properties={'datetype': 3, 'father_sortname': 'Åkerberg#Mathias#Andersson',
                    #            'change': 1585409700, 'rel_type': 'Married', 'mother_sortname': 'Unonius#Catharina Ulrica#',
                    #            'id': 'F0011', 'date2': 1842189, 'date1': 1834016, 'uuid': '01ddf9439408445fb725d580e060c02a'}>
                    #    type='PARENT'
                    #    role='father'
                    #    person=<Node id=547514 labels={'Person'}
                    #        properties={'sortname': 'Åkerberg#Mathias#Andersson', 'death_high': 1831, 'confidence': '2.6', 
                    #            'sex': 1, 'change': 1585409697, 'birth_low': 1750, 'birth_high': 1750, 'id': 'I0022', 
                    #            'uuid': '265b22a5a1544ce2b66371fa195f9d89', 'death_low': 1831}>
                    #    birth=<Node id=539796 labels={'Event'}
                    #        properties={'datetype': 0, 'change': 1585409700, 'description': '', 'id': 'E0238', 
                    #            'date2': 1792123, 'type': 'Birth', 'date1': 1792123, 'uuid': 'f6d314f7e47a431e9a7df5bbdd090fa7'}>
                    # >
                    family_node = record['family']
                    fid = family_node.id
                    if not fid in families:
                        # New family
                        family = FamilyBl.from_node(family_node)
                        family.parents = []
                        families[fid] = family
                    family = families[fid]
                    person_node = record['person']
                    person = PersonBl.from_node(person_node)
                    birth_node = record['birth']
                    if birth_node:
                        birth = EventBl.from_node(birth_node)
                        person.event_birth = birth
                    if record['type'] == 'PARENT':
                        person.role = record['role']
                        family.parents.append(person)
                        if uuid == person.uuid:
                            family.role = 'parent'
                            print(f'# Family {family.id} {family.role} --> {person.id} ({person.role})')
                    else:
                        person.role = "child"
                        family.children.append(person)
                        if uuid == person.uuid:
                            family.role = 'child'
                            print(f'# Family {family.id} {family.role} --> {person.id}')
                    
                if not families:
                    return {"status":Status.NOT_FOUND, 
                            "statustext": f'No families for this person'}

                # Sort parents always on same order
                for family in families.values():
                    if len(family.parents) > 1:
                        family.parents.sort(key=lambda x: x.role)


            except Exception as e:
                return {"status":Status.ERROR, 
                        "statustext": f'Error dr_get_person_families: {e}'}     

        return {"items":list(families.values()), "status":Status.OK}


    def dr_get_place_list_fw(self, user, fw_from, limit, lang='fi'):
        ''' Read place list from given start point
        '''
        ret = []
        if lang not in ['fi', 'sv']:
            lang = 'fi'
        with self.driver.session(default_access_mode='READ') as session: 
            if user == None: 
                #1 get approved common data
                print("Neo4jReadService.dr_get_place_list_fw: approved")
                result = session.run(CypherPlace.get_common_name_hierarchies,
                                     fw=fw_from, limit=limit, lang=lang)
            else: 
                #2 get my own
                print("Neo4jReadService.dr_get_place_list_fw: candidate")
                result = session.run(CypherPlace.get_my_name_hierarchies,
                                     user=user, fw=fw_from, limit=limit, lang=lang)
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
                p = PlaceBl.from_node(node)
                p.ref_cnt = record['uses']
    
                # Set place names and default display name pname
                node = record['name']    
                p.names.append(PlaceName.from_node(node))
                oth_names = []
                for node in record['names']:
                    oth_names.append(PlaceName.from_node(node))
                # Arrage names by local language first 
                lst = PlaceName.arrange_names(oth_names)
    
                p.names += lst
                p.pname = p.names[0].name
                p.uppers = PlaceBl.combine_places(record['upper'], lang)
                p.lowers = PlaceBl.combine_places(record['lower'], lang)
                ret.append(p)

        # Return sorted by first name in the list p.names -> p.pname
        return sorted(ret, key=lambda x:x.pname)


    def dr_get_place_w_names_notes_medias(self, user, uuid, lang='fi'): 
        """ Returns the PlaceBl with PlaceNames, Notes and Medias included.
        """
        pl = None
        node_ids = []   # List of uniq_is for place, name, note and media nodes 
        with self.driver.session(default_access_mode='READ') as session:
            if user == None: 
                result = session.run(CypherPlace.get_common_w_names_notes,
                                     uuid=uuid, lang=lang)
            else:
                result = session.run(CypherPlace.get_my_w_names_notes,
                                     user=user, uuid=uuid, lang=lang)
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
                #    notes=[] 
                #    medias=[]
                # >

                node = record["place"]
                pl = PlaceBl.from_node(node)
                node_ids.append(pl.uniq_id)
                # Default lang name
                name_node = record["name"]
                if name_node:
                    pl.names.append(PlaceName.from_node(name_node))
                # Other name versions
                for name_node in record["names"]:
                    pl.names.append(PlaceName.from_node(name_node))
                    node_ids.append(pl.names[-1].uniq_id)

                for notes_node in record['notes']:
                    n = Note.from_node(notes_node)
                    pl.notes.append(n)
                    node_ids.append(pl.notes[-1].uniq_id)

                for medias_node in record['medias']:
                    m = MediaBl.from_node(medias_node)
                    #Todo: should replace pl.media_ref[] <-- pl.medias[]
                    pl.media_ref.append(m)
                    node_ids.append(pl.media_ref[-1].uniq_id)

        return {"place":pl, "uniq_ids":node_ids}


    def dr_get_place_tree(self, locid, lang="fi"):
        """ Read upper and lower places around this place.
        
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
        t = DbTree(self.driver, CypherPlace.read_pl_hierarchy, 'pname', 'type')
        t.load_to_tree_struct(locid)
        if t.tree.depth() == 0:
            # Vain ROOT-solmu: Tällä paikalla ei ole hierarkiaa.
            # Hae oman paikan tiedot ilman yhteyksiä
            with self.driver.session(default_access_mode='READ') as session:
                result = session.run(CypherPlace.root_query, locid=int(locid))
                record = result.single()
                t.tree.create_node(record["name"], locid, parent=0,
                                   data={'type': record["type"],'uuid':record['uuid']})
        ret = []
        for tnode in t.tree.expand_tree(mode=t.tree.DEPTH):
            logger.debug(f"{t.tree.depth(t.tree[tnode])} {t.tree[tnode]} {t.tree[tnode].bpointer}")
            if tnode != 0:
                n = t.tree[tnode]

                # Get all names: default lang: 'name' and others: 'names'
                with self.driver.session(default_access_mode='READ') as session:
                    result = session.run(CypherPlace.read_pl_names,
                                         locid=tnode, lang=lang)
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
                p = PlaceBl(uniq_id=tnode, ptype=n.data['type'], level=lv)
                p.uuid = n.data['uuid']
                node = record['name']
                if node:
                    p.names.append(PlaceName.from_node(node))
                oth_names = []
                for node in record['names']:
                    oth_names.append(PlaceName.from_node(node))
                # Arrage names by local language first 
                lst = PlaceName.arrange_names(oth_names)
                p.names += lst
                
                # TODO: Order by lang here! (The order field is not in use) 
                p.pname = p.names[0].name
                #logger.info("# {}".format(p))
                p.parent = n.bpointer
                ret.append(p)
        return ret

    def dr_get_place_events(self, uniq_id):
        """ Find events and persons associated to given Place
        
            Haetaan paikkaan liittyvät tapahtumat sekä
            osallisen henkilön nimitiedot.
        """
        result = self.driver.session(default_access_mode='READ').run(CypherPlace.get_person_family_events, 
                                           locid=uniq_id)
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
            e = EventBl.from_node(record['event'])
            # Fields uid (person uniq_id) and names are on standard in EventBl
            e.role = record["role"]
            indi_label = list(record['indi'].labels)[0]
            if indi_label in ['Audit', 'Batch']:
                continue
            if 'Person' == indi_label:
                e.indi_label = 'Person'
                e.indi = PersonBl.from_node(record['indi'])
                if e.indi.too_new:    # Check privacy
                    continue
                for node in record["names"]:
                    e.indi.names.append(Name.from_node(node))
                ##ret.append({'event':e, 'indi':e.indi, 'label':'Person'})
                ret.append(e)
            elif 'Family' == indi_label:
                e.indi_label = 'Family'
                e.indi = FamilyBl.from_node(record['indi'])
                ##ret.append({'event':e, 'indi':e.indi, 'label':'Family'})
                ret.append(e)
            else:   # Audit or Batch
                print(f"r_get_place_events No Person or Family:"
                      f" {e.id} {record['indi'].labels} {record['indi'].get('id')}")
        return {'items':ret, 'status':Status.OK}


    def dr_get_source_list_fw(self, args):
        """ Read all sources with notes and repositories, optionally limited by keywords.
         
            used keyword arguments:
            - user        Username to select data
            - theme1      A keyword (fi) for selecting source titles
            - theme2      Another keyword (sv) for selecting source titles
            - fw          Read sources starting from this keyword
            - count       How many sources to read

            Todo: Valinta vuosien mukaan
            Todo: tuloksen sivuttaminen esim. 100 kpl / sivu
        """
        sources = []
        user = args.get('user')

        with self.driver.session(default_access_mode='READ') as session:
            if args.get('theme1'):
                # Filter sources by searching keywords in fi and sv langiage
                key1 = args.get('theme1')
                key2 = args.get('theme2')
                if user: 
                    # Show my researcher data
                    print("dr_get_source_list_fw: my researcher data")
                    result = session.run(CypherSource.get_own_set_selections,
                                         key1=key1, key2=key2, user=user)
                else:
                    print("dr_get_source_list_fw: approved common only")
                    result = session.run(CypherSource.get_auditted_set_selections,
                                         key1=key1, key2=key2)
            else:
                # Show all themes
                if user: 
                    # Show my researcher data
                    print("dr_get_source_list_fw: my researcher data")
                    result = session.run(CypherSource.get_own_sets, user=user)
                else:
                    print("dr_get_source_list_fw: approved common only")
                    result = session.run(CypherSource.get_auditted_sets)
 
            for record in result:
                # <Record 
                #    owner_type='PASSED' 
                #    source=<Node id=333338 labels={'Source'}
                #        properties={'id': 'S0029', 'stitle': 'Lapinjärvi vihityt 1788-1803 vol  es346', 
                #            'uuid': '4637e07dcc7f42c09236a8482fb01b7c', 'spubinfo': '', 'sauthor': '', 
                #            'change': 1532807569}>
                #    notes=[
                #        <Node id=445002 labels={'Note'} 
                #            properties={'id': 'N2207', 'text': '', 'type': 'Source Note', 
                #                'uuid': 'e6efcc1fbcad4dcd85352fd95cd5bf35', 'url': 'http://www.sukuhistoria.fi/sshy/sivut/jasenille/paikat.php?bid=3788',
                #                'change': 1532807569}>] 
                #    repositories=[
                #        [   'Book', 
                #            <Node id=393661 labels={'Repository'} 
                #                properties={'id': 'R0003', 'rname': 'Lapinjärven seurakunnan arkisto',
                #                    'type': 'Archive', 'uuid': 'b6171feb05bc47de87ee509a79821d8f',
                #                    'change': 1577815469}>]] cit_cnt=0 ref_cnt=0>
                 
                # <Record
                # 0  uniq_id=242567 
                # 1  source=<Node id=242567 labels={'Source'} 
                #        properties={'handle': '_dcb5682a0f47b7de686b3251557', 'id': 'S0334', 
                #            'stitle': 'Åbo stifts herdaminne 1554-1640', 'change': '1516698633'}> 
                # 2  notes=[<Node id=238491 labels={'Note'} 
                #        properties={'handle': '_e07cd6210c57e0d53393a62fa7a', 'id': 'N3952', 
                #        'text': '', 'type': 'Source Note', 'url': 'http://www.narc.fi:8080/...', 
                #        'change': 1542667331}>] 
                # 3  repositories=[
                #        ['Book', <Node id=238996 labels={'Repository'} 
                #            properties={'handle': '_db51a3f358e67ac82ade828edd1', 'id': 'R0057', 
                #            'rname': 'Painoteokset', 'type': 'Collection', 'change': '1541350910'}>]]
                # 4  cit_cnt=1 
                # 5  ref_cnt=1
                # >
                source = record['source']
                s = SourceBl.from_node(source)
                notes = record['notes']
                for note in notes:
                    n = Note.from_node(note)
                    s.notes.append(n)
                repositories = record['repositories']
                for repo in repositories:
                    # [medium, repo_node]
                    if repo[1] != None:
                        rep = Repository.from_node(repo[1])
                        rep.medium = repo[0]
                        s.repositories.append(rep)
                s.cit_cnt = record['cit_cnt']
                s.ref_cnt = record['ref_cnt']
                sources.append(s)
 
        return sources


    def dr_get_source_w_repository(self, user, uuid): 
        """ Returns the PlaceBl with Notes and PlaceNames included.
        """
        source = None
        with self.driver.session(default_access_mode='READ') as session:
            if user == None: 
                result = session.run(CypherSource.get_auditted_set_single_selection,
                                     uuid=uuid)
            else:
                result = session.run(CypherSource.get_own_set_single_selection,
                                     user=user, uuid=uuid)
            for record in result:
                # <Record 
                #    owner_type='PASSED'
                #    source=<Node id=340694 labels={'Source'}
                #        properties={'id': 'S1112', 'stitle': 'Aamulehti (sanomalehti)',
                #            'uuid': '3ac9c9e3c3a0490f8e064225b90139e1', 'spubinfo': '',
                #            'sauthor': '', 'change': 1585409705}>
                #    notes=[]
                #    reps=[
                #        ['Book', <Node id=337715 labels={'Repository'}
                #            properties={'id': 'R0002', 'rname': 'Kansalliskirjaston digitoidut sanomalehdet',
                #                'type': 'Collection', 'uuid': '2fc57cc64197461eb94a4bcc02da9ff9',
                #                'change': 1585409708}>]]
                # >
                source_node = record['source']
                source = SourceBl.from_node(source_node)
                notes = record['notes']
                for note_node in notes:
                    n = Note.from_node(note_node)
                    source.notes.append(n)
                repositories = record['reps']
                for medium, repo_node in repositories:
                    if repo_node != None:
                        rep = Repository.from_node(repo_node)
                        rep.medium = medium
                        source.repositories.append(rep)

            if source:
                return {'item': source, 'status':Status.OK}
            return {'status':Status.NOT_FOUND,
                    'statustext': f"source uuid={uuid} not found"}


    def dr_get_media_list(self, user, fw_from, limit):
        """ Reads Media objects from user batch or common data using context.
        
            :param: user    Active user or None, if approved data is requested
            :param: fw_from The name from which the list is requested
            :param: limit   How many items per page
        """
                        
        with self.driver.session(default_access_mode='READ') as session: 
            if user == None:
                # Show approved common data
                result = session.run(CypherMedia.read_approved_medias,
                                     user=user, start_name=fw_from, limit=limit)
            else:
                # Show user Batch
                result =  session.run(CypherMedia.read_my_medias,
                                      start_name=fw_from, user=user, limit=limit)

            recs = []
            for record in result: 
                recs.append(record)
#             recs = [record for record in result]
            if recs:
                return {'recs':recs, 'status':Status.OK}
            else:
                return {'recs':recs, 'status':Status.NOT_FOUND}


    def dr_get_media_single(self, user, uuid):
        """ Read a Media object, selected by UUID or uniq_id.
        
            :param: user    username, who has access
            :parma: uuid    Media node uuid
        """
        recs = []
        with self.driver.session(default_access_mode='READ') as session:
            try:
                if user:
                    result = session.run(CypherMedia.get_my_media_by_uuid, 
                                         uuid=uuid, user=user)
                else:
                    result = session.run(CypherMedia.get_approved_media_by_uuid, 
                                         uuid=uuid)
                # RETURN media, r, ref, ref2
                for record in result:
                    recs.append((record['media'], record['prop'], 
                                 record['ref'], record['ref2']))

            except Exception as e:
                return {'status':Status.ERROR, 'statustext':
                        f'Neo4jReadService.dr_get_media_single: {e.__class__.__name__} {e}'}

        status = Status.OK if recs else Status.NOT_FOUND
        return {'status':status, 'items':recs }


    def dr_get_source_citations(self, sourceid:int):
        """ Read Events and Person, Family and Media citating this Source.

            Returns
            - citation      Citation node
            - notes         list of Note nodes for this citation
            - near          node connected derectly to Citation
            - targets       list of the Person or Family nodes 
                            (from near or behind near)
        """

        citations = {}      # {uniq_id:citation_object}
        notes = {}          # {uniq_id:[note_object]}
        #near = {}           # {uniq_id:object}
        targets = {}         # {uniq_id:[object]} Person or Family

        with self.driver.session(default_access_mode='READ') as session:
            result = session.run(CypherSource.get_citators_of_source, 
                                 uniq_id=sourceid)
            for record in result:
                # <Record        # (1) A Person or Family
                #                #     referencing directly Citation
                #    citation=<Node id=342041 labels={'Citation'}
                #        properties={'id': 'C2840', 'page': '11.10.1907 sivu 2',
                #            'uuid': '03b2c7a7dac84701b67612bf10f60b6b', 'confidence': '2',
                #            'change': 1585409708}>
                #    notes=[<Node id=384644 labels={'Note'}
                #        properties={'id': 'N3556', 'text': '', 'type': 'Citation', 'uuid': '4a377b0e936d4e68a72cad64a4925db9',
                #            'url': 'https://digi.kansalliskirjasto.fi/sanomalehti/binding/609338?page=2&term=Sommer&term=Maria&term=Sommerin&term=sommer',
                #            'change': 1585409709}>]
                #    near=<Node id=347773 labels={'Person'}
                #            properties={'sortname': 'Johansson#Gustaf#', 'death_high': 1920, 'confidence': '2.0',
                #                'sex': 1, 'change': 1585409699, 'birth_low': 1810, 'birth_high': 1810,
                #                'id': 'I1745', 'uuid': 'dfc866bfa9274071b37ccc2f6c33abed',
                #                'death_low': 1852}>
                #    far=[]
                # >
                # <Record        # (2) A Person or Family having an Event, Name, or Media
                #                #     referencing the Citation
                #    citation=<Node id=342042 labels={'Citation'} properties={...}>
                #    notes=[<Node id=381700 labels={'Note'} properties={...}>]
                #    near=<Node id=359150 labels={'Event'}
                #        properties={'datetype': 0, 'change': 1585409703, 'description': '',
                #            'id': 'E5451', 'date2': 1953097, 'type': 'Death', 'date1': 1953097,
                #            'uuid': '467b67c1a0f84b8baed150b030a7bef0'}>
                #    far=[
                #         [<Node id=347835 labels={'Person'}
                #            properties={'sortname': 'Sommer#Arthur#',...}>,
                #          'Primary']
                #    ]
                # >
                citation_node = record['citation']
                near_node = record['near']
                far_nodes = record['far']
                note_nodes = record['notes']
    
                uniq_id = citation_node.id
                citation = Citation.from_node(citation_node)
                citations[uniq_id] = citation
    
                notelist = []
                for node in note_nodes:
                    notelist.append(Note.from_node(node))
                if notelist:
                    notes[uniq_id] = notelist
    
                targetlist = []     # Persons or Families referring this source
                for node, role in far_nodes:
                    if not node: continue
                    obj = self._obj_from_node(node, role)
                    if obj:         # Far node is the Person or Family
                        obj.eventtype = near_node['type']
                        targetlist.append(obj)
                if not targetlist:  # No far node: there is a middle node near
                    obj = self._obj_from_node(near_node)
                    if obj:
                        targetlist.append(obj)
                if targetlist:
                    targets[uniq_id] = targetlist
                else:
                    print(f'dr_get_source_citations: Event {near_node.id} {near_node.get("id")} without Person or Family?')

        # Result dictionaries using key = Citation uniq_id
        return citations, notes, targets


    def dr_inlay_person_lifedata(self, person): 
        """ Reads person's default name, bith event and death event into Person obj.
        """
        with self.driver.session(default_access_mode='READ') as session:
            result = session.run(CypherSource.get_person_lifedata,
                                 pid=person.uniq_id)
            for record in result:
                # <Record
                #    name=<Node id=379934 labels={'Name'} 
                #        properties={'firstname': 'Gustaf', 'type': 'Also Known As', 'suffix': '', 'prefix': '', 
                #            'surname': 'Johansson', 'order': 0}>
                #    events=[
                #        <Node id=492911 labels={'Event'} 
                #            properties={'datetype': 0, 'change': 1577803201, 'description': '', 
                #                'id': 'E7750', 'date2': 1853836, 'type': 'Birth', 'date1': 1853836, 
                #                'uuid': '794e0c9e6f15479cb5d33dc4cf245a7d'}>
                #    ]
                #>
                name_node = record['name']
                person.names.append(Name.from_node(name_node))
                events = record['events']
                for node in events:
                    e = Event.from_node(node)
                    if e.type == "Birth":
                        person.event_birth = e
                    else:
                        person.event_death = e
        return

#   @functools.lru_cache
    def dr_get_surname_list_by_user(self, username, count):
        result_list = []
        with self.driver.session(default_access_mode='READ') as session:
            result = session.run(CypherPerson.get_surname_list_by_username,
                                 username=username, count=count)
            for record in result:
                surname = record['surname']
                count = record['count']
                result_list.append({"surname":surname,"count":count})
        return result_list

#   @functools.lru_cache
    def dr_get_surname_list_common(self, count):
        result_list = []
        with self.driver.session(default_access_mode='READ') as session:
            result = session.run(CypherPerson.get_surname_list_common,
                                 count=count)
            for record in result:
                surname = record['surname']
                count = record['count']
                result_list.append({"surname":surname,"count":count})
        return result_list

    def dr_get_placename_stats_by_user(self, username, count):
        result_list = []
        with self.driver.session(default_access_mode='READ') as session:
            result = session.run(CypherPlaceStats.get_place_list_by_username, 
                                 username=username, count=count)
            for record in result:
                place = record['place']
                placename = place['pname']
                uuid = place['uuid']
                count = record['count']
                result_list.append({"placename":placename,"count":count, "uuid":uuid})
        return result_list

    def dr_get_placename_stats_common(self, count):
        result_list = []
        with self.driver.session(default_access_mode='READ') as session:
            result = session.run(CypherPlaceStats.get_place_list_common,
                                 count=count)
            for record in result:
                place = record['place']
                placename = place['pname']
                uuid = place['uuid']
                count = record['count']
                result_list.append({"placename":placename,"count":count, "uuid":uuid})
        return result_list
