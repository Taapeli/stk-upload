'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from sys import stderr

from shareds import logger
from models.gen.source import Source
from models.cypher_gramps import Cypher_source_w_handle


class Source_gramps(Source):
    """ Genealogical data source from Gramps xml file.
            
        Properties:
                handle          
                change
                id              esim. "S0001"
                stitle          str lähteen otsikko
                note_handles[]  str list note handles (ent. noteref_hlink)
                repositories[]  Repository object containing 
                                prev. reporef_hlink and reporef_medium
     """

    def __init__(self):
        """ Creates a Source instance for Gramps xml upload.
        """
        Source.__init__(self)
        
        # From gramps xml elements
        self.note_handles = []  # allow multiple; prev. noteref_hlink = ''
        self.repositories = []  # list of Repository objects, containing 
                                # prev. repocitory_id, reporef_hlink and reporef_medium


    def save(self, tx):
        """ Saves this Source and connect it to Notes and Repositories.
        """

        s_attr = {}
        try:
            s_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "stitle": self.stitle
            }

#             self.uniq_id = tx.run(Cypher_source_w_handle.create, s_attr=s_attr).single()[0]
            result = tx.run(Cypher_source_w_handle.create, s_attr=s_attr)
            ids = []
            for record in result:
                self.uniq_id = record[0]
                ids.append(self.uniq_id)
                if len(ids) > 1:
                    print("iError updated multiple Sources {} - {}, attr={}".format(self.id, ids, s_attr))

        except Exception as err:
            print("iError source_save: {0} attr={1}".format(err, s_attr), file=stderr)
            raise RuntimeError("Could not save Source {}".format(self.id))

        # Make relation to the Note nodes
        for note_handle in self.note_handles:
            try:
                tx.run(Cypher_source_w_handle.link_note,
                       handle=self.handle, hlink=note_handle)
            except Exception as err:
                logger.error(f"Source_gramps.save: {err} in linking Notes {self.handle} -> {self.note_handles}")
                #print("iError Source.save note: {0}".format(err), file=stderr)

        # Make relation to the Repository nodes
        for repo in self.repositories:
            try:
                tx.run(Cypher_source_w_handle.link_repository,
                       handle=self.handle, hlink=repo.handle, medium=repo.medium)
            except Exception as err:
                print("iError Source.save Repository: {0}".format(err), file=stderr)
                
        return
