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


    def read_person_names_events(self):
        ''' Read names and events to Person object p.
        '''
        try:
            results = self.session.run(Cypher_person.get_names_events,
                                       uid=self.person.uniq_id)
            for record in results:
                # <Record
                #    rel=<Relationship id=453912
                #        nodes=(
                #            <Node id=261207 labels=set() properties={}>,
                #            <Node id=261208 labels={'Name'}
                #                properties={'firstname': 'Vilhelm Edvard', 'type': 'Also Known As',
                #                    'suffix': '', 'surname': 'Koch', 'prefix': '', 'order': 0}>)
                #        type='NAME' properties={}>
                #    x=<Node id=261208 labels={'Name'}
                #        properties={'firstname': 'Vilhelm Edvard', 'type': 'Also Known As',
                #            'suffix': '', 'surname': 'Koch', 'prefix': '', 'order': 0}>>
                relation = record['rel']
                rel_type = relation.type
                role = relation.get('role', '')
                node = record['x']
                label = list(record['x'].labels)[0]
                #print(f"# -[:{rel_type} {relation._properties}]-> (x:{label})")
                if label == 'Name':
                    x = Name.from_node(node)
                    self.person.names.append(x)
                    self.objs[x.uniq_id] = x
                elif label == 'Event':
                    x = Event_combo.from_node(node)
                    x.role = role
                    self.person.events.append(x)
                    self.objs[x.uniq_id] = x 
                    if x.type == "Cause Of Death":
                        self.person.cause_of_death = x
                print(f"# ({self.person.id}) -[:{rel_type} {role}]-> ({x.uniq_id}:{label} '{x}')")

        except Exception as e:
            print(f"Could not read names and events for person {self.person.uuid}: {e}")
        return


    def read_person_families(self):
        ''' Read the families, where this Person is a member.

            Also return the Family members with their birth event
            and add family events to this person's events.

            (p:Person) <-- (f:Family)
               for f
                 (f) --> (fp:Person) -[*1]-> (fpn:Name)
                 (f) --> (fe:Event)
        '''
        try:
            results = self.session.run(Cypher_person.get_families,
                                       uid=self.person.uniq_id)
            for record in results:
                # <Record
                #  rel=<Relationship id=671269
                #     nodes=(
                #        <Node id=432641 labels={'Family'} 
                #            properties={'datetype': 3, 'father_sortname': 'Järnefelt##August Aleksander', 
                #                'change': 1542401728, 'rel_type': 'Married', 'mother_sortname': 'Clodt von Jürgensburg##Elisabeth', 
                #                'date2': 1941614, 'id': 'F0015', 'date1': 1901974, 'uuid': '90282a3cf6ee47a1b8f9a4a2c710c736'}>, 
                #        <Node id=427799 labels={'Person'} 
                #            properties={'sortname': 'Järnefelt##Aino', 'datetype': 19, 'confidence': '2.0', 
                #                'sex': 2, 'change': 1566323471, 'id': 'I0035', 'date2': 2016423, 'date1': 1916169, 
                #                'uuid': '925ea92d7dab4e8c92b53c1dcbdad36f'}>) 
                #    type='CHILD' 
                #    properties={}> 
                #  family=<Node id=432641 labels={'Family'} properties={...}> 
                #  events=[<Node id=269554 labels={'Event'} properties={'type': 'Marriage', ...}> ...]
                #  members=[[
                #    <Relationship ...  type='CHILD' ...>, 
                #    <Node ... labels={'Person'}...>, 
                #    <Node ... labels={'Name'}...>, 
                #    <Node ... labels={'Event'}...]
                #    ...]>

                # 1. What is the relation this Person to their Family

                relation = record['rel']
                rel_type = relation.type
                role = relation.get('role', "")

                # 2. The Family node

                node = record['family']
                family = Family_combo.from_node(node)
                family.role = rel_type
                family.marriage_dates = ""  # string "" or a DataRange
                if rel_type == "CHILD":
                    self.person.families_as_child.append(family)
                elif rel_type == "PARENT":
                    self.person.families_as_parent.append(family)
                print(f"# ({self.person.id}) -[:{rel_type} {role}]-> (:Family '{family}')")

                # 3. Family Events
                #TODO: Cause of death is not displayed!

                for event_node in record['events']:
                    f_event = Event_combo.from_node(event_node)
                    #print(f"#\tevent {f_event}")
                    if f_event.type == "Marriage":
                        family.marriage_dates = f_event.dates
                    # Add family events to person events, too
                    if rel_type == "PARENT":
                        f_event.role = "Family"
                        print(f"# ({self.person.id}) -[:EVENT {f_event.role}]-> (:Event '{f_event}')")
                        self.person.events.append(f_event)
                        # Add Event to list of those events, who's Citation etc
                        # references must be checked
                        if not f_event.uniq_id in self.objs.keys():
                            self.objs[f_event.uniq_id] = f_event

                # 4. Family members and their birth events

                for relation, member_node, name_node, event_node in record['members']:
                    # relation = <Relationship
                    #    id=671263 
                    #    nodes=(
                    #        <Node id=432641 labels={'Family'} properties={'rel_type': 'Married', ...}>, 
                    #        <Node id=428883 labels={'Person'} properties={'sortname': 'Järnefelt##Caspar Woldemar', ...}>)
                    #    type='CHILD' 
                    #    properties={}>
                    # member_node = <Node id=428883 labels={'Person'} properties={'sortname': 'Järnefelt##Caspar Woldemar', ... }>
                    # name_node = <Node id=428884 labels={'Name'} properties={'firstname': 'Caspar Woldemar' ...}>
                    # event_node = <Node id=267935 labels={'Event'} properties={'type': 'Birth', ... }>
                    role = relation['role']
                    member = Person_combo.from_node(member_node)
                    if name_node:
                        name = Name.from_node(name_node)
                        member.names.append(name)
                    else:
                        name = None
                    if event_node:
                        event = Event_combo.from_node(event_node)
                        member.birth_date = event.dates
                    else:
                        event = None

#                     if rel_type == "CHILD":
#                         print(f"#  parent's family ({relation.start}) -[:CHILD {relation._properties}]-> ({relation.end}) {member} {name} {event}")
#                     elif rel_type == "PARENT":
#                         print(f"#  own family ({relation.start}) -[:PARENT {relation._properties}]-> ({relation.end}) {member} {name} {event}")

                    if role == "father":
                        family.father = member
                    elif role == "mother":
                        family.mother = member
                    else:
                        family.children.append(member)
                    pass

        except Exception as e:
            print(f"Could not read families for person {self.person.uuid}: {e}")
        return


    def read_object_places(self):
        ''' Read Place hierarchies for all objects in objs.
        '''
        try:
            uids = list(self.objs.keys())
            results = self.session.run(Cypher_person.get_places,
                                       uid_list=uids)
            for record in results:
                # <Record label='Event' uniq_id=426916 
                #    pl=<Node id=306042 labels={'Place'}
                #        properties={'id': 'P0456', 'type': 'Parish', 'uuid': '7aeb4e26754d46d0aacfd80910fa1bb1',
                #            'pname': 'Helsingin seurakunnat', 'change': 1543867969}> 
                #    pnames=[
                #        <Node id=306043 labels={'Place_name'}
                #            properties={'name': 'Helsingin seurakunnat', 'lang': ''}>, 
                #        <Node id=306043 labels={'Place_name'} 
                #            properties={'name': 'Helsingin seurakunnat', 'lang': ''}>
                #    ]
                ##    ri=<Relationship id=631695 
                ##        nodes=(
                ##            <Node id=306042 labels={'Place'} properties={'id': 'P0456', ...>, 
                ##            <Node id=307637 labels={'Place'} 
                ##                properties={'coord': [60.16664166666666, 24.94353611111111], 
                ##                    'id': 'P0366', 'type': 'City', 'uuid': '93c25330a25f4fa49c1efffd7f4e941b', 
                ##                    'pname': 'Helsinki', 'change': 1556954884}>
                ##        )
                ##        type='IS_INSIDE' properties={}> 
                #    pi=<Node id=307637 labels={'Place'} 
                #        properties={'coord': [60.16664166666666, 24.94353611111111], 'id': 'P0366', 
                #            'type': 'City', 'uuid': '93c25330a25f4fa49c1efffd7f4e941b', 'pname': 'Helsinki', 'change': 1556954884}> 
                #    pinames=[
                #        <Node id=305800 labels={'Place_name'} properties={'name': 'Helsingfors', 'lang': ''}>, 
                #        <Node id=305799 labels={'Place_name'} properties={'name': 'Helsinki', 'lang': 'sv'}>
                #    ]>

                src_label = record['label']
                if src_label != "Event":
                    traceback.print_exc()
                    raise TypeError(f'An Event excepted, got {src_label}')
                src_uniq_id = record['uniq_id']
                src = None

                # Use the Event from Person events
                for e in self.person.events:
                    if e.uniq_id == src_uniq_id:
                        src = e
                        break
                if not src:
                    traceback.print_exc()
                    raise LookupError(f"ERROR: Unknown Event {src_uniq_id}!?")

                pl = PlaceBl.from_node(record['pl'])
                if not pl.uniq_id in self.objs.keys():
                    # A new place
                    self.objs[pl.uniq_id] = pl
                    #print(f"# new place (x:{src_label} {src.uniq_id} {src}) --> (pl:Place {pl.uniq_id} type:{pl.type})")
                    pl.names = place_names_from_nodes(record['pnames'])
                #else:
                #   print(f"# A known place (x:{src_label} {src.uniq_id} {src}) --> ({list(record['pl'].labels)[0]} {objs[pl.uniq_id]})")
                src.place_ref.append(pl.uniq_id)

                # Surrounding places
                if record['pi']:
                    pl_in = PlaceBl.from_node(record['pi'])
                    ##print(f"# Hierarchy ({pl}) -[:IS_INSIDE]-> (pi:Place {pl_in})")
                    if pl_in.uniq_id in self.objs:
                        pl.uppers.append(self.objs[pl_in.uniq_id])
                        ##print(f"# - Using a known place {objs[pl_in.uniq_id]}")
                    else:
                        pl.uppers.append(pl_in)
                        self.objs[pl_in.uniq_id] = pl_in
                        pl_in.names = place_names_from_nodes(record['pinames'])
                        #print(f"#  ({pl_in} names {pl_in.names})")
                pass

        except Exception as e:
            print(f"Could not read places for person {self.person.id} objects {self.objs}: {e}")
        return


    def read_object_citation_note_media(self, active_objs=[]):
        ''' Read Citations, Notes, Medias for list of objects.

                (x) -[r:CITATION|NOTE|MEDIA]-> (y)

            Returns a list of created new objects, where this search should
            be repeated.
        '''
        new_objs = []

        try:
            if active_objs and active_objs[0] > 0:
                # Search next level destinations x) -[r:CITATION|NOTE|MEDIA]-> (y)
                uids = active_objs
            else:
                # Search all (x) -[r:CITATION|NOTE|MEDIA]-> (y)
                uids = list(self.objs.keys())
            print(f'# --- Search Citations, Notes, Medias for {uids}')

            results = self.session.run(Cypher_person.get_citation_note_media,
                                       uid_list=uids)
            for record in results:
                # <Record label='Person' uniq_id=327766
                #    r=<Relationship id=426799
                #        nodes=(
                #            <Node id=327766 labels=set() properties={}>, 
                #            <Node id=327770 labels={'Note'}
                #                properties={'text': 'Nekrologi HS 4.7.1922 s. 4', 
                #                    'id': 'N2-I0033', 'type': 'Web Search', 'uuid': '14a26a62a6b446339b971c7a54941ed4', 
                #                    'url': 'https://nakoislehti.hs.fi/e7df520d-d47d-497d-a8a0-a6eb3c00d0b5/4', 'change': 0}>
                #        ) 
                #        type='NOTE' properties={}>
                #    y=<Node id=327770 labels={'Note'}
                #            properties={'text': 'Nekrologi HS 4.7.1922 s. 4', 'id': 'N2-I0033', 
                #                'type': 'Web Search', 'uuid': '14a26a62a6b446339b971c7a54941ed4', 
                #                'url': 'https://nakoislehti.hs.fi/e7df520d-d47d-497d-a8a0-a6eb3c00d0b5/4', 'change': 0}
                # >    >

                # The existing object x
                x_label = record['label']
                x = self.objs[record['uniq_id']]

                # Relation r between (x) --> (y)
                rel = record['r']
                #rel_type = rel.type
                #rel_properties = 

                # Target y is a Citation, Note or Media
                y_node = record['y']    # 
                y_label = list(y_node.labels)[0]
                y_uniq_id = y_node.id
                #print(f'# Linking ({x.uniq_id}:{x_label} {x}) --> ({y_uniq_id}:{y_label})')
                #for k, v in rel._properties.items(): print(f"#\trel.{k}: {v}")
                if y_label == "Citation":
                    o = self.objs.get(y_uniq_id, None)
                    if not o:
                        o = Citation.from_node(y_node)
                        if not x.uniq_id in o.citators:
                            # This citation is referenced by x
                            o.citators.append(x.uniq_id)
                        # The list of Citations, for further reference search
                        self.citations[o.uniq_id] = o
                        self.objs[o.uniq_id] = o
                        new_objs.append(o.uniq_id)
                    # Store reference to referee object
                    if hasattr(x, 'citation_ref'):
                        x.citation_ref.append(o.uniq_id)
                    else:
                        traceback.print_exc()
                        raise LookupError(f'Error: No field for {x_label}.{y_label.lower()}_ref')            
                    #print(f'# ({x_label}:{x.uniq_id}) --> (Citation:{o.id})')

                elif y_label == "Note":
                    o = self.objs.get(y_uniq_id, None)
                    if not o:
                        o = Note.from_node(y_node)
                        self.objs[o.uniq_id] = o
                        new_objs.append(o.uniq_id)
                    # Store reference to referee object
                    if hasattr(x, 'note_ref'):
                        x.note_ref.append(o.uniq_id)
                    else:
                        traceback.print_exc()
                        raise LookupError(f'Error: No field for {x_label}.{y_label.lower()}_ref')            

                elif y_label == "Media":
                    o = self.objs.get(y_uniq_id, None)
                    if not o:
                        o = Media.from_node(y_node)
                        self.objs[o.uniq_id] = o
                        new_objs.append(o.uniq_id)
                    # Get relation properties
                    order = rel.get('order')
                    # Store reference to referee object
                    if hasattr(x, 'media_ref'):
                        # Add media reference crop attributes
                        left = rel.get('left')
                        if left != None:
                            upper = rel.get('upper')
                            right = rel.get('right')
                            lower = rel.get('lower')
                            crop = (left, upper, right, lower)
                        else:
                            crop = None
                        print(f'#\tMedia ref {o.uniq_id} order={order}, crop={crop}')
                        x.media_ref.append((o.uniq_id,crop,order))
                    else:
                        print(f'Error: No field for {x_label}.{y_label.lower()}_ref')            
                    #print(f'# ({x_label}:{x.uniq_id} {x}) --> ({y_label}:{o.id})')

                else:
                    traceback.print_exc()
                    raise NotImplementedError(f'No rule for ({x_label}) --> ({y_label})')            
                #print(f'# ({x_label}:{x}) --> ({y_label}:{o.id})')
                if hasattr(x, 'media_ref'):
                    x.media_ref.sort(key=lambda x: x[2])

        except Exception as e:
            traceback.print_exc()
            print(f"Could not read 'Citations, Notes, Medias': {e}")
            print(f"... for Person {self.person.uuid} objects {self.objs}: {e}")
        return new_objs

    def remove_privacy_limit_from_family(self, family):
        if family.father: family.father.too_new = False
        if family.mother: family.mother.too_new = False
        for c in family.children:
            c.too_new = False

    def remove_privacy_limit_from_families(self):
        for family in self.person.families_as_child:
            self.remove_privacy_limit_from_family(family)
        for family in self.person.families_as_parent:
            self.remove_privacy_limit_from_family(family)
            
    
    
    