#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
    Describes filtering rules for Scene pages.

    - active user, if any
    - next person (forward/backwards) in Person list etc

Created on 19.1.2019

@author: jm
'''

from urllib.parse import unquote_plus
from flask_babelex import lazy_gettext as N_
from flask_babelex import _
from bl.root import State, DEFAULT_MATERIAL

class UserContext():
    """ Store filter values for finding the required subset of database.
    
        Usage examples:
            #    Create context with defaults from session and request (1)
            u_context = UserContext(user_session, current_user, request)

            #    Set the scope of data keys using request arguments or previous defalts (2)
            u_context.set_scope_from_request(request, 'person_scope')
            
            #    Set other variables: how many objects shall be shown
            u_context.count = int(request.args.get('c', 100))
            #        Privacy limit: how many years from (calculated) death year
            u_context.privacy_limit = shareds.PRIVACY_LIMIT

            #    < Execute data search here using u_context >

            #    Update data scope for next search
            context.update_session_scope('person_scope', 
                                          persons[0].sortname, persons[-1].sortname, 
                                          context.count, len(persons))

        Useful methods:
            batch_user()                Get effective user id or None
            owner_str()                 Get owner description in current language
            use_owner_filter()          True, if data is filtered by owner id
            use_common()                True, if using common data
            privacy_ok(obj)             returns True, if there is no privacy reason
                                        to hide given object
            set_scope_from_request()    update session scope by request params
            update_session_scope()      update session scope by actually found items
            next_name('fw')             set next object forwards / backwards

        Settings stored in self:

        (1) user context: username and which material to display
        - user          str     Username from current_user, if any
        - user_context  int     Code expressing filter method by data owners
                                from request.div or session.user_context.
                                Default = 1 (common) if neither present

            COMMON - 1          approved common data 'Isotammi'
            OWN - 2             all user's own candidate materials
            BATCH - 3           a selected Batch set
            COMMON+OWN *
            COMMON+BATCH *
            *) NOTE. Not implemented!

        (2) sort keys displayed in the current page
        - first, last          str   Boundary names for current display page [from, to]

                                For Persons page, the scope variable in
                                user session is 'person_scope' and the values 
                                are from Person.sortname field.

            1. For display, the scope tells the names found: [first, last]
            2a. With forward button, show next from last towards bottom of list
            2b. With backward button, show next from first towards top

            - Current page includes the bounding names first,last
            - The limiting boundary name is also included in next page to ensure
              no duplicate names are skipped.

        Scope examples:
            1. starting scope in session     ['y','z']
            2. accessed next fw                  ['z', 'ö']  set first = old last
            2b or accessed next bw      ['x', 'y']           set last = old first

            first (from which name to display, forwards):
                ' '              from first name of data
                name             forwards from the name given
                NEXT_END '>'     top reached: there is nothing forwards
            last (from which name to display, backwards):
                NEXT_END '>'     from last name of data
                name             backwards from the name given
                NEXT_START '<'   bottom reached: there is nothing before
    """
    NEXT_START = '<'  # from first name of data
    NEXT_END = '>'    # end reached: there is nothing forwards


    class ChoicesOfView():
        """ Represents all possible combinations of selection by owner and batch. 

        #TODO Define new context_code values including audit states and approved data
        """
        COMMON = 1  # Approved data
        OWN = 2     # Candidate data
        BATCH = 4   # Selected candicate batch
        CODE_VALUES = ['', 'apr', 'can', 'apr,can', 'bat', 'can,bat']

        def __init__(self):
            ''' Initialise choise texts in user language '''
            self.as_str = {
                self.COMMON:              N_('Approved common data'), #TODO: --> "Audit requested"
                self.OWN:                 N_('My candidate data'), 
                self.BATCH:               N_('My selected candidate batch'),
                self.COMMON + self.OWN:   N_('My own and approved common data'), 
                self.COMMON + self.BATCH: N_('My selected batch and approved common data')
            }
            self.as_status = {
                self.COMMON:              State.ROOT_ACCEPTED, 
                self.OWN:                 State.ROOT_CANDIDATE, 
                self.BATCH:               State.ROOT_CANDIDATE
            }
            self.batch_name = None

        def get_state(self, number):
            # Return the state for given context_code value
            try:
                return self.as_status[number]
            except Exception:
                print(f"UserContext.ChoicesOfView.get_state: invalid key {number} for state")
                return None

        def get_valid_key(self, number):
            # Return the key, if valid number, otherwise 0
            if number in list(self.as_str.keys()):
                return number
            return 0

        def get_valid_number(self, number):
            # Return the key, if valid number, otherwise 0
            if number in list(self.as_str.keys()):
                return number
            return 0

#     class ViewRange(): # NextStartPoint
#         ''' For multi page list display, define view range.
#         '''


    def __init__(self, user_session, current_user=None, request=None):
        '''
            Init UserContext with filtering from user session, request and current user.
        '''
        self.session = user_session
        self.choices = self.ChoicesOfView()     # set of allowed material choices
        self.context_code = self.ChoicesOfView.COMMON
        self.state = None
        self.lang = user_session.get('lang','') # User language
        self.batch_id = None

        self.years = []                         # example [1800, 1899]
        self.series = None                      # 'Source' data theme like "birth"
        self.count = 10000                      # Max count ow objects to display
        self.allow_edit = False                 # Is data edit allowed
        self.is_auditor = False

        # View range: names [first, last]
        self.session_var = None
        self.first = ''
        self.last = self.NEXT_END
        self.direction = 'fw'

        """ Set active user, if any username """
        if current_user:
            if current_user.is_active and current_user.is_authenticated:
                self.user = current_user.username
                self.is_auditor = current_user.has_role('audit')
            else:
                self.user = None
        else:
            self.user = user_session.get('username', None)

        """
        - Stores the request parameter div=1 as session variable user_context.
        - Returns owner context name if detected, otherwise False    
        """
        new_selection = 0
        if request:
            # All args
            self.args = request.args
            # Selected years (from-to) years=1111-2222
            years = request.args.get('years', None)
            if years:
                y1, y2 = years.split('-')
                if y1:  yi1 = int(y1)
                else:   yi1 = 0
                if y2:  yi2 = int(y2)
                else:   yi2 = 9999
                self.years = [yi1, yi2]     # selected years [from, to]
                print(f'UserContext: Objects between years {self.years}')


            """ Use case: Selected material for display
                set-scope = 1 -> set a new scope, common material or a specific user batch 
            """
            set_scope = request.args.get('set-scope')
            if set_scope:
                batch_id = request.args.get('batch_id')
                if batch_id:
                    self.context_code = self.ChoicesOfView.BATCH
                    self.batch_id = batch_id
                else:
                    self.context_code = self.ChoicesOfView.COMMON
                    self.batch_id = ""
                self.session['user_context'] = self.context_code
                self.session['batch_id'] = self.batch_id
                self.session['person_scope'] = ('< start', '> end')
                self.session['family_scope'] = ('< start', '> end')
                self.session['place_scope'] = ('< start', '> end')
                self.session['source_scope'] = ('< start', '> end')
                self.session['media_scope'] = ('< start', '> end')
                self.session['comment_scope'] = ('< start', '> end')
            else:
                # If got no request user_context, use session values
                self.context_code = user_session.get('user_context', self.choices.COMMON)
                self.batch_id = user_session.get('batch_id', "")
                print("UserContext: Uses same or default user_context=" \
                      f"{self.context_code} {self.choices.get_state(self.context_code)}")

        if self.user and self.context_code == self.choices.OWN:
            # Select state by context code
            #TODO: Needs better rule for edit permission
            # May edit data, if user has such role
            if self.context_code == self.choices.OWN:
                self.allow_edit = self.is_auditor

        """ Batch selection by state and material """

        self.material = user_session.get("material", DEFAULT_MATERIAL)
        self.state = user_session.get("state")
        if not self.state:
            self.state = self.choices.get_state(self.context_code)

        #   For logging of scene area pages, set User.current_context variable:
        #   are you browsing common, audited data or your own batches?
        current_user.current_context = self.context_code

    def __str__(self):
        return f"{self.state}/{self.material}"

    def _set_next_from_request(self, request=None):  # UNUSED???
        ''' Calculate scope values from request or session. 
        
            - session_var    str    session variable name
            - request        http request

            If request argument fw is defined, set scope [fw,None].
            If request argument bw is defined, set scope [None,bw].
            If none is present, use the original scope from session.

            The missing limit will be filled by the data afterwards.
        '''
        if request:
            fw = request.args.get('fw', None)
            bw = request.args.get('bw', None)
            if fw is None and bw is None:
                # Use original session_scope as is
                return [self.first, self.last]

            if not fw is None:
                # Direction forward from fw: set first = old last
                self.direction = 'fw'
                return [unquote_plus(fw), None]
            else: # bw != None:
                # Direction backwards from bw: set last = old first
                self.direction = 'bw'
                return [None, unquote_plus(bw)]
        else:
            # No request
            if self.session_var:
                self.session[self.session_var] = self.scope
                print(f"UserContext: Now {self.session_var} is cleared")
            return self.scope


    def batch_user(self):
        # Return current user id, if my candidate data is chosen
        if self.context_code in (self.choices.OWN, self.choices.BATCH):
            return self.user
        else:
            return None

    def owner_str(self):
        # Return current owner choice as text.
        
        # Only used in test_owner_filter.test_ownerfilter_nouser()
        try:
            print("ui.user_context.UserContext.owner_str:",self.material,self.state,self.batch_id)
            return f"{ _(self.material) }: { _(self.state) } {self.batch_id}"
            #return f"{self.choices.as_str[self.context_code]} {self.batch_id}"
        except:
            return ''

    def use_case(self):
        # Return current use case (owner choice) as code 
        try:
            return self.choices.CODE_VALUES[self.context_code]
        except:
            return ''
    
    def use_common(self):
        ''' Tells, if you should select objects from common database.

            Always when self.ChoicesOfView.COMMON is required
        '''
        return (self.context_code & 1) > 0

    def privacy_ok(self, obj):
        ''' Returns True, if there is no privacy reason to hide given object.
        
            Rules:
            - if common data (not researcher's own)
              - use obj.too_new variable, if available
            - else allow
        '''
        if self.use_common():
            # Privacy limits only for common data
            try:
                return (obj.too_new == False)
            except: # No privacy limit for this kind of object
                pass
        return True

#     def obsolete_set_scope_from_request(self, request=None, var_name=None):

    def set_scope_from_request(self, request=None, session_var=None): #set_next_from_request:
        ''' Calculate scope values from request or session. 
        
            :param: request        http request
            :param: session_var    str    session variable name like  'person_scope'
        
            Use request arguments fw or bw, if defined.
            Else use original from session.
            
            If request is missing, try session.session_var.
        '''
        self.session_var = session_var
            
        if request:
            fw = request.args.get('fw', None)
            bw = request.args.get('bw', None)
            if not (fw is None and bw is None):
                if fw is None:
                    # Direction backwards from bw parameter
                    self.last = unquote_plus(bw)
                    return
                else: # bw is None:
                    # Direction forward from fw parameter
                    self.first = unquote_plus(fw)
                    return

        # No request OR no fw or bw in request
        if self.session_var:
            # Scope from session, if defined; else default
            scope = self.session.get(self.session_var, [self.first, self.last])
            self.first = scope[0]
            self.last = scope[1]
            self.session[self.session_var] = scope
            print(f"UserContext.set_scope_from_request: {self.session_var} is cleared {scope}")
        return


    def update_session_scope(self, var_name, name_first, name_last, limit, rec_cnt):
        """ Update the session scope according to items really found from database.
        
            var_name    str    field name in self.session
            name_first  str    the first item name got from database
            name_last   str    the last item name
            limit       int    number of items requested
            rec_cnt     int    records actually received
        
            The new scope is [name_first, name_last]. If end has been reached, 
            the corresponding limit is set to endmark '> end' or '< start'.
        """
        print(f"UserContext.update_session_scope: Got {rec_cnt}  of {limit} items {name_first!r} – {name_last!r}")
        scope_old = (self.first, self.last)
        # 1. starting scope in session     ['y','z']
        # 2a accessed next fw              ['z', 'ö']  set first = old last
        # 2b or accessed next bw           ['x', 'y']  set last = old first
        if self.direction == 'bw':
            self.first = name_first if rec_cnt == limit else '< start'
            self.last = name_last
        else:
            self.first = name_first
            self.last = name_last if rec_cnt == limit else '> end'

        if scope_old[0] != self.first or scope_old[1] != self.last:
            print(f"UserContext.update_session_scope: New {var_name!r} {self.first!r} – {self.last!r}")

        self.session[var_name] = (self.first, self.last)
        print(f"UserContext = {repr(self.session)}")


    def next_name(self, direction='fw'):
        ''' Tells the next name from which the names must be read from.

            :parameter:    direction    str    forwards or backwards

            If direction is fw, display next names [last - ...]
            If direction is bw, display next names [... - first]
            --> anyways, the next names is included.
        '''
        if direction == 'fw':
            if self.last == self.NEXT_END:
                # Generic end mark
                ret = '> end'
            else:
                ret = self.last

        elif direction == 'bw':
            if self.first == self.NEXT_START:
                # Generic start mark
                ret = '< start'
            else:
                ret = self.first
        else:
            print(f'UserContext.next_name: invalid direction="{direction}"')
            ret = None

        #print(f'UserContext.next_name: {[self.first, self.last]}, {direction} next="{ret}"')
        return ret

    def at_end(self):
        ''' Tells, if page contains the last name of data.
        '''
        if self.last.startswith(self.NEXT_END):
            return True
        return False

    def at_start(self):
        ''' Tells, if page contains the first name of data.
        '''
        if self.first == '' or self.first.startswith(self.NEXT_START):
            return True
        return False
