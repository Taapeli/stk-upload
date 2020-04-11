'''
    Describes filtering rules for Scene pages.

    - active user, if any
    - next person (forward/backwards) in Person list
    - next in other lists (ToDo)

Created on 19.1.2019

@author: jm
'''

from urllib.parse import unquote_plus
from flask_babelex import lazy_gettext as N_


class UserContext():
    """ Store filter values for finding the active subset of database.
    
        Usage:
            #    Create context with defaults from session and request (1)
            u_context = UserContext(user_session, current_user, request)

            #    Set the scope of data keys using request arguments or previous defalts (2)
            u_context.set_scope_from_request(request, 'person_scope')
            
            #    Set other variables: how many objects shall be shown
            u_context.count = int(request.args.get('c', 100))
            #        Privacy limit: how many years from (calculated) death year
            u_context.privacy_limit = shareds.PRIVACY_LIMIT

            #    < Execute data search here >

            #    Update data scope for next search
            context.update_session_scope('person_scope', 
                                          persons[0].sortname, persons[-1].sortname, 
                                          context.count, len(persons))

        Settings stored in self:

        (1) user context: username and which material to display
        - user          str     Username from current_user, if any
        - user_context  int     Code expressing filter method by data owners
                                from request.div+div2 or session.user_context.
                                Default = 1 (common) if neither present

            COMMON - 1          approved common data 'Isotammi'
            OWN - 2             all user's own candidate materials
            BATCH - 3           a selected Batch set
            COMMON+OWN
            COMMON+BATCH

        (2) sort key limits displayed in current page
        - scope          list   Boundary names for current display page [from, to]

                                For Persons page, the scope variable in
                                user session is 'person_scope' and the values 
                                are from Person.sortname field.

            - Displayed scope is from scope[0] to scope[1]
            - With forward button, show from scope[1] towards end
            - With backward button, show from scope[0] towards top
            
            - Current page includes the bounding names from scope
            - The same boundary names are included in next pages, too
              to ensure no duplicate names are skipped.

            scope[0] (from which name to display, forwards):
                ' '              from first name of data
                name             from a name given
                NEXT_END '>'     bottom reached: there is nothing forwards
            scope[1] (from which name to display, backwards):
                NEXT_END '>'     from last name of data
                name             from a name given
                NEXT_START '<'   top reached: there is nothing before

    #TODO self.batch_id not set or used
    """
    NEXT_START = '<'  # from first name of data
    NEXT_END = '>'    # end reached: there is nothing forwards


    class ChoicesOfView():
        """ Represents all possible combibations of selection by owner and batch. 
        """
        COMMON = 1
        OWN = 2
        BATCH = 4   # Currently not implemented

        def __init__(self):
            ''' Initialise choise texts in user language '''
            self.as_str = {
                self.COMMON:              N_('Approved common data'), 
                self.OWN:                 N_('My candidate data'), 
                self.BATCH:               N_('My selected candidate batch'),
                self.COMMON + self.OWN:   N_('My own and approved common data'), 
                self.COMMON + self.BATCH: N_('My selected batch and approved common data')
            }
            self.batch_name = None

        def get_valid_key(self, number):
            # Return the key, if valid number, otherwise 0
            if number in list(self.as_str.keys()):
                return number
            return 0

    class NextStartPoint():
        ''' For multi page object display, define next keys forwards/backwards.
        '''

        def __init__(self, session, session_var):
            ''' Initialize session and scope. 
            
                - session_var    str    session variable name
                - request        http request
            
                Use request arguments fw or bw, if defined.
                Else use orifinal from session.
            '''
            self.session = session
            self.session_var = session_var
            self.scope = session.get(session_var, ['', '>'])
    
    
        def set_next_from_request(self, request=None):
            ''' Calculate scope values from request or session. 
            
                - session_var    str    session variable name
                - request        http request
            
                Use request arguments fw or bw, if defined.
                Else use orifinal from session.
            '''
            if request:
                fw = request.args.get('fw', None)
                bw = request.args.get('bw', None)
                if fw == None and bw == None:
                    # Use original session_scope as is
                    return self.scope
    
                if fw != None:
                    # Direction forward from fw parameter
                    return [unquote_plus(fw), None]
                else: # bw != None:
                    # Direction backwards from bw parameter
                    return [None, unquote_plus(bw)]
            else:
                # No request
                self.session[self.session_var] = self.scope
                print(f"UserContext: Now {self.session_var} is cleared")
                return self.scope
            
    
    def __init__(self, user_session, current_user=None, request=None):
        '''
            Set filtering properties from user session, request and current user.
        '''
        self.session = user_session
        self.choices = self.ChoicesOfView()   # set of allowed material choices
        self.context = self.ChoicesOfView.COMMON
        self.years = []                         # example [1800, 1899]
        self.series = None                      # Source data theme like "birth"
        self.count = 10000                      # Max count ow objects to display
        self.lang = user_session.get('lang','') # User language

        ''' Set active user, if any username '''
        if current_user:
            if current_user.is_active and current_user.is_authenticated:
                self.user = current_user.username
            else:
                self.user = None
        else:
            self.user = user_session.get('username', None)

        """ Store the request parameters div=1&div2=2&cmp=1 as session variable user_context.
            Returns owner context name if detected, otherwise False
        """
        new_selection = 0
        if request:
            # Selected years (from-to)
            #    years=1111-2222
            years = request.args.get('years', None)
            if years:
                y1, y2 = years.split('-')
                if y1:  yi1 = int(y1)
                else:   yi1 = 0
                if y2:  yi2 = int(y2)
                else:   yi2 = 9999
                self.years = [yi1, yi2]     # selected years [from, to]
                print(f'UserContext: Objects between years {self.years}')

            # Selected document series for Sources
            self.series = request.args.get('series', None)

            # Selected material for display
            #    div=1 -> show approved material
            #    div2=2 -> show researcher's own data
            new_selection = int(request.args.get('div', 0)) + int(request.args.get('div2', 0))
            if new_selection:
                # Take also common data?
                if request.args.get('cmp', ''): 
                    new_selection = new_selection | 1
                # Got new material selection?
                self.context = self.choices.get_valid_key(new_selection)
                if self.context:
                    self.session['user_context'] = self.context
                    print(f"UserContext: Now user_context={self.context}")
            # Clear obslete session variable
            user_session.pop('owner_filter', None)

        if new_selection == 0:
            # If got no request user_context, use session value or 1
            self.context = user_session.get('user_context', self.choices.COMMON)
            print(f"UserContext: Uses same or default user_context={self.context}")


    def get_my_user_id(self):
        # Return current user id, if my candidate data is chosen
        if self.context == self.choices.OWN:
            return self.user
        else:
            return ''

    def owner_str(self):
        # Return current owner choise as text 
        try:
            return self.choices.as_str[self.context]
        except:
            return ''

    def use_owner_filter(self):
        ''' Tells, if you should select object by data owner.

            Always when others but self.ChoicesOfView.OWN only are required
        '''
        
        return (self.context & 2) > 0
    
    def use_common(self):
        ''' Tells, if you should select objects from common database.

            Always when self.ChoicesOfView.COMMON is required
        '''
        return (self.context & 1) > 0


    def set_scope_from_request(self, request, var_name):
        """ Eventuel request fw or bw parameters are stored in session['person_scope'].

            - If fw is defined, clear bw; otherwise clear bw
            - If neither is given, person_scope is cleared
        """
        self.nextpoint = self.NextStartPoint(self.session, var_name)
        self.scope = self.nextpoint.set_next_from_request(request)
        print(f"UserContext: Now {var_name} next item={self.scope}")


    def update_session_scope(self, var_name, name1, name2, limit, rec_cnt):
        """ Update the session scope according to items really found.
        
            var_name    str    field name in self.session
            name1       str    the first item name got from database
            name2       str    the last item name
            limit       int    number of items requested
            rec_cnt     int    records actually recieved
        """
        print(f"update_session_scope: Got {rec_cnt} items {name1!r} – {name2!r}, "
              f"{rec_cnt}/{limit} records")
        scope0 = self.scope
        if rec_cnt == limit: # Got required amount of items
            self.scope[1] = name2
        else:
            self.scope[1] = '> end' # End reached
        if self.scope[0] > ' ':
            self.scope[0] = name1
        if scope0 != self.scope:
            print(f"update_session_scope: New {var_name} scope {self.scope[0]!r} – {self.scope[1]!r}")

        self.session[var_name] = self.scope
        print(f"--> {repr(self.session)}")


    def next_name_fw(self):
        ''' Tells the name from which the names must be read from.

            scope[0] (from which name to display, forwards):
                ' '              from first name of data
                name             from a name given
                NEXT_END '>'     bottom reached: there is nothing forwards
        '''
        if self.scope[0] == self.NEXT_END:
            # Generic end mark
            return '> end'
        else:
            return self.scope[0]
        
