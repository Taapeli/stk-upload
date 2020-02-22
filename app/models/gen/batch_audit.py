'''
    Data Batch node to connect business nodes to UserProfile.

Created on 29.11.2019

@author: jm
'''
from models.util import format_timestamp
import shareds
from bp.admin.models.cypher_adm import Cypher_adm
from models.gen.cypher import Cypher_batch, Cypher_audit

from datetime import date, datetime


class Batch():
    '''
    User Batch node and statistics about them. 
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

    @staticmethod
    def delete_batch(username, batch_id):
        with shareds.driver.session() as session:
            result = session.run(Cypher_batch.delete,
                                 username=username, batch_id=batch_id)
            return result
                
    @staticmethod
    def get_filename(username, batch_id):
        with shareds.driver.session() as session:
            result = session.run(Cypher_batch.get_filename,
                                 username=username, batch_id=batch_id).single()
            return result.get('b.file')
    
    @staticmethod
    def get_batches():
        result = shareds.driver.session().run(Cypher_batch.list_all)
        for rec in result:
            print("p",rec.get('b').items())
            yield dict(rec.get('b'))


    @staticmethod
    def get_user_stats(user):
        ''' Get statistics of user Batch contents.
        '''
        titles = []
        users = {}
        result = shareds.driver.session().run(Cypher_batch.get_batches, user=user)
        for record in result:
            # <Record batch=<Node id=319388 labels={'Batch'} 
            #    properties={ // 'mediapath': '/home/jm/my_own.media', 
            #        'file': 'uploads/jpek/Julius_vanhemmat_clean.gramps', 
            #        'id': '2019-08-21.002', 'user': 'jpek', 'timestamp': 1566398894787, 
            #        'status': 'completed'}> 
            #  label='Note'
            #  cnt=2>
            b = Batch.from_node(record['batch'])
            label = record['label']
            if not label: label = ""
            cnt = record['cnt']

            batch_id = b.id
            ts = b.timestamp
            if ts:
                t = float(ts)/1000.
                tstring = datetime.fromtimestamp(t).strftime("%d.%m.%Y %H:%M")
                d, t = tstring.split()
                if batch_id[:10] == d:
                    tstring = t
            else:
                tstring = ""

            # Trick: Set Person as first in sort order!
            if label == "Person": label = " Person"
            if label and not label in titles:
                titles.append(label)
            cnt = record['cnt']

            key = f'{user}/{batch_id}/{tstring}'
            if not key in users:
                users[key] = {}
            users[key][label] = cnt

            print(f'users[{key}] {users[key]}')

        return sorted(titles), users

    @staticmethod
    def get_batch_stats(batch_id):
        ''' Get statistics of given Batch contents.
        '''
        labels = []
        batch = None
        result = shareds.driver.session().run(Cypher_batch.get_single_batch, 
                                              batch=batch_id)
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
                #batch_id = batch.get('id')
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

        return user, batch_id, tstring, sorted(labels)


    @staticmethod
    def list_empty_batches():
        ''' Gets a list of db Batches without any linked data.
        '''
        batches = []
        class Upload: pass

        result = shareds.driver.session().run(Cypher_batch.get_empty_batches)

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
            result = shareds.driver.session().run(Cypher_audit.get_my_audits,
                                                  oper=auditor)
        else:
            result = shareds.driver.session().run(Cypher_audit.get_all_audits,
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
        result = shareds.driver.session().run(Cypher_batch.get_single_batch, 
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


#     @staticmethod
#     def get_audit_stats(batch_id):
#         ''' Get statistics of given Batch contents.
#         '''
#         labels = []
#         batch = None
#         result = shareds.driver.session().run(Cypher_batch.get_single_batch, 
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

