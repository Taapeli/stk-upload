'''
Created on 27.11.2021

@author: jm
'''

class IsotammiId(object):
    '''
    Methods to generate new isotammi_id values.
    '''


    def __init__(self, db_session, obj_name: str, count: int = 1):
        '''
        Define an id generator for objects named obj_name.
        '''
        first_id = "Todo"
        return first_id

    def next_id(self):
        ''' Gives next isotammi_id value from reserved pool.
            Returns None, if pool is empty.
            - Or fethes next key from db?
        '''
        return "TODO isotammi_id value"
