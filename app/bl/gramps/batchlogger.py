#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
#from datetime import date
import shareds
from pe.neo4j.cypher.cy_batch_audit import CypherRoot
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


#     def start_batch(self, tx, infile, mediapath): --> bl.batch.BatchDatastore.start_batch()
#         '''
#         Creates a new Batch node


#     def complete(self, tx=None):
#         ''' Mark this data batch completed '''
# #         # 0. Create transaction, if not given
# #         local_tx = False
# #         with shareds.driver.session() as session:
# #             if tx == None:
# #                 tx = session.begin_transaction()
# #                 local_tx = True
# 
#         try:
#             return tx.run(CypherRoot.batch_complete, user=self.userid, bid=self.bid)
#         
# #         if local_tx:
# #             tx.commit()


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
