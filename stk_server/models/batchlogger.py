'''
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


    def add(self, obj):
        ''' The argument object (a BatchEvent) is added to events list
        '''
        self.events.append(obj)


    def save(self):
        """ Stores the BatchEvents in the db as a list of Log nodes """
        pass


    def list(self):
        """ Gets the active BatchEvents as a list """
        return self.events


class BatchEvent(object):
    '''
    Creates an object for storing batch event information:
        level    str    log level: INFO, WARNING, ERROR, FATAL
        title    str    log text message
        count    int    count of processed things in this event
        elapsed  float  time elapsed in seconds
    '''

    def __init__(self, level='INFO', title='', count=None, elapsed=None):
        '''
        Constructor
        '''
        self.level = level
        self.title = title
        self.count = count
        self.elapsed = elapsed
