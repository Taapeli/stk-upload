'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''
from sys import stderr
#import  shareds

#from models.gen.cypher import Cypher_family
from models.gen.family import Family
from models.cypher_gramps import Cypher_family_w_handle


class Family_gramps(Family):
    """ Family suitable for Gramps xml upload
            
        Properties:
            See also models.gen.family.Family

            Gramps variables
                eventref_hlink  str tapahtuman osoite
                eventref_role   str tapahtuman rooli
                childref_hlink  str lapsen osoite
                noteref_hlink   str lisätiedon osoite
     """

    def __init__(self, uniq_id=None):
        """ Creates a Family instance. 
        """
        Family.__init__(self, uniq_id)

        #TODO: Are these actually in use, when data got from Gramps?
        self.father = None
        self.mother = None
        self.children = []      # Child object

        # For Gramps xml fields
        self.note_ref = []      # For a page, where same note may be referenced
                                # from multiple events and other objects
        self.eventref_hlink = []
        self.eventref_role = []
        self.childref_hlink = []    # handles
        self.noteref_hlink = []


    def save(self, tx, batch_id):
        """ Saves the family node to db with its relations.
        
            Connects the family to parent, child and note nodes
        """

        f_attr = {}
        try:
            f_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "rel_type": self.rel_type
            }
            result = tx.run(Cypher_family_w_handle.create_to_batch, 
                            batch_id=batch_id, f_attr=f_attr)
            ids = []
            for record in result:
                self.uniq_id = record[0]
                ids.append(self.uniq_id)
                if len(ids) > 1:
                    print("iError updated multiple Families {} - {}, attr={}".format(self.id, ids, f_attr))
                # print("Family {} ".format(self.uniq_id))
        except Exception as err:
            print("iError Family.save family: {0} attr={1}".format(err, f_attr), file=stderr)

        # Make father and mother relations to Person nodes
        try:
            if hasattr(self,'father') and self.father:
                tx.run(Cypher_family_w_handle.link_parent, role='father',
                       f_handle=self.handle, p_handle=self.father)

            if hasattr(self,'mother') and self.mother:
                tx.run(Cypher_family_w_handle.link_parent, role='mother',
                       f_handle=self.handle, p_handle=self.mother)
        except Exception as err:
            print("iError Family.save parents: {0} {1}".format(err, self.id), file=stderr)

        # Make relations to Event nodes
        try:
            for i in range(len(self.eventref_hlink)):
                tx.run(Cypher_family_w_handle.link_event, 
                       f_handle=self.handle, e_handle=self.eventref_hlink[i],
                       role=self.eventref_role[i])
        except Exception as err:
            print("iError Family.save events: {0} {1}".format(err, self.id), file=stderr)
  
        # Make child relations to Person nodes
        try:
            for handle in self.childref_hlink:
                tx.run(Cypher_family_w_handle.link_child, 
                       f_handle=self.handle, p_handle=handle)
        except Exception as err:
            print("iError Family.save children: {0} {1}".format(err, self.id), file=stderr)
  
        # Make relation(s) to the Note node
        try:
            for handle in self.noteref_hlink:
                tx.run(Cypher_family_w_handle.link_note,
                       f_handle=self.handle, n_handle=handle)
        except Exception as err:
            print("iError Family.save notes: {0} {1}".format(err, self.id), file=stderr)

        return

