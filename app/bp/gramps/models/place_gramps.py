'''
Created on 11.3.2019

@author: jm
'''

from sys import stderr

import shareds
from bl.place import Place, PlaceBl
from pe.neo4j.write_driver import Neo4jWriteDriver
from pe.db_writer import DBwriter

from models.gen.dates import DateRange
#from models.gen.place import Place
from models.cypher_gramps import Cypher_place_in_batch
from shareds import logger
import traceback


class Place_gramps(PlaceBl):     
    """ For storing Place from Gramps xml to database.

        Properties:
            Defined in models.gen.place.Place:
                handle
                change
                id                  esim. "P0001"
                type                str paikan tyyppi
                pname               str paikan nimi
                names[]:
                   name             str paikan nimi
                   lang             str kielikoodi
                   dates            DateRange date expression
                coord               str paikan koordinaatit (leveys- ja pituuspiiri)
                surrounding[]       int uniq_ids of upper
                note_ref[]          int uniq_ids of Notes
            Defined here:
                surround_ref[]      dictionaries {'hlink':handle, 'dates':dates}
                citation_ref[]      int uniq_ids of Citations
                placeref_hlink      str paikan osoite
                noteref_hlink       str huomautuksen osoite (tulostuksessa Note-olioita)

        Classmethods in Place:
            from_node(cls, node)    Creates a node object of type Place from a Neo4j node

     """

    def __init__(self, uniq_id=None):
        """ Creates a new Place_gramps instance for Gramps xml data upload.
        """

        Place.__init__(self, uniq_id)
        self.uuid = self.newUuid()
        self.note_ref = []      # uniq_ids of Notes
        self.surround_ref = []  # members are dictionaries {'hlink':hlink, 'dates':dates}
        self.notes = []
        self.noteref_hlink = []
        self.media_refs = []         # handles of Media [(handle,crop)]


    @staticmethod
    def make_hierarchy(tx, place):
        """ Links the given Place_gramps object to surrounding Places in db.
        
            #TODO: NOT IN USE
        """
        for upper in place.surround_ref:
            try:
                #print("upper {} -> {}".format(self, upper))
                if 'dates' in upper and isinstance(upper['dates'], DateRange):
                    r_attr = upper['dates'].for_db()
                else:
                    r_attr = {}
                tx.run(Cypher_place_in_batch.link_hier,
                       handle=place.handle, hlink=upper['hlink'], r_attr=r_attr)
            except Exception as err:
                print("iError Place_gramps.make_hierarchy: {0}".format(err), file=stderr)


    def save(self, tx, **kwargs):
        """ Saves a Place with Place_names, notes and hierarchy links.

            The 'uniq_id's of already created nodes can be found in 'place_keys' 
            dictionary by 'handle'.

            Create node for Place self:
            1) node exists: update its parameters and link to Batch
            2) new node: create node and link to Batch

            For each 'self.surround_ref' link to upper node:
            3) upper node exists: create link to that node
            4) new upper node: create and link hierarchy to Place self

            Place names are always created as new 'Place_name' nodes.
            - If place has date information, add datetype, date1 and date2 
              parameters to NAME link
            - Notes are linked self using 'noteref_hlink's (the Notes have been 
              saved before)

            Raises an error, if write fails.
        """
        if 'batch_id' in kwargs:
            batch_id = kwargs['batch_id']
        else:
            raise RuntimeError(f"Place_gramps.save needs a batch_id for {self.id}")

        # Create or update this Place

        self.uuid = self.newUuid()
        pl_attr = {}
        try:

            pl_attr = {
                "uuid": self.uuid,
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "type": self.type,
                "pname": self.pname}
            if self.coord:
                # If no coordinates, don't set coord attribute
                pl_attr.update({"coord": self.coord.get_coordinates()})

            # Create Place self

            if 'place_keys' in kwargs:
                # Check if this Place node is already created
                place_keys = kwargs['place_keys']
                plid = place_keys.get(self.handle)
            else:
                plid = None

            if plid:
                # 1) node has been created but not connected to Batch.
                #    update known Place node parameters and link from Batch
                self.uniq_id = plid
                if self.type:
                    #print(f"Pl_save-1 Complete Place ({self.id} #{plid}) {self.handle} {self.pname}")
                    result = tx.run(Cypher_place_in_batch.complete, #TODO
                                    batch_id=batch_id, plid=plid, p_attr=pl_attr)
                else:
                    #print(f"Pl_save-1 NO UPDATE Place ({self.id} #{plid}) attr={pl_attr}")
                    pass
            else:
                # 2) new node: create and link from Batch
                #print(f"Pl_save-2 Create a new Place ({self.id} #{self.uniq_id} {self.pname}) {self.handle}")
                result = tx.run(Cypher_place_in_batch.create, 
                                batch_id=batch_id, p_attr=pl_attr)
                self.uniq_id = result.single()[0]
                place_keys[self.handle] = self.uniq_id

        except Exception as err:
            print(f"iError Place.create: {err} attr={pl_attr}", file=stderr)
            raise

        # Create Place_names

        try:
            for name in self.names:
                n_attr = {"name": name.name,
                          "lang": name.lang}
                if name.dates:
                    n_attr.update(name.dates.for_db())
                result = tx.run(Cypher_place_in_batch.add_name, 
                                pid=self.uniq_id, order=name.order, n_attr=n_attr)
                name.uniq_id = result.single()[0]
                #print(f"# ({self.uniq_id}:Place)-[:NAME]->({name.uniq_id}:{name})")
        except Exception as err:
            print("iError Place.add_name: {err}", file=stderr)
            raise

        # Select default names for default languages
        def_names = PlaceBl.find_default_names(self.names, ['fi', 'sv'])
        # Update default language name links
        dbdriver = Neo4jWriteDriver(shareds.driver, tx)
        db = DBwriter(dbdriver)
        db.place_set_default_names(self, def_names)

        # Make hierarchy relations to upper Place nodes

        for ref in self.surround_ref:
            try:
                up_handle = ref['hlink']
                #print(f"Pl_save-surrounding {self} -[{ref['dates']}]-> {up_handle}")
                if 'dates' in ref and isinstance(ref['dates'], DateRange):
                    rel_attr = ref['dates'].for_db()
                    #_r = f"-[{ref['dates']}]->"
                else:
                    rel_attr = {}
                    #_r = f"-->"

                # Link to upper node

                uid = place_keys.get(up_handle) if place_keys else None 
                if uid:
                    # 3) Link to a known upper Place
                    #    The upper node is already created: create a link to that
                    #    upper Place node
                    #print(f"Pl_save-3 Link ({self.id} #{self.uniq_id}) {_r} (#{uid})")
                    result = tx.run(Cypher_place_in_batch.link_hier,
                                    plid=self.uniq_id, up_id=uid, r_attr=rel_attr)
                else:
                    # 4) Link to unknown place
                    #    A new upper node: create a Place with only handle
                    #    parameter and link hierarchy to Place self
                    #print(f"Pl_save-4 Link to empty upper Place ({self.id} #{self.uniq_id}) {_r} {up_handle}")
                    result = tx.run(Cypher_place_in_batch.link_create_hier,
                                    plid=self.uniq_id, r_attr=rel_attr, 
                                    up_handle=up_handle)
                    place_keys[up_handle] = result.single()[0]

            except Exception as err:
                print(f"iError Place.link_hier: {err} at {self.id} --> {up_handle}", file=stderr)
                raise
            
        try:
            for note in self.notes:
                n_attr = {"url": note.url,
                          "type": note.type,
                          "text": note.text}
                result = tx.run(Cypher_place_in_batch.add_urls, 
                                batch_id=batch_id, pid=self.uniq_id, n_attr=n_attr)
        except Exception as err:
            traceback.print_exc()
            print(f"iError Place.add_urls: {err}", file=stderr)
            raise

        # Make the place note relations; the Notes have been stored before
        #TODO: Voi olla useita Noteja samalla handlella! Käytä uniq_id:tä!
        try:
            for n_handle in self.noteref_hlink:
                result = tx.run(Cypher_place_in_batch.link_note, 
                                pid=self.uniq_id, hlink=n_handle)
        except Exception as err:
            logger.error(f"Place_gramps.save: {err} in linking Notes {self.handle} -> {self.noteref_hlink}")
            #print(f"iError Place.link_notes {self.noteref_hlink}: {err}", file=stderr)
            raise

        # Make relations to the Media nodes and their Note and Citation references
        dbdriver = Neo4jWriteDriver(shareds.driver, tx)
        db = DBwriter(dbdriver)
        db.media_save_w_handles(self.uniq_id, self.media_refs)
            
        return

