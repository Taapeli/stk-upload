'''
Created on 6.5.2019

@author: jm
'''
from datetime import datetime
 
import shareds
from .cypher_audit import Cypher_stats
#from models.gen.batch_audit import Cypher_batch

class Audition(object):
    '''
    Methods for processing user batch and audition.
    
    Target example:
    user    batch                   "Family"    "Note"    "Person"
    ----    -----                   --------    ------    --------
    "usr1"  "usr1 2019-05-03.001"        94       224         153
    "usr1"  "usr1 2019-05-03.002"       736      3990        1949
    '''

    def __init__(self, user=None, is_audit=False):
        '''
        Decide, which user is included in reports (if limited)
        '''
        self.user = user
        self.is_audit = is_audit


#     def get_user_batch_stats(self): moved to models.gen.batch_audit.Batch
#     def get_batch_stats(batch_id):moved to models.gen.batch_audit.Batch

    @staticmethod
    def get_stats(auditor=None):
        ''' #Todo: Get statistics of all common data contents approved by current auditor.
        '''
        titles = []
        users = {}
        audit_id = None

        result = shareds.driver.session().run(Cypher_stats.get_my_auditions, 
                                              oper=auditor)
        for record in result:
            # <Record
            #    b=<Node id=439060 labels={'Audition'}
            #        properties={'auditor': 'juha', 'id': '2020-01-03.001', 
            #        'user': 'jpek', 'timestamp': 1578940247182}> 
            #    label='Note'
            #    cnt=17>
            print(str(record))
#TODO
            if not audit_id: #Todo: Väärin! batch?
                batch = record['batch']
                user = batch.get('user')
                #audit_id = batch.get('id')
                ts = batch.get('timestamp')
                if ts:
                    t = float(ts)/1000.
                    tstring = datetime.fromtimestamp(t).strftime("%-d.%-m.%Y %H:%M")
                else:
                    tstring = ""
            label = record.get('label', '')
            # Trick: Set Person as first in sort order!
            if label == "Person": label = " Person"
            cnt = record['cnt']
            titles.append((label,cnt))

#             key = f'{auditor}/{batch_id}/{tstring}'
#             if not key in users:
#                 users[key] = {}
#             users[key][label] = cnt

            #print(f'users[{key}] {users[key]}')

        return user, audit_id, tstring, sorted(titles)
