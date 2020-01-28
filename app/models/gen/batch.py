'''
    Data Batch node to connect business nodes to UserProfile.

Created on 29.11.2019

@author: jm
'''
from models.util import format_timestamp
import shareds
from bp.admin.models.cypher_adm import Cypher_adm
from bp.audit.models.cypher_audit import Cypher_batch_stats
from datetime import date, datetime


class Batch():
    '''
    Creates a log of userid bach steps.

    append()  Adds a log event to log
    list() Gets the log contenst objects 
    '''

    def __init__(self, userid=None):
        '''
        Creates a Batch object
        '''
        self.uniq_id = None
        self.user = userid
        self.file = None
        self.id = None
        self.status = 'started'
        self.timestamp = 0
            
#     def __init__(self, user=None, is_audit=False):
#         '''
#         Decide, which user is included in reports (if limited)
#         '''
#         self.user = user
#         self.is_audit = is_audit

    
    def __str__(self):
        return f"{self.user} / {self.id}"

    @classmethod
    def from_node(cls, node):
        ''' Convert a Neo4j node to Batch object.
        '''
        obj = cls()
        obj.uniq_id = node.id
        obj.user = node.get('user', "")
        obj.file = node.get('file', None)
        obj.id = node.get('id', None)
        obj.status = node.get('status', "")
        obj.timestamp = node.get('timestamp', 0)
        obj.upload = format_timestamp(obj.timestamp)
        return obj


    def get_user_batch_stats(self):
        ''' Get statistics of user Batch contents.
        
            u["usr1"].append({batch:"usr1 2019-05-03.001", "Family":94, "Note":224, "Person":153})
        '''
        labels = []
        users = {}
        result = shareds.driver.session().run(Cypher_batch_stats.get_batches, 
                                              user=self.user)
        for record in result:
            # <Record batch=<Node id=319388 labels={'Batch'} 
            #    properties={ // 'mediapath': '/home/jm/my_own.media', 
            #        'file': 'uploads/jpek/Julius_vanhemmat_clean.gramps', 
            #        'id': '2019-08-21.002', 'user': 'jpek', 'timestamp': 1566398894787, 
            #        'status': 'completed'}> 
            #  label='Note'
            #  cnt=2>
            batch = record['batch']
            label = record['label']
            cnt = record['cnt']
            batch_id = batch.get('id')
            ts = batch.get('timestamp')
            if ts:
                t = float(ts)/1000.
                tstring = datetime.fromtimestamp(t).strftime("%d.%m.%Y %H:%M")
#                 tstring = datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M")
#                 d, t = tstring.split()
#                 if batch[:10] == d:
#                     tstring = t
            else:
                tstring = ""
            label = record['label']
            if not label: label = ""
            # Trick: Set Person as first in sort order!
            if label == "Person": label = " Person"
            if label and not label in labels:
                labels.append(label)
            cnt = record['cnt']

            key = f'{self.user}/{batch_id}/{tstring}'
            if not key in users:
                users[key] = {}
            users[key][label] = cnt

            #print(f'users[{key}] {users[key]}')

        return sorted(labels), users


    @staticmethod
    def list_empty_batches():
        ''' Gets a list of db Batches without any linked data.
        '''
        batches = []
        class Upload: pass

        result = shareds.driver.session().run(Cypher_stats.get_empty_batches)

        for record in result:
            # <Node id=317098 labels={'Batch'}
            #    properties={'file': 'uploads/juha/Sibelius_20190820_clean.gpkg', 
            #        'id': '2019-09-27.001', 'user': 'juha', 'status': 'started', 
            #        'timestamp': 1569586423509}>
    
            node = record['batch']
            batch = Batch.from_node(node)
            batches.append(batch)

        return batches

    @staticmethod
    def drop_empty_batches():
        ''' Gets a list of db Batches without any linked data.
        '''
        today = str(date.today())
        record = shareds.driver.session().run(Cypher_adm.drop_empty_batches,
                                              today=today).single()
        cnt = record[0]
        return cnt


    