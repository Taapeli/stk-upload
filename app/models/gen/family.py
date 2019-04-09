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
        """ Creates a new Family instance representing a database Family node.
        
        """
        self.handle = ''
        self.change = 0
        self.id = ''
        self.uniq_id = uniq_id
        self.rel_type = ''
        self.dates = None       #TODO DateRange marriage .. divorce
        # Sorting name of family's father and mother
        self.sortfather = ''
        self.sortmother = ''

# See: Family_combo, bp.gramps.models.family_gramps.Family_gramps
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
# 
#     def save(self, tx, batch_id):
#         """ Saves the family node to db and 
#             creates relations to parent, child and note nodes
#         """
