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

'''
Created on 2.3.2018

@author: jm

    Administrator model methods

    stk_upload/
        admin/
            templates/
                admin/
                    index.html
            __init__.py
            form.py
            models.py
            routes.py
'''
import shareds
import logging
logger = logging.getLogger('stkserver')

from flask_babelex import _

from .cypher_adm import Cypher_adm


class DataAdmin():
    '''
    Methods for database maintaining
    '''

    def __init__(self, user):
        '''
        Constructor
        #TODO: Get better error code?
        '''
        self.username = user.username
        self.roles = user.roles
        if user.has_role('admin'):
            return
        raise ValueError(_("User {} has not admin privileges").format(self.username))



    def _remove_chunks(self, cypher_clause, user=None):
        ''' Execute Delete cypher clause in appropriate chunks. '''
        LIMIT=2000
        cnt_all = 0
        cnt_nodes = -1
        while cnt_nodes:
            if user:
                result = shareds.driver.session().run(cypher_clause, limit=LIMIT,
                                                      user=user)
            else:
                result = shareds.driver.session().run(cypher_clause, limit=LIMIT)
            counters = shareds.db.consume_counters(result)
            if counters:
                cnt_nodes = counters.nodes_deleted
                cnt_relations = counters.relationships_deleted
                cnt_all += cnt_nodes
                print(f"Deleted {cnt_nodes} nodes, {cnt_relations} relations")
            else:
                print("That's All, Folks!")
        
        return cnt_all

    def db_reset(self, opt=None):
        if opt == "total":
            """ Koko kanta tyhjennetään """
            msg = _("All data is deleted. ")
            cnt = self._remove_chunks(Cypher_adm.remove_all_nodes)
            #logger.info(f'bp.admin.models.data_admin.DataAdmin.db_reset/{opt} n={cnt}')

        elif opt == "save_users":
            msg = _("All data but users and roles are removed.")
            cnt = self._remove_chunks(Cypher_adm.remove_data_nodes)
            #logger.info(f'bp.admin.models.data_admin.DataAdmin.db_reset/{opt} n={cnt}')

        elif opt == "my_own":
            # It is possible to check, id there are nodes with a foreign owners, 
            # too. It takes 60s for 750 persons data:
            #
            # match (u:User) -[:SUPPLEMENTED]-> (up:UserProfile) -[*]-> (x)  
            #     where u.username="user1"
            # with x
            # match (x) <-[*]- (p:UserProfile) where not p.username="user1"
            #     RETURN labels(x)[0] as lab, count(x)

            msg = _("All persons and event by %(un)s are removed.", un=self.username)
            cnt = self._remove_chunks(Cypher_adm.remove_my_nodes, user=self.username)
            #logger.info(f'bp.admin.models.data_admin.DataAdmin.db_reset/{opt} n={cnt}')

        msg2 = _('Removed %(cnt)d nodes', cnt=cnt)
        return {'msg':'\n'.join((msg, msg2)), 'count':cnt}

    
    @classmethod
    def build_free_text_search_indexes(cls, tx=None):
        if not tx:
            tx = shareds.driver.session()
        result = tx.run(Cypher_adm.build_indexes)
    
        