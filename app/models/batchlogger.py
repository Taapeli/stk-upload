'''
Cumulates Batch steps and stores them as a Log node

    After a series of logical run steps, Batch has a chain of step Logs
    and it has a link to each data node (Person, Event, ...) created.
    The UserProfile has also relation CURRENT_LOAD to most current Batch.

    (u:UserProfile) -[:CURRENT_LOAD]-> (b:Batch)
    (u:UserProfile) -[:HAS_LOADED]-> (b:Batch)
    (u:UserProfile) -[:HAS_LOADED]-> (b:Batch) -[:HAS_STEP*]-> (log:Log)
    (b:Batch) -[:IN_BATCH]-> (anydata_node)

Created on 26.5.2018

@author: jm
'''
from datetime import date
import shareds
from models.cypher_gramps import Cypher_batch


class Batch(object):
    '''
    Creates a log of userid bach steps.
    append()  Adds a log event to log
    save() Stores the log to database #TODO
    list() Gets the log contenst objects 
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
        self.totaltime = 0.0    # Sum of Log.elapsed


    def begin(self, tx, infile):
        '''
        Creates a new Batch node with 
        - id      a date followed by an ordinal number '2018-06-05.001'
        - status  'started'
        - file    input filename
        
        You may give an existing trasnaction tx, 
        else a new transaction is created and committed
        '''

        # 0. Create transaction, if not given
        local_tx = False
        with shareds.driver.session() as session:
            if tx == None:
                tx = session.begin_transaction()
                local_tx = True
            
            # 1. Find the latest Batch id of today from the db
            base = str(date.today())
            try:
                batch_id = tx.run(Cypher_batch.batch_find_id, 
                                  user=self.userid, batch_base=base).single().value()
                print("# Edellinen batch_id={}".format(batch_id))
                i = batch_id.rfind('.')
                ext = batch_id[i+1:]
            except AttributeError as e:
                # print ("Ei vanhaa arvoa {}".format(e))
                ext = 0
            except Exception as e:
                print ("Poikkeus {}".format(e))
                ext = 0
    
            # 2. Form a new batch id
            self.bid = "{}.{:03d}".format(base, int(ext) + 1)
            print("# Uusi batch_id='{}'".format(self.bid))
    
            # 3. Create a new Batch node
            b_attr = {
                'user': self.userid,
                'id': self.bid,
                'status': 'started',
                'file': infile
                }
            tx.run(Cypher_batch.batch_create, file=infile, b_attr=b_attr)
            if local_tx:
                tx.commit()

        return self.bid


    def complete(self, tx, status='completed'):
        #TODO: argumentteja puuttuu
        return tx.run(Cypher_batch.batch_complete, user=self.userid, bid=self.bid)


    def append(self, obj):
        '''
        The argument object (a Log) is added to batch Log list
        '''
        self.steps.append(obj)
        if isinstance(obj, Log) and not obj.elapsed == None:
            self.totaltime += obj.elapsed
            print("# " + str(obj))
            print('# BatchLogger totaltime={:.6f}'.format(obj.elapsed))

        ''' 
        Store the Log in the db to the end of Log node list
        
        (u:UserProfile {username:"Jussi"}) -[:HAS_LOADED]-> 
        (b:Batch {id:"2018-05-10.1"}) -[:HAS_STEP*]-> 
        (l0:Log) -[:HAS_STEP]-> (l1:Log {status: "1_notes", msg:"Notes", 
                                          size:86, elapsed:0.02})
        '''
        pass
        # Return the uniq_id of the created node
        return None

    def list(self):
        """ Gets the active Log steps as a list """
        return self.steps

    def str_list(self):
        """ Gets the active Log steps as a list of strings """
        li = []
        for e in self.steps:
            li.append(str(e))
        return li


class Log(object):
    '''
    Creates an object for storing batch event information:
        level    str    log level: INFO, WARNING, ERROR, FATAL
        title    str    logged text message
        count    int    count of processed things in this event
        elapsed  float  time elapsed in seconds
    '''

    def __init__(self, title='', count=None, elapsed=None, level='INFO'):
        '''
        Constructor
        '''
        self.level = level
        self.title = title
        self.count = count
        self.elapsed = elapsed


    def __str__(self):
        if self.count == None:
            c = ''
        else:
            c = self.count
        if self.elapsed:
            e = "{:.4f}".format(self.elapsed)
        else:
            e = ""
        return "{} {}: {}: {}".format(self.level, self.title, c, e)
