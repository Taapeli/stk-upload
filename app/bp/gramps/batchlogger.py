'''
Cumulates Batch steps and stores them as a LogItem node

    After a series of logical run steps, Batch has a link to each data node with
    label Person or Family.
    The UserProfile has also relation CURRENT_LOAD to most current Batch.

    (u:UserProfile) -[:CURRENT_LOAD]-> (b:Batch)
    (u:UserProfile) -[:HAS_LOADED]-> (b:Batch)
    (b:Batch) -[:BATCH_MEMBER]-> (:Person|Family)

Created on 26.5.2018

@author: jm
'''
from datetime import date
import shareds
from pe.neo4j.cypher.batch_audit import CypherBatch
#from models.cypher_gramps import Cypher_batch
#from models import dbutil


class BatchLog():
    '''
    Creates a log of userid bach steps.

    append()  Adds a log event to log
    list()    Gets the log contenst objects 
    '''

    def __init__(self, userid):
        '''
        Creates a Batch object
        '''
        if userid == None:
            raise AttributeError("Batch.userid must be defined")
        self.bid = None
        self.userid = userid
        self.status = 'started'
        self.file = None
            
        # Runtime variables for batch steps
        self.steps = []
        self.totaltime = 0.0    # Sum of LogItem.elapsed
        self.totalpercent = 0   # Sum of LogItem.percent


#     def start_batch(self, tx, infile, mediapath): --> bl.batch_audit.Batch.start_batch()
#         '''
#         Creates a new Batch node with 
#         - id        a date followed by an ordinal number '2018-06-05.001'
#         - status    'started'
#         - file      input filename
#         - mediapath media files location
#         
#         You may give an existing transaction tx, 
#         otherwise a new transaction is created and committed
#         '''
# 
#         # 0. Create transaction, if not given
#         local_tx = False
#         with shareds.driver.session() as session:
#             if tx == None:
#                 tx = session.begin_transaction()
#                 local_tx = True
#             
#             dbutil.aqcuire_lock(tx, 'batch_id') #####
# 
#             # 1. Find the latest Batch id of today from the db
#             base = str(date.today())
#             try:
#                 result = tx.run(Cypher_batch.batch_find_id, batch_base=base)
#                 batch_id = result.single().value()
#                 print("# Pervious batch_id={}".format(batch_id))
#                 i = batch_id.rfind('.')
#                 ext = int(batch_id[i+1:])
#             except AttributeError as e:
#                 # Normal exception: this is the first batch of day
#                 #print ("Ei vanhaa arvoa {}".format(e))
#                 ext = 0
#             except Exception as e:
#                 print ("Poikkeus {}".format(e))
#                 ext = 0
#     
#             # 2. Form a new batch id
#             self.bid = "{}.{:03d}".format(base, ext + 1)
#             print("# New batch_id='{}'".format(self.bid))
#     
#             # 3. Create a new Batch node
#             b_attr = {
#                 'user': self.userid,
#                 'id': self.bid,
#                 'status': 'started',
#                 'file': infile,
#                 'mediapath': mediapath
#                 }
#             tx.run(Cypher_batch.batch_create, file=infile, b_attr=b_attr)
#             if local_tx:
#                 tx.commit()
# 
#         return self.bid


    def complete(self, tx=None):
        ''' Mark this data batch completed '''
        # 0. Create transaction, if not given
        local_tx = False
        with shareds.driver.session() as session:
            if tx == None:
                tx = session.begin_transaction()
                local_tx = True
            
        return tx.run(CypherBatch.batch_complete, user=self.userid, bid=self.bid)
        if local_tx:
            tx.commit()


    def log_event(self, event_dict):
        # Add a and event dictionary as a new LogItem to Batch log
        batch_event = LogItem(event_dict)
        self.log(batch_event)

    def log(self, batch_event):
        # Add a bp.gramps.batchlogger.LogItem to Batch log
        self.append(batch_event)


    def append(self, obj):
        '''
        The argument object (a LogItem) is added to batch LogItem list
        '''
        if not isinstance(obj, LogItem):
            raise AttributeError("Batch.append need a LogItem instance")

        self.steps.append(obj)
        if isinstance(obj, LogItem) and isinstance(obj.elapsed, float):
            self.totaltime += obj.elapsed
            print("# " + str(obj))
            #print('# BatchLogger totaltime={:.6f}'.format(obj.elapsed))
        return None

    def list(self):
        """ Gets the active LogItem steps as a list """
        return self.steps

    def str_list(self):
        """ Gets the active LogItem steps as a list of strings """
        li = []
        for e in self.steps:
            li.append(str(e))
        return li


class LogItem():
    '''
    Creates an object for storing batch event information:
        level    str    log level: INFO, WARNING, ERROR, FATAL
        title    str    logged text message
        count    int    count of processed things in this event
        elapsed  float  time elapsed in seconds
        percent  int    process progress grade 1..100
    '''

    def __init__(self, ev):
        '''
        Constructor
        '''
        self.level = ev['level']        if 'level' in ev    else 'INFO'
        self.title = ev['title']        if 'title' in ev    else ''
        self.count = ev['count']        if 'count' in ev    else None
        self.elapsed = ev['elapsed']    if 'elapsed' in ev  else None
        self.percent = ev['percent']    if 'percent' in ev  else None

    def __str__(self):
        if self.count == None:
            c = ''
        else:
            c = self.count
        if self.elapsed:
            e = "{:.4f}".format(self.elapsed)
            return f"{self.level} {self.title}: {c} / {e} sek"
        return f"{self.level} {self.title}: {c}"
