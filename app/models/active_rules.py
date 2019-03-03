'''

    Describe filtering rules for Scene pages:
    - active user, if any
    - next person (forward/backwards) in Person list

Created on 19.1.2019

@author: jm
'''

from enum import Enum
from flask_babelex import _


class OwnerFilter():
    """ Store filter values for finding the active subset of database

        Filters:
        - user          str  username from current_user, if any
        - owner_filter  int  code expressing filter method by data owners
        - next_person   list starting names for next Persons page []
    """

    # using Enum data structure in accordance with Two Scoops of Django 1.11 (ch. 6.4.8) 
    # and the following article
    # https://hackernoon.com/using-enum-as-model-field-choice-in-django-92d8b97aaa63

    class OwnerChoices(Enum):
        common = (1, _('Isotammi database'))    # Suomikanta
        own   =  (2, _('all my candidate data')) # kaikki ehdokasaineistoni
        batch =  (4, _('my candidate batch'))    # tuontierä
        common_own = (common + own, _('my own and Isotammi'))       # omat ja Suomikanta
        common_batch = (common+batch, _('my batch and Isotammi')) # tuontierä ja Suomikanta

        @classmethod
        def get_value(cls, member):
            return cls[member].value[0]

        @classmethod
        def get_str(cls, member):
            # Return given key, if it in in this enum, else 0
            return cls[member].value[1]

        @classmethod
        def get_key(cls, number):
            # Return the key, if number is in in this enum, else ''
            for name in cls._member_names_:
                if cls.get_value(name) == number:
                    return name
            return ''


    def __init__(self, user_session):
        '''
            User_session is used for storing the values set
        '''
        self.user_session = user_session
        self.user = None
        self.owner_filter = ''
        self.next_person = ['', '']

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
        # filter_div tells, which data shall be displayed:
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
                return self.owner_filter
        return 0

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

    def use_owner_filter(self):
        ''' Tells, if you should select object by data owner:
            Always if 'common' is not required
        '''
        return self.owner_filter != self.OwnerChoices.common 
    
    def use_common(self):
        ''' Tells, if you should select objects from common database 
        '''
        return self.owner_filter == self.OwnerChoices.common \
            or self.owner_filter == self.OwnerChoices.common_own \
            or self.owner_filter == self.OwnerChoices.common_batch



# ============================= NOT IN USE YET ================================

class ActiveRules():
    '''
    UserSession object carries user parameters transferred between different
    pages. 
    
    Parameters in self.session
        filter_div            which data shall be displayed, values
              001 1 = common Suomikanta data
              010 2 = user's own candidate data
              100 4 = data from an input batch
              011 3 = 1+2 = users data & Suomikanta
              101 5 = 1+4 = user batch & Suomikanta
        next_person = [backwards, forwards]  
                            the names from which next listing page starts
        is_member = 1, if logged in with a role of member, admin or reserach

    Methods
        __init__(session)      load parameter values from session object
        reset_persons()        set default values for next_person
        setFilter(request)     update parameters from request arguments
        testFilter(key)        check if given property is set
        strFilter()            selected filter as clear text
        
    '''
    FILTER_PUBLIC = 1
    FILTER_OWN = 2
    FILTER_BATCH = 4
    FILTER_STR = {FILTER_PUBLIC:                'Suomikanta', 
                  FILTER_OWN:                   'omat aineistoni', 
                  FILTER_BATCH:                 'tuontierä',
                  FILTER_PUBLIC + FILTER_OWN:   'omat ja Suomikanta', 
                  FILTER_PUBLIC + FILTER_BATCH: 'tuontierä ja Suomikanta'}

    def __init__(self, session, roles=[]):
        '''
        Constructor using session parameters and a list of Role objects
        '''
        self.next_person = [session.get('next_person_fw', ''), 
                            session.get('next_person_bw', '')]
        next.filter_div = session.get('filter_div', '')
        
        self.is_member = False
        for role in roles:
            if hasattr(role, 'name') and role.name in ['member', 'admin', 'reserach']:
                self.is_member = True
        session['is_member'] = self.is_member

        self.session = session

    def reset_persons(self):
        '''
        Forget next_person
        '''
        self.next_person = []
        self.session['next_person'] = []

    def setFilter(self, request):
        """ The given url parameters div=2&cmp=1 are stored as session variable 
            filter_div
        """
        # filter_div tells, which data shall be displayed:
        #   001 1 = common Suomikanta data
        #   010 2 = user's own candidate data
        #   100 4 = data from specific input batch
        #   011 3 = 1+2 = users data & Suomikanta
        #   101 5 = 1+4 = user batch & Suomikanta
    
        div = int(request.args.get('div', 0))
        if div:
            if request.args.get('cmp', ''):
                div = div | 1 
            self.session['filter_div'] = int(div)
            print("Now filter div {}".format(div))

#     @staticmethod
    def is_only_my_data(self):
        " Returns True, if return set is restrected to items of owner's Batch"
        if 'filter_div' in self.session and not self.session['filter_div'] & 1:
            return True
        else:
            return False
