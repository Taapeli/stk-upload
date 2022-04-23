#   Isotammi Genealogical Service for combining multiple researchers' results.
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
"""
Created on 23.3.2020

@author: jm
"""
import logging
import traceback
from neo4j.exceptions import ClientError

logger = logging.getLogger("stkserver")
from datetime import date  # , datetime

from bl.base import Status, IsotammiException, NodeObject
from bl.dates import DateRange
from bl.person_name import Name
from bl.place import PlaceBl
from bl.family import FamilyBl
from bl.note import Note

from pe.dataservice import ConcreteService

from .cypher.cy_citation import CypherCitation
from .cypher.cy_comment import CypherComment
from .cypher.cy_event import CypherEvent
from .cypher.cy_family import CypherFamily
from .cypher.cy_gramps import CypherObjectWHandle
from .cypher.cy_media import CypherMedia
from .cypher.cy_note import CypherNote
from .cypher.cy_object import CypherObject
from .cypher.cy_person import CypherPerson
from .cypher.cy_place import CypherPlace, CypherPlaceMerge
from .cypher.cy_refname import CypherRefname
from .cypher.cy_repository import CypherRepository
from .cypher.cy_root import CypherRoot #, CypherAudit
from .cypher.cy_source import CypherSourceByHandle

from pe.neo4j.nodereaders import Comment_from_node
from pe.neo4j.nodereaders import PlaceBl_from_node
from pe.neo4j.nodereaders import PlaceName_from_node
from pe.neo4j.nodereaders import SourceBl_from_node



class Neo4jUpdateService(ConcreteService):
    """
    This service for Neo4j database maintains transaction and executes
    different read/write/update functions.

    Referenced as shareds.dataservices["update"] class.
    """

    def __init__(self, driver):
        """Create a writer/updater object with db driver and user context.

        :param: driver             neo4j.DirectDriver object
        """
        logger.debug(f"#~~~~{self.__class__.__name__} init")
        self.driver = driver
        self.tx = None  # Until started in Dataservice.__enter__()

    def ds_commit(self):
        """Commit transaction."""
        #         if self.tx.closed():
        #             print("Transaction already closed!")
        #             return {'status':Status.OK}
        try:
            self.tx.commit()

            print("Transaction committed")
            return {"status": Status.OK}
        except Exception as e:
            msg = f"{e.__class__.__name__}, {e}"
            logger.info('-> pe.neo4j.updateservice.Neo4jUpdateService.ds_commit/fail"')
            print("Neo4jUpdateService.ds_commit: Transaction failed " + msg)
            return {"status": Status.ERROR, "statustext": f"Commit failed: {msg}"}

    def ds_rollback(self):
        """Rollback transaction."""
        try:
            self.tx.rollback()
            print("Transaction discarded")
            logger.info("-> pe.neo4j.write_driver.Neo4jUpdateService.ds_rollback")
            return {"status": Status.OK}
        except Exception as e:
            msg = f"{e.__class__.__name__}, {e}"
            logger.info(
                '-> pe.neo4j.updateservice.Neo4jUpdateService.ds_rollback/fail"'
            )
            print("Neo4jUpdateService.ds_rollback: Transaction failed " + msg)
            #             self.blog.log_event({'title':_("Database save failed due to {}".\
            #                                  format(msg)), 'level':"ERROR"})
            return {"status": Status.ERROR, "statustext": f"Rollback failed: {msg}"}

    # ----- Batch Audit -----

    @staticmethod
    def ds_aqcuire_lock(tx, lock_id):
        """Create a lock"""
        tx.run(CypherRoot.acquire_lock, lock_id=lock_id).single()
        return True  # value > 0

    # def ds_find_last_used_batch_seq(self, tx): # --> ds_new_batch_id

    @staticmethod
    def ds_new_batch_id(tx):
        """Find next unused Batch id using BatchId node.

        Returns batch_id
        """
        base = str(date.today())
        # seq = self.ds_find_last_used_batch_seq(tx)
        # 1. Find the latest Batch id from the BatchId singleton node
        # print("base="+base)
        seq = 0
        record = tx.run(CypherRoot.read_batch_id).single()
        if record:
            node = record["n"]
            # print("#ds_new_batch_id: BatchId node",node)
            if node.get("prefix") == base:
                seq = node.get("seq")
        seq += 1
        batch_id = "{}.{:03d}".format(base, seq)
        tx.run(CypherRoot.save_batch_id, prefix=base, seq=seq)
        print("#Neo4jUpdateService.ds_new_batch_id: id='{}'".format(batch_id))
        return batch_id

    def ds_get_batch(self, user, batch_id):
        """Get Batch node by username and batch id. 
           Note. 'user' actually not used!
        """
        #TODO: To optimize split to two clauses:
        # - fetch profile, root, auditors, prev_auditors, has_access
        # - fetch statistics: label, cnt
        result = self.tx.run(CypherRoot.get_single_batch, 
                             user=user, batch=batch_id)
        for record in result:
            node = record.get("root")
            if node:
                return {"status":Status.OK, "node":node}
            else:
                return {"status":Status.NOT_FOUND, "node":None,
                        "statustext": "Batch not found"}

    @staticmethod
    def ds_batch_save(tx, attr):
        """Creates a Batch node.

        attr = {"mediapath", "file", "id", "user", "status"}

        Batch.timestamp is created in the Cypher clause.
        """
        record = tx.run(CypherRoot.batch_merge, b_attr=attr).single()
        if not record:
            raise IsotammiException("Unable to save Batch",
                            cypher=CypherRoot.batch_merge,
                            b_attr=attr,
                            )
        return record["id"] #{"status": Status.OK, "identity": uniq_id}


    def ds_batch_set_state(self, batch_id, user, state):
        """Updates Batch node selected by Batch id and user.
        """
        result = self.tx.run(
            CypherRoot.batch_set_state, bid=batch_id, user=user, state=state
        )
        uniq_id = result.single()[0]
        return {"status": Status.OK, "identity": uniq_id}

    def ds_batch_set_audited(self, batch_id, user, new_state):
        """Updates the auditing Batch node selected by Batch id and auditor links.
           For each auditor, DOES_AUDIT relation is replaced by DID_AUDIT with
           ending timestamp added.
        """
        auditors=[]
        # 1. Change Root state and 
        #    replace my auditing [DOES_AUDIT] with completed [DID_AUDIT]
        result = self.tx.run(CypherRoot.batch_set_i_audited, 
                             bid=batch_id, audi=user, state=new_state)
        # _Record__keys (uniq_id, relation_new)
        for record in result:
            root_id = record["root"].id
            root_audited = record["root"]["audited"]
            auditors = [root_audited]
            r = record["relation_new"]
            ts_from = r.get("ts_from")
            ts_to = r.get("ts_to")
            print(f"#ds_batch_set_audited: Auditor {root_audited} "
                  f"{type(r).__name__} {r.get('ts_from')}-{r.get('ts_to','')}")
        if not auditors:
            auditors = [root_audited]
            return {"status": Status.ERROR, "auditors": auditors}
        
        # 3. Update other auditors [DOES_AUDIT] with completed [DID_AUDIT]
        result = self.tx.run(CypherRoot.batch_compelete_does_audits, 
                             uid=root_id, ts=ts_to)
        # _Record__keys <(user, relation_new)
        for record in result:
            auditor = record['user']
            auditors.append(auditor)
            #myself = record['myself']
            r = record["relation_new"]
            print(f"#ds_batch_set_audited: others {auditor} "
                  f"{type(r).__name__} {r.get('ts_from')}-{r.get('ts_to','')}")

        return {"status": Status.OK, "auditors": auditors}


    def ds_batch_set_auditor(self, batch_id, auditor_user, old_states):
        """Updates Batch node selected by Batch id and user.
           We also check that the state is expected.
        """
        result = self.tx.run(
            CypherRoot.batch_set_auditor, 
            bid=batch_id, audi=auditor_user, states=old_states
        )
        uniq_id = result.single()[0]
        return {"status": Status.OK, "identity": uniq_id}

    def ds_batch_purge_auditors(self, batch_id, auditor_user):
        """Removes other auditors, if there are multiple auditors.
           (Used to revert multi-auditor operations.)
        """
        result = self.tx.run(CypherRoot.batch_purge_auditors, 
                             bid=batch_id, me=auditor_user)
        # Return example {
        #    batch_id:"2021-09-05.007", // Not used
        #    me:"juha",                 // Not used
        #    my_rels:[268031, 1487411], // Not used. Should be only one!
        #    user:"valta",
        #    rtype:"DOES_AUDIT",        // Not used
        #    rel_id:113743
        # }
        removed = []
        for record in result:
            # {batch_id,me,my_rels,user,rtype,rel_id}
            username = record.get("user")
            rel_uniq_id = record.get("rel_id")
            print("#Neo4jUpdateService.ds_batch_purge_auditors: removed "
                  f"id={rel_uniq_id} DOES_AUDIT from {username}")
            removed.append(username)

        return {"status": Status.OK, "removed_auditors": removed}

    def ds_batch_remove_auditor(self, batch_id, auditor_user, new_state):
        """Updates Root node and relation from UserProfile.
           We also check that the state is expected.
        """
        record = self.tx.run(
            CypherRoot.batch_remove_auditor, 
            bid=batch_id, 
            audi=auditor_user, 
            new_state=new_state,
        ).single()
        # Returns: b: Root node, audi: UserProfile, oth_cnt: cnt of other auditors,
        #          ts_from: time from the removed DOES_AUDIT relation data
        #          ts_to:   creation time of (audi) -[r:DOES_AUDIT]-> (b)
        node_root = record["root"]
        node_audi = record["audi"]
        root_id = node_root.id
        audi_id = node_audi.id
        ts_from = record["ts_from"]
        ts_to = record["ts_to"] # probably None
        print("#ds_batch_remove_auditor: "
              f"Removed r ({audi_id}:{node_audi['username']}) "
              f"-[r:DOES_AUDIT {ts_from},{ts_to}]-> ({root_id}:Root)")

        relation = self.tx.run(
            CypherRoot.link_did_audit, 
            audi_id=audi_id,
            uid=root_id, 
            fromtime = ts_from,
        ).single()[0] # Returns r: Relationship object
        ts_to = relation["ts_to"]
        d_days = ""
        try:
            d_days = (ts_to - ts_from) / (1000*60*60*24)
        except Exception:
            pass
        print("#ds_batch_remove_auditor: "
              f"Added r ({audi_id}:{node_audi['username']}) "
              f"-[r:DID_AUDIT time {ts_from}..{ts_to}]-> "
              f"({root_id}:Root({batch_id}))")

        return {"status": Status.OK, "identity": root_id, "d_days": d_days}

    # ----- Common objects -----

    def ds_merge_check(self, id1, id2):
        """Check that given objects are mergeable.

        Rules:
        - Objects have same label
        - Both objects have the same type of end relation (OWNS or PASSED)
        """

        class RefObj:
            def __str__(self):
                return f"{self.uniq_id}:{self.label} {self.str}"

        objs = {}
        try:
            print("pe.neo4j.updateservice.Neo4jUpdateService.ds_merge_check: TODO fix merge_check")
            # result = self.tx.run(CypherAudit.merge_check, id_list=[id1, id2])
            # # for root_id, root_str, rel, obj_id, obj_label, obj_str in result:
            # for record in result:
            #     ro = RefObj()
            #     ro.uniq_id = record["obj_id"]
            #     ro.label = record["obj_label"]
            #     ro.str = record["obj_str"]
            #     ro.root = (
            #         record.get("rel"),
            #         record.get("root_id"),
            #         record.get("root_str"),
            #     )
            #     # rint(f'#ds_merge_check {root_id}:{root_str} -[{rel}]-> {obj_id}:{obj_label} {obj_str}')
            #     print(f"#ds_merge_check {ro.uniq_id}:{ro.label} {ro.str} in {ro.root}")
            #     if ro.uniq_id in objs.keys():
            #         # Error if current uniq_id exists twice
            #         msg = f"Object {ro} has two roots {objs[ro.uniq_id].root} and {ro.root}"
            #         return {"status": Status.ERROR, "statustext": msg}
            #     for i, obj2 in objs.items():
            #         print(f"#ds_merge_check {obj2} <> {ro}")
            #         if i == ro.uniq_id:
            #             continue
            #         # Error if different labels or has different root node
            #         if obj2.label != ro.label:
            #             msg = f"Objects {obj2} and {ro} are different"
            #             return {"status": Status.ERROR, "statustext": msg}
            #         if obj2.root[1] != ro.root[1]:
            #             msg = (
            #                 f"Object {ro} has different roots {obj2.root} and {ro.root}"
            #             )
            #             return {"status": Status.ERROR, "statustext": msg}
            #     objs[ro.uniq_id] = ro

            if len(objs) == 2:
                print(f"ds_merge_check ok {objs}")
                return {"status": Status.OK}
            else:
                msg = f"ds_merge_check failed, found {len(objs)} objects"
                return {"status": Status.ERROR, "statustext": msg}

        except ClientError as e:
            # traceback.print_exc()
            return {
                "status": Status.ERROR,
                "statustext": "Neo4jUpdateService.ds_merge_check "
                f"{id1}<-{id2} failed: {e.__class__.__name__} {e}",
            }

    def ds_obj_remove_gramps_handles(self, batch_id):
        """Remove all Gramps handles."""
        status = Status.OK
        total = 0
        unlinked = 0
        # Remove handles from nodes connected to given Batch
        result = self.tx.run(CypherRoot.remove_all_handles, batch_id=batch_id)
        for count, label in result:
            print(f"# - cleaned {count} {label} handles")
            total += count
        # changes = result.summary().counters.properties_set

        # Find handles left: missing link (:Batch) --> (x)
        result = self.tx.run(CypherRoot.find_unlinked_nodes)
        for count, label in result:
            print(
                f"Neo4jUpdateService.ds_obj_remove_gramps_handles WARNING: Found {count} {label} not linked to batch"
            )
            unlinked += count
        return {"status": status, "count": total, "unlinked": unlinked}

    # ----- Citation -----

    def ds_save_citation(self, tx, citation, batch_id):
        """Saves this Citation and connects it to it's Notes and Sources."""
        citation.uuid = NodeObject.newUuid()

        c_attr = {
            "uuid": citation.uuid,
            "handle": citation.handle,
            "change": citation.change,
            "id": citation.id,
            "page": citation.page,
            "confidence": citation.confidence,
        }
        if citation.dates:
            c_attr.update(citation.dates.for_db())

        result = tx.run(
            CypherCitation.create_to_batch,
            batch_id=batch_id,
            c_attr=c_attr,
        )
        ids = []
        for record in result:
            citation.uniq_id = record[0]
            ids.append(citation.uniq_id)
            if len(ids) > 1:
                print(
                    "iError updated multiple Citations {} - {}, attr={}".format(
                        citation.id, ids, c_attr
                    )
                )

        # Make relations to the Note nodes
        for handle in citation.note_handles:
            tx.run(
                CypherCitation.link_note, handle=citation.handle, hlink=handle
            )

        # Make relation to the Source node
        if citation.source_handle != "":
            tx.run(
                CypherCitation.link_source,
                handle=citation.handle,
                hlink=citation.source_handle,
            )


    # ----- Note -----

    def ds_save_note_list(self, tx, parent, batch_id):
        """Save the parent.notes[] objects as a descendant of the parent node.

        Arguments:
            parent          NodeObject  Object to link: (parent) --> (Note)
            - parent.notes  list        Note objects
            batch_id        str         Batch id, alternative object to link:
                                        (:Batch{id:batch_id}) --> (Note)

        Called from bl.person.PersonBl.save, models.gen.repository.Repository.save
        """
        n_cnt = 0
        for note in parent.notes:
            if isinstance(note, Note):
                if not note.id:
                    n_cnt += 1
                    note.id = f"N{n_cnt}-{parent.id}"
                self.ds_save_note(tx, note, batch_id, parent.uniq_id)
            else:
                raise AttributeError("note.save_note_list: Argument not a Note")

    def ds_save_note(self, tx, note, batch_id, parent_id=None):
        """Creates this Note object as a Note node

        Arguments:
            parent_uid      uniq_id     Object to link: (parent) --> (Note)
            batch_id        str         Batch id, alternative object to link:
                                        (:Batch{id:batch_id}) --> (Note)
        """
        note.uuid = NodeObject.newUuid()
        if not "batch_id":
            raise RuntimeError(f"Note.save needs batch_id for {note.id}")
        n_attr = {
            "uuid": note.uuid,
            #"change": note.change,
            "id": note.id,
            "priv": note.priv,
            "type": note.type,
            "text": note.text,
            "url": note.url,
        }
        if note.handle:
            n_attr["handle"] = note.handle
        if not parent_id is None:
            # print(f"Note.save: (Root {batch_id}) --> (Note {note.id}) <-- (parent {parent_id})")
            result = tx.run(
                CypherNote.create_in_batch_as_leaf,
                bid=batch_id,
                parent_id=parent_id,
                n_attr=n_attr,
            )
        elif not batch_id is None:
            # print(f"Note.save: (Root {batch_id}) --> (Note {note.id})")
            result = tx.run(
                CypherNote.create_in_batch, 
                bid=batch_id, 
                n_attr=n_attr
            )
        else:
            raise RuntimeError(
                f"Note.save needs batch_id or parent_id for {note.id}"
            )
        record = result.single()
        # print(f"Note.save: summary={result.summary().counters}")
        note.uniq_id = record[0]

    # ----- Media -----

    def ds_save_media(self, tx, media, batch_id):
        """Saves this new Media object to db.

        #TODO: Process also Notes for media?
        #TODO: Use MediaWriteService
        """
        media.uuid = NodeObject.newUuid()
        m_attr = {
            "handle": media.handle,
            "change": media.change,
            "id": media.id,
            "src": media.src,
            "mime": media.mime,
            "name": media.name,
            "description": media.description,
        }
        m_attr["batch_id"] = batch_id
        result = tx.run(
            CypherMedia.create_in_batch,
            bid=batch_id,
            uuid=media.uuid,
            m_attr=m_attr,
        )
        media.uniq_id = result.single()[0]


    def ds_create_link_medias_w_handles(self, tx, uniq_id: int, media_refs: list):
        """Save media object and it's Note and Citation references
        using their Gramps handles.

        media_refs:
            media_handle      # Media object handle
            media_order       # Media reference order nr
            crop              # Four coordinates
            note_handles      # list of Note object handles
            citation_handles  # list of Citation object handles
        """
        doing = "?"
        try:
            for resu in media_refs:
                r_attr = {"order": resu.media_order}
                if resu.crop:
                    r_attr["left"] = resu.crop[0]
                    r_attr["upper"] = resu.crop[1]
                    r_attr["right"] = resu.crop[2]
                    r_attr["lower"] = resu.crop[3]
                doing = f"(src:{uniq_id}) -[{r_attr}]-> Media {resu.media_handle}"
                # print(doing)
                result = tx.run(
                    CypherObjectWHandle.link_media,
                    root_id=uniq_id,
                    handle=resu.media_handle,
                    r_attr=r_attr,
                )
                # media_uid = result.single()[0]    # for media object
                media_uid = None
                for record in result:
                    if media_uid:
                        print(doing)
                        print(
                            f"ds_create_link_medias_w_handles: double link_media, "
                            f"replacing media_uid={media_uid} with uid={record[0]}. "
                            f"handle={resu.media_handle}"
                        )
                    else:
                        media_uid = record[0]

                for handle in resu.note_handles:
                    doing = f"{media_uid}->Note {handle}"
                    tx.run(
                        CypherObjectWHandle.link_note, root_id=media_uid, handle=handle
                    )

                for handle in resu.citation_handles:
                    doing = f"{media_uid}->Citation {handle}"
                    tx.run(
                        CypherObjectWHandle.link_citation,
                        root_id=media_uid,
                        handle=handle,
                    )

        except Exception as err:
            traceback.print_exc()
            logger.error(
                f"Neo4jUpdateService.create_link_medias_by_handles {doing}: {err}"
            )

    # ----- Place -----

    def ds_save_place(self, tx, place, batch_id, place_keys=None):
        """Save Place, Place_names, Notes and connect to hierarchy.

        :param: place_keys    dict {handle: uniq_id}
        :param: batch_id      batch id where this place is linked

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
        - Notes are linked to self using 'note_handles's (the Notes have been
          saved before)

        NOT Raises an error, if write fails.
        """

        # Create or update this Place

        place.uuid = place.newUuid()
        #TODO place.isotammi_id = place.new_isotammi_id(dataservice, "P")
        pl_attr = {
            "uuid": place.uuid,
            "handle": place.handle,
            "change": place.change,
            "id": place.id,
            "type": place.type,
            "pname": place.pname,
        }
        if place.coord:
            # If no coordinates, don't set coord attribute
            pl_attr["coord"] = place.coord.get_coordinates()

        # Create Place place

        if place_keys:
            # Check if this Place node is already created
            plid = place_keys.get(place.handle)
        else:
            plid = None

        if plid:
            # 1) node has been created but not connected to Batch.
            #    update known Place node parameters and link from Batch
            place.uniq_id = plid
            if place.type:
                # print(f">Pl_save-1 Complete Place ({place.id} #{plid}) {place.handle} {place.pname}")
                result = tx.run(
                    CypherPlace.complete,  # TODO
                    batch_id=batch_id,
                    plid=plid,
                    p_attr=pl_attr,
                )
            else:
                # print(f">Pl_save-1 NO UPDATE Place ({place.id} #{plid}) attr={pl_attr}")
                pass
        else:
            # 2) new node: create and link from Batch
            # print(f">Pl_save-2 Create a new Place ({place.id} #{place.uniq_id} {place.pname}) {place.handle}")
            result = tx.run(CypherPlace.create, batch_id=batch_id, p_attr=pl_attr)
            place.uniq_id = result.single()[0]
            place_keys[place.handle] = place.uniq_id

        # Create Place_names

        for name in place.names:
            n_attr = {"name": name.name, "lang": name.lang}
            if name.dates:
                n_attr.update(name.dates.for_db())
            result = tx.run(
                CypherPlace.add_name,
                pid=place.uniq_id,
                order=name.order,
                n_attr=n_attr,
            )
            name.uniq_id = result.single()[0]
            # print(f"# ({place.uniq_id}:Place)-[:NAME]->({name.uniq_id}:{name})")

        # Select default names for default languages
        ret = PlaceBl.find_default_names(place.names, ["fi", "sv"])
        if ret.get("status") == Status.OK:
            # Update default language name links

            # def_names: dict {lang, uid} uniq_id's of PlaceName objects
            def_names = ret.get("ids")
            self.ds_place_set_default_names(tx, place.uniq_id, def_names["fi"], def_names["sv"])

        # Make hierarchy relations to upper Place nodes

        for ref in place.surround_ref:
            up_handle = ref["hlink"]
            # print(f"Pl_save-surrounding {place} -[{ref['dates']}]-> {up_handle}")
            if "dates" in ref and isinstance(ref["dates"], DateRange):
                rel_attr = ref["dates"].for_db()
                # _r = f"-[{ref['dates']}]->"
            else:
                rel_attr = {}
                # _r = f"-->"

            # Link to upper node

            uid = place_keys.get(up_handle) if place_keys else None
            if uid:
                # 3) Link to a known upper Place
                #    The upper node is already created: create a link to that
                #    upper Place node
                # print(f"Pl_save-3 Link ({place.id} #{place.uniq_id}) {_r} (#{uid})")
                result = tx.run(
                    CypherPlace.link_hier,
                    plid=place.uniq_id,
                    up_id=uid,
                    r_attr=rel_attr,
                )
            else:
                # 4) Link to unknown place
                #    A new upper node: create a Place with only handle
                #    parameter and link hierarchy to Place place
                # print(f"Pl_save-4 Link to empty upper Place ({place.id} #{place.uniq_id}) {_r} {up_handle}")
                result = tx.run(
                    CypherPlace.link_create_hier,
                    plid=place.uniq_id,
                    r_attr=rel_attr,
                    up_handle=up_handle,
                )
                place_keys[up_handle] = result.single()[0]


        for note in place.notes:
            n_attr = {"url": note.url, "type": note.type, "text": note.text}
            result = tx.run(
                CypherPlace.add_urls,
                batch_id=batch_id, pid=place.uniq_id, n_attr=n_attr)

        # Make the place note relations; the Notes have been stored before
        # TODO: There may be several Notes for the same handle! You shold use uniq_id!

        for n_handle in place.note_handles:
            result = tx.run(
                CypherPlace.link_note,
                pid=place.uniq_id, hlink=n_handle)

        for handle in place.citation_handles:
            # Link to existing Citation
            result = tx.run(
                CypherObject.link_citation, 
                handle=place.handle, c_handle=handle)

        if place.media_refs:
            # Make relations to the Media nodes and their Note and Citation references
            result = self.ds_create_link_medias_w_handles(
                tx, place.uniq_id, place.media_refs)


    def ds_place_set_default_names(self, tx, place_id, fi_id, sv_id):
        """Creates default links from Place to fi and sv PlaceNames.

        - place_id      Place object id
        - fi_id         PlaceName object id for fi
        - sv_id         PlaceName object id for sv
        """
        try:
            if fi_id == sv_id:
                result = tx.run(
                    CypherPlace.link_name_lang_single, place_id=place_id, fi_id=fi_id
                )
            else:
                result = tx.run(
                    CypherPlace.link_name_lang,
                    place_id=place_id,
                    fi_id=fi_id,
                    sv_id=sv_id,
                )
            x = None
            for x, _fi, _sv in result:
                # print(f"# Linked ({x}:Place)-['fi']->({fi}), -['sv']->({sv})")
                pass

            if not x:
                logger.warning(
                    "eo4jWriteDriver.place_set_default_names: not created "
                    f"Place {place_id}, names fi:{fi_id}, sv:{sv_id}"
                )

        except Exception as err:
            logger.error(f"Neo4jUpdateService.place_set_default_names: {err}")
            return err

    def ds_places_merge(self, id1, id2):
        """Merges given two Place objects using apoc library."""
        try:
            self.tx.run(CypherPlaceMerge.delete_namelinks, id=id1)
            record = self.tx.run(
                CypherPlaceMerge.merge_places, id1=id1, id2=id2
            ).single()
            node = record["node"]
            place = PlaceBl_from_node(node)
            name_nodes = record["names"]
            place.names = [PlaceName_from_node(n) for n in name_nodes]
        except ClientError as e:
            # traceback.print_exc()
            return {
                "status": Status.ERROR,
                "statustext": f"Neo4jUpdateService.ds_places_merge {id1}<-{id2} failed: {e.__class__.__name__} {e}",
            }

        return {"status": Status.OK, "place": place}

    # ----- Repository -----
    def ds_save_repository(self, tx, repository, batch_id):
        """Saves this Repository to db under given batch."""

        repository.uuid = NodeObject.newUuid()
        r_attr = {
            "uuid": repository.uuid,
            "handle": repository.handle,
            "change": repository.change,
            "id": repository.id,
            "rname": repository.rname,
            "type": repository.type,
        }
        result = tx.run(
            CypherRepository.create_in_batch,
            bid=batch_id,
            r_attr=r_attr
        )
        repository.uniq_id = result.single()[0]

        # Save the notes attached to repository
        if repository.notes:
            self.ds_save_note_list(tx, parent=repository, batch_id=batch_id)

        return

    # ----- Source -----

    def ds_save_source(self, tx, source, batch_id):   
        """ Saves this Source and connect it to Notes and Repositories.

            :param: batch_id      batch id where this source is linked

        """
        source.uuid = NodeObject.newUuid()
        s_attr = {}
        try:
            s_attr = {
                "uuid": source.uuid,
                "handle": source.handle,
                "change": source.change,
                "id": source.id,
                "stitle": source.stitle,
                "sauthor": source.sauthor,
                "spubinfo": source.spubinfo
            }

            result = tx.run(CypherSourceByHandle.create_to_batch,
                            batch_id=batch_id, s_attr=s_attr)
            ids = []
            for record in result:
                source.uniq_id = record[0]
                ids.append(source.uniq_id)
                if len(ids) > 1:
                    print("iError updated multiple Sources {} - {}, attr={}".format(source.id, ids, s_attr))

        except Exception as err:
            print("iError source_save: {0} attr={1}".format(err, s_attr))
            raise RuntimeError("Could not save Source {}".format(source.id))

        # Make relation to the Note nodes
        for note_handle in source.note_handles:
            try:
                tx.run(CypherSourceByHandle.link_note, 
                       handle=source.handle, hlink=note_handle)
            except Exception as err:
                logger.error(f"Source_gramps.save: {err} in linking Notes {source.handle} -> {source.note_handles}")
                #print("iError Source.save note: {0}".format(err), file=stderr)

        # Make relation to the Repository nodes
        for repo in source.repositories:
            try:
                tx.run(CypherSourceByHandle.link_repository, 
                       handle=source.handle, 
                       hlink=repo.handle, 
                       medium=repo.medium)
            except Exception as err:
                print("iError Source.save Repository: {0}".format(err))
                

    def mergesources(self, id1, id2):
        cypher_mergesources = """
            match (p1:Source)        where id(p1) = $id1 
            match (p2:Source)        where id(p2) = $id2
            call apoc.refactor.mergeNodes([p1,p2],
                {properties:'discard',mergeRels:true})
            yield node
            return node
        """
        rec = self.tx.run(cypher_mergesources,id1=id1,id2=id2).single()
        if rec is None: return None
        node = rec['node']
        source = SourceBl_from_node(node)
        return source
            # ----- Citation -----

    # ----- Event -----
    def ds_save_event(self, tx, event, batch_id):
        """Saves event to database:
        - Creates a new db node for this Event
        - Sets self.uniq_id

        - links to existing Place, Note, Citation, Media objects
        - Does not link it from UserProfile or Person
        """

        event.uuid = NodeObject.newUuid()
        e_attr = {
            "uuid": event.uuid,
            "handle": event.handle,
            "change": event.change,
            "id": event.id,
            "type": event.type,
            "description": event.description,
        }
        if event.attr:
            # Convert 'attr' dict to list for db
            a = []
            for key, value in event.attr.items():
                a = a + [key, value]
                e_attr.update({"attr": a})
        if event.dates:
            e_attr.update(event.dates.for_db())

        result = tx.run(
            CypherEvent.create_to_batch, batch_id=batch_id, e_attr=e_attr
        )
        ids = []
        for record in result:
            event.uniq_id = record[0]
            ids.append(event.uniq_id)
            if len(ids) > 1:
                print(
                    "iError updated multiple Events {} - {}, attr={}".format(
                        event.id, ids, e_attr
                    )
                )

        # Make relation to the Place node
        for pl_handle in event.place_handles:
            tx.run(
                CypherEvent.link_place, handle=event.handle, place_handle=pl_handle
            )

        # Make relations to the Note nodes
        if event.note_handles:
            result = tx.run(
                CypherEvent.link_notes,
                handle=event.handle,
                note_handles=event.note_handles,
            )
            _cnt = result.single()["cnt"]
            # print(f"##Luotiin {cnt} Note-yhteyttä: {event.id}->{event.note_handles}")

        # Make relations to the Citation nodes
        if event.citation_handles:  #  citation_handles != '':
            tx.run(
                CypherEvent.link_citations,
                handle=event.handle,
                citation_handles=event.citation_handles,
            )

        # Make relations to the Media nodes and their Note and Citation references
        if event.media_refs:
            self.ds_create_link_medias_w_handles(
                tx, event.uniq_id, event.media_refs
            )

    # ----- Person -----

    def ds_save_person(self, tx, person, batch_id):
        """Saves the Person object and possibly the Names, Events ja Citations.

        On return, the self.uniq_id is set

        @todo: Remove those referenced person names, which are not among
               new names (:Person) --> (:Name)
        """

        person.uuid = NodeObject.newUuid()
        #TODO person.isotammi_id = person.new_isotammi_id(dataservice, "H")

        # Save the Person node under UserProfile; all attributes are replaced

        p_attr = {
            "uuid": person.uuid,
            "handle": person.handle,
            "change": person.change,
            "id": person.id,
            "priv": person.priv,
            "sex": person.sex,
            "confidence": person.confidence,
            "sortname": person.sortname,
        }
        if person.dates:
            p_attr.update(person.dates.for_db())

        result = tx.run(CypherPerson.create_to_batch, 
                        batch_id=batch_id, p_attr=p_attr)
        ids = []
        for record in result:
            person.uniq_id = record[0]
            ids.append(person.uniq_id)
            if len(ids) > 1:
                print(
                    "iError updated multiple Persons {} - {}, attr={}".format(
                        person.id, ids, p_attr
                    )
                )
            # print("Person {} ".format(person.uniq_id))
        if person.uniq_id == None:
            print("iWarning got no uniq_id for Person {}".format(p_attr))

        # Save Name nodes under the Person node
        for name in person.names:
            self.ds_save_name(tx, name, parent_id=person.uniq_id)

        # Save web urls as Note nodes connected under the Person
        if person.notes:
            self.ds_save_note_list(tx, parent=person, batch_id=batch_id)

        """ Connect to each Event loaded from Gramps """
        # for i in range(len(person.eventref_hlink)):
        for event_handle, role in person.event_handle_roles:
            tx.run(
                CypherPerson.link_event,
                p_handle=person.handle,
                e_handle=event_handle,
                role=role,
            )

        # Make relations to the Media nodes and it's Note and Citation references
        if person.media_refs:
            self.ds_create_link_medias_w_handles(
                tx, person.uniq_id, person.media_refs
            )

        # The relations to the Family node will be created in Family.save(),
        # because the Family object is not yet created

        # Make relations to the Note nodes

        for handle in person.note_handles:
            tx.run(CypherPerson.link_note, p_handle=person.handle, n_handle=handle)

        # Make relations to the Citation nodes

        for handle in person.citation_handles:
            tx.run(
                CypherObject.link_citation, handle=person.handle, c_handle=handle
            )
        return

    def ds_save_name(self, tx, name, parent_id):
        """Creates or updates this Name node. (There is no handle)
        If parent_id is given, a link (parent) -[:NAME]-> (Name) is created

        #TODO: Check, if this name exists; then update or create new
        """

        n_attr = {
            "order": name.order,
            "type": name.type,
            "firstname": name.firstname,
            "surname": name.surname,
            "prefix": name.prefix,
            "suffix": name.suffix,
            "title": name.title,
        }
        
        if name.dates:
            n_attr.update(name.dates.for_db())
            
        tx.run(
            CypherPerson.create_name_as_leaf,
            n_attr=n_attr,
            parent_id=parent_id,
            citation_handles=name.citation_handles,
        )

    def ds_get_personnames(self, uniq_id=None):
        """Picks all Name versions of this Person or all persons.

        Use optionally refnames or sortname for person selection
        """
        if uniq_id:
            result = self.tx.run(CypherPerson.get_names, pid=uniq_id)
        else:
            result = self.tx.run(CypherPerson.get_all_persons_names)
        # <Record
        #    pid=82
        #    name=<Node id=83 labels=frozenset({'Name'})
        #        properties={'title': 'Sir', 'firstname': 'Jan Erik', 'surname': 'Mannerheimo',
        #            'prefix': '', 'suffix': 'Jansson', 'type': 'Birth Name', 'order': 0}> >

        return [(record["pid"], record["name"]) for record in result]

    def ds_set_people_lifetime_estimates(self, uids):
        """Get estimated lifetimes to Person.dates for given person.uniq_ids.

        :param: uids  list of uniq_ids of Person nodes; empty = all lifetimes
        """
        from models import lifetime
        from models.lifetime import BIRTH, DEATH, BAPTISM, BURIAL #, MARRIAGE
        from bl.dates import DR
        
        def sortkey(event): # sorts events so that BIRTH, DEATH, BAPTISM, BURIAL come first
            if event.eventtype in (BIRTH, DEATH):
                return 0
            elif event.eventtype in (BAPTISM, BURIAL):
                return 1
            else:
                return 2
            
        personlist = []
        personmap = {}
        res = {"status": Status.OK}
        # print(f"### ds_set_people_lifetime_estimates: self.tx = {self.tx}")

        if uids is not None:
            result = self.tx.run(
                CypherPerson.fetch_selected_for_lifetime_estimates, idlist=uids
            )
        else: # for whole database, this is not actually used?
            result = self.tx.run(CypherPerson.fetch_all_for_lifetime_estimates)
        # RETURN p, id(p) as pid,
        #     COLLECT(DISTINCT [e,r.role]) AS events,
        #     COLLECT(DISTINCT [fam_event,r2.role]) AS fam_events,
        #     COLLECT(DISTINCT [c,id(c)]) as children,
        #     COLLECT(DISTINCT [parent,id(parent)]) as parents
        for record in result:
            # Person
            p = lifetime.Person()
            p.pid = record["pid"]
            p.gramps_id = record["p"]["id"]

            # Person and family event dates
            events = record["events"]
            fam_events = record["fam_events"]
            for e, role in events + fam_events:
                if e is None:
                    continue
                # print("e:",e)
                eventtype = e["type"]
                datetype = e["datetype"]
                datetype1 = None
                datetype2 = None
                date1 = e["date1"]
                date2 = e["date2"]
                year1 = None
                year2 = None
                if date1: year1 = date1 // 1024 
                if date2: year2 = date1 // 1024 
                if datetype == DR["DATE"]:
                    datetype1 = "exact"
                elif datetype == DR["BEFORE"]:
                    datetype1 = "before"
                elif datetype == DR["AFTER"]:
                    datetype1 = "after"
                elif datetype == DR["BETWEEN"]:
                    datetype1 = "after"
                    datetype2 = "before"
                elif datetype == DR["PERIOD"]:
                    if eventtype in (BIRTH, DEATH, BAPTISM, BURIAL):
                        # cannot be a span, must be between
                        datetype = DR["BETWEEN"]
                        datetype1 = "after"
                        datetype2 = "before"
                    else:
                        datetype1 = "exact"
                        datetype2 = "exact"
                elif datetype == DR["ABOUT"]:
                    year1 = year1 - 50
                    year2 = year2 + 50
                    datetype1 = "after"
                    datetype2 = "before"
                if datetype1 and year1 is not None:
                    #year1 = date1 // 1024
                    ev = lifetime.Event(eventtype, datetype1, year1, role)
                    p.events.append(ev)
                if datetype2 and year2 is not None:
                    #year2 = date2 // 1024
                    ev = lifetime.Event(eventtype, datetype2, year2, role)
                    p.events.append(ev)
                p.events.sort(key=sortkey)
                    

            # List Parent, Child and Spouse identities
            p.parent_pids = []
            for _parent, pid in record["parents"]:
                if pid:
                    p.parent_pids.append(pid)

            p.child_pids = []
            for _parent, pid in record["children"]:
                if pid:
                    p.child_pids.append(pid)

            p.spouse_pids = []
            for _spouse, pid in record["spouses"]:
                if pid:
                    p.spouse_pids.append(pid)

            # print(f"#> lifetime.Person {p}")
            personlist.append(p)
            personmap[p.pid] = p

        # Add parents and children to lifetime.Person objects
        for p in personlist:
            for pid in p.parent_pids:
                xid = personmap.get(pid)
                if xid:
                    p.parents.append(xid)
            for pid in p.child_pids:
                xid = personmap.get(pid)
                if xid:
                    p.children.append(xid)
            for pid in p.spouse_pids:
                xid = personmap.get(pid)
                if xid:
                    p.spouses.append(xid)
        lifetime.calculate_estimates(personlist)

        for p in personlist:
            result = self.tx.run(
                CypherPerson.update_lifetime_estimate,
                id=p.pid,
                birth_low=p.birth_low.getvalue(),
                death_low=p.death_low.getvalue(),
                birth_high=p.birth_high.getvalue(),
                death_high=p.death_high.getvalue(),
            )

        res["count"] = len(personlist)
        # print(f"Estimated lifetime for {res['count']} persons")
        return res


    def ds_build_refnames(self, person_uid: int, name: Name):
        """Set Refnames to the Person with given uniq_id."""

        def link_to_refname(person_uid, nm, use):
            result = self.tx.run(
                CypherRefname.link_person_to, pid=person_uid, name=nm, use=use
            )
            rid = result.single()[0]
            if rid is None:
                raise RuntimeError(f"Error for ({person_uid})-->({nm})")
            return rid

        count = 0
        # 1. firstnames
        if name.firstname and name.firstname != "N":
            for nm in name.firstname.split(" "):
                if link_to_refname(person_uid, nm, "firstname"):
                    count += 1

        # 2. surname and patronyme
        if name.surname and name.surname != "N":
            if link_to_refname(person_uid, name.surname, "surname"):
                count += 1

        if name.suffix:
            if link_to_refname(person_uid, name.suffix, "patronyme"):
                count += 1
        #xxx
        return {"status": Status.OK, "count": count}

    def ds_update_person_confidences(self, uniq_id: int):
        """Collect Person confidence from Person and Event nodes and store result in Person.

        Voidaan lukea henkilön tapahtumien luotettavuustiedot kannasta
        """
        sumc = 0
        confs = []
        result = self.tx.run(CypherPerson.get_confidences, id=uniq_id)
        for record in result:
            # Returns person.uniq_id, COLLECT(confidence) AS list
            orig_conf = record["confidence"]
            confs = record["list"]
            for conf in confs:
                sumc += int(conf)

        if confs:
            conf_float = sumc / len(confs)
            new_conf = "%0.1f" % conf_float  # string with one decimal
        else:
            new_conf = ""
        if orig_conf != new_conf:
            # Update confidence needed
            self.tx.run(
                CypherPerson.set_confidence, id=uniq_id, confidence=new_conf
            )
            return {"confidence": new_conf, "status": Status.UPDATED}
        return {"confidence": new_conf, "status": Status.OK}


    def ds_link_person_to_refname(self, pid, name, reftype): # not used?
        """Connects a reference name of type reftype to Person(pid)."""
        from bl.refname import REFTYPES

        if not name > "":
            logging.warning("Missing name {} for {} - not added".format(reftype, name))
            return
        if not (reftype in REFTYPES):
            raise ValueError("Invalid reftype {}".format(reftype))
            return

        try:
            _result = self.tx.run(
                CypherRefname.link_person_to, pid=pid, name=name, use=reftype
            )
            return {"status": Status.OK}

        except Exception as e:
            msg = f"Neo4jUpdateService.ds_link_person_to_refname: person={pid}, {e.__class__.__name__}, {e}"
            print(msg)
            return {"status": Status.ERROR, "statustext": msg}

    # ----- Refname -----

    def ds_get_person_by_uid(self, uniq_id: int):
        """Set Person object by uniq_id.

        NOT USED!
        """
        try:
            self.tx.run(CypherPerson.get_person_by_uid, uid=uniq_id)
            return {"status": Status.OK}
        except Exception as e:
            msg = f"Neo4jUpdateService.ds_get_person_by_uid: person={uniq_id}, {e.__class__.__name__}, {e}"
            print(msg)
            return {"status": Status.ERROR, "statustext": msg}

    def ds_set_person_sortname(self, uniq_id: int, sortname):
        """ Set sortname property to Person object by uniq_id."""
        self.tx.run(CypherPerson.set_sortname, uid=uniq_id, key=sortname)
        return {"status": Status.OK}

    # ----- Family -----

    def ds_set_family_dates_sortnames(
        self, uniq_id, dates, father_sortname, mother_sortname
    ):
        """Update Family dates and parents' sortnames.

        :param:    uniq_id      family identity
        :dates:    dict         representing DateRange for family
                                (marriage ... death or divorce

        Called from self.ds_set_family_calculated_attributes only
        """
        f_attr = {
            "father_sortname": father_sortname,
            "mother_sortname": mother_sortname,
        }
        if dates:
            f_attr.update(dates)

        result = self.tx.run(CypherFamily.set_dates_sortname, id=uniq_id, f_attr=f_attr)
        counters = result.consume().counters
        cnt = counters.properties_set
        return {"status": Status.OK, "count": cnt}

    def ds_set_family_calculated_attributes(self, uniq_id=None):
        """Set Family sortnames and estimated marriage DateRange.

        :param: uids  list of uniq_ids of Person nodes; empty = all lifetimes

        Called from bp.gramps.xml_dom_handler.DOM_handler.set_family_calculated_attributes

        Set Family.father_sortname and Family.mother_sortname using the data in Person
        Set Family.date1 using the data in marriage Event
        Set Family.datetype and Family.date2 using the data in divorce or death Events
        """
        from bl.dates import DateRange, DR

        dates_count = 0
        sortname_count = 0
        status = Status.OK
        # print(f"### ds_set_family_calculated_attributes: self.tx = {self.tx}")
        # Process the family
        #### Todo Move and refactor to bl.FamilyBl
        # result = Family_combo.get_dates_parents(my_tx, uniq_id)
        result = self.tx.run(CypherFamily.get_dates_parents, id=uniq_id)
        for record in result:
            # RETURN father.sortname AS father_sortname, father_death.date1 AS father_death_date,
            #        mother.sortname AS mother_sortname, mother_death.date1 AS mother_death_date,
            #        event.date1 AS marriage_date, divorce_event.date1 AS divorce_date
            father_death_date = record["father_death_date"]
            mother_death_date = record["mother_death_date"]
            marriage_date = record["marriage_date"]
            divorce_date = record["divorce_date"]

            # Dates calculation
            dates = None
            end_date = None
            if divorce_date:
                end_date = divorce_date
            elif father_death_date and mother_death_date:
                if father_death_date < mother_death_date:
                    end_date = father_death_date
                else:
                    end_date = mother_death_date
            elif father_death_date:
                end_date = father_death_date
            elif mother_death_date:
                end_date = mother_death_date

            if marriage_date:
                if end_date:
                    dates = DateRange(DR["PERIOD"], marriage_date, end_date)
                else:
                    dates = DateRange(DR["DATE"], marriage_date)
            elif end_date:
                dates = DateRange(DR["BEFORE"], end_date)
            dates_dict = dates.for_db() if dates else None

            # Save the dates from Event node and sortnames from Person nodes
            ret = self.ds_set_family_dates_sortnames(
                uniq_id,
                dates_dict,
                record.get("father_sortname"),
                record.get("mother_sortname"),
            )
            # print('Neo4jUpdateService.ds_set_family_calculated_attributes: '
            #      f'id={uniq_id} properties_set={ret.get("count","none")}')
            dates_count += 1
            sortname_count += 1

        return {
            "status": status,
            "dates": dates_count,
            "sortnames": sortname_count,
            "statustext": ret.get("statustext", ""),
        }

    def ds_save_family(self, tx, f:FamilyBl, batch_id):
        """Saves the family node to db with its relations.

        Connects the family to parent, child, citation and note nodes.
        """
        f.uuid = NodeObject.newUuid()
        #TODO self.isotammi_id = self.new_isotammi_id(dataservice, "F")
        f_attr = {
            "uuid": f.uuid,
            "handle": f.handle,
            "change": f.change,
            "id": f.id,
            "rel_type": f.rel_type,
        }
        result = tx.run(
            CypherFamily.create_to_batch, batch_id=batch_id, f_attr=f_attr
        )
        ids = []
        for record in result:
            f.uniq_id = record[0]
            ids.append(f.uniq_id)
            if len(ids) > 1:
                logger.warning(
                    f"bl.family.FamilyBl.save updated multiple Families {self.id} - {ids}, attr={f_attr}"
                )

        # Make father and mother relations to Person nodes

        if hasattr(f, "father") and f.father:
            tx.run(
                CypherFamily.link_parent,
                role="father",
                f_handle=f.handle,
                p_handle=f.father,
            )

        if hasattr(f, "mother") and f.mother:
            tx.run(
                CypherFamily.link_parent,
                role="mother",
                f_handle=f.handle,
                p_handle=f.mother,
            )

        # Make relations to Event nodes

        for handle_role in f.event_handle_roles:
            # a tuple (event_handle, role)
            tx.run(
                CypherFamily.link_event,
                f_handle=f.handle,
                e_handle=handle_role[0],
                role=handle_role[1],
            )

        # Make child relations to Person nodes

        for handle in f.child_handles:
            tx.run(CypherFamily.link_child, f_handle=f.handle, p_handle=handle)

        # Make relation(s) to the Note node

        # print(f"Family_gramps.save: linking Notes {self.handle} -> {self.note_handles}")
        for handle in f.note_handles:
            tx.run(CypherFamily.link_note, f_handle=f.handle, n_handle=handle)

        # Make relation(s) to the Citation node

        # print(f"Family_gramps.save: linking Citations {self.handle} -> {self.citationref_hlink}")
        for handle in f.citation_handles:
            tx.run(
                CypherObject.link_citation, handle=f.handle, c_handle=handle
            )


    # ----- Discussions -----

    def ds_comment_save(self, attr):
        """Creates a Comment node linked from commenting object and the commenter.

        attr = {object_id:int, username:str, title:str, text:str, reply:bool}

        Comment.timestamp is created in the Cypher clause.
        
        Case object_id refers to a Comment or Topic, create a Comment; else create a Topic
        """
        is_reply = attr.get("reply")
        if is_reply:
            cypher = CypherComment.create_comment
        else: # default
            cypher = CypherComment.create_topic

        record = self.tx.run(cypher, attr=attr).single()
        if not record:
            raise IsotammiException(
                "Unable to save " + "Comment" if is_reply else "Topic",
                cypher=cypher, attr=attr)

        node = record.get("comment")
        if not node:
            return {"status": Status.ERROR, "statustext": _("Could not save a comment")}
        comment = Comment_from_node(node)
        comment.obj_type = record.get("obj_type")
        comment.user = attr.get("username")
        return {"status": Status.OK, "comment": comment}

