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
from collections import defaultdict
from datetime import date  # , datetime
from neo4j.exceptions import ClientError

logger = logging.getLogger("stkserver")

from bl.base import Status, IsotammiException, NodeObject #, NodeObject
from bl.person import Person
from bl.person_name import Name
from bl.place import PlaceBl
from bl.family import FamilyBl
from bl.note import Note
from bl.dates import DateRange, DR

from pe.dataservice import ConcreteService

from .cypher.cy_citation import CypherCitation
from .cypher.cy_comment import CypherComment
from .cypher.cy_event import CypherEvent
from .cypher.cy_family import CypherFamily
from .cypher.cy_gramps import CypherLink
from .cypher.cy_media import CypherMedia
from .cypher.cy_note import CypherNote
from .cypher.cy_person import CypherPerson
from .cypher.cy_place import CypherPlace, CypherPlaceMerge
from .cypher.cy_refname import CypherRefname
from .cypher.cy_repository import CypherRepository
from .cypher.cy_root import CypherRoot, CypherAudit
from .cypher.cy_source import CypherSource

from pe.neo4j.nodereaders import Comment_from_node
from pe.neo4j.nodereaders import PlaceBl_from_node
from pe.neo4j.nodereaders import PlaceName_from_node
from pe.neo4j.nodereaders import SourceBl_from_node
from pe.neo4j.util import IidGenerator



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
        return record["id"] #{"status": Status.OK, "identity": iid}


    def ds_batch_set_state(self, batch_id, user, state):
        """Updates Batch node selected by Batch id and user.
        
            Called: bl.batch.root_updater.RootUpdater.change_state,
                    bp.admin.uploads.get_meta
        """
        result = self.tx.run(
            CypherRoot.batch_set_state, bid=batch_id, user=user, state=state
        )
        bid = result.single()[0]
        return {"status": Status.OK, "identity": bid}

    # ---- Auditor ops ----

    def ds_batch_set_access(self, batch_id, auditor_user):
        """Checks, if auditor has read access to this batch.
           If not, creates a HAS_ACCESS relation from UserProfile to Root.
        """
        result1 = self.tx.run(CypherAudit.does_need_batch_access, 
                             bid=batch_id, audi=auditor_user)
        for record1 in result1:
            # Returned batch id => must create a HAS_ACCESS for browsing; else no match
            _user = record1[0]
            result = self.tx.run(CypherAudit.batch_set_access, 
                                 bid=batch_id, audi=auditor_user)
            for record in result:
                root_id = record["bid"]
                rel_id = record["rel_id"]
                return {"status": Status.UPDATED, "identity": root_id, "rel_id": rel_id}
        # No match: no need create a HAS_ACCESS for browsing
        return {"status": Status.OK}

    def ds_batch_end_auditions(self, batch_id, auditor_user):
        """Removes active auditors by replacing DOES_AUDIT relations with DID_AUDIT.
        """
        removed = []
        st = Status.OK
        result = self.tx.run(CypherAudit.batch_end_audition, bid=batch_id)
        for record in result:
            username = record.get("user")
            rel_id = record.get("relation_new").id
            print("#Neo4jUpdateService.ds_batch_end_auditions: removed "
                  f"rel={rel_id} DOES_AUDIT from {username}")
            removed.append(username)
            st = Status.UPDATED

        return {"status": st, "removed_auditors": removed}

    def ds_batch_start_audition(self, batch_id, auditor_user, old_states):
        """Updates Batch node selected by Batch id and user.

           - Check that the state is expected
           - Updates Batch node selected by Batch id and user
           - Create DOES_AUDIT link
        """
        result = self.tx.run(CypherAudit.batch_start_audition, 
                             bid=batch_id, audi=auditor_user, states=old_states
        )
        for record in result:
            root_id = record[0]
            return {"status": Status.OK, "identity": root_id}
        return {"status": Status.NOT_FOUND}

    def ds_batch_set_audited(self, batch_id, user, new_state):
        """Updates the auditing Batch node and return duration.
        
           The DOES_AUDIT link have been changed to DID_AUDIT
           by ds_batch_end_auditions().
        """
        auditors=[]
        result = self.tx.run(CypherAudit.batch_set_state_complete, 
                             audi=user, bid=batch_id, state=new_state)
        # _Record__keys (root, audi, relation_new)
        for record in result:
            node_root = record["root"]
            node_audi = record["audi"]
            r = record["relation_new"]
            ts_from = r.get("ts_from")
            ts_to = r.get("ts_to", 0)
            root_id = node_root.id # Batch id
            #!audi_id = node_audi.id
            auditor = node_audi["username"]
            auditors.append(auditor)
            try:
                d_days = (ts_to - ts_from) / (1000*60*60*24)
            except Exception:
                d_days = "?"
            print(f"#ds_batch_set_audited: (:UserProfile({auditor}))"
                  f" DID_AUDIT {ts_from}..{ts_to} ->"
                  f" (:Root({batch_id})), {d_days} days")

        if not auditors:
            return {"status": Status.ERROR, "text": "No match", "d_days": 0}
        return {"status": Status.OK, "identity": root_id, "d_days": d_days}
        #return {"status": Status.OK, "auditors": auditors}

    # def ds_batch_remove_auditor(self, batch_id, auditor_user, new_state): -> ds_batch_set_audited

    #- --- End auditor ops ----
    
    def ds_batch_purge_access(self, batch_id, auditor_user):
        """Removes other auditors, if there are multiple auditors.
           (Used to revert multi-auditor operations.)
        """
        result = self.tx.run(CypherRoot.batch_purge_access, 
                             bid=batch_id, audi=auditor_user)
        removed = []
        for record in result:
            # <Record id=190386, rel_id="...">
            rel_id = record.get("rel_id")
            if rel_id:
                print("#Neo4jUpdateService.ds_batch_purge_access: removed "
                      f"id={rel_id} DOES_AUDIT from {auditor_user}")
                removed.append(auditor_user)
                return {"status": Status.UPDATED, "removed_auditors": removed}

        return  {"status": Status.NOT_FOUND, "removed_auditors": removed}


    # ----- Common objects -----

    def ds_merge_check(self, id1, id2):
        """Check that given objects are mergeable.

        Rules:
        - Objects have same label
        - Both objects have the same type of end relation (OWNS or PASSED)
        """

        class RefObj:
            def __str__(self):
                return f"{self.iid}:{self.label} {self.str}"

        return {"status": Status.OK}  # TODO
        objs = {}
        try:
            print("pe.neo4j.updateservice.Neo4jUpdateService.ds_merge_check: TODO fix merge_check")
            # result = self.tx.run(CypherAudit.merge_check, id_list=[id1, id2])
            # # for root_id, root_str, rel, obj_id, obj_label, obj_str in result:
            # for record in result:
            #     ro = RefObj()
            #     ro.iid = record["obj_id"]
            #     ro.label = record["obj_label"]
            #     ro.str = record["obj_str"]
            #     ro.root = (
            #         record.get("rel"),
            #         record.get("root_id"),
            #         record.get("root_str"),
            #     )
            #     # rint(f'#ds_merge_check {root_id}:{root_str} -[{rel}]-> {obj_id}:{obj_label} {obj_str}')
            #     print(f"#ds_merge_check {ro.iid}:{ro.label} {ro.str} in {ro.root}")
            #     if ro.iid in objs.keys():
            #         # Error if current iid exists twice
            #         msg = f"Object {ro} has two roots {objs[ro.iid].root} and {ro.root}"
            #         return {"status": Status.ERROR, "statustext": msg}
            #     for i, obj2 in objs.items():
            #         print(f"#ds_merge_check {obj2} <> {ro}")
            #         if i == ro.iid:
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
            #     objs[ro.iid] = ro

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

    # def obolete_ds_obj_remove_gramps_handles(self, batch_id):
    #     """Remove all Gramps handles."""
    #     status = Status.OK
    #     total = 0
    #     unlinked = 0
    #     # Remove handles from nodes connected to given Batch
    #     result = self.tx.run(CypherRoot.remove_all_handles, batch_id=batch_id)
    #     for count, label in result:
    #         print(f"# - cleaned {count} {label} handles")
    #         total += count
    #     # changes = result.summary().counters.properties_set
    #
    #     # Find handles left: missing link (:Batch) --> (x)
    #     result = self.tx.run(CypherRoot.find_unlinked_nodes)
    #     for count, label in result:
    #         print(
    #             f"Neo4jUpdateService.ds_obj_remove_gramps_handles WARNING: Found {count} {label} not linked to batch"
    #         )
    #         unlinked += count
    #     return {"status": status, "count": total, "unlinked": unlinked}

    # ----- Citation -----

    def ds_save_citation(self, tx, citation, batch_id, iids):
        """Saves this Citation and connects it to it's Notes and Sources."""
        citation.iid = iids.get_one()

        c_attr = {
            "iid": citation.iid,
            "handle": citation.handle,
            "change": citation.change,
            "id": citation.id,
            "page": citation.page,
            "confidence": citation.confidence,
            "attrs": citation.attrs_for_db(),
        }
        if citation.dates:
            c_attr.update(citation.dates.for_db())

        tx.run(CypherCitation.create_to_batch, batch_id=batch_id, c_attr=c_attr)
        #!ids = []
        # for record in result:
        #     citation.iid = record[0]
        #     ids.append(citation.iid)
        #     if len(ids) > 1:
        #         print(
        #             "iError updated multiple Citations {} - {}, attr={}".format(
        #                 citation.id, ids, c_attr
        #             )
        #         )

        # Make relations to the Note nodes
        if citation.note_handles:
            query = CypherLink.link_handle("Citation", "Note")
            for hlink in citation.note_handles:
                tx.run(query, src=citation.handle, dst=hlink)
        #!for handle in citation.note_handles:
        #     tx.run(CypherCitation.c_link_note, handle=citation.handle, hlink=handle)

        # Make relation to the Source node
        if citation.source_handle:
            query = CypherLink.link_handle("Citation", "Source")
            tx.run(query, src=citation.handle, dst=citation.source_handle)
            #! tx.run(CypherCitation.link_source, handle=citation.handle, hlink=citation.source_handle)


    # ----- Note -----

    def ds_save_note_list(self, tx, parent:NodeObject, batch_id, iids:IidGenerator):
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
                    note.id = f"N{n_cnt}.{parent.id}"
                self.ds_save_note(tx, note, batch_id, iids, parent.iid)
            else:
                raise AttributeError("note.save_note_list: Argument not a Note")

    def ds_save_note(self, tx, note, batch_id, iids, parent_id=None):
        """Creates this Note object as a Note node

        Arguments:
            parent_id       str         Object to link: (parent) --> (Note)
            batch_id        str         Batch id, alternative object to link:
                                        (:Batch{id:batch_id}) --> (Note)
        """
        #from bl.dates import ITimer
        #elapsed = ITimer()  # Start timer

        note.iid = iids.get_one()
        if not batch_id:
            raise RuntimeError(f"Note.save needs batch_id for {note.id}")
        n_attr = {
            "iid": note.iid,
            #"change": note.change,
            "id": note.id,
            "priv": note.priv,
            "type": note.type,
            "text": note.text,
            "url": note.url,
            "attrs": note.attrs_for_db(),
        }
        if note.handle:
            n_attr["handle"] = note.handle
        # if note.url: print(f"#ds_save_note: {note.iid} {note.url!r}")
        if not parent_id is None:
            tx.run(CypherNote.create_in_batch_as_leaf(parent_id),
                   bid=batch_id,
                   parent_id=parent_id,
                   n_attr=n_attr,
            )
        elif not batch_id is None:
            # print(f"#Neo4jUpdateService.ds_save_note: {batch_id=}, {n_attr=}")
            tx.run(CypherNote.create_in_batch, 
                   bid=batch_id,
                   n_attr=n_attr,
            )
        else:
            raise RuntimeError(
                f"Note.save needs batch_id or parent_id for {note.id}"
            )
        #print(f"Note.save: ({batch_id}) --> ({note.id}) <-- ({parent_id}) | {elapsed}")


    # ----- Media -----

    def ds_save_media(self, tx, media, batch_id, iids):
        """Saves this new Media object to db.

        #TODO: Process also Notes for media?
        #TODO: Use MediaWriteService
        """
        media.iid = iids.get_one()
        m_attr = {
            "iid": media.iid,
            "handle": media.handle,
            "change": media.change,
            "id": media.id,
            "src": media.src,
            "mime": media.mime,
            "name": media.name,
            "description": media.description,
            "attrs": media.attrs_for_db(),
            "batch_id": batch_id,
        }
        #m_attr["batch_id"] = batch_id

        _result = tx.run(CypherMedia.create_in_batch,
            bid=batch_id, iid=media.iid, m_attr=m_attr)
        #!media.iid = result.single()[0]

        # Make relation(s) to the Note and Citation nodes

        if media.note_handles:
            query = CypherLink.link_handle("Media", "Note")
            for hlink in media.note_handles:
                tx.run(query, src=media.handle, dst=hlink)
        #! if media.note_handles:
        #     result = tx.run(
        #         CypherMedia.m_link_notes,
        #         handle=media.handle,
        #         hlinks=media.note_handles,
        #         )
        #     _cnt=result.single()["cnt"]

        if media.citation_handles:
            query = CypherLink.link_handle("Media", "Citation")
            for hlink in media.citation_handles:
                tx.run(query, src=media.iid, dst=hlink)
        #! if media.citation_handles:  #  citation_handles != '':
        #     tx.run(
        #         CypherMedia.m_link_citations,
        #         handle=media.handle,
        #         hlinks=media.citation_handles,
        #     )


    def ds_create_link_medias_w_handles(self, tx, src_handle, media_refs: list):
        """Save media object and it's Note and Citation references
        using their Gramps handles.

        media_refs:
            obj_name          # Label of referee object
            handle            # Media object handle
            media_order       # Media reference order nr
            crop              # Four coordinates
            note_handles      # list of Note object handles
            citation_handles  # list of Citation object handles
        """
        doing = "?"
        try:
            for m_ref in media_refs:
                r_attr = {"order": m_ref.media_order}
                if m_ref.crop:
                    r_attr["left"] = m_ref.crop[0]
                    r_attr["upper"] = m_ref.crop[1]
                    r_attr["right"] = m_ref.crop[2]
                    r_attr["lower"] = m_ref.crop[3]
                doing = f"(src:{src_handle}) -[{r_attr}]-> Media {m_ref.handle}"
                # print(doing)

                # Save media node
                
                query = CypherLink.link_handle(m_ref.obj_name, "Media", True)
                tx.run(query, src=src_handle, dst=m_ref.handle, r_attr=r_attr)

                # Save listed notes and citations for this media
                
                if m_ref.note_handles:
                    query = CypherLink.link_handle(m_ref.obj_name, "Note", True)
                    #print("#! ds_create_link_medias_w_handles "+query)
                    for hlink in m_ref.note_handles:
                        doing = f" {m_ref.obj_name} {src_handle}-> Note {hlink}"
                        tx.run(query, src=src_handle, dst=hlink, r_attr=r_attr)
                        # tx.run(CypherLink.link_note,
                        #        lbl=m_ref.obj_name, src_iid=iid, handle=hlink)

                if m_ref.citation_handles:
                    query = CypherLink.link_handle(m_ref.obj_name, "Citation", True)
                    #print("#! ds_create_link_medias_w_handles "+query)
                    for hlink in m_ref.citation_handles:
                        doing = f" {m_ref.obj_name} {src_handle}-> Citation {hlink}"
                        tx.run(query, src=src_handle, dst=hlink, r_attr=r_attr)
                        # tx.run(CypherLink.link_citation,
                        #        lbl=m_ref.obj_name, src_iid=iid, handle=hlink)

        except Exception as err:
            traceback.print_exc()
            logger.error(
                f"Neo4jUpdateService.create_link_medias_by_handles {doing}: {err}"
            )

    # ----- Place -----

    def ds_save_place(self, tx, place, batch_id, iids:IidGenerator, place_keys=None):
        """Save Place, Place_names, Notes and connect to hierarchy.

        :param: place_keys    dict {handle: iid}
        :param: batch_id      batch id where this place is linked

        The 'iid's of already created nodes can be found in 'place_keys'
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

        Does NOT raise an error, if write fails.
        """

        # A. Create or update this Place

        place.iid = iids.get_one()
        pl_attr = {
            "iid": place.iid,
            "handle": place.handle,
            "change": place.change,
            "id": place.id,
            "type": place.type,
            "pname": place.pname,
            "attrs": place.attrs_for_db(),
        }
        if place.coord:
            # If no coordinates, don't set coord attribute
            pl_attr["coord"] = place.coord.get_coordinates()

        #    Create Place place

        # Check if this Place node is already created
        if place_keys and place.handle in place_keys.keys():
            # 1) node has been created but not connected to Batch.
            #    update known Place node parameters and link from Batch
            if place.type:
                # print(f">Pl_save-1 Complete Place ({place.id} #{pl_iid}) {place.handle} {place.pname}")
                result = tx.run(CypherPlace.complete_handle,
                                batch_id=batch_id,
                                p_handle=place.handle,
                                p_attr=pl_attr,
                )
                #iid = result.single[0]
                place_keys[place.handle] = place.iid
                
            else:
                # print(f">Pl_save-1 NO UPDATE Place ({place.id} #{pl_iid}) attr={pl_attr}")
                pass
        else:
            # 2) new node: create and link from Batch
            #print(f"#!>Pl_save-2 Create a new Place ({place.id} #{place.iid} {place.pname}) {place.handle}")
            tx.run(CypherPlace.create, batch_id=batch_id, p_attr=pl_attr)
            place_keys[place.handle] = place.iid

        #    Create Place_names

        for i in range(len(place.names)):
            place.names[i].iid = f"A{place.iid}.{i+1}"
        for name in place.names:
            # name.lang is set later to name links
            n_attr = {"name": name.name, "iid":name.iid}
            if name.dates:
                n_attr.update(name.dates.for_db())
            tx.run(CypherPlace.add_name,
                   pid=place.iid,
                   order=name.order,
                   n_attr=n_attr,
            )
            #print(f"#! ({place.iid}:Place)-[:NAME]->({name.iid}:{name})")

        # Select default names for the default languages
        ret = PlaceBl.find_default_names(place.names, ["fi", "sv"])
        if ret.get("status") == Status.OK:
            # Update default language name links
            # def_names: dict {lang, uid} iid's of PlaceName objects
            def_names = ret.get("ids")
            self.ds_place_set_default_names(tx, place.iid, def_names["fi"], def_names["sv"])

        # B. Make hierarchy relations to upper Place nodes

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

            if place_keys and up_handle in place_keys.keys():
                # 3) Link to a known upper Place
                #    The upper node is already created: create a link to that
                #    upper Place node
                # print(f"Pl_save-3 Link ({place.id} #{place.iid}) {_r} (#{up_iid})")
                result = tx.run(CypherPlace.link_hier_handle,
                                p_handle=place.handle, up_handle=up_handle,
                                r_attr=rel_attr,
                )
                place_keys[up_handle] = result.single()[0]
            else:
                # 4) Link to unknown place
                #    A new upper node: create a Place with only handle
                #    parameter and link hierarchy to Place place
                # print(f"Pl_save-4 Link to empty upper Place ({place.id} #{place.iid}) {_r} {up_handle}")
                result = tx.run(CypherPlace.link_create_hier_handle,
                                p_handle=place.handle, up_handle=up_handle,
                                r_attr=rel_attr,
                )
                place_keys[up_handle] = result.single()[0]


        for i in range(len(place.notes)):
            place.notes[i].iid = f"D{place.iid}.{i+1}"
        for note in place.notes:
            n_attr = {
                "url": note.url, 
                "type": note.type, 
                "text": note.text,
                "iid": place.iid
                }
            result = tx.run(CypherPlace.add_urls,
                            batch_id=batch_id, pid=place.iid, n_attr=n_attr
            )

        # Make the place note relations; the Notes have been stored before
        # TODO: There may be several Notes for the same handle! You shold use iid!

        if place.note_handles:
            query = CypherLink.link_handle("Place", "Note")
            for hlink in place.note_handles:
                tx.run(query, src=place.handle, dst=hlink)
                # tx.run(CypherPlace.pl_link_note,
                #        p_handle=place.handle, hlinks=n_handle)
                # # .run(CypherPlace.link_note, pid=place.iid, hlink=n_handle)

        if place.citation_handles:
            query = CypherLink.link_handle("Place", "Citation")
            for hlink in place.citation_handles:
                # Link to existing Citation
                tx.run(query, src=place.handle, dst=hlink)
                # result = tx.run(CypherLink.link_citation,
                #                 lbl=place.label(), src_iid=place.iid, handle=hlink)

        if place.media_refs:
            query = CypherLink.link_handle("Place", "Media")
            for m_ref in place.media_refs:
                tx.run(query, src=place.handle, dst=m_ref.handle)
        # if place.media_refs:
        #     # Make relations to the Media nodes and their Note and Citation references
        #     result = self.ds_create_link_medias_w_handles(
        #         tx, place.iid, place.media_refs)


    def ds_place_set_default_names(self, tx, place_id, fi_id, sv_id):
        """Creates default links from Place to fi and sv PlaceNames identified by iid.

        - place_id      Place object id
        - fi_id         PlaceName object id for fi
        - sv_id         PlaceName object id for sv
        """
        try:
            if fi_id == sv_id:
                result = tx.run(CypherPlace.link_name_lang_single,
                                place_id=place_id, fi_id=fi_id
                )
            else:
                result = tx.run(CypherPlace.link_name_lang,
                                place_id=place_id, fi_id=fi_id, sv_id=sv_id,
                )
            x = None
            for x, _fi, _sv in result:
                # print(f"# Linked ({x}:Place)-['fi']->({fi}), -['sv']->({sv})")
                pass

            if not x:
                logger.warning(
                    "Neo4jUpdateService.ds_place_set_default_names: not created "
                    f"Place {place_id}, names fi:{fi_id}, sv:{sv_id}"
                )

        except Exception as err:
            logger.error(f"Neo4jUpdateService.ds_place_set_default_names: {err}")
            return err

    def ds_places_merge(self, id1, id2):
        """Merges given two Place objects using apoc library."""

        def merge_name_nodes(name_nodes):
            """
            Merge Place_name nodes if the names are identical.
            
            For each unique name this will generate Cypher code like:
            
                #!match (n1:Place_name) where id(n1) = $id1
                #!match (n2:Place_name) where id(n2) = $id2
                match (n1:Place_name) where n1.iid = $id1
                match (n2:Place_name) where n2.iid = $id2
                call apoc.refactor.mergeNodes([n1,n2],
                    {properties:'discard',mergeRels:true})
                yield node
                return node
                
            The idmap variable contains the node ids:
            
                idmap = {'id1': 'DP-32ge.1, 'id2': 'DP-32ge.2'}
            
            """
            nodemap = defaultdict(list)
            for node in name_nodes:
                nodemap[node["name"]].append(node)
            new_nodes = []
            for _name, nodes in nodemap.items():
                if len(nodes) > 1:
                    cypher = ""
                    namelist = []
                    idmap = {}
                    for i, node in enumerate(nodes, start=1):
                        cypher += f"\nmatch (n{i}:Place_name) where n{i}.iid = $id{i}"
                        namelist.append(f"n{i}")
                        idmap[f"id{i}"] =  node.iid
                    cypher += f"\ncall apoc.refactor.mergeNodes([{','.join(namelist)}],"
                    cypher += f"\n    {{properties:'discard',mergeRels:true}})"
                    cypher += f"\nyield node"
                    cypher += f"\nreturn node"
                    rec = self.tx.run(cypher, **idmap).single()
                    node = rec["node"]
                else:
                    node = nodes[0]                    
                new_nodes.append(node)
            return new_nodes
        
        try:
            record = self.tx.run(
                CypherPlaceMerge.merge_places, id1=id1, id2=id2
            ).single()
            node = record["node"]
            place = PlaceBl_from_node(node)
            name_nodes = record["names"]
            name_nodes = merge_name_nodes (name_nodes) 
            place.names = [PlaceName_from_node(n) for n in name_nodes]
        except ClientError as e:
            # traceback.print_exc()
            return {
                "status": Status.ERROR,
                "statustext": f"Neo4jUpdateService.ds_places_merge {id1}<-{id2} failed: {e.__class__.__name__} {e}",
            }

        return {"status": Status.OK, "place": place}

    # ----- Repository -----
    def ds_save_repository(self, tx, repository, batch_id, iids):
        """Saves this Repository to db under given batch."""

        repository.iid = iids.get_one()
        r_attr = {
            "iid": repository.iid,
            "handle": repository.handle,
            "change": repository.change,
            "id": repository.id,
            "rname": repository.rname,
            "type": repository.type,
            "attrs": repository.attrs_for_db(),
        }
        result = tx.run(
            CypherRepository.create_in_batch,
            bid=batch_id,
            r_attr=r_attr
        )
        #!repository.iid = result.single()[0]

        # Save the notes attached to repository
        if repository.notes:
            self.ds_save_note_list(tx, parent=repository, batch_id=batch_id, iids=iids)

        # Make relations to the Note nodes
        if repository.note_handles:
            result = tx.run(
                CypherRepository.r_link_notes,
                handle=repository.handle,
                hlinks=repository.note_handles,
                )
            _cnt=result.single()["cnt"]
            
        return

    # ----- Source -----

    def ds_save_source(self, tx, source, batch_id, iids:IidGenerator):   
        """ Saves this Source and connect it to Notes and Repositories.

            :param: batch_id      batch id where this source is linked

        """
        source.iid = iids.get_one()
        s_attr = {}
        try:
            s_attr = {
                "iid": source.iid,
                "handle": source.handle,
                "change": source.change,
                "id": source.id,
                "stitle": source.stitle,
                "sauthor": source.sauthor,
                "spubinfo": source.spubinfo,
                "attrs": source.attrs_for_db(),
            }

            tx.run(CypherSource.create_to_batch, batch_id=batch_id, s_attr=s_attr)
            #!ids = []
            # for record in result:
            #     source.iid = record[0]
            #     ids.append(source.iid)
            #     if len(ids) > 1:
            #         print("iError updated multiple Sources {} - {}, attr={}".format(source.id, ids, s_attr))

        except Exception as err:
            print("Neo4jUpdateService.ds_save_source: {0} attr={1}".format(err, s_attr))
            raise RuntimeError("Could not save Source {}".format(source.id))

        # Make relation to the Note nodes
        for hlink in source.note_handles:
            #!tx.run(CypherSource.s_link_note, 
            query = CypherLink.link_handle("Source", "Note")
            tx.run(query, src=source.handle, dst=hlink)
            #!except Exception as err:
            #     logger.error(f"Source_gramps.save: {err} in linking Notes {source.handle} -> {source.note_handles}")
            #     #print("iError Source.save note: {0}".format(err), file=stderr)

        # Make relation to the Repository nodes
        for repo in source.repositories:
            try:
                tx.run(CypherSource.link_repository, 
                       handle=source.handle, 
                       hlink=repo.handle, 
                       medium=repo.medium)
            except Exception as err:
                print("iError Source.save Repository: {0}".format(err))
                

    def mergesources(self, id1:str, id2:str):
        
            # match (p1:Source)        where id(p1) = $id1 
            # match (p2:Source)        where id(p2) = $id2
        cypher_mergesources = """
            match (p1:Source)        where p1.iid = $id1 
            match (p2:Source)        where p2.iid = $id2
            call apoc.refactor.mergeNodes([p1,p2],
                {properties:'discard',mergeRels:true})
            yield node
            return node
        """
        rec = self.tx.run(cypher_mergesources, id1=id1, id2=id2).single()
        if rec is None: return None
        node = rec['node']
        source = SourceBl_from_node(node)
        return source
            # ----- Citation -----

    # ----- Event -----
    def ds_save_event(self, tx, event, batch_id, iids):
        """Saves event to database:
        - Creates a new db node for this Event

        - links to existing Place, Note, Citation, Media objects
        - Does not link it from UserProfile or Person
        """

        event.iid = iids.get_one()
        e_attr = {
            "iid": event.iid,
            # "uuid": event.uuid,
            "handle": event.handle,
            "change": event.change,
            "id": event.id,
            "type": event.type,
            "description": event.description,
            "attrs": event.attrs_for_db(),
        }
        if event.dates:
            e_attr.update(event.dates.for_db())

        tx.run(CypherEvent.create_to_batch, batch_id=batch_id, e_attr=e_attr)
        #!ids = []
        # for record in result:
        #     event.iid = record[0]
        #     ids.append(event.iid)
        #     if len(ids) > 1:
        #         print(
        #             "iError updated multiple Events {} - {}, attr={}".format(
        #                 event.id, ids, e_attr
        #             )
        #         )

        # Make relation to the Place node
        if event.place_handles:
            query = CypherLink.link_handle("Event", "Place")
            for hlink in event.place_handles:
                tx.run(query, src=event.handle, dst=hlink)
            #!for pl_handle in event.place_handles:
            #     tx.run(CypherEvent.link_place, handle=event.handle, place_handle=pl_handle)

        # Make relations to the Note nodes
        if event.note_handles:
            #!result = tx.run(CypherEvent.e_link_notes,...)
            query = CypherLink.link_handle("Event", "Note")
            for hlink in event.note_handles:
                tx.run(query, src=event.handle, dst=hlink)
            #!_cnt = result.single()["cnt"]
            # print(f"##Luotiin {cnt} Note-yhteyttä: {event.id}->{event.note_handles}")

        # Make relations to multiple Citation nodes
        if event.citation_handles:  #  citation_handles != '':
            query = CypherLink.link_handle("Event", "Citation")
            for hlink in event.note_handles:
                tx.run(query, src=event.handle, dst=hlink)
            #  tx.run(CypherEvent.link_citations,
            #     handle=event.handle,
            #     citation_handles=event.citation_handles, )

        # Make relations to the Media nodes and their Note and Citation references
        if event.media_refs:
            self.ds_create_link_medias_w_handles(tx, event.handle, event.media_refs)

    # ----- Person -----

    def ds_save_person(self, tx, person:Person, batch_id, iids:IidGenerator):
        """Saves the Person object and possibly the Names, Events ja Citations.

        @todo: Remove those referenced person names, which are not among
               new names (:Person) --> (:Name)
        """
        person.iid = iids.get_one()

        # Save the Person node under Root; all attributes are replaced

        p_attr = {
            "iid": person.iid,
            "handle": person.handle,
            "change": person.change,
            "id": person.id,
            "priv": person.priv,
            "sex": person.sex,
            "confidence": person.confidence,
            "sortname": person.sortname,
            "attrs": person.attrs_for_db(),
        }
        if person.dates:
            p_attr.update(person.dates.for_db())

        tx.run(CypherPerson.create_to_batch, batch_id=batch_id, p_attr=p_attr)
        #!for record in result:
        #     #!person.iid = record[0]
        #     ids.append(person.iid)
        #     if len(ids) > 1:
        #         print(
        #             "iError updated multiple Persons {} - {}, attr={}".format(
        #                 person.id, ids, p_attr
        #             )
        #         )
        #     # print("Person {} ".format(person.iid))
        # if person.iid == None:
        #     print("iWarning got no iid for Person {}".format(p_attr))

        # Save Name nodes under the Person node
        niid = 0
        for name in person.names:
            niid += 1
            name.iid = f"A{person.iid}.{niid}"
            self.ds_save_name(tx, name, parent_id=person.iid)

        # Save web urls as Note nodes connected under the Person
        if person.notes:
            self.ds_save_note_list(tx, parent=person, batch_id=batch_id, iids=iids)

        """ Connect to each Event loaded from Gramps """

        # for i in range(len(person.eventref_hlink)):
        if person.event_handle_roles:
            query = CypherLink.link_handle("Person", "Event", True)
            for href, role in person.event_handle_roles:
                r_attr = {"role": role}
                #print(f"#!! {person.id}/{person.iid} -> Event {href} {r_attr}")
                tx.run(query, src=person.handle, dst=href, r_attr=r_attr)
                #!tx.run(CypherPerson.link_event, p_handle=person.handle, e_handle=event_handle, role=role,)

        # Make relations to the Media nodes and it's Note and Citation references
        if person.media_refs:
            self.ds_create_link_medias_w_handles(
                tx, person.handle, person.media_refs
            )

        # The relations to the Family node will be created in Family.save(),
        # because the Family object is not yet created

        # Make relations to the Note nodes

        if person.note_handles:
            # Link to existing Notes
            query = CypherLink.link_handle("Person", "Note")
            for href in person.note_handles:
                #print(f"#!! {person.id}/{person.iid} -> Note {href}")
                tx.run(query, src=person.handle, dst=href)
        # for handle in person.note_handles:
        #     tx.run(CypherPerson.p_link_note, 
        #            lbl=lbl, src_iid=person.iid, handle=handle)

        # Make relations to the Citation nodes

        if person.citation_handles:
            # Link to existing Citations
            query = CypherLink.link_handle("Person", "Citation")
            for href in person.citation_handles:
                #print(f"#!! {person.id}/{person.iid} -> Citation {href}")
                tx.run(query, src=person.handle, dst=href)
        # for handle in person.citation_handles:
        #     tx.run(CypherLink.link_citation, 
        #            lbl=lbl, src_iid=person.iid, handle=handle)
        return

    def ds_save_name(self, tx, name, parent_id):
        """Creates or updates this Name node. (There is no handle)
        If parent_id is given, a link (parent) -[:NAME]-> (Name) is created

        #TODO: Check, if this name exists; then update or create new
        """

        n_attr = {
            #!"iid": name.iid,
            "order": name.order,
            "type": name.type,
            "firstname": name.firstname,
            "surname": name.surname,
            "prefix": name.prefix,
            "suffix": name.suffix,
            "title": name.title,
            "attrs": name.attrs_for_db(),
        }
        #TODO Remove temporary fix '-' for missing iid values
        if name.iid and not name.iid.startswith("-"):
            # Do not save temporary iid starting with hyphen
            n_attr["iid"] = name.iid
        if name.dates:
            n_attr.update(name.dates.for_db())
            
        tx.run(CypherPerson.create_name_as_leaf,
            n_attr=n_attr,
            parent_id=parent_id,
            citation_handles=name.citation_handles,
        )

    def ds_get_personnames(self, iid=None):
        """Picks all Name versions of this Person or all persons.

        Use optionally refnames or sortname for person selection
        """
        if iid:
            result = self.tx.run(CypherPerson.get_names, pid=iid)
        else:
            result = self.tx.run(CypherPerson.get_all_persons_names)
        # <Record
        #    pid=82
        #    name=<Node id=83 labels=frozenset({'Name'})
        #        properties={'title': 'Sir', 'firstname': 'Jan Erik', 'surname': 'Mannerheimo',
        #            'prefix': '', 'suffix': 'Jansson', 'type': 'Birth Name', 'order': 0}> >

        return [(record["pid"], record["name"]) for record in result]


    def ds_set_people_lifetime_estimates(self, uids):
        """Get estimated lifetimes to Person.dates for given person.iids.

        :param: uids  list of iids of Person nodes; empty = all lifetimes
        """
        from models import lifetime
        from models.lifetime import BIRTH, DEATH, BAPTISM, BURIAL #, MARRIAGE

        def key_birth_1st(event):
            " sorts events so that BIRTH, DEATH, BAPTISM, BURIAL come first "
            if event.eventtype in (BIRTH, DEATH):
                return 0
            elif event.eventtype in (BAPTISM, BURIAL):
                return 1
            else:
                return 2

        def list_object_keys(node_list):
            " Usage: pids = list_object_keys(record['parents'']) "
            objects = []
            for node, iid in node_list:
                if node:
                    objects.append(iid)
            return objects


        personlist = []
        personmap = {}
        res = {"status": Status.OK}
        # print(f"### ds_set_people_lifetime_estimates: self.tx = {self.tx}")

        if uids is not None:
            result = self.tx.run(
                CypherPerson.fetch_selected_for_lifetime_estimates, 
                idlist=uids
            )
        else: # for whole database, this is not actually used?
            result = self.tx.run(CypherPerson.fetch_all_for_lifetime_estimates)
        # RETURN p, #! id(p) as pid,
        #     COLLECT(DISTINCT [e,r.role]) AS events,
        #     COLLECT(DISTINCT [fam_event,r2.role]) AS fam_events,
        #     COLLECT(DISTINCT [c,id(c)]) as children,
        #     COLLECT(DISTINCT [parent,id(parent)]) as parents
        for record in result:
            # Person
            p = lifetime.Person()
            #! p.pid = record["pid"]
            p.iid = record["p"]["iid"]
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
                p.events.sort(key=key_birth_1st)
                    

            # List Parent, Child and Spouse identities

            #!for _parent, pid in record["parents"]:
            #     if pid:
            #         p.parent_pids.append(pid)
            p.parent_pids = list_object_keys(record["parents"])
            p.child_pids = list_object_keys(record["children"])
            p.spouse_pids = list_object_keys(record["spouses"])

            # print(f"#> lifetime.Person {p}")
            personlist.append(p)
            personmap[p.iid] = p

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
                id=p.iid,
                birth_low=p.birth_low.getvalue(),
                death_low=p.death_low.getvalue(),
                birth_high=p.birth_high.getvalue(),
                death_high=p.death_high.getvalue(),
            )

        res["count"] = len(personlist)
        # print(f"Estimated lifetime for {res['count']} persons")
        return res


    def ds_build_refnames(self, person_uid: int, name: Name):
        """Set Refnames to the Person with given iid."""

        def link_to_refname(person_iid, nm, use):
            result = self.tx.run(
                CypherRefname.link_person_to, pid=person_iid, name=nm, use=use
            )
            rid = result.single()[0]
            if rid is None:
                raise RuntimeError(f"Error for ({person_iid})-->({nm})")
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

    def ds_update_person_confidences(self, iid: str):
        """Collect Person confidence from Person and Event nodes and store result in Person.

        Voidaan lukea henkilön tapahtumien luotettavuustiedot kannasta
        """
        sumc = 0
        confs = []
        result = self.tx.run(CypherPerson.get_confidences, id=iid)
        for record in result:
            # Returns person.iid, COLLECT(confidence) AS list
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
            self.tx.run(CypherPerson.set_confidence, id=iid, confidence=new_conf)
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
            self.tx.run(CypherRefname.link_person_to, pid=pid, name=name, use=reftype)
            return {"status": Status.OK}

        except Exception as e:
            msg = f"Neo4jUpdateService.ds_link_person_to_refname: person={pid}, {e.__class__.__name__}, {e}"
            print(msg)
            return {"status": Status.ERROR, "statustext": msg}

    # ----- Refname -----

    def ds_get_person_by_uid(self, iid: str):
        """Set Person object by iid.

        NOT USED!
        """
        try:
            self.tx.run(CypherPerson.get_person_by_uid, uid=iid)
            return {"status": Status.OK}
        except Exception as e:
            msg = f"Neo4jUpdateService.ds_get_person_by_uid: person={iid}, {e.__class__.__name__}, {e}"
            print(msg)
            return {"status": Status.ERROR, "statustext": msg}

    def ds_set_person_sortname(self, iid: str, sortname):
        """ Set sortname property to Person object by iid."""
        self.tx.run(CypherPerson.set_sortname, uid=iid, key=sortname)
        return {"status": Status.OK}

    # ----- Family -----

    def ds_set_family_dates_sortnames(self, iid:str, dates, f_sortname, m_sortname):
        """Update Family dates and parents' sortnames.

        :param:    iid      family identity
        :dates:    dict         representing DateRange for family
                                (marriage ... death or divorce

        Called from self.ds_set_family_calculated_attributes only
        """
        f_attr = {
            "father_sortname": f_sortname,
            "mother_sortname": m_sortname,
        }
        if dates:
            f_attr.update(dates)

        result = self.tx.run(CypherFamily.set_dates_sortname, id=iid, f_attr=f_attr)
        summary = result.consume()
        cnt = summary.counters.properties_set
        return {"status": Status.OK, "count": cnt}

    def ds_set_family_calculated_attributes(self, iid):
        """Set Family sortnames and estimated marriage DateRange.

        :param: uids  list of iids of Person nodes

        Called from bp.gramps.xml_dom_handler.DOM_handler.set_family_calculated_attributes

        Set Family.father_sortname and Family.mother_sortname using the data in Person
        Set Family.date1 using the data in marriage Event
        Set Family.datetype and Family.date2 using the data in divorce or death Events
        """
        dates_count = 0
        sortname_count = 0
        status = Status.OK
        # print(f"### ds_set_family_calculated_attributes: self.tx = {self.tx}")

        result = self.tx.run(CypherFamily.get_dates_parents, id=iid)
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
                iid,
                dates_dict,
                record.get("father_sortname"),
                record.get("mother_sortname"),
            )
            # print('Neo4jUpdateService.ds_set_family_calculated_attributes: '
            #      f'id={iid} properties_set={ret.get("count","none")}')
            dates_count += 1
            sortname_count += 1

        return {
            "status": status,
            "dates": dates_count,
            "sortnames": sortname_count,
            "statustext": ret.get("statustext", ""),
        }

    def ds_save_family(self, tx, f:FamilyBl, batch_id, iids:IidGenerator):
        """Saves the family node to db with its relations.

        Connects the family to parent, child, citation and note nodes.
        """
        f.iid = iids.get_one()
        f_attr = {
            "iid": f.iid,
            "handle": f.handle,
            "change": f.change,
            "id": f.id,
            "rel_type": f.rel_type,
            "attrs": f.attrs_for_db(),
        }

        tx.run(CypherFamily.create_to_batch, batch_id=batch_id, f_attr=f_attr)

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

        # Make relation(s) to the Note and Citation nodes

        if f.note_handles:
            query = CypherLink.link_handle("Family", "Note")
            for href in f.note_handles:
                tx.run(query, src=f.handle, dst=href)
        #!for handle in f.note_handles:
        #     tx.run(CypherFamily.f_link_note, handle=f.handle, hlink=handle)

        if f.citation_handles:
            query = CypherLink.link_handle("Family", "Citation")
            for href in f.citation_handles:
                tx.run(query, src=f.handle, dst=href)
        #!for handle in f.citation_handles:
        #     tx.run(CypherLink.link_citation,
        #            lbl=f.label(), src_iid=f.iid, handle=handle)


    # ----- Discussions -----

    def ds_comment_save(self, attr):
        """Creates a Comment node linked from commenting object and the commenter.

        attr = {object_id:int, username:str, title:str, text:str, reply:bool}

        Comment.timestamp is created in the Cypher clause.
        
        Case object_id refers to a Comment or Topic, create a Comment; else create a Topic
        """
        is_reply = attr.get("reply")
        #NOTE. Uses ID() key for all kind of objects
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

