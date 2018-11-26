'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''
from sys import stderr
import  shareds

from .cypher import Cypher_family
from .person_combo import Person_as_member
from .person_name import Name
from models.cypher_gramps import Cypher_family_w_handle


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
        self.father = None
        self.mother = None
        self.children = []      # Child object
        self.events = []        # Event objects
        self.notes = []
        self.dates = None       #TODO DateRange marriage .. divorce
        self.note_ref = []

        #TODO Obsolete parameters???
        self.eventref_hlink = []
        self.eventref_role = []
        self.childref_hlink = []    # handles
        self.noteref_hlink = []

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

    @staticmethod
    def get_family_paths_apoc(uniq_id):
        ''' Read a person and paths for all connected nodes
        '''
        all_nodes_query_w_apoc="""
MATCH (f:Family) WHERE id(f) = $fid
CALL apoc.path.subgraphAll(f, {maxLevel:2, relationshipFilter: 
        'CHILD>|FATHER>|MOTHER>|EVENT>|NAME>|PLACE>|CITATION>|SOURCE>|NOTE>|HIERARCHY>'}) YIELD nodes, relationships
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
        """ Luetaan perheen tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)
  WHERE ID(family)=$pid
RETURN family"""
        family_result = shareds.driver.session().run(query, {"pid": pid})
        
        for family_record in family_result:
            self.change = int(family_record["family"]['change'])  #TODO only temporary int()
            self.id = family_record["family"]['id']
            self.rel_type = family_record["family"]['rel_type']
            
        father_result = self.get_father_by_id()
        for father_record in father_result:            
            self.father = father_record["father"]

        mother_result = self.get_mother_by_id()
        for mother_record in mother_result:            
            self.mother = mother_record["mother"]

        event_result = self.get_family_events()
        for event_record in event_result:            
            self.eventref_hlink.append(event_record["eventref_hlink"])
            self.eventref_role.append(event_record["eventref_role"])

        children_result = self.get_children_by_id()
        for children_record in children_result:            
            self.childref_hlink.append(children_record["children"])
            
        return True
    
    
    @staticmethod       
    def get_marriage_parent_names(event_uniq_id):
        """ Find the parents and all their names
        
            Returns a dictionary like 
            {'FATHER': (77654, 'Mattias Abrahamsson  • Matts  Lindlöf'), ...}

╒════════╤═════╤═══════════════════════════════════════════════════╕
│"frole" │"pid"│"names"                                            │
╞════════╪═════╪═══════════════════════════════════════════════════╡
│"FATHER"│73538│[{"alt":"","firstname":"Carl","type":"Birth Name","│
│        │     │suffix":"","surname":"Forstén"}]                   │
├────────┼─────┼───────────────────────────────────────────────────┤
│"MOTHER"│73540│[{"alt":"","firstname":"Catharina Margareta","type"│
│        │     │:"Birth Name","suffix":"","surname":"Stenfeldt"},{"│
│        │     │alt":"1","firstname":"Catharina Margareta","type":"│
│        │     │Also Known As","suffix":"","surname":"Forstén"}]   │
└────────┴─────┴───────────────────────────────────────────────────┘
        """
                        
        result = shareds.driver.session().run(Cypher_family.get_wedding_couple_names, 
                                              eid=event_uniq_id)
        namedict = {}
        for record in result:
            role = record['frole']
#             pid = record['pid']
            names = []
            for name in record['names']:
                fn = name['firstname']
                sn = name['surname']
                pn = name['suffix']
                names.append("{} {} {}".format(fn, pn, sn))
            namedict[role] = ' • '.join(names)
        return namedict

    
    def get_father_by_id(self):
        """ Luetaan perheen isän tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)-[r:FATHER]->(person:Person)
  WHERE ID(family)=$pid
RETURN ID(person) AS father"""
        return  shareds.driver.session().run(query, {"pid": pid})
    
    
    def get_mother_by_id(self):
        """ Luetaan perheen äidin tiedot """
                        
        pid = int(self.uniq_id)
        query = """
MATCH (family:Family)-[r:MOTHER]->(person:Person)
  WHERE ID(family)=$pid
RETURN ID(person) AS mother"""
        return  shareds.driver.session().run(query, {"pid": pid})
        
    
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


    def save(self, tx, batch_id):
        """ Saves the family node to db and 
            creates relations to parent, child and note nodes
        """

        try:
            f_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "rel_type": self.rel_type
            }
            result = tx.run(Cypher_family_w_handle.create_to_batch, 
                            batch_id=batch_id, f_attr=f_attr)
            for res in result:
                self.uniq_id = res[0]
                print("Family {} ".format(self.uniq_id))
        except Exception as err:
            print("Virhe (Family.save:Family): {0}".format(err), file=stderr)

        # Make father and mother relations to Person nodes
        try:
            if hasattr(self,'father') and self.father != '':
                tx.run(Cypher_family_w_handle.link_father, 
                       f_handle=self.handle, p_handle=self.father)

            if hasattr(self,'mother') and self.mother != '':
                tx.run(Cypher_family_w_handle.link_mother,
                       f_handle=self.handle, p_handle=self.mother)
        except Exception as err:
            print("Virhe (Family.save:parents): {0}".format(err), file=stderr)

        # Make relations to Event nodes
        if len(self.eventref_hlink) > 0:
            for i in range(len(self.eventref_hlink)):
                try:
                    tx.run(Cypher_family_w_handle.link_event, 
                           f_handle=self.handle, e_handle=self.eventref_hlink[i],
                           role=self.eventref_role[i])
                except Exception as err:
                    print("Virhe (Family.save:Event): {0}".format(err), file=stderr)
  
        # Make child relations to Person nodes
        if len(self.childref_hlink) > 0:
            for i in range(len(self.childref_hlink)):
                try:
                    tx.run(Cypher_family_w_handle.link_child, 
                           f_handle=self.handle, p_handle=self.childref_hlink[i])
                except Exception as err:
                    print("Virhe (Family.save:Child): {0}".format(err), file=stderr)
  
        # Make relation(s) to the Note node
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                try:
                    tx.run(Cypher_family_w_handle.link_note,
                           f_handle=self.handle, n_handle=self.noteref_hlink[i])
                except Exception as err:
                    print("Virhe (Family.save:Note): {0}".format(err), file=stderr)

        return


class Family_for_template(Family):
    """ Templaten perhe perii Perhe luokan
        Käytetään datareader.get_families_data_by_id() metodissa
        sivua table_families_by_id.html varten
            
        Properties:
                role        str    henkilön rooli perheessä: "Child", "Parent"
                father      Person isän tiedot
                mother      Person äidin tiedot
                spouse      Person puolisoiden tiedot
                children[]  Person lasten tiedot
     """

    def __init__(self, uniq_id=None):
        """ Luo uuden family_for_template-instanssin """
        Family.__init__(self, uniq_id)
        self.role = ""
        self.father = None
        self.mother = None
        self.spouse = None
        self.children = []

    @staticmethod       
    def get_person_families_w_members(uid):
        ''' NOT IN USE!
            Finds all Families, where Person uid belongs to
            and return them as a Families list
        '''
# ╒═══════╤══════════╤════════╤═════════════════════╤═════════════════════╕
# │"f_id" │"rel_type"│"myrole"│"members"            │"names"              │
# ╞═══════╪══════════╪════════╪═════════════════════╪═════════════════════╡
# │"F0000"│"Married" │"FATHER"│[[72533,"CHILD",     │[[72533,             │
# │       │          │        │  "CHILD",{"han      │  {"alt":"","fi      │
# │       │          │        │dle":"_dd2c613026e752│rstname":"Jan Erik","│
# │       │          │        │8c1a21f78da8a","id":"│type":"Birth Name","s│
# │       │          │        │I0000","priv":"","gen│uffix":"Jansson","sur│
# │       │          │        │der":"M","confidence"│name":"Mannerheim","r│
# │       │          │        │:"2.0","change":15363│efname":""},{}],     │
# │       │          │        │24580}],             │ [72537,             │
# │       │          │        │ [72537,"MOTHER",    │{"alt":"1","firstname│
# │       │          │        │{"handle":...        │":"Liisa Maija",...  │
# └───────┴──────────┴────────┴─────────────────────┴─────────────────────┘

        families = []
        result = shareds.driver.session().run(Cypher_family.get_members, pid=uid)
        for record in result:
            # Fill Family properties
#                 handle          
#                 change
#                 id              esim. "F0001"
#                 uniq_id         int database key
#                 rel_type        str suhteen tyyppi
#                 father          int isän osoite
#                 mother          int äidin osoite
#                 children[]      int lasten osoitteet

            f = Family_for_template()
            f.id = record['f_id']
            f.rel_type = record['rel_type']
            # Family members
            for member in record['members']:
                # [ id(node), role, <Person node> ]
                p = Person_as_member()
                p.uniq_id = member[0]
                p.role = member[1]
                rec = member[2]
                # rec = {"handle":"_df908d402906150f6ac6e0cdc93",
                #  "id":"I0004","priv":"","gender":"F","confidence":"",
                #  "change":1536324696}
                p.handle = rec['handle']
                p.id = rec['id']
                p.priv = rec['priv']
                p.gender = rec['gender']
                p.confidence = rec['confidence']
                p.change = rec['change']
                # Names
                order = ""
                for persid, namerec, namerel in record['names']:
                    if persid == p.uniq_id and not namerec['order'] > order:
                        # A name of this family member,
                        # preferring the one with lowest order value
                        n = Name()
                        n.type = namerec['type']
                        n.firstname = namerec['firstname']
                        n.surname = namerec['surname']
                        n.suffix = namerec['suffix']
                        n.order = namerec['order']
                        order = n.order
                        p.names.append(n)
                        
                # Members role
                if p.role == 'CHILD':
                    f.children.append(p)
                elif p.role == 'FATHER':
                    f.father = p
                elif p.role == 'MOTHER':
                    f.mother = p
                else:
                    raise LookupError("Invalid Family member role {}".format(member.role))

            families.append(f)

        return families
