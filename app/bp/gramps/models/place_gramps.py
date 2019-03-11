'''
Created on 11.3.2019

@author: jm
'''

from sys import stderr

from models.gen.dates import DateRange
from models.gen.place import Place
from models.cypher_gramps import Cypher_place_in_batch


class Place_gramps(Place):     
    """ Place for storing Gramps xml to database.

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
            Defined here:
                surround_ref[]      dictionaries {'hlink':handle, 'dates':dates}
                note_ref[]          int uniq_ids of Notes
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
        self.note_ref = []      # uniq_ids of Notes
        self.surround_ref = []  # members are dictionaries {'hlink':hlink, 'dates':dates}
        self.noteref_hlink = []


    def save(self, tx, batch_id, place_keys=None):
        """ Saves a Place with Place_names, notes and hierarchy links.

            Raises an error, if write fails.

            If self.handle is in place_keys dictionary, the node will be updated;
            else a new node will be created and linked to batch.

            If surround_ref has upper hierarchy handles,
            - if handle is in place_keys keys, create a hierarchy relation
            - else create both upper node and relation
            
            - Place names are always created as new Place_name nodes
            - If place has date information, add datetype, date1 and date2 
              to NAME link
            - Notes are linked self using 'noteref_hlink's, the Notes are saved before
        """

        pl_attr = {}
        try:
            pl_attr = {"handle": self.handle,
                      "change": self.change,
                      "id": self.id,
                      "type": self.type,
                      "pname": self.pname}
            if self.coord:
                # If no coordinates, don't set coord attribute
                pl_attr.update({"coord": self.coord.get_coordinates()})

            plid = place_keys.get(self.handle) if place_keys else None 
            if plid:
                # Update known place node and link 
                print(f"Update Place node {self.id}, id={plid}")
                result = tx.run(Cypher_place_in_batch.merge, 
                                batch_id=batch_id, plid=plid, p_attr=pl_attr)
            else:
                # Create and link to Batch node
                print(f"Create a new Place node {self.id}")
                result = tx.run(Cypher_place_in_batch.create, 
                                batch_id=batch_id, p_attr=pl_attr)
                place_keys[self.handle] = result.single()[0]

            self.uniq_id = result.single()[0]
        except Exception as err:
            print("iError Place.create: {err} attr={p_attr}", file=stderr)
            raise

        # Create Place_names
        try:
            for name in self.names:
                n_attr = {"name": name.name,
                          "lang": name.lang}
                if name.dates:
                    n_attr.update(name.dates.for_db())
                tx.run(Cypher_place_in_batch.add_name,
                       pid=self.uniq_id, n_attr=n_attr)
        except Exception as err:
            print("iError Place.add_name: {err}", file=stderr)
            raise

        # Make hierarchy relations to upper Place nodes
        try:
            for up_handle in self.surround_ref:
                #print(f"up_handle {self} -> {up_handle}")
                if 'dates' in up_handle and isinstance(up_handle['dates'], DateRange):
                    rel_attr = up_handle['dates'].for_db()
                else:
                    rel_attr = {}
                uid = place_keys.get(up_handle) if place_keys else None 
                if uid:
                    # Link to upper Place node, which has already batch connection
                    print(f"Link {self.id} to upper Place node id={plid}")
                    result = tx.run(Cypher_place_in_batch.link_hier,
                                    plid=self.uniq_id, up_id=uid, r_attr=rel_attr)
                else:
                    # Create and link upper node with minimal data
                    print(f"Update Place node {self.id}, id={plid}")
                    result = tx.run(Cypher_place_in_batch.link_create_hier,
                                    plid=self.uniq_id, r_attr=rel_attr, 
                                    up_handle=up_handle)
                    place_keys[up_handle] = result.single()[0]
        except Exception as err:
            print("iError Place.link_hier: {err}", file=stderr)
            raise

        # Make the place note relations; the Notes have been stored before
        #TODO: Voi olla useita Noteja samalla handlella! Käytä uniq_id:tä!
        try:
            for n_handle in self.noteref_hlink:
                result = tx.run(Cypher_place_in_batch.link_note, 
                                pid=self.uniq_id, hlink=n_handle)
        except Exception as err:
            print(f"iError Place.link_notes {self.noteref_hlink}: {err}", file=stderr)
            raise

        return
