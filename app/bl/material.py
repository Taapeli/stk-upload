#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2021       Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu,
#                            Ismo Peltonen, Pekka Valta
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
Created on 11.11.2021

@author: jm
'''
#from flask import session, request
#from flask_security import current_user
from flask_babelex import _

from bl.base import Status
from bl.root import State, Root

class Material():
    '''
    Material defines a seleced view to Root data objects and data behind that.
    '''

    def __init__(self, session, request):
        """ Initialize Material object using session and request information.
        """

        self.breed = session.get("current_context", "")
        
        self.m_type = session.get("material_type")
        self.state = session.get("state", "")
        self.batch_id = session.get("batch_id", "")

        self.request_args = Material.get_request_args(session, request)
        
        # # 2. From current_user (login data)
        #
        # self.user = None
        # self.allow_edit = False  # By default data edit is not allowed
        # self.is_auditor = False
        # """ Set active user, if any username """
        # if current_user.is_active and current_user.is_authenticated:
        #     self.user = current_user.username
        #     self.is_auditor = current_user.has_role("audit")
        print(
            f"#bl.material.Material: {self.get_current()}"
            f" REQUEST values={self.request_args}"
        )
        return

    def to_display(self):
        """ Return current material and batch choice for display. """
        try:
            m = self.m_type or "Unknown material"
            # if m == "Place": m = "Places"
            print(
                f"#bl.material.Material.to_display: "
                f'[{self.breed!r}, {self.state!r}, {m!r}, {self.batch_id!r}]'
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


    #----- Static methods
    
    @staticmethod
    def set_session_material(session, request, breed, username):
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
        args = Material.get_request_args(session, request)
        print(f"#Material.set_session_material: request {args}")
        session["breed"] = breed
        session["set_scope"] = True  # Reset material and scope
        session["current_context"] = breed
        if "material" in session:
            print(
                f"ui.context.Material.set_session_material: "
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
                root = Root.get_batch(username, session["batch_id"])
                session["material_type"] = root.material_type
                session["state"] = root.state

            print(
                "Material.select_material: the material is single batch "
                f'{Material.get_from_session(session)})'
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
                "Material.select_material: The material is batch collection "
                f'{Material.get_from_session(session)}'
            )
            if not (
                "material_type" in session
                and "state" in session
                and session["material_type"]
                and session["state"]
            ):
                return {
                    "status": Status.ERROR,
                    "statustext": _("Missing material_type or state"),
                }
            return {"status": Status.OK, "breed": breed, "args": args}
        return {
            "status": Status.ERROR,
            "statustext": _("Undefined breed of materials"),
        }

    def get_current(self):
        """Return current material properties.
        """
        return [
            self.breed,   # "batch" / "common"
            self.state,             # Root.state "Candidate", ... "Accepted"
            self.m_type,     # "Family Tree", ...
            self.batch_id           # Root.batch_id
        ]

    @staticmethod
    def get_from_session(session):
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
    def get_request_args(session, request):
        """Return request arguments from request.args or request.form.
        """
        if request is None:
            return {}
        if request.method == "GET":
            return request.args.to_dict()
        else:
            return request.form.to_dict()