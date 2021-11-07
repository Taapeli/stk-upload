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
"""
    User Context for Scene pages has information of 
    - current user,
    - the material concerned
    - view properties enabling object listing division to concurrent pages.

Created on 1.11.2021

@author: jm
"""
from flask import session, request
from flask_security import current_user
from flask_babelex import _
from urllib.parse import unquote_plus

from bl.base import Status
from bl.root import State


class UserContext:
    """ Store user and data context from session and current_user.
    """

    NEXT_START = "<"  # from first name of data
    NEXT_END = ">"  # end reached: there is nothing forwards

    COMMON = "common" # Approved data
    BATCH = "batch"   # Selected candidate or approved batch
    # OWN = "own"     # Candidate data

    def __init__(self):
        """ Initialize UserContext by user and material info.
        """

        # 1. From session (previous settings)

        self.session = session
        self.batch_id = self.session.get("batch_id")
        self.material = self.session.get("material")
        self.state = self.session.get("state")
        self.lang = self.session.get("lang", "")  # User language
        print(f"#UserContext: session={self.session}")
        print(f"#UserContext: SESSION material={self.material}, batch={self.batch_id}, state={self.state}")
        
        # 2. From current_user (login data)

        self.current_context = self.COMMON
        self.user = None
        self.allow_edit = False  # By default data edit is not allowed
        self.is_auditor = False
        """ Set active user, if any username """
        if current_user:
            if current_user.is_active and current_user.is_authenticated:
                self.user = current_user.username
                self.is_auditor = current_user.has_role("audit")

        # 3. From request parameters (calling page)
        #    overriding session data

        self.args = UserContext.get_request_args()
        print(f"#UserContext: REQUEST material={self.args.get('material')},"
              f" batch={self.args.get('batch_id')} / {self.current_context}")
        self.material = self.args.get("material", self.material)
        self.session["material"] = self.material
        if "batch_id" in self.args:
            # Access data by batch_id
            self.batch_id = self.args["batch_id"] #, self.batch_id)
            self.session["batch_id"] = self.batch_id
        else:
            # Access data by material and state
            self.state = State.ROOT_ACCEPTED
        return

    @staticmethod
    def select_material(breed):
        """
        Save material selection from request to session.

            breed == "batch"     the material is single batch
            breed == "common"    the material is batches selected by material_type and state

        1.1 The material is single batch
            /gramps/commands/2021-10-09.001 HTTP/1.1
            --> "GET /scene/material/batch?batch_id=2021-10-09.001 HTTP/1.1" 200 -
        
        From /start/logged
        ------------------
        1.2 The material is single batch
            /start/logged HTTP/1.1
            --> "POST /scene/material/batch HTTP/1.1" 200 -
        
        2. The material is batches selected by material_type and state
            /start/logged HTTP/1.1
            --> "GET /scene/material/common?material_type=Family+Tree HTTP/1.1" 200 -
        """
        args = UserContext.get_request_args()
        print(f"ui.context.UserContext.select_material: {args}")
        print(f"ui.context.UserContext.select_material: {session}")
        session["breed"] = breed
        session['set_scope'] = True     # Reset material and scope

        if breed == "batch":
            # request args:  {'batch_id': '2021-10-09.001'}
            session['batch_id'] = args.get('batch_id')
            # optional args: {'material_type': 'Family Tree', 'state': 'Candidate'}
            session['material_type'] = args.get('material_type')
            session['state'] = args.get('state')

            print("ui.context.UserContext.select_material: the material is single batch")
            if not ( "batch_id" in session and session["batch_id"] ):
                return {"status": Status.ERROR, "statustext": _("Missing batch id")}
            return {"status": Status.OK, "breed": breed, "args":args}
            
        elif breed == "common":
            # request args: {'material_type': 'Place Data', 'state': 'Candidate', 'batch_id': '2021-10-26.001'}
            session['material_type'] = args.get('material_type')
            session['state'] = args.get('state', State.ROOT_DEFAULT_STATE)
            session['batch_id'] = None

            print("ui.context.UserContext.select_material: "
                  "The material is batches selected by material_type and state")
            if not ( "material_type" in session and "state" in session and
                     session["material_type"] and session["state"] ):
                return {"status": Status.ERROR, 
                        "statustext": _("Missing material type or state")}
            return {"status": Status.OK, "breed": breed, "args":args}
        return {"status": Status.ERROR, "breed": breed, "statustext": _("Undefined breed of materials")}

    def get(self, var_name, default=None):
        """ Get request argument value from args or form data.
        
            If datatype is int, returns the argument valie converted to int.
        """
        value = self.args.get(var_name, default)
        if value is None and var_name in self.session:
            value = self.session.get(var_name)
        print(f"#UserContext.get({var_name}) = {value}")
        return value

    def is_common(self):
        """ Tells, if current material may be formed from multiple batches.

            - True, if current material may have multiple batches
            - False, if current material is limited by batch_id
        """
        return self.current_context == self.COMMON

    def use_case(self):
        """ Return current use case (owner choice) as code.
        """
        if self.batch_id:
            return self.BATCH # Selected candidate or approved batch
        else:
            return self.COMMON # Approved data
        # else self.OWN - Collection of own data not in use

    def set_scope(self, browse_var:str):
        """ Store data context from request for listing page.

            Define self.current_context "common"/"batch", if set_scope is given in args. 
            set a new scope: common material or a specific user batch 

            Optional browse settings from request args:
            - first         Lower limit of display scope for 'browse_var' view
            - last          Higher limit of display scope
            - years         optional time limit like [1800, 1899]
            - series        Source data theme like "birth"
            - count         Max count of objects to display
            - allow_edit    User is granted to edit objects
        """
        # Defaults values
        self.first = ''
        self.last = self.NEXT_END
        self.direction = 'fw' # or "bw"

        if self.args:
            # Selected years [from,to] years=1111-2222
            self.years = []
            years = self.args.get('years', None)
            if years:
                y1, y2 = years.split('-')
                if y1: yi1 = int(y1)
                else: yi1 = 0
                if y2: yi2 = int(y2)
                else: yi2 = 9999
                self.years = [yi1, yi2]
                print(f'#UserContext.set_scope: Objects between years {self.years}')

            if self.args.get('set_scope'):
                self.session[browse_var] = ('< start', '> end')
            else:
                # If got no request user_context, use session values
                print("#UserContext: Uses same or default user_context: " \
                      f"{self.current_context} {self.material} in state {self.state}")
        else:
            self.request_args = {}
            self.years = []                         # example [1800, 1899]
            self.series = None                      # 'Source' data theme like "birth"
            self.count = 10000                      # Max count ow objects to display

        #   For logging of scene area pages, set User.current_context variable:
        #   are you browsing common, audited data or your own batches?
        if not self.is_common():     #self.user and self.batch_id:
            # Data selection by Root.batch_id and username
            self.current_context = self.BATCH   # "batch"
            # May edit data, if user has appropriate role
            self.allow_edit = self.is_auditor
        else:
            # Data selection by Root.state and Root.material
            self.current_context = self.COMMON  # "common"
            self.state = State.ROOT_ACCEPTED
        current_user.current_context = self.current_context

        # State selection, if any
        self.state = self.session.get("state", None)
        return

    def display_current_material(self):
        """ Return current material and batch choice for display. """
        try:
            m = self.material or 'Unknown material'
            #if m == "Place": m = "Places"
            print(f"#UserContext.display_current_material: {m}: {self.batch_id}, state={self.state}" )
            if self.state is None:
                return f"{ _(m) }: {self.batch_id}"
            elif self.state == State.ROOT_ACCEPTED:
                return f"{ _(m) }: { _('Approved Isotammi tree') } {self.batch_id}"
            else:
                return f"{ _(m) }: { _(self.state) } {self.batch_id}"
        except Exception as e:
            return "Error: " + str(e)

    def set_scope_from_request(self, request=None, browse_var=None):
        ''' Calculate list display scope values from request or session. 
        
            :param: request        http request
            :param: browse_var    str    session variable name like  'person_scope'
        
            Use request arguments fw or bw, if defined.
            Else use original from session.
            
            If request is missing, try session.browse_var.
        '''
        self.browse_var = browse_var
        if self.args:
            fw = self.args.get('fw', None)
            bw = self.args.get('bw', None)
            if fw is None and bw is None:
                return
            if fw is None:
                # Direction backwards from bw parameter
                self.last = unquote_plus(bw)
                return
            else: # bw is None:
                # Direction forward from fw parameter
                self.first = unquote_plus(fw)
                return

        # No request OR no fw or bw in request
        if self.browse_var:
            # Scope from session, if defined; else default
            scope = self.session.get(self.browse_var, [self.first, self.last])
            self.first = scope[0]
            self.last = scope[1]
            self.session[self.browse_var] = scope
            print(f"UserContext.set_scope_from_request: {self.browse_var} is set to {scope}")

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
        print(f"#UserContext.update_session_scope: Got {rec_cnt}  of {limit} items {name_first!r} – {name_last!r}")
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
            print(f"#UserContext.update_session_scope: New {var_name!r} {self.first!r} – {self.last!r}")

        self.session[var_name] = (self.first, self.last)
        print(f"#UserContext.update_session_scope: UserContext = {repr(self.session)}")

    @staticmethod
    def get_request_args():
        """Return request arguments from request.args or request.form, if available.
        """
        if request is None:
            return {}
        if request.method == "GET":
            return request.args.to_dict()
        else:
            return request.form.to_dict()
