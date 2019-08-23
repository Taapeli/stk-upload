'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''
#from sys import stderr
import  shareds

from .base import NodeObject
from .dates import DateRange


class Family(NodeObject):
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
        """ Luo uuden media-instanssin """
        NodeObject.__init__(self, uniq_id)

        self.handle = ''
        self.change = 0
        self.id = ''
        self.uniq_id = uniq_id
        self.rel_type = ''
        self.dates = None       #TODO DateRange marriage .. divorce
        # Sorting name of family's father and mother
        self.father_sortname = ''
        self.mother_sortname = ''

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
        
        You can create a Family or Family_combo instance. (cls is the class 
        where we are, either Family or Family_combo)
        
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
        n.father_sortname = node['father_sortname']
        n.mother_sortname = node['mother_sortname']
        if "datetype" in node:
            n.lifetime = DateRange(node["datetype"], node["date1"], node["date2"])
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
