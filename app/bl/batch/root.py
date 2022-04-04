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
#from pe import dataservice

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
#from typing import Any, Optional
#from bl.base import IsotammiException
import logging

logger = logging.getLogger('stkserver')

import shareds
from models.util import format_ms_timestamp
from bl.admin.models.cypher_adm import Cypher_adm
from bl.base import Status, NodeObject
from bl.material import Material

from .root_updater import RootUpdater
from pe.dataservice import DataService
from pe.neo4j.cypher.cy_root import CypherRoot, CypherAudit
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
    
    #See value translations in ui.jinja_filters
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
    ROOT_DELETED = "Deleted"
    ROOT_UNKNOWN = "Unknown"
    ROOT_DEFAULT_STATE = ROOT_ACCEPTED

    OBJECT_CANDICATE = "Candidate"  # old BATCH_CANDIDATE  = "completed"
    OBJECT_ACCEPTED = "Accepted"
    OBJECT_MERGED = "Merged"
    OBJECT_REJECTED = "Rejected"


class Root(NodeObject):
    """
    Data Root node for candidate, auditing and approved material chunks.
    
    Given timestamp is milliseconds from epoch. Convert to string by 
    """

    def __init__(self, userid:str=None):
        """
        Creates a Root object
        """
        self.uniq_id = None
        self.user = userid
        self.file = None
        self.id = ""  # batch_id
        self.material_type = None   #DEFAULT_MATERIAL "Family Tree" or other
        self.state = State.FILE_LOADING
        self.mediapath = None  # Directory for media files
        self.timestamp = 0 # Milliseconds; Convert to string by 
        self.description = ""
        self.xmlname = ""
        self.metaname = ""
        self.logname = ""

    def __str__(self):
        return f"Root {self.user} / {self.id} {self.material_type}({self.state})"

    def for_auditor(self):
        """ Is relevant for auditor? """
        if self.state in [
            State.ROOT_AUDIT_REQUESTED, 
            State.ROOT_AUDITING, 
            State.ROOT_ACCEPTED, 
            State.ROOT_REJECTED]:
            return True
        return False

    def filename(self):
        """ Get filenname of Root.file. """
        try:
            return os.path.split(self.file)[1]
        except Exception:
            return ""

    def state_transition(self, oper:str) -> bool:
        """ Allowed auditor operations and state transitions.

        Some operations may be depending on i_am_auditor (if you are
        registered as auditor for this batch).

        For current (self.state, oper) returns one of following -
            - True, if allowed operation
            - False, if not allowed
        """
        # Allowed transitions
        if self.state == State.ROOT_AUDIT_REQUESTED:
            ret = oper in ["browse", "start"]
        elif self.state == State.ROOT_AUDITING:
            # Presuming you are one of auditors. (withdraw/reject not used)
            ret = oper in ["browse", "accept", "withdraw", "reject"]
        elif self.state == State.ROOT_ACCEPTED:
            ret = oper in ["browse", "start"]
        elif self.state == State.ROOT_REJECTED:
            ret = oper in ["browse", "start", "delete"]

        # print(f"#bl.batch.root.Root.state_transition: {self.state} {oper} -> {ret}")
        return ret
        

    def save(self, tx):
        """Create or update Root node.

        Returns {'id':self.id, 'status':Status.OK}
        """
        # Root node variables
        attr = {
            "id": self.id,
            "user": self.user,
            "file": self.file,
            "mediapath": self.mediapath,
            # timestamp": <to be set in cypher>,
            # id: <uniq_id from result>,
            "state": self.state,
            "material": self.material_type,
            "description": self.description,
            "xmlname": self.xmlname,
            "metaname": self.metaname,
            "logname": self.logname,
        }

        with RootUpdater("update", tx=tx) as bl_service:
            self.uniq_id = bl_service.dataservice.ds_batch_save(tx, attr)
        return {"status": Status.OK, "identity": self.uniq_id}


    @classmethod
    def from_node(cls, node):
        # type: (Any) -> Root
        """Convert a Neo4j node to Root object."""
        obj = cls()
        obj.uniq_id = node.id
        obj.user = node.get("user", "")
        obj.file = node.get("file", None)
        obj.id = node.get("id", None)
        obj.state = node.get("state", "")
        obj.mediapath = node.get("mediapath")
        obj.timestamp = node.get("timestamp", 0)
        obj.upload = format_ms_timestamp(obj.timestamp)
        #obj.auditor = node.get("auditor", None)
        obj.material_type = node.get("material", DEFAULT_MATERIAL)
        obj.description = node.get("description", "")
        obj.xmlname = node.get("xmlname", "")
        obj.metaname = node.get("metaname", "")
        obj.logname = node.get("logname", "")
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
    def get_batch(username: str, batch_id: str):
        # Returns None or Root object with user and rel_type fields
        with shareds.driver.session() as session:
            record = session.run(
                CypherRoot.get_batch, username=username, batch_id=batch_id
            ).single()
            if record:
                root = Root.from_node(record['b'])
                root.user = username
                root.rel_type = record.get('rel_type')
                return root
        return None

    @staticmethod
    def get_batches():
        result = shareds.driver.session().run(CypherRoot.list_all)
        for rec in result:
            yield dict(rec.get("b"))

    # @staticmethod # def get_batch_pallette(username):
    #     """ Get my batches and batch collections.
    #  -- Ei toimi näin, hyväksyttyjä materiaaleja ei voi palauttaa Root-solmuina
    #
    #         my_batches      batches loaded by username
    #         collections     sets of accepted batches by material type
    #     """
    #     batches = []
    #     commons = []
    #     result = shareds.driver.session().run(CypherRoot.get_root_pallette, 
    #                                           user=username)
    #     for record in result:
    #         # Record: <Record  user='juha' material_type='Place Data' 
    #         #    state='Candidate' batch_id='2021-11-14.005' 
    #         #    description='Käkisalmi, Catharina Javanaisen esivanhemmat'>
    #         user = record.get("user")
    #         root = Root.from_node(record.get("root"))
    #         if user:
    #             print(f"#Root.get_batch_pallette: batch {root}")
    #             batches.append(root)
    #         else:
    #             print(f"#Root.get_batch_pallette: common {root}")
    #             commons.append(root)
    #
    #     return batches, commons

    @staticmethod
    def get_my_batches(username:str, material:Material):
        """ Returns user's batches, which are in Candidate state. """
        with shareds.driver.session() as session:
            result = run_cypher(session, CypherRoot.get_my_batches, username, material)
            for rec in result:
                root = Root.from_node(rec["root"])
                # print(f"#get_my_batches: {root}")
                yield root

    @staticmethod
    def get_materials_accepted(material_type):
        """ Returns list of accepted materials of material_type. 
        """
        roots = []
        with shareds.driver.session() as session:
            result = session.run(CypherRoot.get_materials_accepted,
                                 m_type=material_type)
            for rec in result:
                root = Root.from_node(rec.get("root"))
                user = rec.get("user")
                root.user = dict(user.items())
                roots.append(root)
        print(f"#get_materials_accepted: {len(roots)} nodes of {material_type})")
        return roots

    @staticmethod
    def count_materials_accepted():
        """ Returns number of accepted materials by material_type. 
        """
        with shareds.driver.session() as session:
            result = session.run(CypherRoot.count_materials_accepted)
            for rec in result:
                # Record: <Record root.material='Family Tree' count(*)=6>
                m_type = rec.get("material_type")
                m_count = rec.get("nodes")
                print(f"#count_materials_accepted: {m_type} ({rec.get('nodes')} nodes)")
                yield {"material_type": m_type, "count": m_count }

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
            #print(f"bl.batch.Root.get_user_stats: user_data[{key}] {user_data[key]}")

        return sorted(titles), user_data

    @staticmethod
    def get_batch_stats(batch_id):
        """Get statistics of given Batch contents.

           Called from bp.audit.routes.audit_pick
        """
        labels = []
        user = None
        b = None
        node = None
        result = shareds.driver.session().run(
            CypherRoot.get_single_batch, batch=batch_id
        )
        for record in result:
            # <Record
            #    profile=<Node id=21 labels=frozenset({'UserProfile'})
            #        properties={'apikey': '05dba9c9bfb643b39bf385de8dcac272', 'software': 'Gramps', 
            #            'research_years': '11', 'created_at': 1620043583370, 'language': 'fi', 
            #            'researched_names': 'Ankka, Hanhi', 'text_message': 'Jos olet ...', 
            #            'GSF_membership': 'yes', 'name': 'Aku Ankka', 'email': 'aku@ankkalinna.com',
            #            'researched_places': 'Ankkalinna', 'username': 'aku', 'agreed_at': 1620032783307}>
            #    root=<Node id=119472 labels=frozenset({'Root'})
            #        properties={'file': 'uploads/juha/Untitled_1.isotammi.gpkg', 'material':'Family Tree',
            #            'description': 'Pieni koeaineisto', 'id': '2021-05-27.002', 'state': 'Candidate', 
            #            'user': 'aku', 'timestamp': 1622140130273}>
            #    label='Person'
            #    cnt=6
            #    auditors=['juha',1620570475208,None]
            #    prev_audits=['joku',1630402986262,1648739430163]
            #    has_access=['jpek']
            # >
            if node is None or \
                    (node.id != record["root"].id and \
                     user != record['profile']['username']):
                # Not same user and root
                user = record['profile']['username']
                node = record["root"]
                b = Root.from_node(node)
                # Users granted special access
                b.has_access = record['has_access'] 
                b.auditors = []
                for au_user, ms_from, ms_to in record["auditors"]:
                    # [username, time_start]
                    if au_user:
                        b.auditors.append([au_user, ms_from, ms_to])
                b.prev_audits = []
                for au_user, ms_from, ms_to in record["prev_audits"]:
                    # [username, time_end, time_start]
                    if au_user:
                        b.prev_audits.append([au_user, ms_from, ms_to])
            label = record.get("label", "-")
            # Trick: Set Person as first in sort order!
            if label == "Person":
                label = " Person"
            cnt = record["cnt"]
            labels.append((label, cnt))

        return user, b, sorted(labels)


    @staticmethod
    def list_empty_batches():
        """Gets a list of db Batches without any linked data."""
        batches = []
        print('Batch.list_empty_batches: ERROR obsolete!')
        # class Upload:
        #     pass        # result = shareds.driver.session().run(CypherRoot.TODO_get_empty_batches)
        #
        # for record in result:
        #     # <Node id=317098 labels={'Batch'}
        #     #    properties={'file': 'uploads/juha/Sibelius_20190820_clean.gpkg',
        #     #        'id': '2019-09-27.001', 'user': 'juha', 'status': 'started',
        #     #        'timestamp': 1569586423509}>
        #
        #     node = record["batch"]
        #     batch = Root.from_node(node)
        #     batches.append(batch)

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
        #TODO Get DOES_AUDIT timestamp
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

# class BatchUpdater(DataService): # -> bl.batch.root_updater.RootUpdater
#     """ Root data store for write and update. 


class BatchReader(DataService):

    def __init__(self, service_name: str):
        super().__init__(service_name)
        self.idstr = f"{self.__class__.__name__}"
        # logger.debug(f'#~~~{self.idstr} init')
        # Find <class 'pe.neo4j.*service'> and initialize it
        self.service_name = service_name
        service_class = shareds.dataservices.get(self.service_name)
        if not service_class:
            raise KeyError(
                f"BatchReader.__init__: name {self.service_name} not found"
            )
        # Initiate selected service object
        self.dataservice = service_class(shareds.driver)

    # Not used! / JMä 3.4.2022
    # def batch_get_one(self, user, batch_id):
    #     """Get Root object by username and batch id (in BatchReader). """
    #     try:
    #         ret = self.dataservice.ds_get_batch(user, batch_id)
    #         # returns {"status":Status.OK, "node":record}
    #         # print(f"bl.batch.BatchReader.batch_get_one: return {ret}")
    #         node = ret['node']
    #         batch = Root.from_node(node)
    #         return {"status":Status.OK, "item":batch}
    #     except Exception as e:
    #         statustext = (
    #             f"BatchUpdater.batch_get_one failed: {e.__class__.__name__} {e}"
    #         )
    #         return {"status": Status.ERROR, "statustext": statustext}
