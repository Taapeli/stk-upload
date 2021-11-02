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
from urllib.parse import unquote_plus

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
        self.state = None
        self.lang = self.session.get("lang", "")  # User language
        self.batch_id = self.session.get("batch_id")
        self.material = self.session.get("material")
        self.is_approved = self.batch_id is None or self.batch_id == ""

        # 2. From current_user (login data)

        self.user = None
        self.allow_edit = False  # By default data edit is not allowed
        self.is_auditor = False
        """ Set active user, if any username """
        if current_user:
            if current_user.is_active and current_user.is_authenticated:
                self.user = current_user.username
                self.is_auditor = current_user.has_role("audit")

        # obsolete set_material(self, request_args={}):

        # 3. From request parameters (calling page)
        #    overriding session data

        self.args = UserContext.get_request_args()
        self.material = self.args.get("material", self.material)
        self.session["material"] = self.material
        if "batch_id" in self.args:
            self.batch_id = self.args.get("batch_id", self.batch_id)
            self.session["batch_id"] = self.batch_id
        return

    def get(self, var, default=None, datatype=None):
        """ Get request argument value from args or form data.
        
            If datatype is int, returns the argument valie converted to int.
        """
        if datatype is int and not default is None:
            return int(self.args.get(var, default))
        return self.args.get(var, default)

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
                print(f'UserContext.set_scope: Objects between years {self.years}')

            if self.args.get('set_scope'):
                self.session[browse_var] = ('< start', '> end')
            else:
                # If got no request user_context, use session values
                print("UserContext: Uses same or default user_context: " \
                      f"{self.current_context} {self.material} in state {self.state}")
        else:
            self.request_args = {}
            self.years = []                         # example [1800, 1899]
            self.series = None                      # 'Source' data theme like "birth"
            self.count = 10000                      # Max count ow objects to display

        #   For logging of scene area pages, set User.current_context variable:
        #   are you browsing common, audited data or your own batches?
        if self.user and self.batch_id: #self.context_code == self.choices.OWN:
            self.current_context = "batch"
            # May edit data, if user has appropriate role
            self.allow_edit = self.is_auditor
        else:
            self.current_context = "common"
        current_user.current_context = self.current_context

        """ Batch selection by state (and material?) """

        self.state = self.session.get("state", None)
        # if not self.state: self.state = self.choices.get_state(self.context_code)
        return

    def show_current_material(self):
        """ Return current material and batch choice for display. """
        try:
            m = self.material or 'Family Tree'
            if m == "Place": m = "Places"
            print(f"UserContext.show_current_material: {m}:{self.batch_id}, {self.state}" )
            if self.state is None or self.state == State.ROOT_ACCEPTED:
                return f"{ _(m) }: { _('Approved Isotammi tree') } {self.batch_id}"
            else:
                return f"{ _(m) }: { _(self.state) } {self.batch_id}"
        except:
            return ''

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

    def use_case(self):
        """ Return current use case (owner choice) as code.
        """
        if self.batch_id:
            return self.BATCH # Selected candidate or approved batch
        else:
            return self.COMMON # Approved data
        # else self.OWN - Collection of own data not in use

    @staticmethod
    def get_request_args():
        """Return request arguments from request.args or request.form, if available.
        """
        if request is None:
            return {}
        if request.method == "GET":
            return dict(request.args)
        else:
            return dict(request.form)
