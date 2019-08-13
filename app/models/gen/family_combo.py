'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''
#from sys import stderr
import  shareds

from .cypher import Cypher_family
from .family import Family
from .person_combo import Person_combo, Person_as_member
from .event_combo import Event_combo
from .person_name import Name
from .note import Note
from models.gen.dates import DateRange
from models.gen.place_combo import Place_combo


class Family_combo(Family):
    """ Perhe
            
        Properties:
                handle          
                change
                id              esim. "F0001"
                uniq_id         int database key
                rel_type        str suhteen tyyppi
                father          Person isä (isän osoite?)
                mother          Person äiti (äidin osoite?)
                children[]      [Person,] lapset (lasten osoitteet?)
            #TODO: Obsolete properties?
                eventref_hlink  str tapahtuman osoite
                eventref_role   str tapahtuman rooli
                childref_hlink  str lapsen osoite
                noteref_hlink   str lisätiedon osoite
     """

    def __init__(self, uniq_id=None):
        """ Creates a Family instance for carrying whole family information. 
        """
        Family.__init__(self, uniq_id)

        self.father = None
        self.mother = None
        self.children = []      # Child object
        self.events = []        # Event objects
        self.notes = []
        self.sources = []
        self.note_ref = []      # For a page, where same note may be referenced
                                # from multiple events and other objects

        #TODO Obsolete parameters???
        self.eventref_hlink = []
        self.eventref_role = []
        self.childref_hlink = []    # handles
        self.noteref_hlink = []


    @staticmethod
    def get_family_paths_apoc(uniq_id):
        ''' Read a person and paths for all connected nodes.
        
            Experimental!
        '''
        all_nodes_query_w_apoc="""
MATCH (f:Family) WHERE id(f) = $fid
CALL apoc.path.subgraphAll(f, {maxLevel:2, relationshipFilter: 
        'CHILD>|PARENT>|EVENT>|NAME>|PLACE>|CITATION>|SOURCE>|NOTE>|HIERARCHY>'}) YIELD nodes, relationships
RETURN extract(x IN relationships | 
        [id(startnode(x)), type(x), x.role, id(endnode(x))]) as relations,
        extract(x in nodes | x) as nodelist"""
        return  shareds.driver.session().run(all_nodes_query_w_apoc, fid=uniq_id)


    def get_children_by_id(self):
        """ Luetaan perheen lasten tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)-[r:CHILD]->(person:Person)
  WHERE ID(family)=$pid
RETURN ID(person) AS children"""
        return  shareds.driver.session().run(query, {"pid": pid})


    def get_family_events(self):
        """ Luetaan perheen tapahtumien tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)-[r:EVENT]->(event:Event)
  WHERE ID(family)=$pid
RETURN r.role AS eventref_role, event.handle AS eventref_hlink"""
        return  shareds.driver.session().run(query, {"pid": pid})
    
    
    def get_family_data_by_id(self):
        """ Luetaan perheen tiedot.
        
            Called from models.datareader.get_families_data_by_id 
        """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)
  WHERE ID(family)=$pid
RETURN family"""
        family_result = shareds.driver.session().run(query, {"pid": pid})
        
        for family_record in family_result:
            family = family_record["family"]
            self.change = family['change']
            self.id = family['id']
            self.rel_type = family['rel_type']
            
            self.father_sortname = family['father_sortname']
            self.mother_sortname = family['mother_sortname']
            datetype = family['datetype']
            date1 = family['date1']
            date2 = family['date2']
            if datetype != None:
                self.marriage_date = DateRange(datetype, date1, date2)
            
        father_result = self.get_parent_by_id('father')
        for father_record in father_result:            
            self.father = father_record["father"]

        mother_result = self.get_parent_by_id('mother')
        for mother_record in mother_result:            
            self.mother = mother_record["father"]

        event_result = self.get_family_events()
        for event_record in event_result:            
            self.eventref_hlink.append(event_record["eventref_hlink"])
            self.eventref_role.append(event_record["eventref_role"])

        children_result = self.get_children_by_id()
        for children_record in children_result:            
            self.childref_hlink.append(children_record["children"])
            
        return True
    
    
    @staticmethod
    def get_family_data(uniq_id):
        """ Read Family information including Events, Children, Notes and Sources.
        
            1) read 
                (f:Family) --> (e:Event)
                (f:Family) -[:PARENT]-> (pp:Person) -> (np:Name)
                (f:Family) -[:CHILD]->  (pc:Person) -> (nc:Name)
                (f:Family) --> (fn:Note)
                (e:Event) --> (en:Note)
                (f:Family) --> (fac:Citation) --> (fas:Source) --> (far:Repository)
                (e:Event) --> (evc:Citation) --> (evs:Source) --> (evr:Repository)
╒═══════════════╤═══════════════╤═══════════════╤═══════════════╤═══════════════╤═══════╕
│"family"       │"events"       │"parents"      │"children"     │"sources"      │"notes"│
╞═══════════════╪═══════════════╪═══════════════╪═══════════════╪═══════════════╪═══════╡
│family         │[event, fep]   │[r.role, parent│[child, cn, ce]│[ID(event), re,│[note] │
│               │               │, pn, pe]      │               │s, c]          │       │
└───────────────┴───────────────┴───────────────┴───────────────┴───────────────┴───────┘
 
            2) read
                (pp:Person) --> (ppe:Event) --> (:Place)
                (pc:Person) --> (pce:Event) --> (:Place)

            3) build
                Family_combo.mother, .names, event_birth, event_death
                Family_combo.father, .names, event_birth, event_death
                Family_combo.events
                Family_combo.notes
                Family_combo.sources / citation -> source -> repocitory ?
                Family_combo.children, .names, event_birth, event_death
            Returns a Family object with other objects included
        """

        def set_birth_death(person, birth_node, death_node):
            '''
            Set person.birth and person.death events from db nodes
            '''
            if birth_node:
                person.event_birth = Event_combo.from_node(birth_node)
            if death_node:
                person.event_death = Event_combo.from_node(death_node)


        family = None

        with shareds.driver.session() as session:
            try:
                result = session.run(Cypher_family.get_family_data, 
                                     pid=uniq_id)
                for record in result:
                    if record['f']:
                        # <Node id=272710 labels={'Family'} 
                        #    properties={'father_sortname': '#Andersson#Anders', 
                        #        'change': 1519839324, 'rel_type': 'Married', 'handle': '_dcf94f357ea7b126cd8277f4495', 
                        #        'id': 'F0268', 'mother_sortname': 'Gröndahl#Juhantytär#Fredrika', 
                        #        'datetype': 3, 'date2': 1878089, 'date1': 1875043}>
                        node = record['f']
                        family = Family_combo.from_node(node)

                        for event_node, place_node in record['family_event']:
                            if event_node:
                                # event_node:
                                # <Node id=242570 labels={'Event'} 
                                #    properties={'datetype': 0, 'change': 1528183878, 'description': '', 
                                #        'handle': '_dcf94f35ea262b7e1a0a0066d6e', 'id': 'E1692', 
                                #        'date2': 1875043, 'type': 'Marriage', 'date1': 1875043}>
                                e = Event_combo.from_node(event_node)
                                if place_node:
                                    # place_node:
                                    # <Node id=251746 labels={'Place'} 
                                    #    properties={'coord': [60.5625, 21.609722222222224], 'handle': '_dc388cd23f634d21dbce8ea8775', 
                                    #        'id': 'P0468', 'type': 'City', 'pname': 'Taivassalo', 
                                    #        'change': 1556953682}>
                                    e.place = Place_combo.from_node(place_node)

                                family.events.append(e)
        
                        uniq_id = -1
                        
                        for role, person_node, name_node, birth_node, death_node in record['parent']:
                            # ['mother', 
                            #    <Node id=235105 labels={'Person'} 
                            #        properties={'sortname': 'Gröndahl#Juhantytär#Fredrika', 'datetype': 19, 
                            #            'confidence': '2.0', 'sex': 2, 'change': 1536161195, 
                            #            'handle': '_dcf94f357d9f565664a975f99f', 'id': 'I2475', 
                            #            'date2': 1937706, 'date1': 1856517}>, 
                            #    <Node id=235106 labels={'Name'} 
                            #        properties={'firstname': 'Fredrika', 'type': 'Married Name', 
                            #            'suffix': 'Juhantytär', 'prefix': '', 'surname': 'Gröndahl', 'order': 0}>, 
                            #    <Node id=242532 labels={'Event'} 
                            #        properties={'datetype': 0, 'change': 1519151217, 'description': '', 
                            #            'handle': '_dcf94f357db6f3c846e6472915f', 'id': 'E1531', 
                            #            'date2': 1856517, 'type': 'Birth', 'date1': 1856517}>, 
                            #    <Node id=242536 labels={'Event'} 
                            #        properties={'datetype': 0, 'change': 1519150640, 'description': '', 
                            #            'handle': '_dcf94f357e2d61f5f76e1ba7cb', 'id': 'E1532', 
                            #            'date2': 1937700, 'type': 'Death', 'date1': 1937700}>
                            # ]
                            if person_node:
                                if uniq_id != person_node.id:
                                    # Skip person with double default name
                                    p = Person_combo.from_node(person_node)
                                    p.role = role
                                    if name_node:
                                        p.names.append(Name.from_node(name_node))

                                    set_birth_death(p, birth_node, death_node)

                                    if role == 'father':
                                        family.father = p
                                    elif role == 'mother':
                                        family.mother = p
                        
                        for person_node, name_node, birth_node, death_node in record['child']:
                            # record['child'][0]:
                            # [<Node id=235176 labels={'Person'} 
                            #    properties={'sortname': '#Andersdotter#Maria Christina', 
                            #        'datetype': 19, 'confidence': '2.0', 'sex': 2, 'change': 1532009600, 
                            #        'handle': '_dd2a65b2f8c7e05bc664bd49d54', 'id': 'I0781', 'date2': 1877226, 'date1': 1877219}>, 
                            #  <Node id=235177 labels={'Name'} 
                            #    properties={'firstname': 'Maria Christina', 'type': 'Birth Name', 'suffix': 'Andersdotter', 
                            #        'prefix': '', 'surname': '', 'order': 0}>, 
                            #  <Node id=242697 labels={'Event'} 
                            #    properties={'datetype': 0, 'change': 1532009545, 'description': '', 'handle': '_dd2a65b218a14e81692d77955d2', 
                            #        'id': 'E1886', 'date2': 1877219, 'type': 'Birth', 'date1': 1877219}>, 
                            #  <Node id=242702 labels={'Event'} 
                            #    properties={'datetype': 0, 'change': 1519916327, 'description': '', 'handle': '_dd2a65b218a4e85ab141faeab48', 
                            #        'id': 'E1887', 'date2': 1877226, 'type': 'Death', 'date1': 1877226}>
                            # ]
                            if person_node:
                                p = Person_combo.from_node(person_node)
                                if name_node:
                                    p.names.append(Name.from_node(name_node))
                                set_birth_death(p, birth_node, death_node)
                                family.children.append(p)
                        
                        family.no_of_children = len(family.children)
                            
                        for repository_node, source_node, citation_node in record['sources']:
                            # record['sources'][0]:
                            # [<Node id=253027 labels={'Repository'} 
                            #    properties={'handle': '_dcad22f5914b34fe61c341dad0', 'id': 'R0068', 'rname': 'Taivassalon seurakunnan arkisto', 
                            #        'type': 'Archive', 'change': '1546265916'}>, 
                            #  <Node id=247578 labels={'Source'} 
                            #    properties={'handle': '_e085cd6d68d256a94afecd2162d', 'id': 'S1418', 
                            #        'stitle': 'Taivassalon seurakunnan syntyneiden ja kastettujen luettelot 1790-1850 (I C:4)', 
                            #        'change': '1543186596'}>, 
                            #  <Node id=246371 labels={'Citation'} 
                            #    properties={'handle': '_dd12b0b88d5741ee11d8bef1ca5', 'id': 'C0854', 'page': 'Vigde år 1831 April 4', 
                            #        'dateval': '', 'change': 1543186596, 'confidence': '2'}>
                            # ]
                            if repository_node:
                                rname = repository_node['rname']
                                s_pid = source_node.id
                                stitle = source_node['stitle']
                                sauthor = source_node['sauthor']
                                spubinfo = source_node['spubinfo']
                                page = citation_node['page']
                                family.sources.append([rname, s_pid, stitle, sauthor, spubinfo, page])
                            
                        for n in record['note']:
                            note = Note()
                            note.uniq_id = n.id
                            note.type = n['type']
                            note.text = n['text']
                            note.url = n['url']
                            family.notes.append(note)
            
            except Exception as e:
                print('Error get_family_data: {} {}'.format(e.__class__.__name__, e))            
                raise      
    
        return family

    
    @staticmethod           
    def get_dates_parents(tx, uniq_id):
        return tx.run(Cypher_family.get_dates_parents,id=uniq_id)

    @staticmethod           
    def set_dates_sortnames(tx, uniq_id, dates, father_sortname, mother_sortname):
        ''' Update Family dates and parents' sortnames.
        '''
        f_attr = {
            "father_sortname": father_sortname,
            "mother_sortname": mother_sortname
        }
        f_attr.update(dates.for_db())

        return tx.run(Cypher_family.set_dates_sortname, 
                      id=uniq_id, f_attr=f_attr)


    @staticmethod       
    def get_families(o_filter, opt='father', limit=100):
        """ Find families from the database """
        
        def _read_family_list(o_filter, opt, limit):
            """ Read Family data from given fw/fwm
            """
            # Select a) filter by user b) show Isotammi common data (too)
            show_by_owner = o_filter.use_owner_filter()
            show_with_common = o_filter.use_common()
            #print("read_my_persons_list: by owner={}, with common={}".format(show_by_owner, show_with_common))
            user = o_filter.user
            try:
                """
                               show_by_owner    show_all
                            +-------------------------------
                with common |  me + common      common
                no common   |  me                -
                """
                with shareds.driver.session() as session:
                    if show_by_owner:

                        if show_with_common: 
                            if opt == 'father':
                                #1 get all with owner name for all
                                print("_read_families_p: by owner with common")
                                result = session.run(Cypher_family.read_families_p,
                                                     fw=fw, limit=limit)
                            elif opt == 'mother':
                                #1 get all with owner name for all
                                print("_read_families_m: by owner with common")
                                result = session.run(Cypher_family.read_families_m,
                                                     fwm=fw, limit=limit)
                        else: 
                            if opt == 'father':
                                #2 get my own (no owner name needed)
                                print("_read_families_p: by owner only")
                                result = session.run(Cypher_family.read_my_families_p,
                                                     user=user, fw=fw, limit=limit)
                            elif opt == 'mother':
                                #1 get all with owner name for all
                                print("_read_families_m: by owner only")
                                result = session.run(Cypher_family.read_my_families_m,
                                                     user=user, fwm=fw, limit=limit)

                    else: 
                        if opt == 'father':
                            #3 == #1 simulates common by reading all
                            print("_read_families_p: common only")
                            result = session.run(Cypher_family.read_families_p, #user=user, 
                                                 fw=fw, limit=limit)
                        elif opt == 'mother':
                            #1 get all with owner name for all
                            print("_read_families_m: common only")
                            result = session.run(Cypher_family.read_families_m,
                                                 fwm=fw, limit=limit)
                        
                    return result
            except Exception as e:
                print('Error _read_families_p: {} {}'.format(e.__class__.__name__, e))            
                raise      
                
        families = []
        fw = o_filter.next_name_fw()     # next name

        ustr = "user " + o_filter.user if o_filter.user else "no user"
        print(f"read_my_family_list: Get max {limit} persons "
              f"for {ustr} starting at {fw!r}")
        result = _read_family_list(o_filter, opt, limit)
        
        for record in result:
            if record['f']:
                # <Node id=55577 labels={'Family'} 
                #    properties={'rel_type': 'Married', 'handle': '_d78e9a206e0772ede0d', 
                #    'id': 'F0000', 'change': 1507492602}>
                f_node = record['f']
                family = Family_combo(f_node.id)
                family.id = f_node['id']
                family.type = f_node['rel_type']
                family.father_sortname = f_node['father_sortname']
                family.mother_sortname = f_node['mother_sortname']
                datetype = f_node['datetype']
                date1 = f_node['date1']
                date2 = f_node['date2']
                if datetype != None:
                    family.marriage_date = DateRange(datetype, date1, date2)
                family.marriage_place = record['marriage_place']

                uniq_id = -1
                for role, parent_node, name_node in record['parent']:
                    if parent_node:
                        # <Node id=214500 labels={'Person'} 
                        #    properties={'sortname': 'Airola#ent. Silius#Kalle Kustaa', 
                        #    'datetype': 19, 'confidence': '2.7', 'change': 1504606496, 
                        #    'sex': 0, 'handle': '_ce373c1941d452bd5eb', 'id': 'I0008', 
                        #    'date2': 1997946, 'date1': 1929380}>
                        if uniq_id != parent_node.id:
                            # Skip person with double default name
                            pp = Person_as_member()
                            uniq_id = parent_node.id
                            pp.uniq_id = uniq_id
                            pp.sortname = parent_node['sortname']
                            pp.sex = parent_node['sex']
                            if role == 'father':
                                family.father = pp
                            elif role == 'mother':
                                family.mother = pp

                        pname = Name.from_node(name_node)
                        pp.names.append(pname)

                
                for ch in record['child']:
                    # <Node id=60320 labels={'Person'} 
                    #    properties={'sortname': '#Björnsson#Simon', 'datetype': 19, 
                    #    'confidence': '', 'sex': 0, 'change': 1507492602, 
                    #    'handle': '_d78e9a2696000bfd2e0', 'id': 'I0001', 
                    #    'date2': 1609920, 'date1': 1609920}>
                    child = Person_as_member()
                    child.uniq_id = ch.id
                    child.sortname = ch['sortname']
                    family.children.append(child)
                
                if record['no_of_children']:
                    family.no_of_children = record['no_of_children']
                families.append(family)
                
        # Update the page scope according to items really found 
        if families:
            if opt == 'father':
                o_filter.update_session_scope('person_scope', 
                                              families[0].father_sortname, families[-1].father_sortname, 
                                              limit, len(families))
            else:
                o_filter.update_session_scope('person_scope', 
                                              families[0].mother_sortname, families[-1].mother_sortname, 
                                              limit, len(families))

        return (families)

    
#     @staticmethod       
#     def get_all_families():
#         """ Find all families from the database - not in use!
#         """
#         
#         query = """
# MATCH (f:Family)
# OPTIONAL MATCH (f)-[:FATHER]->(ph:Person)-[:NAME]->(nh:Name) 
# OPTIONAL MATCH (f)-[:MOTHER]-(pw:Person)-[:NAME]->(nw:Name) 
# OPTIONAL MATCH (f)-[:CHILD]-(pc:Person) 
# RETURN f, ph, nh, pw, nw, COUNT(pc) AS child ORDER BY ID(f)"""
#         result = shareds.driver.session().run(query)
#                 
#         families = []
#         for record in result:
#             if record['f']:
#                 f = record['f']
#                 family = Family_combo(f.id)
#                 family.type = f['rel_type']
#             
#                 if record['ph']:
#                     husband = record['ph']
#                     ph = Person_as_member()
#                     ph.uniq_id = husband.id
#                     
#                     if record['nh']:
#                         hname = record['nh']
#                         ph.names.append(hname)
#                     family.father = ph
#                 
#                 if record['pw']:
#                     wife = record['pw']
#                     pw = Person_as_member()
#                     pw.uniq_id = wife.id
#                     
#                     if record['nw']:
#                         wname = record['nw']
#                         pw.names.append(wname)
#                     family.mother = pw
#                 
#                 if record['child']:
#                     c = record['child']
#                     family.no_of_children = c
#                 families.append(family)
#         return (families)
    
#     @staticmethod       
#     def get_own_families(user=None):
#         """ Find all families from the database - not in use!
#         """
#         
#         query = """
# MATCH (prof:UserProfile)-[:HAS_LOADED]->(batch:Batch)-[:OWNS]->(f:Family) WHERE prof.username=$user 
# OPTIONAL MATCH (f)-[:FATHER]->(ph:Person)-[:NAME]->(nh:Name)  
# OPTIONAL MATCH (f)-[:MOTHER]-(pw:Person)-[:NAME]->(nw:Name) 
# OPTIONAL MATCH (f)-[:CHILD]-(pc:Person) 
# WITH f, pc, pw, nw.surname AS wsn, nw.suffix AS wx, nw.firstname AS wfn, 
#    ph, nh.surname AS hsn, nh.firstname AS hfn, nh.suffix AS hx 
# RETURN ID(f) AS uniq_id, f.rel_type AS type, 
#    ID(ph) AS hid, hsn, hx, hfn, 
#    ID(pw) AS wid, wsn, wx, wfn, 
#    COUNT(pc) AS child ORDER BY hsn, hfn"""
#         result = shareds.driver.session().run(query, {"user":user})
#                 
#         families = []
#         for record in result:
#             family = []
#             data = []
#             if record['uniq_id']:
#                 data.append(record['uniq_id'])
#             if record['type']:
#                 data.append(record['type'])
#             else:
#                 data.append("-")
#             if record['child']:
#                 data.append(record['child'])
#             else:
#                 data.append("-")
#             family.append(data)
#             
#             father = []
#             if record['hid']:
#                 father.append(record['hid'])
#             else:
#                 father.append("-")
#             if record['hsn']:
#                 father.append(record['hsn'])
#             else:
#                 father.append("-")
#             if record['hx']:
#                 father.append(record['hx'])
#             else:
#                 father.append("-")
#             if record['hfn']:
#                 father.append(record['hfn'])
#             else:
#                 father.append("-")
#             family.append(father)
#             
#             mother = []
#             if record['wid']:
#                 mother.append(record['wid'])
#             else:
#                 mother.append("-")
#             if record['wsn']:
#                 mother.append(record['wsn'])
#             else:
#                 mother.append("-")
#             if record['wx']:
#                 mother.append(record['wx'])
#             else:
#                 mother.append("-")
#             if record['wfn']:
#                 mother.append(record['wfn'])
#             else:
#                 mother.append("-")
#             family.append(mother)
#             families.append(family)
#         
#         return (families)


#     @staticmethod       
#     def get_marriage_parent_names(event_uniq_id):
#         """ Find the parents and all their names - not in use!
# 
#             Called from models.datareader.get_source_with_events
#             #TODO Use [:PARENT] link
#         
#             Returns a dictionary like 
#             {'FATHER': (77654, 'Mattias Abrahamsson  • Matts  Lindlöf'), ...}
# 
# ╒════════╤═════╤═══════════════════════════════════════════════════╕
# │"frole" │"pid"│"names"                                            │
# ╞════════╪═════╪═══════════════════════════════════════════════════╡
# │"FATHER"│73538│[{"alt":"","firstname":"Carl","type":"Birth Name","│
# │        │     │suffix":"","surname":"Forstén"}]                   │
# ├────────┼─────┼───────────────────────────────────────────────────┤
# │"MOTHER"│73540│[{"alt":"","firstname":"Catharina Margareta","type"│
# │        │     │:"Birth Name","suffix":"","surname":"Stenfeldt"},{"│
# │        │     │alt":"1","firstname":"Catharina Margareta","type":"│
# │        │     │Also Known As","suffix":"","surname":"Forstén"}]   │
# └────────┴─────┴───────────────────────────────────────────────────┘
#         """
#                         
#         result = shareds.driver.session().run(Cypher_family.get_wedding_couple_names, 
#                                               eid=event_uniq_id)
#         namedict = {}
#         for record in result:
#             role = record['frole']
# #             pid = record['pid']
#             names = []
#             for name in record['names']:
#                 fn = name['firstname']
#                 sn = name['surname']
#                 pn = name['suffix']
#                 names.append("{} {} {}".format(fn, pn, sn))
#             namedict[role] = ' • '.join(names)
#         return namedict


    def get_parent_by_id(self, role='father'):
        """ Luetaan perheen isän (tai äidin) tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family) -[r:PARENT]-> (person:Person)
  WHERE ID(family)=$pid and r.role = $role
RETURN ID(person) AS father"""
        return  shareds.driver.session().run(query, pid=pid, role=role)


#     def get_mother_by_id(self):
#         """ Luetaan perheen äidin tiedot """
#         return self.get_parent_by_id(self, role='mother')
        
    
    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Family*****")
        print ("Handle: " + self.handle)
        print ("Change: {}".format(self.change))
        print ("Id: " + self.id)
        print ("Rel: " + self.rel_type)
        print ("Father: " + self.father)
        print ("Mother: " + self.mother)
        if len(self.eventref_hlink) > 0:
            for i in range(len(self.eventref_hlink)):
                print ("Eventref_hlink: " + self.eventref_hlink[i])
        if len(self.eventref_role) > 0:
            for i in range(len(self.eventref_role)):
                print ("Role: " + self.eventref_role[i])
        if len(self.childref_hlink) > 0:
            for i in range(len(self.childref_hlink)):
                print ("Childref_hlink: " + self.childref_hlink[i])
        return True


#    @staticmethod       
#     def get_person_families_w_members(uid):
#         ''' NOT IN USE!
#             Finds all Families, where Person uid belongs to
#             and return them as a Families list
#         '''
# # ╒═══════╤══════════╤════════╤═════════════════════╤═════════════════════╕
# # │"f_id" │"rel_type"│"myrole"│"members"            │"names"              │
# # ╞═══════╪══════════╪════════╪═════════════════════╪═════════════════════╡
# # │"F0000"│"Married" │"FATHER"│[[72533,"CHILD",     │[[72533,             │
# # │       │          │        │  "CHILD",{"han      │  {"alt":"","fi      │
# # │       │          │        │dle":"_dd2c613026e752│rstname":"Jan Erik","│
# # │       │          │        │8c1a21f78da8a","id":"│type":"Birth Name","s│
# # │       │          │        │I0000","priv":"","gen│uffix":"Jansson","sur│
# # │       │          │        │der":"M","confidence"│name":"Mannerheim","r│
# # │       │          │        │:"2.0","change":15363│efname":""},{}],     │
# # │       │          │        │24580}],             │ [72537,             │
# # │       │          │        │ [72537,"MOTHER",    │{"alt":"1","firstname│
# # │       │          │        │{"handle":...        │":"Liisa Maija",...  │
# # └───────┴──────────┴────────┴─────────────────────┴─────────────────────┘
# 
#         families = []
#         result = shareds.driver.session().run(Cypher_family.get_members, pid=uid)
#         for record in result:
#             # Fill Family properties
# #                 handle          
# #                 change
# #                 id              esim. "F0001"
# #                 uniq_id         int database key
# #                 rel_type        str suhteen tyyppi
# #                 father          int isän osoite
# #                 mother          int äidin osoite
# #                 no_of_children  int lasten lukumäärä
# #                 children[]      int lasten osoitteet
# 
#             f = Family_for_template()
#             f.id = record['f_id']
#             f.rel_type = record['rel_type']
#             # Family members
#             for member in record['members']:
#                 # [ id(node), role, <Person node> ]
#                 p = Person_as_member()
#                 p.uniq_id = member[0]
#                 p.role = member[1]
#                 rec = member[2]
#                 # rec = {"handle":"_df908d402906150f6ac6e0cdc93",
#                 #  "id":"I0004","priv":"","sex":"2","confidence":"",
#                 #  "change":1536324696}
#                 p.handle = rec['handle']
#                 p.id = rec['id']
#                 if 'priv' in rec:
#                     p.priv = rec['priv']
#                 p.sex = rec['sex']
#                 p.confidence = rec['confidence']
#                 p.change = rec['change']
#                 # Names
#                 order = ""
#                 for persid, namerec, namerel in record['names']:
#                     if persid == p.uniq_id and not namerec['order'] > order:
#                         # A name of this family member,
#                         # preferring the one with lowest order value
#                         n = Name()
#                         n.type = namerec['type']
#                         n.firstname = namerec['firstname']
#                         n.surname = namerec['surname']
#                         n.suffix = namerec['suffix']
#                         n.order = namerec['order']
#                         order = n.order
#                         p.names.append(n)
#                         
#                 # Members role
#                 if p.role == 'CHILD':
#                     f.children.append(p)
#                 elif p.role == 'FATHER':
#                     f.father = p
#                 elif p.role == 'MOTHER':
#                     f.mother = p
#                 else:
#                     raise LookupError("Invalid Family member role {}".format(member.role))
# 
#             families.append(f)
# 
#         return families
