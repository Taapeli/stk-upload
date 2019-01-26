'''
Created on 19.1.2019

@author: jm
'''
from setups import Role

class UserFilter():
    as_text = {1:'Suomikanta', 2:'kaikki ehdokasaineistoni', 4:'tuontierä',
               3:'omat ja Suomkanta', 5:'tuotierä ja Suomikanta'}

    def __init__(self, user_session):
        '''
            User_session is used for storing given values
        '''
        self. user_session = user_session

    def store_div(self, request):
        "The parameters div=2&cmp=1 are stored as session variable filter_div"
        # filter_div tells, which data shall be displayed:
        #   001 1 = public Suomikanta data
        #   010 2 = user's own candidate data
        #   100 4 = data from specific input batch
        #   011 3 = 1+2 = users data & Suomikanta
        #   101 5 = 1+4 = user batch & Suomikanta
    
        div = int(request.args.get('div', 0))
        if div:
            if request.args.get('cmp', ''):
                div = div | 1 
            self.user_session['filter_div'] = int(div)
            print("Now filter_div={}".format(div))
            return div
        return None

    def store_next_person(self, request):
        """ Eventuel fb or bw parameters are stored in session['next_person'].
            If neither is given, next_person is cleared.
        """
        next_person = [' ', ' ']
        if request:
            fw = request.args.get('fw', None)
            bw = request.args.get('bw', None)
            if fw == None and bw == None:
                # Do not change next_person
                return self.user_session.get('next_person', [' ', ' '])

            if fw == None and 'next_person' in self.user_session:
                next_person = self.user_session.get('next_person')
            else:
                if fw != None:
                    fw = fw.title()
                    next_person[1] = fw
            if bw != None:
                next_person[0] = bw
            self.user_session['next_person'] = next_person
            print("Now next_person={}".format(next_person))
        else:
            next_person = [' ', ' ']
            self.user_session['next_person'] = next_person
            print("Now next_person is cleared")
        return next_person

# NOT IN USE YET:

class ActiveRules():
    '''
    UserSession object carries user parameters transferred between different
    pages. 
    
    Parameters in self.session
        filter_div            which data shall be displayed, values
              001 1 = public Suomikanta data
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
                  FILTER_PUBLIC + FILTER_BATCH: 'tuotierä ja Suomikanta'}

    def __init__(self, session, roles=[]):
        '''
        Constructor using session parameters and a list of Role objects
        '''
        self.next_person = [session.get('next_person_fw', ''), 
                            session.get('next_person_bw', '')]
        next.filter_div = session.get('filter_div', '')
        
        self.is_member = False
        for role in roles:
            if isinstance(role, Role) and role.name in ['member', 'admin', 'reserach']:
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
        #   001 1 = public Suomikanta data
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

    def is_only_mine_data(self):
        " Returns True, if return set is restrected to items of owner's Batch"
        if 'filter_div' in self.session and not self.session['filter_div'] & 1:
            return True
        else:
            return False
