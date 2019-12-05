'''
Created on 5.12.2019

@author: jm
'''
import shareds


class Batch_merge(object):
    '''
    Methods to move a new Batch to Isotammi database
    '''
    ROOT_USER = "master"

    find_master_profile = '''
match (root:User {username:$root})
merge (root) -[:SUPPLEMENTED]-> (rp:UserProfile {username:$root})
on create set rp.timestamp = timestamp()
return rp'''

    find_batch = '''
match (u:User {username:$owner})
     -[:SUPPLEMENTED]-> (up:UserProfile)
     -[:HAS_LOADED]-> (b:Batch{id:$batch})
return u,up,b'''

    give_batch_to_root = '''
match (u:User {username:$user}) -[:SUPPLEMENTED]-> (up0:UserProfile)
    -[r0:HAS_LOADED]-> (b:Batch{id:$batch})
match (root:User {username:$root}) -[:SUPPLEMENTED]-> (up1:UserProfile)
optional match (up1) -[r1:HAS_LOADED]-> (b)
return up0, r0, b, r1, up1'''

    def __init__(self):
        '''
        Constructor; check existence of root UserProfile
        '''
        self.root_uniq_id = None    # Root user's id()

        count = None
        with shareds.driver.session() as session:
            result = session.run(self.find_master_profile, root=self.ROOT_USER)
            count = result.summary().counters.nodes_created
            record = result.single()
            self.root_uniq_id = record['rp'].id
            #print(record['rp'])
        if count:
            print(f'Created {count} UserProfile for Isotammi root')
    
    def move_whole_batch(self, batch_id, user):
        ''' A Batch supplemented by given user moved to root user.
        '''
        counters = None
        with shareds.driver.session() as session:
            result = session.run(self.give_batch_to_root, 
                                 user=user, batch=batch_id, root=self.ROOT_USER)
            counters = result.summary().counters
        print(counters)
