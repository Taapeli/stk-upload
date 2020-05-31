'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''
#from sys import stderr
import  shareds

from bl.base import NodeObject
from .dates import DateRange


class Family(NodeObject): # -> bl.family.Family
    """ Family Node object.
    
        Perhe
            
        Properties:
                change
                id              esim. "F0001"
                uniq_id         int database key
                uuid            str UUID key
                rel_type        str suhteen tyyppi
                priv            str private if exists
                father_sortname str search key
                mother_sortname str search key
     """

    def __init__(self, uniq_id=None):
        """ Creates a new Family instance representing a database Family node.
        
        """
        """ Luo uuden family-instanssin """
        NodeObject.__init__(self, uniq_id)
        self.priv = None
        self.rel_type = ''
        self.dates = None       #TODO DateRange marriage .. divorce
        # Sorting name of family's father and mother
        self.father_sortname = ''
        self.mother_sortname = ''


    def __str__(self):
        if self.rel_type:   rel = self.rel_type.lower()
        else:               rel = _('undefined relation')
        return "{} {}".format(self.id, rel, self.dates)

    
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
        n.uuid = node['uuid']
        n.handle = node['handle']
        n.change = node['change']
        n.rel_type = node['rel_type'] or ''
        n.father_sortname = node['father_sortname']
        n.mother_sortname = node['mother_sortname']
        if "datetype" in node:
            n.dates = DateRange(node["datetype"], node["date1"], node["date2"])
        return n

    def sortnames(self):
        ''' Return 'family name' created from sortnames.
        
            Note. Consider using Family_combo.get_marriage_parent_names instead 
        '''
        a = self.father_sortname.split('#')
        fn = f"{a[0]} {a[2]} {a[1]}"
        a = self.mother_sortname.split('#')
        mn = f"{a[0]} {a[2]} {a[1]}"
        
        return f"{fn} <> {mn}"
    
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
