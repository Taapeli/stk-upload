'''
Created on 17.3.2020

@author: jm
'''

class DBreader:
    ''' Public methods for accessing active database.
    
        Returns a PersonResult object
    '''
    def __init__(self, dbdriver, my_context):
        ''' Create a reader object with db driver and user context.
        '''
        self.dbdriver = dbdriver
        self.user_context = my_context  
        self.username = my_context.user
    
    def person_list(self):
        ''' List person data including all data needed to Person page.
        
            Calls Neo4jDriver.person_list(user, fw_from, limit)
        '''
        context = self.user_context
        fw = context.next_name_fw()
        if context.context == context.ChoicesOfView.COMMON:
            use_user = context.user
        else:
            use_user=None
        persons = self.dbdriver.person_list(use_user, fw, context.count)

        # Update the page scope according to items really found 
        if persons:
            context.update_session_scope('person_scope', 
                                          persons[0].sortname, persons[-1].sortname, 
                                          context.count, len(persons))

        #Todo: remove this later
        if 'next_person' in context.session: # Remove an obsolete field
            context.session.pop('next_person')
            context.session.modified = True

        person_result = PersonResult(persons)
        #Todo:Calculate hidden persons
        #person_result.num_hidden = 0
        return person_result


class PersonResult:
    ''' Person's result object.
    '''
    def __init__(self, persons):
        self.error = 0  
        self.num_hidden = 0
        self.persons = persons  

