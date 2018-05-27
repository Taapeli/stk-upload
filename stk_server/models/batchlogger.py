'''
Cumulates BatchLog events and stores them as a Log node

Created on 26.5.2018

@author: jm
'''

class BatchLog(object):
    '''
    Creates a log of user bach steps.
    add()  Adds a log event to log
    save() Stores the log to database
    list() Gets the log contenst objects 
    '''

    def __init__(self, params=None):
        '''
        Creates a log of user bach steps.
        If params is present, fills the events from the db
        '''
        self.events = []
        self.totaltime = 0.0    # Sum of BatchEvent.elapsed


    def add(self, obj):
        ''' The argument object (a BatchEvent) is added to events list
        '''
        self.events.append(obj)
        if isinstance(obj, BatchEvent) and not obj.elapsed == None:
            self.totaltime += obj.elapsed
            print("# " + str(obj))
            print('# BatchLogger totaltime={:.6f}'.format(obj.elapsed))

    def save(self):
        """ Stores the BatchEvents in the db as a list of Log nodes """
        pass


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
        title    str    log text message
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
