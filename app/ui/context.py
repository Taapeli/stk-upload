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
    - view properties enabling multi page object listing pages.

Created on 1.11.2021

@author: jm
"""
# blacked 12.11.2021
from flask import session, request
from flask_security import current_user
from urllib.parse import unquote_plus

from bl.root import State
from bl.material import Material


class UserContext:
    """
    Store user and data context from session and current_user.
    
    Steps:
        1. Material.select_material()
           Stores current material (material_type, batch, state)
           from request to session
        2. u_context = UserContext()
           Access user context (material, request, list scope)
           from session and user_profile
        3. u_context.update_session_scope(var_name, name_first, name_last, limit, rec_cnt)
           Updates changed list scope to session for next page
    """

    NEXT_START = "<"  # from first name of data
    NEXT_END = ">"  # end reached: there is nothing forwards

    COMMON = "common"  # Multi-batch data like Approved data
    BATCH = "batch"  # Selected candidate or approved batch
    # OWN = "own"     # Candidate data

    def __init__(self):
        """ Initialize UserContext by user and material info.
        """

        # 1. From session (previous settings)

        self.material = Material(session, request)
        # self.material.breed = session.get("current_context", "")
        # self.material.m_type = session.get("material_type")
        # self.material.state = session.get("state", "")
        # self.material.batch_id = session.get("batch_id", "")
        self.lang = session.get("lang", "")  # User language

        print(f"#UserContext: session={session}")
        # print(f"#UserContext: {self.get_current()} SESSION")
        self.first = ""
        self.last = self.NEXT_END
        self.direction = "fw"  # or "bw"

        # 2. From current_user (login data)

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

        # self.request_args = Material.get_request_args()
        print(
            f"#UserContext: {self.material.get_current()}"
            f" REQUEST values={self.material.request_args}"
        )
        return

    def get(self, var_name, default=None):
        """ Get a REQUEST argument value from args, form data or session.
        """
        value = self.material.request_args.get(var_name)
        if value is None and var_name in session:
            value = session.get(var_name)
        if not value:
            value = default
        print(f"#Material.get({var_name}) = {value!r}")
        return value

    def is_common(self):
        """ Tells, if current material may be formed from multiple batches.

            - True, if current material may have multiple batches
            - False, if current material is limited by batch_id
        """
        return self.material.breed == self.COMMON

    def batch_user(self):
        """ Return current user id, if my candidate data is chosen. """
        # if self.context_code in (self.choices.OWN, self.choices.BATCH):
        if not self.is_common():
            return self.user
        else:
            return None

    def privacy_ok(self, obj):
        """ Returns True, if there is no privacy reason to hide given object.
        """
        if self.is_common():
            # Privacy limits only for common data
            try:
                return obj.too_new == False
            except:  # No privacy limit for this kind of object
                pass
        return True

    def use_case(self):
        """ Return current use case (owner choice) as code.
        """
        if self.material.batch_id:
            return self.BATCH  # Selected candidate or approved batch
        else:
            return self.COMMON  # Approved data
        # else self.OWN - Collection of own data not in use

    def next_name(self, direction="fw"):
        """ For template pages, tells the next page starting name.

            :parameter:    direction    str    forwards or backwards

            If direction is fw, display next names [last - ...]
            If direction is bw, display next names [... - first]
            --> anyways, the next names is included.
        """
        if direction == "fw":
            if self.last == self.NEXT_END:
                ret = "> end"  # Generic end mark
            else:
                ret = self.last
        elif direction == "bw":
            if self.first == self.NEXT_START:
                ret = "< start"  # Generic start mark
            else:
                ret = self.first
        else:
            print(f'UserContext.next_name: invalid direction="{direction}"')
            ret = None
        # print(f'UserContext.next_name: {[self.first, self.last]}, {direction} next="{ret}"')
        return ret

    def at_end(self):
        """ For template pages, tells if page contains the last name of data.
        """
        return self.last.startswith(self.NEXT_END)

    def at_start(self):
        """ For template pages, tells if page contains the first name of data.
        """
        return self.first == "" or self.first.startswith(self.NEXT_START)

    def set_scope(self, browse_var: str):
        """ Store data context from request for listing page.

            Define self.material.breed "common"/"batch", if set_scope is given in args. 
            set a new scope: common material or a specific user batch 

            Optional browse settings from request args:
            - first         Lower limit of display scope for 'browse_var' view
            - last          Higher limit of display scope
            - years         optional time limits like [1800, 1899]
            - series        optional Source data theme like "birth"
            - count         Max count of objects to display
            - allow_edit    User is granted to edit objects
        """
        print(f"#Material.set_scope: {browse_var}")
        # Defaults values
        # self.first = ""
        # self.last = self.NEXT_END
        # self.direction = "fw"  # or "bw"

        if self.material.request_args:
            # Selected years [from,to] years=1111-2222
            self.years = []
            years = self.material.request_args.get("years", None)
            if years:
                y1, y2 = years.split("-")
                if y1:
                    yi1 = int(y1)
                else:
                    yi1 = 0
                if y2:
                    yi2 = int(y2)
                else:
                    yi2 = 9999
                self.years = [yi1, yi2]
                print(f"#Material.set_scope: Objects between years {self.years}")

            if self.material.request_args.get("set_scope"):
                session[browse_var] = ("< start", "> end")
            else:
                # If got no request user_context, use session values
                print(
                    "#UserContext: Uses same or default user_context: "
                    f"{self.material.get_current()})"
                )
        else:
            # self.material.request_args = {}
            self.years = []  # example [1800, 1899]
            self.series = None  # 'Source' data theme like "birth"
            self.count = 10000  # Max count ow objects to display

        #   For logging of scene area pages, set User.breed variable:
        #   are you browsing common, audited data or your own batches?
        if not self.is_common():  # self.user and self.material.batch_id:
            # Data selection by Root.batch_id and username
            self.material.breed = self.BATCH  # "batch"
            # May edit data, if user has appropriate role
            self.allow_edit = self.is_auditor
        else:
            # Data selection by Root.state and Root.material_type
            # self.material.breed = self.COMMON  # "common"
            self.material.state = State.ROOT_ACCEPTED
        current_user.breed = self.material.breed

        # State selection, if any
        self.material.state = session.get("state", None)
        return

    def display_current_material(self):
        """ Return current material and batch choice for display. """
        return self.material.to_display()

    def set_scope_from_request(self, browse_var=None):
        """ Calculate list display scope values from request or session. 

            :param: request     http request
            :param: browse_var  str         session variable name like  'person_scope'
            :return:            dict        arguments for list pageing fw/bw
        
            #?
            # Use request arguments fw or bw, if defined.
            # Else use original from session.
            #
            # If request is missing, try session.browse_var.
        """
        return_args = {}
        self.browse_var = browse_var
        self.first = self.NEXT_START
        self.last = self.NEXT_END
        req_args = self.material.request_args
        if req_args:
            # New values from request?
            years = req_args.get("years")
            if years:
                return_args["years"] = years
            c = req_args.get("c")
            if c:
                return_args["c"] = c

            fw = req_args.get("fw", None)
            bw = req_args.get("bw", None)
            if fw is None and bw is None:
                return return_args
            if fw is None:
                # bw: Direction backwards from bw parameter
                self.last = unquote_plus(bw)
                return_args["bw"] = self.last
                return return_args
            else:
                # fw: Direction forward from fw parameter
                self.first = unquote_plus(fw)
                return_args["fw"] = self.first
                return return_args

        # No request OR no fw or bw in request
        if self.browse_var:
            # Scope from session, if defined; else default
            scope = session.get(self.browse_var, [self.first, self.last])
            self.first = scope[0]
            self.last = scope[1]
            return_args["fw"] = self.first
            session[self.browse_var] = scope
            print(
                f"Material.set_scope_from_request: {self.browse_var} is set to {scope}"
            )

        return return_args

    def update_session_scope(self, var_name, name_first, name_last, limit, rec_cnt):
        """ Update the session scope according to items really found from database.
        
            var_name    str    field name in session
            name_first  str    the first item name got from database
            name_last   str    the last item name
            limit       int    number of items requested
            rec_cnt     int    records actually received
        
            The new scope is [name_first, name_last]. If end has been reached, 
            the corresponding limit is set to endmark '> end' or '< start'.
        """
        print(
            f"#Material.update_session_scope: Got {rec_cnt}  of {limit} items {name_first!r} – {name_last!r}"
        )
        scope_old = (self.first, self.last)
        # 1. starting scope in session     ['y','z']
        # 2a accessed next fw              ['z', 'ö']  set first = old last
        # 2b or accessed next bw           ['x', 'y']  set last = old first
        if self.direction == "bw":
            self.first = name_first if rec_cnt == limit else "< start"
            self.last = name_last
        else:
            self.first = name_first
            self.last = name_last if rec_cnt == limit else "> end"

        if scope_old[0] != self.first or scope_old[1] != self.last:
            print(
                f"#Material.update_session_scope: New {var_name!r} {self.first!r} – {self.last!r}"
            )

        session[var_name] = (self.first, self.last)
        print(f"#Material.update_session_scope: UserContext = {repr(session)}")
