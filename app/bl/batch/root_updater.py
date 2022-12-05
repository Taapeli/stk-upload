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
'''
Created on 7.12.2021

@author: jm
'''
import os
import time
from flask_babelex import _

import shareds
from models import loadfile
from database.accessDB import DB_SCHEMA_VERSION
from bl.base import IsotammiException #, Status
from bp.admin import uploads
from pe.dataservice import DataService
from pe.neo4j.nodereaders import Root_from_node

class RootUpdater(DataService):
    """
    Root data store for write and update. 
    """

    def __init__(self, service_name: str, tx=None):
        """
        Initiate data store for update in given transaction or without transaction.
        """
        super().__init__(service_name, tx=tx)

    # @staticmethod
    # def root_save(tx, attr):
    #     return RootUpdater.md_batch_save(tx, attr)

    def create_batch(self, username, infile):
        """ Create a new Root node for given user and infile. 
        """
        from .root import Root, State, Status
        def new_batch_tx(tx, dataservice, username):
            """ A session.write_transaction function.
                :param:    dataservice    Neo4jUpdateService
                :param:    username   str
            """
            # Lock db to avoid concurrent Batch loads
            if not dataservice.ds_aqcuire_lock(tx, "batch_id"):
                return None

            # New Root object with next free batch id
            root = Root()
            root.id = dataservice.ds_new_batch_id(tx)
            root.user = username
            root.db_schema = DB_SCHEMA_VERSION
            res = root.save(tx)
            if Status.has_failed(res):
                raise IsotammiException("Could not create Root node")

            # Prepare uploads folder
            upload_folder = uploads.get_upload_folder(username)
            batch_upload_folder = os.path.join(upload_folder, root.id)
            os.makedirs(batch_upload_folder, exist_ok=True)

            # Load user's XML file
            root.file = loadfile.upload_file(infile, batch_upload_folder)

            root.xmlname = infile.filename
            root.metaname = root.file + ".meta"
            root.logname = root.file + ".log"
            root.save(tx)
            shareds.tdiff = time.time() - t0    #TODO Wrong place!

            # Create metafile
            uploads.set_meta(
                username,
                root.id,
                infile.filename,
                status=State.FILE_UPLOADED,
                upload_time=time.time(),
                # material_type=material_type, description=description,
            )
            return root

        t0 = time.time()
        # with RootUpdater("update") as root_service:
        with shareds.driver.session() as session:

            # Create Root node with next free batch id
            root = session.write_transaction(new_batch_tx,
                                             self.dataservice, username)
            shareds.tdiff = time.time() - t0
            return root

    # @staticmethod def new_batch(username): # -> create_batch

    def batch_get_one(self, user, batch_id):
        """Get Root object by username and batch id (in BatchUpdater). """
        from .root import Status # ,Root
        try:
            ret = self.dataservice.ds_get_batch(user, batch_id)
            # returns {"status":Status.OK, "node":record}
            node = ret['node']
            batch = Root_from_node(node)
            return {"status":Status.OK, "item":batch}
        except Exception as e:
            statustext = (
                f"BatchUpdater.batch_get_one failed: {e.__class__.__name__} {e}"
            )
            return {"status": Status.ERROR, "statustext": statustext}

    def change_state(self, batch_id, username, b_state):
        """ Set this data batch status. """
        res = self.dataservice.ds_batch_set_state(batch_id, username, b_state)
        return res

    def select_auditor(self, batch_id, auditor_username):
        """ Mark auditor for this data batch and set status. 

            # - (3) Change auditor's DOES_AUDIT --> DID_AUDIT
            # If there is multiple auditors, purge others but current
            res1 = serv.purge_former_auditors(batch_id, user_audit)
            # 5. "start"     Audit request -> Auditing (1,2,3)
            # - (2) Add DOES_AUDIT
            _res = serv.select_auditor(batch_id, user_audit)
        """
        from .root import State

        allowed_states = [State.ROOT_AUDIT_REQUESTED,
                          State.ROOT_AUDITING,
                          State.ROOT_ACCEPTED,
                          State.ROOT_REJECTED]
        res = self.dataservice.ds_batch_set_auditor(batch_id,
                                                    auditor_username, 
                                                    allowed_states)
        return res

    def purge_old_access(self, batch_id, auditor_username):
        """ Removes old HAS_ACCESS permission. NOT USED
        
            Returns 
                - ID(Root), if removed
                - None if no HAS_ACCESS found
        """
        res = self.dataservice.ds_batch_purge_access(batch_id, auditor_username)
        return res

    def purge_former_auditors(self, batch_id, auditor_username):
        """ Make current auditors as former auditors.
            1. If there is multiple auditors, purge others but current
            2. If the auditor has HAS_ACCESS permission but not HAS_LOADED,
               replace it with DOES_AUDIT
        """
        res = self.dataservice.ds_batch_purge_auditors(batch_id, auditor_username)
        # Got {status, removed_auditors}
        removed_auditors = res.get("removed_auditors", [])
        if len(removed_auditors) > 0:
            auditors = ", ".join(removed_auditors)
            msg = _("Superseded auditor '%(a)s' from batch %(b)s", a=auditors, b=batch_id)
            # Return removed auditors
            #res["removed_auditors"] = removed_auditors
            res["msg"] = msg
        return res

    def set_access(self, batch_id, auditor_username):
        """ Create HAS_ACCESS permission, if the user has no previous accesses.
        """
        res = self.dataservice.ds_batch_set_access(batch_id, auditor_username)
        return res
    
    def set_audited(self, batch_id, user_audit, b_state):
        """ Set batch status and mark all auditions completed.
            - called from bp.audit.routes.auditor_ops.find_request_op
              with State.ROOT_ACCEPTED, State.ROOT_REJECTED
            - TODO: how about self.select_auditor?
        """
        res = self.dataservice.ds_batch_set_audited(batch_id, user_audit, b_state)
        return res

    def remove_auditor(self, batch_id, auditor_username):
        """ Mark auditor for this data batch and set status.

            (4) Change all DOES_AUDIT -> DID_AUDIT, ts_to=now
            If no other is auditing, the status is changed.
        
            Returns {status, identity, d_days}, where identity = Root.id
            and d_days duration of (last) audition in days.
        """
        from .root import State
        new_state = State.ROOT_AUDIT_REQUESTED
        res = self.dataservice.ds_batch_remove_auditor(batch_id,
                                                       auditor_username, 
                                                       new_state)
        return res

    def batch_update_descr(self, batch_id, description, username):
        """ Update Root.description. """
        from bl.base import Status
    
        res = self.batch_get_one(username, batch_id)
        if Status.has_failed(res):
            raise RuntimeError(_("Failed to retrieve batch"))
        batch = res['item']
        batch.description = description
        res = batch.save(self.dataservice.tx)
        return res

    def commit(self):
        self.dataservice.ds_commit()
    def rollback(self):
        self.dataservice.ds_rollback()

    # def media_create_and_link_by_handles(self, uniq_id, media_refs):
    #     """NOT IN USE: Save media object and it's Note and Citation references
    #     using their Gramps handles.
    #     """
    #     if media_refs:
    #         self.dataservice.ds_create_link_medias_w_handles(uniq_id, media_refs)

