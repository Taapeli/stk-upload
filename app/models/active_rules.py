'''

    Describe filtering rules for Scene pages:
    - active user, if any
    - next person (forward/backwards) in Person list

Created on 19.1.2019

@author: jm
'''

#from enum import Enum
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

        #TODO: Oletusarvot anonyymin käyttäjän aloittaessa
        #TODO: Milloin nollataan kukin arvo
        #TODO: Yhdistä kaikki asetukset set_filters_from(session, current_user)
    """

    # using Enum data structure in accordance with Two Scoops of Django 1.11 (ch. 6.4.8) 
    # and the following article
    # https://hackernoon.com/using-enum-as-model-field-choice-in-django-92d8b97aaa63

    class OwnerChoices():
        """
        """
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
            # Return the key, if valid number, else 0
            for i in cls.as_str.keys():
                if i == number:
                    return i
            return 0
        
    def __init__(self, user_session):
        '''
            User_session is used for storing the values set
        '''
        self.user_session = user_session
        if 'username' in user_session.__dict__:
            self.user = user_session.username 
        else:
            self.user = None
        self.owner_filter = self.OwnerChoices.COMMON
        self.next_person = ['', '']

    def owner_str(self):
        # Return current owner choise as text 
        try:
            return self.OwnerChoices.as_str[self.owner_filter]
        except:
            return ''

    def store_user(self, current_user=None):
        ''' Set active user, if any username '''
        if current_user and hasattr(current_user, 'is_authenticated') \
                        and current_user.is_authenticated:
            self.user = current_user.username
        else:
            self.user = None

    def store_owner_filter(self, request):
        """ The parameters div=2&cmp=1 are stored as session variable owner_filter.
            Returns owner filter name id detected, otherwise False
        """
        # owner_filter tells, which data shall be displayed:
        #   common       001 1 = common Suomikanta data
        #   own          010 2 = user's own candidate data
        #   batch        100 4 = data from specific input batch
        #   common_own   011 3 = 1+2 = users data & Suomikanta
        #   common_batch 101 5 = 1+4 = user batch & Suomikanta
    
        div = int(request.args.get('div', 0))
        if div:
            if request.args.get('cmp', ''):
                div = div | 1
            self.owner_filter = self.OwnerChoices.get_key(div)
            if self.owner_filter:
                self.user_session.owner_filter = self.owner_filter
                print("OwnerFilter: Now owner_filter={}".format(self.owner_filter))
                #return self.owner_filter
        else:
            # If no div variable, clear next and reset owner_filter ??
            self.owner_filter = self.OwnerChoices.COMMON
            if not self.user_session.owner_filter:
                self.user_session.owner_filter = self.OwnerChoices.COMMON
        #return 0

    def store_next_person(self, request):
        """ Eventuel fb or bw parameters are stored in session['next_person'].
            If neither is given, next_person is cleared.
        """
        self.next_person = [' ', ' ']
        if request:
            fw = request.args.get('fw', None)
            bw = request.args.get('bw', None)
            if fw == None and bw == None:
                # Do not change next_person
                return self.user_session.get('next_person', self.next_person)

            if fw == None and 'next_person' in self.user_session:
                self.next_person = self.user_session.get('next_person')
            else:
                if fw != None:
                    fw = fw.title()
                    self.next_person[1] = fw
            if bw != None:
                self.next_person[0] = bw
            self.user_session.next_person = self.next_person
            print("OwnerFilter: Now next_person={}".format(self.next_person))
        else:
            # No request
            self.user_session.next_person = self.next_person
            print("OwnerFilter: Now next_person is cleared")
        return self.next_person

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
