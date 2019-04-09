'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''
#from sys import stderr
import  shareds

#from .cypher import Cypher_family
#from .person_combo import Person_as_member
#from .person_name import Name
#from models.cypher_gramps import Cypher_family_w_handle


class Family:
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
        """ Luo uuden family-instanssin """
        self.handle = ''
        self.change = 0
        self.id = ''
        self.uniq_id = uniq_id
        self.rel_type = ''
        self.dates = None       #TODO DateRange marriage .. divorce
        # Sorting name of family's father and mother
        self.sortfather = ''
        self.sortmother = ''

# See: Family_combo
#         self.father = None
#         self.mother = None
#         self.children = []      # Child object
#         self.events = []        # Event objects
#         self.notes = []
#         self.note_ref = []
#         #TODO Obsolete parameters???
#         self.eventref_hlink = []
#         self.eventref_role = []
#         self.childref_hlink = []    # handles
#         self.noteref_hlink = []

    def __str__(self):
        if self.rel_type:   rel = self.rel_type
        else:               rel = 'undefined relation'
        return "{} {}".format(self.id, rel)

    
    @classmethod
    def from_node(cls, node):
        '''
        Transforms a db node to an object of type Family.
        
        <Node id=99991 labels={'Family'} 
            properties={'rel_type': 'Married', 'handle': '_da692e4ca604cf37ac7973d7778', 
            'id': 'F0031', 'change': 1507492602}>
        '''
        n = cls()
        n.uniq_id = node.id
        n.id = node['id'] or ''
        n.handle = node['handle']
        n.change = node['change']
        n.rel_type = node['rel_type'] or ''
        return n


# See: Family_combo
#     def get_children_by_id(self):
#         """ Luetaan perheen lasten tiedot """
#                         
#         pid = int(self.uniq_id)
#         query = """
# MATCH (family:Family)-[r:CHILD]->(person:Person)
#   WHERE ID(family)=$pid
# RETURN ID(person) AS children"""
#         return  shareds.driver.session().run(query, {"pid": pid})
#     
#     
#     def get_family_events(self):
#         """ Luetaan perheen tapahtumien tiedot """
#                         
#         pid = int(self.uniq_id)
#         query = """
# MATCH (family:Family)-[r:EVENT]->(event:Event)
#   WHERE ID(family)=$pid
# RETURN r.role AS eventref_role, event.handle AS eventref_hlink"""
#         return  shareds.driver.session().run(query, {"pid": pid})
#     
#     
#     def get_family_data_by_id(self):
#         """ Luetaan perheen tiedot """
#                         
#         pid = int(self.uniq_id)
#         query = """
# MATCH (family:Family)
#   WHERE ID(family)=$pid
# RETURN family"""
#         family_result = shareds.driver.session().run(query, {"pid": pid})
#         
#         for family_record in family_result:
#             self.change = family_record["family"]['change']
#             self.id = family_record["family"]['id']
#             self.rel_type = family_record["family"]['rel_type']
#             
#         father_result = self.get_father_by_id()
#         for father_record in father_result:            
#             self.father = father_record["father"]
# 
#         mother_result = self.get_mother_by_id()
#         for mother_record in mother_result:            
#             self.mother = mother_record["mother"]
# 
#         event_result = self.get_family_events()
#         for event_record in event_result:            
#             self.eventref_hlink.append(event_record["eventref_hlink"])
#             self.eventref_role.append(event_record["eventref_role"])
# 
#         children_result = self.get_children_by_id()
#         for children_record in children_result:            
#             self.childref_hlink.append(children_record["children"])
#             
#         return Tru
#     @staticmethod       
#     def get_families(fw=0, bw=0, limit=100):
#         """ Find families from the database """
#         
#         try:
#             with shareds.driver.session() as session:
#                 result = session.run(Cypher_family.read_families_p,
#                                      fw=fw, limit=limit)
#                 
#             families = []
#             for record in result:
#                 if record['f']:
#                     # <Node id=55577 labels={'Family'} 
#                     #    properties={'rel_type': 'Married', 'handle': '_d78e9a206e0772ede0d', 
#                     #    'id': 'F0000', 'change': 1507492602}>
#                     f_node = record['f']
#                     family = Family_for_template(f_node.id)
#                     family.id = f_node['id']
#                     family.type = f_node['rel_type']
#                 
# #                     if record['ph']:
# #                         husband = record['ph']
# #                         ph = Person_as_member()
# #                         ph.uniq_id = husband.id
# #                         if record['nh']:
# #                             hname = record['nh']
# #                             ph.names.append(hname)
# #                         family.father = ph
# #                     if record['pw']:
# #                         wife = record['pw']
# #                         pw = Person_as_member()
# #                         pw.uniq_id = wife.id
# #                         if record['nw']:
# #                             wname = record['nw']
# #                             pw.names.append(wname)
# #                         family.mother = pw
# 
#                     uniq_id = -1
#                     for role, parent_node, name_node in record['parent']:
#                         if parent_node:
#                             # <Node id=214500 labels={'Person'} 
#                             #    properties={'sortname': 'Airola#ent. Silius#Kalle Kustaa', 
#                             #    'datetype': 19, 'confidence': '2.7', 'change': 1504606496, 
#                             #    'sex': 0, 'handle': '_ce373c1941d452bd5eb', 'id': 'I0008', 
#                             #    'date2': 1997946, 'date1': 1929380}>
#                             if uniq_id != parent_node.id:
#                                 # Skip person with double default name
#                                 pp = Person_as_member()
#                                 uniq_id = parent_node.id
#                                 pp.uniq_id = uniq_id
#                                 pp.sortname = parent_node['sortname']
#                                 pp.sex = parent_node['sex']
#                                 if role == 'father':
#                                     family.father = pp
#                                 elif role == 'mother':
#                                     family.mother = pp
# 
#                             pname = Name.from_node(name_node)
#                             pp.names.append(pname)
# 
#                     
#                     for ch in record['child']:
#                         # <Node id=60320 labels={'Person'} 
#                         #    properties={'sortname': '#Björnsson#Simon', 'datetype': 19, 
#                         #    'confidence': '', 'sex': 0, 'change': 1507492602, 
#                         #    'handle': '_d78e9a2696000bfd2e0', 'id': 'I0001', 
#                         #    'date2': 1609920, 'date1': 1609920}>
#                         child = Person_as_member()
#                         child.uniq_id = ch.id
#                         child.sortname = ch['sortname']
#                         family.children.append(child)
#                     
#                     if record['no_of_children']:
#                         family.no_of_children = record['no_of_children']
#                     families.append(family)
#             return (families)
# 
#         except Exception as e:
#             print('Error _read_families: {} {}'.format(e.__class__.__name__, e))            
#             raise      
# 
#     
#     @staticmethod       
#     def get_all_families():
#         """ Find all families from the database 
#             #TODO Use [:PARENT] link
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
#                 family = Family_for_template(f.id)
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
#     
#     @staticmethod       
#     def get_own_families(user=None):
#         """ Find all families from the database 
#             #TODO Use [:PARENT] link
#         """
#         
#         query = """
# MATCH (prof:UserProfile)-[:HAS_LOADED]->(batch:Batch)-[:BATCH_MEMBER|OWNS]->(f:Family) WHERE prof.userName=$user 
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
#         
#     
#     @staticmethod       
#     def get_marriage_parent_names(event_uniq_id):
#         """ Find the parents and all their names
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
# 
#     
#     def get_father_by_id(self, role='father'):
#         """ Luetaan perheen isän (tai äidin) tiedot """
#                         
#         pid = int(self.uniq_id)
#         query = """
# MATCH (family:Family) -[r:PARENT]-> (person:Person)
#   WHERE ID(family)=$pid and r.role = $role
# RETURN ID(person) AS father"""
#         return  shareds.driver.session().run(query, pid=pid, role=role)
#     
#     
#     def get_mother_by_id(self):
#         """ Luetaan perheen äidin tiedot """
#         return self.get_father_by_id(self, role='mother')
#         
    
    @staticmethod       
    def get_total():
        """ Tulostaa perheiden määrän tietokannassa """
        
        global session
                
        query = """
            MATCH (f:Family) RETURN COUNT(f)
            """
        results =  shareds.driver.session().run(query)
        
        for result in results:
            return str(result[0])

# See: Family_combo
#     def print_data(self):
#         """ Tulostaa tiedot """
#         print ("*****Family*****")
#         print ("Handle: " + self.handle)
#         print ("Change: {}".format(self.change))
#         print ("Id: " + self.id)
#         print ("Rel: " + self.rel_type)
#         print ("Father: " + self.father)
#         print ("Mother: " + self.mother)
#         if len(self.eventref_hlink) > 0:
#             for i in range(len(self.eventref_hlink)):
#                 print ("Eventref_hlink: " + self.eventref_hlink[i])
#         if len(self.eventref_role) > 0:
#             for i in range(len(self.eventref_role)):
#                 print ("Role: " + self.eventref_role[i])
#         if len(self.childref_hlink) > 0:
#             for i in range(len(self.childref_hlink)):
#                 print ("Childref_hlink: " + self.childref_hlink[i])
#         return True
# 
# 
#     def save(self, tx, batch_id):
#         """ Saves the family node to db and 
#             creates relations to parent, child and note nodes
#         """
# 
#         f_attr = {}
#         try:
#             f_attr = {
#                 "handle": self.handle,
#                 "change": self.change,
#                 "id": self.id,
#                 "rel_type": self.rel_type
#             }
#             result = tx.run(Cypher_family_w_handle.create_to_batch, 
#                             batch_id=batch_id, f_attr=f_attr)
#             ids = []
#             for record in result:
#                 self.uniq_id = record[0]
#                 ids.append(self.uniq_id)
#                 if len(ids) > 1:
#                     print("iError updated multiple Families {} - {}, attr={}".format(self.id, ids, f_attr))
#                 # print("Family {} ".format(self.uniq_id))
#         except Exception as err:
#             print("iError Family.save family: {0} attr={1}".format(err, f_attr), file=stderr)
# 
#         # Make father and mother relations to Person nodes
#         try:
#             if hasattr(self,'father') and self.father:
#                 tx.run(Cypher_family_w_handle.link_parent, role='father',
#                        f_handle=self.handle, p_handle=self.father)
# 
#             if hasattr(self,'mother') and self.mother:
#                 tx.run(Cypher_family_w_handle.link_parent, role='mother',
#                        f_handle=self.handle, p_handle=self.mother)
#         except Exception as err:
#             print("iError Family.save parents: {0} {1}".format(err, self.id), file=stderr)
# 
#         # Make relations to Event nodes
#         try:
#             for i in range(len(self.eventref_hlink)):
#                 tx.run(Cypher_family_w_handle.link_event, 
#                        f_handle=self.handle, e_handle=self.eventref_hlink[i],
#                        role=self.eventref_role[i])
#         except Exception as err:
#             print("iError Family.save events: {0} {1}".format(err, self.id), file=stderr)
#   
#         # Make child relations to Person nodes
#         try:
#             for handle in self.childref_hlink:
#                 tx.run(Cypher_family_w_handle.link_child, 
#                        f_handle=self.handle, p_handle=handle)
#         except Exception as err:
#             print("iError Family.save children: {0} {1}".format(err, self.id), file=stderr)
#   
#         # Make relation(s) to the Note node
#         try:
#             for handle in self.noteref_hlink:
#                 tx.run(Cypher_family_w_handle.link_note,
#                        f_handle=self.handle, n_handle=handle)
#         except Exception as err:
#             print("iError Family.save notes: {0} {1}".format(err, self.id), file=stderr)
# 
#         return
