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
from pe.managed_dataservice import ManagedDataService
#from pe.dataservice import DataService
from bl.root.root import Root, State, Status

class RootUpdater(ManagedDataService):
    """
    Root data store for write and update. 
    """

    def __init__(self, service_name: str, u_context=None, tx=None):
        """
        Initiate datastore for update in given transaction or without transaction.
        """
        super().__init__(service_name, user_context=u_context, tx=tx)
        self.batch = None

    def new_batch(self, username):
        """
        Initiate new Batch.
        """
        def new_batch_tx(tx, username):
            """ A session.write_transaction function. """
            # Lock db to avoid concurent Batch loads
            self.dataservice.ds_aqcuire_lock(tx, "batch_id")
            # Find the next free Batch id
            res = self.dataservice.ds_new_batch_id(tx)
            batch = Root()
            batch.id = res.get("id")
            batch.user = username
            if batch.id:
                res = batch.save(tx, self.dataservice) #, self.dataservice)
                if not Status.has_failed(res):
                    return batch
            return None

        # Creates neo4j.work.simple.Session object and 
        # runs write_transaction function 'new_batch_id_tx'
        with self.dataservice.driver.session() as session:
            batch = session.write_transaction(new_batch_tx, username)
        
        return batch

    def batch_get_one(self, user, batch_id):
        """Get Root object by username and batch id (in BatchUpdater). """
        try:
            ret = self.dataservice.ds_get_batch(user, batch_id)
            # returns {"status":Status.OK, "node":record}
            node = ret['node']
            batch = Root.from_node(node)
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
        """ Mark auditor for this data batch and set status. """

        allowed_states = [State.ROOT_AUDIT_REQUESTED,
                          State.ROOT_AUDITING,
                          State.ROOT_REJECTED]
        res = self.dataservice.ds_batch_set_auditor(batch_id, auditor_username, 
                                                    allowed_states)
        return res

# def batch_mark_status(self, batch, b_status): --> change_state
#     """ Mark this data batch status. """

    def commit(self):
        """ Commit transaction. """
        self.dataservice.ds_commit()

    def rollback(self):
        """ Commit transaction. """
        self.dataservice.ds_rollback()

    def media_create_and_link_by_handles(self, uniq_id, media_refs):
        """Save media object and it's Note and Citation references
        using their Gramps handles.
        """
        if media_refs:
            self.dataservice.ds_create_link_medias_w_handles(uniq_id, media_refs)

