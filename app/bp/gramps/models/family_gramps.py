'''
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: jm
'''
from sys import stderr
#import  shareds

#from models.gen.cypher import Cypher_family
from models.gen.family import Family
from models.cypher_gramps import Cypher_family_w_handle
from shareds import logger


class Family_gramps(Family):
    """ Family suitable for Gramps xml upload
            
        Properties:
            See also models.gen.family.Family

            Gramps variables
                eventref_hlink      str tapahtuman osoite
                eventref_role       str tapahtuman rooli
                childref_hlink      str lapsen osoite
                noteref_hlink       str lisätiedon osoite
                citationref_hlink   str lähteen osoite
     """

    def __init__(self, uniq_id=None):
        """ Creates a Family instance. 
        """
        Family.__init__(self, uniq_id)

        self.father = None      # Gramps handles
        self.mother = None
        self.children = []

        # For Gramps xml fields
        self.note_ref = []      # For a page, where same note may be referenced
                                # from multiple events and other objects
        self.eventref_hlink = []
        self.eventref_role = []
        self.childref_hlink = []    # handles
        self.noteref_hlink = []
        self.citationref_hlink = []


    def save(self, tx, batch_id):
        """ Saves the family node to db with its relations.
        
            Connects the family to parent, child and note nodes
        """

        self.uuid = self.newUuid()
        f_attr = {}
        try:
            f_attr = {
                "uuid": self.uuid,
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
                    logger.warning(f"Family_gramps.save updated multiple Families {self.id} - {ids}, attr={f_attr}")
                # print("Family {} ".format(self.uniq_id))
        except Exception as err:
            logger.error(f"Family_gramps.save: {err} in #{self.uniq_id} - {f_attr}")
            #print("iError Family.save family: {0} attr={1}".format(err, f_attr), file=stderr)

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
            #print(f"Family_gramps.save: linking Notes {self.handle} -> {self.noteref_hlink}")
            for handle in self.noteref_hlink:
                tx.run(Cypher_family_w_handle.link_note,
                       f_handle=self.handle, n_handle=handle)
        except Exception as err:
            logger.error(f"Family_gramps.save: {err} in linking Notes {self.handle} -> {self.noteref_hlink}")
            #print("iError Family.save notes: {0} {1}".format(err, self.id), file=stderr)
  
        # Make relation(s) to the Citation node
        try:
            #print(f"Family_gramps.save: linking Citations {self.handle} -> {self.citationref_hlink}")
            for handle in self.citationref_hlink:
                tx.run(Cypher_family_w_handle.link_citation,
                       f_handle=self.handle, c_handle=handle)
        except Exception as err:
            logger.error(f"Family_gramps.save: {err} in linking Citations {self.handle} -> {self.citationref_hlink}")
            #print("iError Family.save citations: {0} {1}".format(err, self.id), file=stderr)

        return

