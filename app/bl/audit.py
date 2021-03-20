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
    Data Batch node to connect business nodes to UserProfile.

Created on 29.11.2019

@author: jm
'''
import shareds
from datetime import datetime #,date
from flask import flash
from flask_babelex import _

from bl.base import Status
from pe.neo4j.cypher.cy_batch_audit import CypherBatch
from pe.neo4j.cypher.cy_batch_audit import CypherAudit

from models.util import format_timestamp

class Audit():
    '''
    Audit batch node and statistics about them. 
    '''

    def __init__(self, auditor=None):
        '''
        Creates an Audit object.
        '''
        self.uniq_id = None
        self.auditor = auditor
        self.user = None
        self.id = None
        #self.status = 'started'
        self.timestamp = 0
        self.updated = ""   # timestamp as string

    def __str__(self):
        return f"{self.auditor} > {self.user} {self.id}"

    @classmethod
    def from_node(cls, node):
        ''' Convert a Neo4j node to an Audit object.

        <Node id=439060 labels={'Audit'}
            properties={'auditor': 'juha', 'id': '2020-01-03.001', 
                        'user': 'jpek', 'timestamp': 1578940247182}>
        '''
        obj = cls()
        obj.uniq_id = node.id
        obj.user = node.get('user', "")
        obj.auditor = node.get('auditor')
        obj.id = node.get('id', None)
        #obj.status = node.get('status', "")
        obj.timestamp = node.get('timestamp', 0)
        if obj.timestamp:
            obj.updated = format_timestamp(obj.timestamp/1000.)
        return obj


    @staticmethod
    def get_auditor_stats(auditor=None):
        ''' Get statistics of auditor's audition batch contents.
        '''
        titles = []
        labels = {}
        if auditor:
#             #self.tx.run(CypherBatch.batch_create, b_attr=attr)
#             res = shareds.datastore._batch_save(attr)

            result = shareds.driver.session().run(CypherAudit.get_my_audits,
                                                  oper=auditor)
        else:
            result = shareds.driver.session().run(CypherAudit.get_all_audits,
                                                  oper=auditor)
        for record in result:
            # <Record
            #    b=<Node id=439060 labels={'Audit'}
            #        properties={'auditor': 'juha', 'id': '2020-01-03.001', 
            #        'user': 'jpek', 'timestamp': 1578940247182}> 
            #    label='Note'
            #    cnt=17>
            b = Audit.from_node(record['b'])
            label = record['label']
            if not label: label = ""
            cnt = record['cnt']

            # Trick: Set Person as first in sort order!
            if label == "Person": label = " Person"
            if label and not label in titles:
                titles.append(label)

            key = f'{b.auditor}/{b.user}/{b.id}/{b.updated}'
            if not key in labels:
                labels[key] = {}
            labels[key][label] = cnt
            #print(f'labels[{key}] {labels[key]}')

        return sorted(titles), labels

    @staticmethod
    def get_stats(audit_id):
        ''' Get statistics of given Batch contents.
        '''
        labels = []
        batch = None
        result = shareds.driver.session().run(CypherBatch.get_single_batch, 
                                              batch=audit_id)
        for record in result:
            # <Record batch=<Node id=319388 labels={'Batch'} 
            #    properties={ // 'mediapath': '/home/jm/my_own.media', 
            #        'file': 'uploads/jpek/Julius_vanhemmat_clean.gramps', 
            #        'id': '2019-08-21.002', 'user': 'jpek', 'timestamp': 1566398894787, 
            #        'status': 'completed'}> 
            #  label='Note'
            #  cnt=2>

            if not batch:
                batch = record['batch']
                user = batch.get('user')
                #audit_id = batch.get('id')
                ts = batch.get('timestamp')
                if ts:
                    t = float(ts)/1000.
                    tstring = datetime.fromtimestamp(t).strftime("%-d.%-m.%Y %H:%M")
                else:
                    tstring = ""
            label = record['label']
            if label == None: label = '-'
            # Trick: Set Person as first in sort order!
            if label == "Person": label = " Person"
            cnt = record['cnt']
            labels.append((label,cnt))

        return user, audit_id, tstring, sorted(labels)

    @staticmethod
    def delete_audit(username, batch_id):
        ''' Delete an audited batch having the given id.
        '''
        label_sets = [  # Grouped for decent size chunks in logical order
                ["Note"],
                ["Repository", "Media"],
                ["Place"],
                ["Source"],
                ["Event"],
                ["Person"],
                ["Family"]
            ]

        msg, deleted = '', 0
        try:
            with shareds.driver.session() as session:
                # Delete the node types that are not directly connected to Audit node
                with session.begin_transaction() as tx:
                    result = tx.run(CypherAudit.delete_names,
                                    batch=batch_id)
                    this_delete = result.single()[0]
                    print(f"bl.audit.delete_audit: deleted {this_delete} name nodes")
                    deleted += this_delete

                    result = tx.run(CypherAudit.delete_place_names,
                                    batch=batch_id)
                    this_delete = result.single()[0]
                    print(f"bl.audit.delete_audit: deleted {this_delete} place name nodes")
                    deleted += this_delete

                    # result = tx.run(CypherAudit.delete_citations,
                    #                 batch=batch_id)
                    # this_delete = result.single()[0]
                    # print(f"bl.audit.delete_audit: deleted {this_delete} citation nodes")
                    # deleted += this_delete

                # Delee the directly connected node types as defined by the labels
                for labels in label_sets:
                    with session.begin_transaction() as tx:
                        result = tx.run(CypherAudit.delete,
                                        batch=batch_id,
                                        labels=labels)
                        this_delete = result.single()[0]
                        print(f"bl.audit.delete_audit: deleted {this_delete} nodes of type {labels}")
                        deleted += this_delete

                # Finally, delete the audit node itself
                with session.begin_transaction() as tx:
                    result = tx.run(CypherAudit.delete_audit_node,
                                    batch=batch_id)

            flash(_("Approved batch id %(batch_id)s with %(deleted)d nodes has been deleted",
                batch_id=batch_id, deleted=deleted), 'info')
                                    
        except Exception as e:
            msg = f'Only {deleted} objects deleted: {e.__class__.__name__} {e}'
            print(f'Audit.delete_audit: {msg}')
            flash(msg, "flash_error")

        return msg, deleted
   

#     @staticmethod
#     def get_audit_stats(batch_id):
#         ''' Get statistics of given Batch contents.
#         '''
#         labels = []
#         batch = None
#         result = shareds.driver.session().run(CypherBatch.get_single_batch, 
#                                               batch=batch_id)
#         for record in result:
#             # <Record batch=<Node id=319388 labels={'Batch'} 
#             #    properties={ // 'mediapath': '/home/jm/my_own.media', 
#             #        'file': 'uploads/jpek/Julius_vanhemmat_clean.gramps', 
#             #        'id': '2019-08-21.002', 'user': 'jpek', 'timestamp': 1566398894787, 
#             #        'status': 'completed'}> 
#             #  label='Note'
#             #  cnt=2>
# 
#             if not batch:
#                 batch = record['batch']
#                 user = batch.get('user')
#                 #batch_id = batch.get('id')
#                 ts = batch.get('timestamp')
#                 if ts:
#                     t = float(ts)/1000.
#                     tstring = datetime.fromtimestamp(t).strftime("%-d.%-m.%Y %H:%M")
#                 else:
#                     tstring = ""
#             label = record['label']
#             if label == None: label = '-'
#             # Trick: Set Person as first in sort order!
#             if label == "Person": label = " Person"
#             cnt = record['cnt']
#             labels.append((label,cnt))
# 
#         return user, batch_id, tstring, sorted(labels)
#  

