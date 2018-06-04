'''
Cumulates Batch steps and stores them as a Log node

    After a series of logical run steps, Batch has a chain of step Logs
    and it has a link to each data node (Person, Event, ...) created.
    The UserProfile has also relation type CURRENT_LOAD to most currnet Batch

    (u:UserProfile) -[:CURRENT_LOAD]-> (b:Batch)
    (u:UserProfile) -[:HAS_LOADED]-> (b:Batch)
    (u:UserProfile) -[:HAS_LOADED]-> (b:Batch) -[:HAS_STEP*]-> (log:Log)
    (b:Batch) -[:IN_BATCH]-> (anydata_node)

Created on 26.5.2018

@author: jm
'''

# class Batch():
#     '''
#     Represents the user's import (etc) batch
#     - The Batch has relation chain to each batch step result node Log
#     - The Batch has relations to each data node
#     ''' 
#     def __init__(self, username, status, file):
#         '''
#         Creates a new Batch node and connects it to UserProfile
#         
#         (u:UserProfile {username:"Jussi"}) -[:HAS_LOADED {status:'started'}]-> 
#         (b:Batch {id:"2018-05-10.1", file:"/tmp/abo.xml"})
#         '''
#         self.bid = self._create_id()
#         self.username = username
#         self.status = status
#         self.file = file
#         # Creates the Batch node? #TODO
#         return
# 
#     def _create_id(self):
#         '''
#         Returns a new Batch id, which is 
#         - a date '2018-06-01' or
#         - a date followed by an ordinal number '2018-06-01.01'
#         '''
#         # 1. Find the latest Batch id of today from the db
#         pass
#         # 2. Form a new batch id
#         pass
#         # Return the uniq_id of the created node
#         return None


class Batch(object):
    '''
    Creates a log of user bach steps.
    add()  Adds a log event to log
    save() Stores the log to database #TODO
    list() Gets the log contenst objects 
    '''

    def __init__(self, params=None):
        '''
        Creates a log of a batch step
        
        #TODO The params may be: ...?
        
        '''
        self.steps = []
        self.totaltime = 0.0    # Sum of Log.elapsed


    def add(self, obj):
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
