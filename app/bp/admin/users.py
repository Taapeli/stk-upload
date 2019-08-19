'''
Created on 6.5.2019

@author: jm
'''
from datetime import datetime
 
import shareds
from .models.cypher_adm import Cypher_stats

class Batches(object):
    '''
    Methods for collectiong user batch statistics.
    
    Target example:
    user    batch                   "Family"    "Note"    "Person"
    ----    -----                   --------    ------    --------
    "usr1"  "usr1 2019-05-03.001"        94       224         153
    "usr1"  "usr1 2019-05-03.002"       736      3990        1949
    '''

    def __init__(self, user=None):
        '''
        Decide, which users are included in reports
        '''
        self.user = user

    def get_user_batch_stats(self):
        ''' Get statistics of user Batch contents.
        
            u["usr1"].append({batch:"usr1 2019-05-03.001", "Family":94, "Note":224, "Person":153})
        '''
        labels = []
        users = {}
        result = shareds.driver.session().run(Cypher_stats.get_batches, user=self.user)
        for record in result:
            # <Record user='jpek' batch='jpek 2019-05-03.001' label='Person' cnt=1949>
            user = record['user']
            batch = record['batch']
            ts = record['timestamp']
            if ts:
                if isinstance(ts, int):
                    t = float(ts)/1000.
                tstring = datetime.fromtimestamp(t).strftime("%d.%m.%Y %H:%M")
            else:
                tstring = ""
            label = record['label']
            if not label: label = ""
            if label and not label in labels:
                labels.append(label)
            cnt = record['cnt']

            key = f'{user}/{batch}/{tstring}'
            if not key in users:
                users[key] = {}
            users[key][label] = cnt

            print(f'users[{key}] {users[key]}')

        return sorted(labels), users

