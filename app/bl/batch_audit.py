'''
    Data Batch node to connect business nodes to UserProfile.

Created on 29.11.2019

@author: jm
'''
import shareds
from datetime import date, datetime

from bp.admin.models.cypher_adm import Cypher_adm
from pe.neo4j.cypher.batch_audit import CypherBatch

from models.util import format_timestamp
from models import dbutil


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


    def start_batch(self, tx, infile, mediapath):
        '''
        Creates a new Batch node with 
        - id        a date followed by an ordinal number '2018-06-05.001'
        - status    'started'
        - file      input filename
        - mediapath media files location
         
        You may give an existing transaction tx, 
        otherwise a new transaction is created and committed
        '''
 
        # 0. Create transaction, if not given
#         local_tx = False
#         with shareds.driver.session() as session:
#             if tx == None:
#                 tx = session.begin_transaction()
#                 local_tx = True
             
        dbutil.aqcuire_lock(tx, 'batch_id') #####
        
        # 1. Find the latest Batch id of today from the db
        base = str(date.today())
        try:
            result = tx.run(CypherBatch.batch_find_id, batch_base=base)
            batch_id = result.single().value()
            print("# Pervious batch_id={}".format(batch_id))
            i = batch_id.rfind('.')
            ext = int(batch_id[i+1:])
        except AttributeError as e:
            # Normal exception: this is the first batch of day
            #print ("Ei vanhaa arvoa {}".format(e))
            ext = 0
        except Exception as e:
            print ("Poikkeus {}".format(e))
            ext = 0
        
        # 2. Form a new batch id
        self.bid = "{}.{:03d}".format(base, ext + 1)
        print("# New batch_id='{}'".format(self.bid))
        
        # 3. Create a new Batch node
        b_attr = {
            'user': self.userid,
            'id': self.bid,
            'status': 'started',
            'file': infile,
            'mediapath': mediapath
            }
        tx.run(CypherBatch.batch_create, file=infile, b_attr=b_attr)
        #if local_tx:
        #   tx.commit()
 
        return self.bid


    def save(self):
        ''' create or update Batch node.
        '''
        try:
            attr = { ####
                "order": self.order,
                "type": self.type,
                "firstname": self.firstname,
                "surname": self.surname,
                "prefix": self.prefix,
                "suffix": self.suffix,
                "title": self.title
            }
            
            tx.run(CypherBame.####,
                   n_attr=n_attr, parent_id=kwargs['parent_id'], 
                   citation_handles=self.citation_handles)
        except ConnectionError as err:
            raise SystemExit("Stopped in Name.save: {}".format(err))
        except Exception as err:
            print("iError (Name.save): {0}".format(err), file=stderr)            


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

