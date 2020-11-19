'''
    Data Batch node to connect business nodes to UserProfile.

Created on 29.11.2019

@author: jm
'''
import shareds
from datetime import date, datetime

from bl.base import Status
from pe.neo4j.cypher.cy_batch_audit import CypherBatch ######

from bp.admin.models.cypher_adm import Cypher_adm

from models.util import format_timestamp
from pe.db_writer import DbWriter


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
        self.id = None              # batch_id
        self.status = 'started'
        self.mediapath = None       # Directory for media files
        self.timestamp = 0
    
    def __str__(self):
        return f"{self.user} / {self.id}"

    def save(self, tx):
        ''' Create or update Batch node.
        
            Returns {'id':self.id, 'status':Status.OK}
        '''
        try:
            attr = {
                "id": self.id,
                "user": self.user,
                "file": self.file,
                "mediapath": self.mediapath,
                #timestamp": <to be set in cypher>,
                #id: <uniq_id from result>,
                "status": self.status
            }
            #self.tx.run(CypherBatch.batch_create, b_attr=attr)
            res = shareds.datastore._batch_save(attr)
            return res

        except Exception as e:
            return {'id':self.id, 'status':Status.ERROR, 
                    'statustext':f'bl.batch_audit.Batch.save: {e.__class__.__name__} {e}'}

#     def start_batch(self):
#         ''' Creates a new unique Batch node.
#         
#         The Batch obj argument contains - 
#         - id        a date followed by a new ordinal number '2018-06-05.001'
#         - user      batch creator
#         - status    'started'
#         - file      input filename
#         - mediapath media files location
#         '''
#         shareds.datastore._aqcuire_lock('batch_id')
# 
#         # 1. Find the next free Batch id
#         res = shareds.datastore._get_new_batch_id()
#         if res.get('status') != Status.OK:
#             # Failed to get an id
#             return res
# 
#         # 2. Save the new Batch node
#         self.id = res.get('id')
#         res = self.save()
# 
#         return res 

#     def get_new_batch_id(self):
#         ''' Find next unused Batch id.
#         
#             Returns {id, status, [statustext]}
#         '''
#         res = shareds.datastore._get_new_batch_id()
#         
#         if res.get('status') != Status.OK:
#             return res
#         batch_id = res.get('batch')
#         print("# New batch_id='{}'".format(batch_id))
#         return res #{'status':Status.OK, 'id':batch_id}


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
        obj.mediapath = node.get('mediapath')
        obj.timestamp = node.get('timestamp', 0)
        obj.upload = format_timestamp(obj.timestamp)
        obj.auditor = node.get('auditor', None)
        return obj

    @staticmethod
    def delete_batch(username, batch_id):
        with shareds.driver.session() as session:
            result = session.run(CypherBatch.delete,
                                 username=username, batch_id=batch_id)
            return result
                
    @staticmethod
    def get_filename(username, batch_id):
        with shareds.driver.session() as session:
            result = session.run(CypherBatch.get_filename,
                                 username=username, batch_id=batch_id).single()
            return result.get('b.file')
    
    @staticmethod
    def get_batches():
        result = shareds.driver.session().run(CypherBatch.list_all)
        for rec in result:
            print("p",rec.get('b').items())
            yield dict(rec.get('b'))


    @staticmethod
    def get_user_stats(user):
        ''' Get statistics of user Batch contents.
        
            If the Batch has been moved to an Audit batch, tis method returns
            ("Audit", count) to user_data data
        '''
        # Get your approved batches
        approved = {}
        result = shareds.driver.session().run(CypherBatch.get_passed, user=user)
        for node, count in result:
            # <Record batch=<Node id=435790 labels={'Audit'} 
            #    properties={'auditor': 'juha', 'id': '2020-03-24.002', 
            #    'user': 'juha', 'timestamp': 1585070354153}>
            #  cnt=200>
            b = Batch.from_node(node)
            approved[b.id] = count

        # Get current researcher batches
        titles = []
        user_data = {}
        result = shareds.driver.session().run(CypherBatch.get_batches, user=user)
        for record in result:
            # <Record batch=<Node id=319388 labels={'Batch'} 
            #    properties={ // 'mediapath': '/home/jm/my_own.media', 
            #        'file': 'uploads/jpek/Julius_vanhemmat_clean.gramps', 
            #        'id': '2019-08-21.002', 'user': 'jpek', 'timestamp': 1566398894787, 
            #        'status': 'completed'}> 
            #  label='Note'
            #  cnt=2>
            b = Batch.from_node(record['batch'])
            label = record.get('label')
            if not label: label = ''
            cnt = record['cnt']
                    
            batch_id = b.id
            tstring = Batch.timestamp_to_str(b.timestamp)

            # Trick: Set Person as first in sort order!
            if label == "Person": label = " Person"
            if label and not label in titles:
                titles.append(label)

            key = f'{user}/{batch_id}/{tstring}'
            if not key in user_data:
                user_data[key] = {}
            user_data[key][label] = cnt

            audited = approved.get(batch_id)
            if audited:
                user_data[key]['Audit'] = audited

            print(f'user_data[{key}] {user_data[key]}')

        return sorted(titles), user_data


    @staticmethod
    def timestamp_to_str(ts):
        ''' Timestamp to display format. '''
        if ts:
            t = float(ts) / 1000.
            tstring = datetime.fromtimestamp(t).strftime("%-d.%-m.%Y %H:%M")
        else:
            tstring = ""
        return tstring

    @staticmethod
    def get_batch_stats(batch_id):
        ''' Get statistics of given Batch contents.
        '''
        labels = []
        batch = None
        result = shareds.driver.session().run(CypherBatch.get_single_batch, 
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
                tstring = Batch.timestamp_to_str(ts)
            label = record.get('label','-')
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

        result = shareds.driver.session().run(CypherBatch.get_empty_batches)

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


class BatchDatastore:
    '''
    Abstracted batch datastore.

        - Create:
          BatchWriter(dbdriver, use_transaction=True), which calls
          pe.db_writer.DbWriter.__init__(dbdriver, use_transaction=True) 
          to define the database driver and transaction.

        - Methods return a dict result object {'status':Status, ...}
    '''
    # Uses classes Role, User, UserProfile from setups.py

    def __init__(self, driver, dbservice):
        ''' Initiate datastore.

        :param: driver    neo4j.DirectDriver object
        :param: dbservice pe.neo4j.write_driver.Neo4jWriteDriver
        '''
        self.driver = driver
        self.dbservice = dbservice
        self.batch  = None

    def start_batch(self,userid, file, mediapath):
        '''
        Initiate new Batch.
        
        :param: userid    user
        :param: file      input file
        :param: mediapath media file store path
        '''
        # Lock db to avoid concurent Batch loads
        self.dbservice._aqcuire_lock('batch_id')

        # Find the next free Batch id
        self.batch = Batch()
        res = self.dbservice._get_new_batch_id()
        if res.get('status') != Status.OK:
            # Failed to get an id
            #TODO shareds.datastore._remove_lock('batch_id')
            return res

        self.batch.id = res.get('id')
        self.batch.user = userid
        self.batch.file = file
        self.batch.mediapath = mediapath 
        print(f'bl.batch_audit.BatchDatastore: new Batch {self.batch.id} identity={self.batch.uniq_id}')
    
#         # Create Batch node
#         handler.batch.start_batch()
#     handler.batch.id = handler.blog.start_batch(handler.dbdriver.tx,
#                                                 file_cleaned, handler.batch.mediapath)


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

