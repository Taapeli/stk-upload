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
    Data Batch node to connect business nodes to UserProfile.

Created on 29.11.2019

@author: jm
"""
# blacked 2021-05-01 JMä
from flask_babelex import _
import shareds
from datetime import date, datetime
from models.util import format_timestamp

# from bp.scene.routes import stk_logger
from bl.admin.models.cypher_adm import Cypher_adm

from bl.base import Status
from pe.dataservice import DataService
from pe.neo4j.cypher.cy_batch_audit import CypherBatch


class Batch:
    """
    User Batch node and statistics about them.
    """

    # Batch status values:
    #    1. Import file; no Batch node created
    BATCH_LOADING = "loading"
    BATCH_UPLOADED = "uploaded"
    BATCH_DONE = "done"  # Obsolete
    BATCH_FAILED = "failed"
    BATCH_ERROR = "error"
    BATCH_REMOVED = "removed"
    BATCH_STORING = "storing"
    #    2. Batch node exists
    BATCH_STARTED = "started"
    BATCH_CANDIDATE = "completed"  # Means candidate
    #    3. Batch is empty
    BATCH_FOR_AUDIT = "audit_requested"

    def __init__(self, userid=None):
        """
        Creates a Batch object
        """
        self.uniq_id = None
        self.user = userid
        self.file = None
        self.id = None  # batch_id
        self.status = Batch.BATCH_STARTED
        self.mediapath = None  # Directory for media files
        self.timestamp = 0
        self.material_type = ""
        self.description = ""

    def __str__(self):
        return f"{self.user} / {self.id}"

    def save(self):
        """Create or update Batch node.

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
            "status": self.status,
            "material_type": self.material_type,
            "description": self.description,
        }
        res = shareds.dservice.ds_batch_save(attr)
        # returns {status, identity}

        self.uniq_id = res.get("identity")
        return res


    @classmethod
    def from_node(cls, node):
        """Convert a Neo4j node to Batch object."""
        obj = cls()
        obj.uniq_id = node.id
        obj.user = node.get("user", "")
        obj.file = node.get("file", None)
        obj.id = node.get("id", None)
        obj.status = node.get("status", "")
        obj.mediapath = node.get("mediapath")
        obj.timestamp = node.get("timestamp", 0)
        obj.upload = format_timestamp(obj.timestamp)
        obj.auditor = node.get("auditor", None)
        obj.material_type = node.get("material_type", "")
        obj.description = node.get("description", "")
        return obj

    @staticmethod
    def delete_batch(username, batch_id):
        """Delete a Batch with reasonable chunks."""
        total = 0
        try:
            with shareds.driver.session() as session:
                removed = -1
                while removed != 0:
                    result = session.run(
                        CypherBatch.delete_chunk, user=username, batch_id=batch_id
                    )
                    # Supports both Neo4j version 3 and 4:
                    counters = shareds.db.consume_counters(result)
                    d1 = counters.nodes_deleted
                    d2 = counters.relationships_deleted
                    removed = d1 + d2
                    total += removed
                    if removed:
                        print(f"Batch.delete_batch: removed {d1} nodes, {d2} relations")
                    else:
                        # All connected nodes deleted. delete the batch node
                        result = session.run(
                            CypherBatch.delete_batch_node,
                            user=username,
                            batch_id=batch_id,
                        )
                        counters = shareds.db.consume_counters(result)
                        # if counters:
                        d1 = counters.nodes_deleted
                        d2 = counters.relationships_deleted
                        if d1:
                            print(
                                f"Batch.delete_batch: removed "
                                f"{d1} batch node {batch_id}, {d2} relations"
                            )
                            total += d1 + d2
                            removed = 0
                        else:
                            print(
                                f"Batch.delete_batch: "
                                f"{_('Could not delete batch')} \"{batch_id}\""
                            )
                            return {
                                "status": Status.ERROR,
                                "statustext": "Batch not deleted",
                            }

            return {"status": Status.OK, "total": total}

        except Exception as e:
            msg = f"{e.__class__.__name__} {e}"
            print(f"Batch.delete_batch: ERROR {msg}")
            return {"status": Status.ERROR, "statustext": msg}

    @staticmethod
    def get_filename(username, batch_id):
        with shareds.driver.session() as session:
            record = session.run(
                CypherBatch.get_filename, username=username, batch_id=batch_id
            ).single()
            if record:
                return record[0]
            return None

    @staticmethod
    def get_batches():
        result = shareds.driver.session().run(CypherBatch.list_all)
        for rec in result:
            print("p", rec.get("b").items())
            yield dict(rec.get("b"))

    @staticmethod
    def get_user_stats(user):
        """Get statistics of user Batch contents.

        If the Batch has been moved to an Audit batch, this method returns
        ("Audit", count) to user_data data
        """
        # Get your approved batches
        approved = {}
        result = shareds.driver.session().run(CypherBatch.get_passed, user=user)
        for node, count in result:
            # <Record batch=<Node id=435790 labels={'Audit'}
            #    properties={'auditor': 'juha', 'id': '2020-03-24.002',
            #    'user': 'juha', 'timestamp': 1585070354153}>
            #  cnt=200>
            b = Batch.from_node(node)
            if not b.status:
                # Audit node has no status field; the material has been sent forwards
                b.status = Batch.BATCH_FOR_AUDIT
            approved[b.id] = count

        # Get current researcher batches
        titles = []
        user_data = {}
        result = shareds.driver.session().run(
            CypherBatch.get_batches, user=user, status=Batch.BATCH_CANDIDATE
        )
        for record in result:
            # <Record batch=<Node id=319388 labels={'Batch'}
            #    properties={ // 'mediapath': '/home/jm/my_own.media',
            #        'file': 'uploads/jpek/Julius_vanhemmat_clean.gramps',
            #        'id': '2019-08-21.002', 'user': 'jpek', 'timestamp': 1566398894787,
            #        'status': 'completed'}>
            #  label='Note'
            #  cnt=2>
            b = Batch.from_node(record["batch"])
            label = record.get("label", "")
            cnt = record["cnt"]

            batch_id = b.id
            tstring = Batch.timestamp_to_str(b.timestamp)

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
    def timestamp_to_str(ts):
        """ Timestamp to display format. """
        if ts:
            t = float(ts) / 1000.0
            tstring = datetime.fromtimestamp(t).strftime("%-d.%-m.%Y %H:%M")
        else:
            tstring = ""
        return tstring

    @staticmethod
    def get_batch_stats(batch_id):
        """Get statistics of given Batch contents."""
        labels = []
        batch = None
        result = shareds.driver.session().run(
            CypherBatch.get_single_batch, batch=batch_id
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
                # batch_id = batch.get('id')
                ts = batch.get("timestamp")
                tstring = Batch.timestamp_to_str(ts)
            label = record.get("label", "-")
            # Trick: Set Person as first in sort order!
            if label == "Person":
                label = " Person"
            cnt = record["cnt"]
            labels.append((label, cnt))

        return user, batch_id, tstring, sorted(labels)

    @staticmethod
    def list_empty_batches():
        """Gets a list of db Batches without any linked data."""
        batches = []

        class Upload:
            pass

        print(
            'Batch.list_empty_batches: #TODO Tähän aikarajoitus "vvv-kk", nyt siinä on vakio "2019-10"!'
        )
        result = shareds.driver.session().run(CypherBatch.TODO_get_empty_batches)

        for record in result:
            # <Node id=317098 labels={'Batch'}
            #    properties={'file': 'uploads/juha/Sibelius_20190820_clean.gpkg',
            #        'id': '2019-09-27.001', 'user': 'juha', 'status': 'started',
            #        'timestamp': 1569586423509}>

            node = record["batch"]
            batch = Batch.from_node(node)
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


class BatchUpdater(DataService):
    """
    Batch datastore for write and update in transaction.
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
        batch = Batch()
        res = shareds.dservice.ds_new_batch_id()

        batch.id = res.get("id")
        batch.user = userid
        batch.file = file.replace("_clean.", ".")
        batch.mediapath = mediapath

        res = batch.save()
        self.batch = batch

        return {"batch": batch, "status": Status.OK}

    def batch_get_one(self, user, batch_id):
        """Get Batch object by username and batch id. """
        ret = shareds.dservice.ds_get_batch(user, batch_id)
        # returns {"status":Status.OK, "node":record}
        try:
            node = ret['node']
            batch = Batch.from_node(node)
            return {"status":Status.OK, "item":batch}
        except Exception as e:
            statustext = (
                f"BatchUpdater.get_batch failed: {e.__class__.__name__} {e}"
            )
            return {"status": Status.ERROR, "statustext": statustext}

    def batch_mark_status(self, b_status):
        """ Mark this data batch status. """
        res = shareds.dservice.ds_batch_set_status(
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
