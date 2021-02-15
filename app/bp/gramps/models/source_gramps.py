#   Isotammi Geneological Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from sys import stderr

from shareds import logger
from bl.source import Source
#from models.gen.source import Source
from models.cypher_gramps import Cypher_source_w_handle


class Source_gramps(Source):
    """ Genealogical data source from Gramps xml file.
            
        Properties:
                handle          
                change
                id              esim. "S0001"
                stitle          str lähteen otsikko
                sauthor         str lähteen tekijä
                spubinfo        str lähteen julkaisutiedot
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


    def save(self, tx, **kwargs):
        """ Saves this Source and connect it to Notes and Repositories.
        """
        if 'batch_id' in kwargs:
            batch_id = kwargs['batch_id']
        else:
            raise RuntimeError(f"Source_gramps.save needs batch_id for {self.id}")
            
        self.uuid = self.newUuid()
        s_attr = {}
        try:
            s_attr = {
                "uuid": self.uuid,
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "stitle": self.stitle,
                "sauthor": self.sauthor,
                "spubinfo": self.spubinfo
            }

            result = tx.run(Cypher_source_w_handle.create_to_batch,
                            batch_id=batch_id, s_attr=s_attr)
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
