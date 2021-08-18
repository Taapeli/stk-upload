#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2021       Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu,
#                            Ismo Peltonen, Pekka Valta
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
    Data Root node to access Batch data sets.

    Derived from bl.batch.Batch, bl.audit.Audit

Created on 9.6.2021

@author: jm
"""
# blacked 2021-05-01 JMä
import os
from datetime import date, datetime

from flask_babelex import _

import shareds
from models.util import format_timestamp

from bl.admin.models.cypher_adm import Cypher_adm

from bl.base import Status, NodeObject
from pe.dataservice import DataService
from pe.neo4j.cypher.cy_batch_audit import CypherRoot, CypherAudit
from pe.neo4j.util import run_cypher

DEFAULT_MATERIAL = "Family Tree"

class State:
    """File, Material or Object state.

    State value    File state          Root state          Object state *
    -----------    ----------          ----------          ------------
    Loading        FILE_LOADING
    File           FILE_UPLOADED       ROOT_REMOVED
    Load Failed    FILE_LOAD_FAILED
    Storing                            ROOT_STORING
    Candidate                          ROOT_CANDIDATE     OBJECT_CANDICATE

    Audit Requested                    ROOT_AUDIT_REQUESTED
    Auditing                           ROOT_AUDITING
    Accepted                           ROOT_ACCEPTED      OBJECT_ACCEPTED
    Merged                                                OBJECT_MERGED
    Rejected                           ROOT_REJECTED      OBJECT_REJECTED
    
    *)  Mikäli Kohteiden näkyminen Isotammen hyväksyttynä aineistona osoittautuu
        ongelmaksi, lisätään Kohteille auditoinnin aikaisiksi tilat / Ismo
        - OBJECT_REJECTED_IN_AUDIT = "Audit Rejected"
        - OBJECT_ACCEPTED_IN_AUDIT = "Audit Accepted"
        ja siirretään ne varsinaisiksi Rejected ja Accepted -tiloiksi vasta
        auditoinnin valmistuessa.
    
    """
    FILE_LOADING = "Loading"
    FILE_LOAD_FAILED = "Load Failed"
    FILE_UPLOADED = "File"          # old BATCH_UPLOADED = "uploaded", BATCH_REMOVED = "removed"

    ROOT_REMOVED = "File"           # old BATCH_UPLOADED = "uploaded", BATCH_REMOVED = "removed"
    ROOT_STORING = "Storing"        # old BATCH_STARTED  = "started"
    ROOT_CANDIDATE = "Candidate"    # old BATCH_CANDIDATE  = "completed"
    ROOT_AUDIT_REQUESTED = "Audit Requested" # Old BATCH_FOR_AUDIT = "audit_requested"
    ROOT_AUDITING = "Auditing"
    ROOT_ACCEPTED = "Accepted"
    ROOT_REJECTED = "Rejected"

    OBJECT_CANDICATE = "Candidate"  # old BATCH_CANDIDATE  = "completed"
    OBJECT_ACCEPTED = "Accepted"
    OBJECT_MERGED = "Merged"
    OBJECT_REJECTED = "Rejected"


class Root(NodeObject):
    """
    Data Root node for candidate, auditing and approved material chunks.
    
    Given timestamp is milliseconrd from epoch. Convert to string by 
    """

    def __init__(self, userid=None):
        """
        Creates a Root object
        """
        self.uniq_id = None
        self.user = userid
        self.file = None
        self.id = None  # batch_id
        self.material = DEFAULT_MATERIAL      # Material type "Family Tree" or other
        self.state = State.FILE_LOADING
        self.mediapath = None  # Directory for media files
        self.timestamp = 0 # Milliseconds; Convert to string by 
        self.description = ""

    def __str__(self):
        return f"Root {self.user} / {self.id} {self.material}({self.state})"


#===============================================================================
# class Batch:
#     """
#     User Batch node and statistics about them.
#     """
# 
#     # Batch status values:
#     #    1. Import file; no Batch node created
#     BATCH_LOADING = "loading"
#     BATCH_UPLOADED = "uploaded"
#     BATCH_DONE = "done"         # Obsolete
#     BATCH_FAILED = "failed"     # in bp.admin.uploads
#     BATCH_ERROR = "error"       # in bp.admin.uploads
#     BATCH_REMOVED = "removed"
#     BATCH_STORING = "storing"   # NOT IN USE
#     #    2. Batch node exists
#     BATCH_STARTED = "started"
#     BATCH_CANDIDATE = "completed"  # Means candidate
#     #    3. Batch is empty
#     BATCH_FOR_AUDIT = "audit_requested"
# 
#     def __init__(self, userid=None):
#         """
#         Creates a Batch object
#         """
#         self.uniq_id = None
#         self.user = userid
#         self.file = None
#         self.id = None  # batch_id
#         self.status = Batch.BATCH_STARTED
#         self.mediapath = None  # Directory for media files
#         self.timestamp = 0
#         self.material_type = ""
#         self.description = ""
#===============================================================================

    def save(self):
        """Create or update Root node.

        Returns {'id':self.id, 'status':Status.OK}
        """
        # print(f"Batch.save with {shareds.dservice.__class__.__name__}")
        attr = {
            "id": self.id,
            "user": self.user,
            "file": self.file,
            "mediapath": self.mediapath,
            # timestamp": <to be set in cypher>,
            # id: <uniq_id from result>,
            "state": self.state,
            "material": self.material,
            "description": self.description,
        }
        #TODO Create new root_save()
        res = shareds.dservice.ds_batch_save(attr)
        # returns {status, identity}

        self.uniq_id = res.get("identity")
        return res


    @classmethod
    def from_node(cls, node):
        """Convert a Neo4j node to Root object."""
        obj = cls()
        obj.uniq_id = node.id
        obj.user = node.get("user", "")
        obj.file = node.get("file", None)
        obj.id = node.get("id", None)
        obj.state = node.get("state", "")
        obj.mediapath = node.get("mediapath")
        obj.timestamp = node.get("timestamp", 0)
        obj.upload = format_timestamp(obj.timestamp)
        obj.auditor = node.get("auditor", None)
        obj.material = node.get("material", "")
        obj.description = node.get("description", "")
        return obj

    @staticmethod
    def delete_batch(username, batch_id):
        """Delete a Root batch with reasonable chunks."""
        total = 0
        try:
            with shareds.driver.session() as session:
                removed = -1
                while removed != 0:
                    result = session.run(
                        CypherRoot.delete_chunk, user=username, batch_id=batch_id
                    )
                    # Supports both Neo4j version 3 and 4:
                    counters = shareds.db.consume_counters(result)
                    d1 = counters.nodes_deleted
                    d2 = counters.relationships_deleted
                    removed = d1 + d2
                    total += removed
                    if removed:
                        print(f"Root.delete_batch: removed {d1} nodes, {d2} relations")
                    else:
                        # All connected nodes deleted. delete the batch node
                        result = session.run(
                            CypherRoot.delete_batch_node,
                            user=username,
                            batch_id=batch_id,
                        )
                        counters = shareds.db.consume_counters(result)
                        # if counters:
                        d1 = counters.nodes_deleted
                        d2 = counters.relationships_deleted
                        if d1:
                            print(
                                f"Root.delete_batch: removed "
                                f"{d1} batch node {batch_id}, {d2} relations"
                            )
                            total += d1 + d2
                            removed = 0
                        else:
                            print(
                                f"Root.delete_batch: "
                                f"{_('Could not delete batch')} \"{batch_id}\""
                            )
                            return {
                                "status": Status.ERROR,
                                "statustext": "Batch not deleted",
                            }

            return {"status": Status.OK, "total": total}

        except Exception as e:
            msg = f"{e.__class__.__name__} {e}"
            print(f"Root.delete_batch: ERROR {msg}")
            return {"status": Status.ERROR, "statustext": msg}

    @staticmethod
    def get_filename(username, batch_id):
        with shareds.driver.session() as session:
            record = session.run(
                CypherRoot.get_filename, username=username, batch_id=batch_id
            ).single()
            if record:
                return record[0]
            return None

    @staticmethod
    def get_batches():
        result = shareds.driver.session().run(CypherRoot.list_all)
        for rec in result:
            yield dict(rec.get("b"))

    @staticmethod
    def get_my_batches(username):
        with shareds.driver.session() as session:
            result = run_cypher(session, "where root.state='Candidate' return root", username)
            for rec in result:
                print(rec.get("root"))
                values = dict(rec.get("root"))
                fname = values["file"]
                filename = os.path.split(fname)[1]
                values["filename"] = filename
                yield values

    @staticmethod
    def get_user_stats(user):
        """Get statistics of user Batch contents (for profile page).

        If the Batch has been moved to an Audit batch, this method returns
        ("Audit", count) to user_data data
        """
        # Get your approved batches
        approved = {}
        result = shareds.driver.session().run(CypherRoot.get_passed, user=user)
        for node, count in result:
            # <Record batch=<Node id=435790 labels={'Audit'}
            #    properties={'auditor': 'juha', 'id': '2020-03-24.002',
            #    'user': 'juha', 'timestamp': 1585070354153}>
            #  cnt=200>
            b = Root.from_node(node)
            approved[b.id] = count

        # Get current researcher batches
        titles = []
        user_data = {}
        result = shareds.driver.session().run(
            CypherRoot.get_batches, user=user, status=State.ROOT_CANDIDATE # Batch.BATCH_CANDIDATE
        )
        for record in result:
            # <Record batch=<Node id=319388 labels={'Batch'}
            #    properties={ // 'mediapath': '/home/jm/my_own.media',
            #        'file': 'uploads/jpek/Julius_vanhemmat_clean.gramps',
            #        'id': '2019-08-21.002', 'user': 'jpek', 'timestamp': 1566398894787,
            #        'status': 'completed'}>
            #  label='Note'
            #  cnt=2>
            b = Root.from_node(record["batch"])
            label = record.get("label", "")
            cnt = record["cnt"]

            batch_id = b.id
            tstring = b.timestamp_str()

            # Trick: Set Person as first in sort order!
            if label == "Person":
                label = " Person"
            if label and not label in titles:
                titles.append(label)

            key = f"{user}/{batch_id}/{tstring}"
            if not key in user_data:
                user_data[key] = {}
            user_data[key][label] = cnt

            audited = approved.get(batch_id)
            if audited:
                user_data[key]["Audit"] = audited

            print(f"user_data[{key}] {user_data[key]}")

        return sorted(titles), user_data

    @staticmethod
    def get_batch_stats(batch_id):
        """Get statistics of given Batch contents (for move for approval)."""
        labels = []
        result = shareds.driver.session().run(
            CypherRoot.get_single_batch, batch=batch_id
        )
        for record in result:
            # <Record batch=<Node id=319388 labels={'Batch'}
            #    properties={ // 'mediapath': '/home/jm/my_own.media',
            #        'file': 'uploads/jpek/Julius_vanhemmat_clean.gramps',
            #        'id': '2019-08-21.002', 'user': 'jpek', 'timestamp': 1566398894787,
            #        'status': 'completed'}>
            #  label='Note'
            #  cnt=2>

            node = record["batch"]
            b = Root.from_node(node)
            tstring = b.timestamp_str()
            label = record.get("label", "-")
            # Trick: Set Person as first in sort order!
            if label == "Person":
                label = " Person"
            cnt = record["cnt"]
            labels.append((label, cnt))

        return b.user, b.id, tstring, sorted(labels)

    @staticmethod
    def list_empty_batches():
        """Gets a list of db Batches without any linked data."""
        batches = []

        class Upload:
            pass

        print(
            'Batch.list_empty_batches: #TODO Tähän aikarajoitus "vvv-kk", nyt siinä on vakio "2019-10"!'
        )
        result = shareds.driver.session().run(CypherRoot.TODO_get_empty_batches)

        for record in result:
            # <Node id=317098 labels={'Batch'}
            #    properties={'file': 'uploads/juha/Sibelius_20190820_clean.gpkg',
            #        'id': '2019-09-27.001', 'user': 'juha', 'status': 'started',
            #        'timestamp': 1569586423509}>

            node = record["batch"]
            batch = Root.from_node(node)
            batches.append(batch)

        return batches

    @staticmethod
    def drop_empty_batches():
        """Gets a list of db Batches without any linked data."""
        today = str(date.today())
        record = (
            shareds.driver.session()
            .run(Cypher_adm.drop_empty_batches, today=today)
            .single()
        )
        cnt = record[0]
        return cnt

    @staticmethod
    def get_auditor_stats(auditor=None):
        """Get statistics of auditor's audition batch contents (for audit/approvals)."""
        titles = []
        labels = {}
        if auditor:
            result = shareds.driver.session().run(
                CypherAudit.get_my_audits, oper=auditor
            )
        else:
            result = shareds.driver.session().run(
                CypherAudit.get_all_audits, oper=auditor
            )
        for record in result:
            # <Record
            #    b=<Node id=439060 labels={'Audit'}
            #        properties={'auditor': 'juha', 'id': '2020-01-03.001',
            #        'user': 'jpek', 'timestamp': 1578940247182}>
            #    label='Note'
            #    cnt=17>
            b = Root.from_node(record["b"])
            label = record["label"]
            if not label:
                label = ""
            cnt = record["cnt"]
            timestring = b.timestamp_str()
            file = b.file.rsplit('/',1)[-1] if b.file else ""

            # Trick: Set Person as first in sort order!
            if label == "Person":
                label = " Person"
            if label and not label in titles:
                titles.append(label)

            key = f"{b.auditor}/{b.user}/{b.id}/{file} {timestring}"
            if not key in labels:
                labels[key] = {}
            labels[key][label] = cnt
            # print(f'labels[{key}] {labels[key]}')

        return sorted(titles), labels

    @staticmethod
    def get_stats(audit_id):
        """Get statistics of given Batch contents."""
        labels = []
        batch = None
        result = shareds.driver.session().run(
            CypherRoot.get_single_batch, batch=audit_id
        )
        for record in result:
            # <Record batch=<Node id=319388 labels={'Batch'}
            #    properties={ // 'mediapath': '/home/jm/my_own.media',
            #        'file': 'uploads/jpek/Julius_vanhemmat_clean.gramps',
            #        'id': '2019-08-21.002', 'user': 'jpek', 'timestamp': 1566398894787,
            #        'status': 'completed'}>
            #  label='Note'
            #  cnt=2>

            if not batch:
                batch = record["batch"]
                user = batch.get("user")
                ts = batch.get("timestamp")
                if ts:
                    t = float(ts) / 1000.0
                    tstring = datetime.fromtimestamp(t).strftime("%-d.%-m.%Y %H:%M")
                else:
                    tstring = ""
            label = record["label"]
            if label == None:
                label = "-"
            # Trick: Set Person as first in sort order!
            if label == "Person":
                label = " Person"
            cnt = record["cnt"]
            labels.append((label, cnt))

        return user, audit_id, tstring, sorted(labels)

    @staticmethod
    def delete_audit(username, batch_id):
        """Delete an audited batch having the given id."""
        label_sets = [  # Grouped for decent size chunks in logical order
            ["Note"],
            ["Repository", "Media"],
            ["Place"],
            ["Source"],
            ["Event"],
            ["Person"],
            ["Family"],
        ]

        deleted = 0
        with shareds.driver.session() as session:
            # Delete the node types that are not directly connected to Audit node
            with session.begin_transaction() as tx:
                result = tx.run(CypherAudit.delete_names, batch=batch_id)
                this_delete = result.single()[0]
                print(f"bl.audit.delete_audit: deleted {this_delete} name nodes")
                deleted += this_delete

                result = tx.run(CypherAudit.delete_place_names, batch=batch_id)
                this_delete = result.single()[0]
                print(
                    f"bl.audit.delete_audit: deleted {this_delete} place name nodes"
                )
                deleted += this_delete

                # result = tx.run(CypherAudit.delete_citations,
                #                 batch=batch_id)
                # this_delete = result.single()[0]
                # print(f"bl.audit.delete_audit: deleted {this_delete} citation nodes")
                # deleted += this_delete

            # Delete the directly connected node types as defined by the labels
            for labels in label_sets:
                with session.begin_transaction() as tx:
                    result = tx.run(
                        CypherAudit.delete, batch=batch_id, labels=labels
                    )
                    this_delete = result.single()[0]
                    print(
                        f"bl.audit.delete_audit: deleted {this_delete} nodes of type {labels}"
                    )
                    deleted += this_delete

            # Finally, delete the audit node itself
            with session.begin_transaction() as tx:
                result = tx.run(CypherAudit.delete_audit_node, batch=batch_id)

        msg = _(
                "Approved batch id %(batch_id)s with %(deleted)d nodes has been deleted",
                batch_id=batch_id,
                deleted=deleted,
        )
        return msg, deleted

class BatchUpdater(DataService):
    """
    Root datastore for write and update in transaction.
    """

    def __init__(self, service_name: str, u_context=None, tx=None):
        """
        Initiate datastore for update in given transaction or without transaction.
        """
        super().__init__(service_name, user_context=u_context, tx=tx)
        self.batch = None

    def start_data_batch(self, userid, file, mediapath, tx=None):
        """
        Initiate new Batch.

        :param: userid    user
        :param: file      input file name
        :param: mediapath media file store path

        The stored Batch.file name is the original name with '_clean' removed.
        """
        # Lock db to avoid concurent Batch loads
        shareds.dservice.ds_aqcuire_lock("batch_id")
        # TODO check res

        # Find the next free Batch id
        batch = Root()
        res = shareds.dservice.ds_new_batch_id()

        batch.id = res.get("id")
        batch.user = userid
        batch.file = file.replace("_clean.", ".")
        batch.mediapath = mediapath

        res = batch.save()
        self.batch = batch

        return {"batch": batch, "status": Status.OK}

    def batch_get_one(self, user, batch_id):
        """Get Root object by username and batch id. """
        ret = shareds.dservice.ds_get_batch(user, batch_id)
        # returns {"status":Status.OK, "node":record}
        try:
            node = ret['node']
            batch = Root.from_node(node)
            return {"status":Status.OK, "item":batch}
        except Exception as e:
            statustext = (
                f"BatchUpdater.get_batch failed: {e.__class__.__name__} {e}"
            )
            return {"status": Status.ERROR, "statustext": statustext}

    def batch_mark_status(self, b_status):
        """ Mark this data batch status. """
        res = shareds.dservice.ds_batch_set_state(
            self.batch.id, self.batch.user, b_status
        )
        return res

    def commit(self):
        """ Commit transaction. """
        shareds.dservice.ds_commit()

    def rollback(self):
        """ Commit transaction. """
        shareds.dservice.ds_rollback()

    def media_create_and_link_by_handles(self, uniq_id, media_refs):
        """Save media object and it's Note and Citation references
        using their Gramps handles.
        """
        if media_refs:
            shareds.dservice.ds_create_link_medias_w_handles(uniq_id, media_refs)
