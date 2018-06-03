'''
Cumulates BatchLog events and stores them as a Log node

    After a series of logical run steps, BatchLog has a chain of BatchEvents
    and it has a link to each data node (Person, Event, ...) created.
    The UserProfile has also relation type CURRENT_LOAD to most currnet Batch

    (u:UserProfile) -[:CURRENT_LOAD]-> (b:Batch)
    (u:UserProfile) -[:HAS_LOADED]-> (b:Batch)
    (u:UserProfile) -[:HAS_LOADED]-> (b:Batch) -[:COMPLETED*]-> (log:BatchEvent)
    (b:Batch) -[:IN_BATCH]-> (anydata_node)

Created on 26.5.2018

@author: jm
'''

class Batch():
    '''
    Represents the user's import (etc) batch
    - The Batch has relation chain to each batch step result node BatchEvent
    - The Batch has relations to each data node
    ''' 
    def __init__(self, username, status, file):
        '''
        Creates a new Batch node and connects it to UserProfile
        
        (u:UserProfile {username:"Jussi"}) -[:HAS_LOADED {status:'started'}]-> 
        (b:Batch {id:"2018-05-10.1", file:"/tmp/abo.xml"})
        '''
        self.bid = self._create_id()
        self.username = username
        self.status = status
        self.file = file
        # Creates the Batch node? #TODO
        return

    def _create_id(self):
        '''
        Returns a new Batch id, which is 
        - a date '2018-06-01' or
        - a date followed by an ordinal number '2018-06-01.01'
        '''
        # 1. Find the latest Batch id of today from the db
        pass
        # 2. Form a new batch id
        pass
        # Return the uniq_id of the created node
        return None


class BatchLog(object):
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
        self.events = []
        self.totaltime = 0.0    # Sum of BatchEvent.elapsed


    def add(self, obj):
        '''
        The argument object (a BatchEvent) is added to events list
        '''
        self.events.append(obj)
        if isinstance(obj, BatchEvent) and not obj.elapsed == None:
            self.totaltime += obj.elapsed
            print("# " + str(obj))
            print('# BatchLogger totaltime={:.6f}'.format(obj.elapsed))

        ''' 
        Store the BatchEvent in the db to the end of Log node list
        
        (u:UserProfile {username:"Jussi"}) -[:HAS_LOADED]-> 
        (b:Batch {id:"2018-05-10.1"}) -[:COMPLETED*]-> 
        (l0:Log) -[:COMPLETED]-> (l1:Log {status: "1_notes", msg:"Notes", 
                                          size:86, elapsed:0.02})
        '''
        pass
        # Return the uniq_id of the created node
        return None

    def list(self):
        """ Gets the active BatchEvents as a list """
        return self.events

    def str_list(self):
        """ Gets the active BatchEvents as a list of strings """
        li = []
        for e in self.events:
            li.append(str(e))
        return li


class BatchEvent(object):
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
        c = self.count      if self.count   else ""
        if self.elapsed:
            e = "{:.4f}".format(self.elapsed)
        else:
            e = ""
        return "{} {}: {}: {}".format(self.level, self.title, c, e)
