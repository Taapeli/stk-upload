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
# blacked 8.11.2021
from flask import session, request
from flask_security import current_user
from flask_babelex import _
from urllib.parse import unquote_plus

from bl.base import Status
from bl.root import State, Root


class UserContext:
    """
    Store user and data context from session and current_user.
    
    Steps:
        1. UserContext.select_material()
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

        self.current_context = session.get("current_context", "")
        self.material_type = session.get("material_type")
        self.state = session.get("state", "")
        self.batch_id = session.get("batch_id", "")
        # if self.batch_id:
        #     self.current_context = self.BATCH
        # else:
        #     self.current_context = self.COMMON
        # if session.get("breed", "") == self.COMMON:
        #     # Material changed to 'common' asked in self.material_select()
        #     self.batch_id = ""
        self.lang = session.get("lang", "")  # User language

        print(f"#UserContext: session={session}")
        #print(f"#UserContext: {self.get_material_tuple()} SESSION")

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

        self.request_args = UserContext.get_request_args()
        print(
            f"#UserContext: {self.get_material_tuple()}"
            f" REQUEST values={self.request_args}"
        )
        return

    @staticmethod
    def set_session_material(breed):
        """
        Save material selection from request to session.

        1.1 The material is single batch (breed="batch")
            From /gramps/commands/2021-10-09.001 HTTP/1.1
            --> "GET /scene/material/batch?batch_id=2021-10-09.001 HTTP/1.1" 200 -
        
        1.2 The material is single batch (breed="batch")
            From /start/logged HTTP/1.1
            --> "POST /scene/material/batch HTTP/1.1" 200 -
                form --> ImmutableMultiDict([('material_type', 'Place Data'),
                         ('state', 'Candidate'), ('batch_id', '2021-10-26.001')])

        2. The material is batches selected by material_type and state (breed="common")
            From /start/logged HTTP/1.1
            --> "GET /scene/material/common?material_type=Family+Tree HTTP/1.1" 200 -
        """
        args = UserContext.get_request_args()
        print(f"#UserContext.set_session_material: request {args}")
        session["breed"] = breed
        session["set_scope"] = True  # Reset material and scope
        session["current_context"] = breed
        if "material" in session:
            print(
                f"ui.context.UserContext.set_session_material: "
                f'Removed obsolete session.material={session.pop("material")!r}'
            )

        if breed == "batch":
            # request args:  {'batch_id': '2021-10-09.001'}
            session["state"] = args.get("state")
            session["material_type"] = args.get("material_type")
            session["batch_id"] = args.get("batch_id")

            # Missing material type or state?
            # - optional args: {'material_type': 'Family Tree', 'state': 'Candidate'}
            if session["batch_id"] and (
                not session["material_type"] or not session["state"]
            ):
                # Get from database
                root = Root.get_batch(current_user.username, session["batch_id"])
                session["material_type"] = root.material_type
                session["state"] = root.state

            print(
                "UserContext.select_material: the material is single batch "
                f'{UserContext.get_session_material_tuple()})'
            )
            # if not ("batch_id" in session and session["batch_id"]):
            #     return {"status": Status.ERROR, "statustext": _("Missing batch id")}
            return {"status": Status.OK, "breed": breed, "args": args}

        elif breed == "common":
            # request args: {'state': 'Candidate', 'material_type': 'Place Data', 'batch_id': '2021-10-26.001'}
            session["state"] = args.get("state", State.ROOT_DEFAULT_STATE)
            session["material_type"] = args.get("material_type")
            session["batch_id"] = None

            print(
                "UserContext.select_material: The material is batch collection "
                f'{UserContext.get_session_material_tuple()}'
            )
            if not (
                "material_type" in session
                and "state" in session
                and session["material_type"]
                and session["state"]
            ):
                return {
                    "status": Status.ERROR,
                    "statustext": _("Missing material type or state"),
                }
            return {"status": Status.OK, "breed": breed, "args": args}
        return {
            "status": Status.ERROR,
            "statustext": _("Undefined breed of materials"),
        }

    def get(self, var_name, default=None):
        """ Get a REQUEST argument value from args, form data or session.
        """
        value = self.request_args.get(var_name)
        if value is None and var_name in session:
            value = session.get(var_name)
        if not value:
            value = default
        print(f"#UserContext.get({var_name}) = {value!r}")
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
            return self.BATCH  # Selected candidate or approved batch
        else:
            return self.COMMON  # Approved data
        # else self.OWN - Collection of own data not in use

    def set_scope(self, browse_var: str):
        """ Store data context from request for listing page.

            Define self.current_context "common"/"batch", if set_scope is given in args. 
            set a new scope: common material or a specific user batch 

            Optional browse settings from request args:
            - first         Lower limit of display scope for 'browse_var' view
            - last          Higher limit of display scope
            - years         optional time limits like [1800, 1899]
            - series        optional Source data theme like "birth"
            - count         Max count of objects to display
            - allow_edit    User is granted to edit objects
        """
        print(f"#UserContext.set_scope: {browse_var}")
        # Defaults values
        self.first = ""
        self.last = self.NEXT_END
        self.direction = "fw"  # or "bw"

        if self.request_args:
            # Selected years [from,to] years=1111-2222
            self.years = []
            years = self.request_args.get("years", None)
            if years:
                y1, y2 = years.split("-")
                if y1: yi1 = int(y1)
                else: yi1 = 0
                if y2: yi2 = int(y2)
                else: yi2 = 9999
                self.years = [yi1, yi2]
                print(f"#UserContext.set_scope: Objects between years {self.years}")

            if self.request_args.get("set_scope"):
                session[browse_var] = ("< start", "> end")
            else:
                # If got no request user_context, use session values
                print(
                    "#UserContext: Uses same or default user_context: "
                    f"{self.get_material_tuple()})"
                )
        else:
            # self.request_args = {}
            self.years = []  # example [1800, 1899]
            self.series = None  # 'Source' data theme like "birth"
            self.count = 10000  # Max count ow objects to display

        #   For logging of scene area pages, set User.current_context variable:
        #   are you browsing common, audited data or your own batches?
        if not self.is_common():  # self.user and self.batch_id:
            # Data selection by Root.batch_id and username
            self.current_context = self.BATCH  # "batch"
            # May edit data, if user has appropriate role
            self.allow_edit = self.is_auditor
        else:
            # Data selection by Root.state and Root.material_type
            self.current_context = self.COMMON  # "common"
            self.state = State.ROOT_ACCEPTED
        current_user.current_context = self.current_context

        # State selection, if any
        self.state = session.get("state", None)
        return

    def display_current_material(self):
        """ Return current material and batch choice for display. """
        try:
            m = self.material_type or "Unknown material"
            # if m == "Place": m = "Places"
            print(
                f"#UserContext.display_current_material: "
                f'[{self.current_context!r}, {self.state!r}, {m!r}, {self.batch_id!r}]'
                )
            if self.state is None:
                return f"{ _(m) }: {self.batch_id}"
            elif self.state == State.ROOT_ACCEPTED:
                batch = self.batch_id if self.batch_id else ""
                return f"{ _(m) }: { _('Approved Isotammi tree') } {batch}"
            else:
                return f"{ _(m) }: { _(self.state) } {self.batch_id}"
        except Exception as e:
            return "Error: " + str(e)

    def set_scope_from_request(self, browse_var=None):
        """ Calculate list display scope values from request or session. 
        
            :param: request        http request
            :param: browse_var    str    session variable name like  'person_scope'
        
            Use request arguments fw or bw, if defined.
            Else use original from session.
            
            If request is missing, try session.browse_var.
        """
        self.browse_var = browse_var
        if self.request_args:
            # New values from request?
            fw = self.request_args.get("fw", None)
            bw = self.request_args.get("bw", None)
            if fw is None and bw is None:
                self.first = self.NEXT_START
                self.last = self.NEXT_END
                return
            if fw is None:
                # bw: Direction backwards from bw parameter
                self.last = unquote_plus(bw)
                return
            else:
                # fw: Direction forward from fw parameter
                self.first = unquote_plus(fw)
                return
        else:
            self.first = self.NEXT_START
            self.last = self.NEXT_END

        # No request OR no fw or bw in request
        if self.browse_var:
            # Scope from session, if defined; else default
            scope = session.get(self.browse_var, [self.first, self.last])
            self.first = scope[0]
            self.last = scope[1]
            session[self.browse_var] = scope
            print(
                f"UserContext.set_scope_from_request: {self.browse_var} is set to {scope}"
            )

        return

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
            f"#UserContext.update_session_scope: Got {rec_cnt}  of {limit} items {name_first!r} – {name_last!r}"
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
                f"#UserContext.update_session_scope: New {var_name!r} {self.first!r} – {self.last!r}"
            )

        session[var_name] = (self.first, self.last)
        print(f"#UserContext.update_session_scope: UserContext = {repr(session)}")

    def get_material_tuple(self):
        """Return current material properties.
        """
        return [
            self.current_context,   # "batch" / "common"
            self.state,             # Root.state "Candidate", ... "Accepted"
            self.material_type,     # "Family Tree", ...
            self.batch_id           # Root.batch_id
        ]

    @staticmethod
    def get_session_material_tuple():
        """Return session material properties.
        """
        if "current_context" in session: cc = session["current_context"]
        else: cc = ""
        if "state" in session: st = session["state"]
        else: st = ""
        if "material_type" in session: mt = session["material_type"]
        else: mt = ""
        if "batch_id" in session: bi = session["batch_id"]
        else: bi = ""
        return [ cc, st, mt, bi ]

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
