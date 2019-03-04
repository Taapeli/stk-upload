'''

    Describe filtering rules for Scene pages:
    - active user, if any
    - next person (forward/backwards) in Person list

Created on 19.1.2019

@author: jm
'''

from flask_babelex import _


class OwnerFilter():
    """ Store filter values for finding the active subset of database

        Filters:
        - user          str  Username from current_user, if any
        - owner_filter  int  Code expressing filter method by data owners
                             from request.div or session.owner_filter.
                             Default = 1 (common) if neither present
        - next_person   list Starting names for prev/next Persons page
                             values [backward, forward] sortnames
                             from request.fw, equest.bw variables.
                             default ['', '']
    """

    class OwnerChoices():
        """ Represents all possible values of owner selection code. """
        COMMON = 1
        OWN = 2
        BATCH = 4
        as_str = {
            COMMON:         _('Isotammi database'), 
            OWN:            _('all my candidate data'), 
            BATCH:          _('my candidate batch'),
            COMMON + OWN:   _('my own and Isotammi'), 
            COMMON + BATCH: _('my batch and Isotammi')
        }

        @classmethod
        def get_key(cls, number):
            # Return the key, if valid number, otherwise 0
            if number in list(cls.as_str.keys()):
                    return number
            return 0
        
    def __init__(self, user_session, current_user=None, request=None):
        '''
            User_session knows the values from session and request.
        '''
        self.user_session = user_session
        self.owner_filter = self.OwnerChoices.COMMON

        ''' Set active user, if any username '''
        if current_user:
            if current_user.is_active and current_user.is_authenticated:
                self.user = current_user.username
            else:
                self.user = None
        else:
            self.user = user_session.get('username', None)

        #def store_owner_filter(self):
        """ The parameters div=2&cmp=1 are stored as session variable owner_filter.
            Returns owner filter name id detected, otherwise False
        """
        div = 0
        if request:
            ''' The div argument from request is stored in self.owner_filter
            '''
            div = int(request.args.get('div', 0))
            if div:
                # div tells, which data shall be displayed:
                #   common       001 1 = common Suomikanta data
                #   own          010 2 = user's own candidate data
                #   batch        100 4 = data from specific input batch
                #   common_own   011 3 = 1+2 = users data & Suomikanta
                #   common_batch 101 5 = 1+4 = user batch & Suomikanta
                if request.args.get('cmp', ''):
                    div = div | 1
                self.owner_filter = self.OwnerChoices.get_key(div)
                if self.owner_filter:
                    self.user_session['owner_filter'] = self.owner_filter
                    print("OwnerFilter: Now owner_filter={}".format(self.owner_filter))
        if div == 0:
            # If got no request owner_filter, use session value or 1
            self.owner_filter = user_session.get('owner_filter', self.OwnerChoices.COMMON)
            print("OwnerFilter: Uses default owner_filter={}".format(self.owner_filter))


    def store_next_person(self, request):
        """ Eventuel fb or bw parameters are stored in user_session['next_person'].
            If neither is given, next_person is cleared.
        """
        self.next_person = ['', '']
        session_next = self.user_session.get('next_person', self.next_person)

        if request:
            fw = request.args.get('fw', None)
            bw = request.args.get('bw', None)
            if fw == None and bw == None:
                # Do not change next_person
                self.next_person = session_next
                return 

            if fw != None:
                self.next_person[1] = fw
            else:
                self.next_person[1] = session_next[1]
            if bw != None:
                self.next_person[0] = bw
            else:
                self.next_person[0] = session_next[0]

            self.user_session['next_person'] = self.next_person
            print("OwnerFilter: Now next_person={}".format(self.next_person))
        else:
            # No request
            self.user_session['next_person'] = self.next_person
            print("OwnerFilter: Now next_person is cleared")
        #return self.next_person


    def owner_str(self):
        # Return current owner choise as text 
        try:
            return self.OwnerChoices.as_str[self.owner_filter]
        except:
            return ''

# owner_filter tells which data shall be displayed:
#   common       001 1 = common Suomikanta data
#   own          010 2 = user's own candidate data
#   batch        100 4 = data from specific input batch
#   common_own   011 3 = 1+2 = users data & Suomikanta
#   common_batch 101 5 = 1+4 = user batch & Suomikanta

    def use_owner_filter(self):
        ''' Tells, if you should select object by data owner:
            Always if 'common' is not required
        '''
        return not (self.owner_filter & 1) 
    
    def use_common(self):
        ''' Tells, if you should select objects from common database 
        '''
        return (self.owner_filter & 1) != 0
