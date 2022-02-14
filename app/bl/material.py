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
from flask_babelex import _

from bl.base import Status

MATERIAL_COMMON = "common"  # Multiple batch data like Approved data
MATERIAL_BATCH = "batch"  # Selected candidate or approved batch

class Material():
    '''
    Material defines a selected view to Root and data objects.
    
    breed="batch"   -> selection by Root.batch_id only
                       Store also request.material_type and request.state, if given;
                       else clear old session.material_type and session.state
    breed="common"  -> selection by Root.material_type and Root.state
                       Ignore and clear session.batch_id
    '''

    def __init__(self, session, request=None):
        """ Initialize Material object using session and request information.
        """
        if request is None:
            # Dummy material
            self.breed, self.m_type, self.state, self.batch_id = ("", "", "", "")
            return

        self.request_args = Material.get_request_args(session, request)
        self.breed = session.get("current_context", "")

        self.m_type = session.get("material_type")
        if "material_type" in self.request_args:
            self.m_type = self.request_args.get("material_type")
        self.state = session.get("state", "")
        if "state" in self.request_args:
            self.state = self.request_args.get("state")
        self.batch_id = session.get("batch_id")
        if "batch_id" in self.request_args:
            self.batch_id = self.request_args.get("batch_id")

        # print(f"#Material(): {self.get_current()} REQUEST values={self.request_args}")
        return

    def __str__(self):
        return f"({self.breed}/{self.state}/{self.m_type}/{self.batch_id})"
    
    def to_display(self):
        """ Return current material and batch choice for display. """
        from bl.batch.root import State
        try:
            m = self.m_type or "Unknown material"
            # if m == "Place": m = "Places"
            # print(f"#bl.material.Material.to_display: "
            #       f'[{self.breed!r}, {self.state!r}, {m!r}, {self.batch_id!r}]')
            if self.state is None:
                return f"{ _(m) }: {self.batch_id}"
            elif self.state == State.ROOT_ACCEPTED:
                batch = self.batch_id if self.batch_id else ""
                return f"{ _(m) } / { _('Approved Isotammi tree') } {batch}"
            else:
                return f"{ _(m) } / { _(self.state) } {self.batch_id}"
        except Exception as e:
            return "Error: " + str(e)

    def get_current(self):
        """Return current material tuple [breed, state, material_type, batch_id].
        """
        return [
            self.breed,     # "batch" / "common"
            self.state,     # Root.state "Candidate", ... "Accepted"
            self.m_type,    # "Family Tree", ...
            self.batch_id   # Root.batch_id
        ]

    #----- Static methods
    
    @staticmethod
    def set_session_material(session, request, breed, username):
        """
        Save material selection from request to session.

        When the material is changed, also reset the context scope.

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
        from bl.batch.root import State, Root
        def reset_scope(session, params):
            """ Check, if any of session [state, material_type, batch_id] is changed """
            if (
                params[0] != session["state"] or \
                params[1] != session["material_type"] or \
                params[2] != session["batch_id"]
                ):
                print ("#Material.set_session_material.reset_scope:")
                print(f' - session     from {params}\n'
                      f' - session to batch {[session["state"], session["material_type"], session["batch_id"]]}')
                for scope in [a for a in session.keys() if a.endswith("_scope")]:
                    print(f" - Cleared: {scope}")
                    session.pop(scope)
            else:
                print ("#Material.set_session_material: No scope change")
            return

        args = Material.get_request_args(session, request)
        print(f"#Material.set_session_material/{request.endpoint}: request {args}")
        old_params = [session.get("state"), session.get("material_type"), session.get("batch_id")]

        session["breed"] = breed
        #session["set_scope"] = True  # Reset material and scope
        session["current_context"] = breed
        # Remove obsolete var: #TODO Remove after next production version at 2022
        if "material" in session:
            print(f'Removed obsolete session.material={session.pop("material")!r}')

        if breed == MATERIAL_BATCH:
            # request args:  {'batch_id': '2021-10-09.001'}
            if "state" in args:
                session["state"] = args.get("state")
            if "material_type" in args:
                session["material_type"] = args.get("material_type")
            if "batch_id" in args:
                session["batch_id"] = args.get("batch_id")

            # Missing material type or state?
            # - optional args: {'material_type': 'Family Tree', 'state': 'Candidate'}
            if session["batch_id"] and (
                not session.get("material_type") or not session.get("state")
            ):
                # Get from database
                root = Root.get_batch(username, session["batch_id"])
                session["material_type"] = root.material_type
                session["state"] = root.state
            reset_scope(session, old_params)

            print(
                "Material.select_material: The material is single batch "
                f'{Material.get_from_session(session)})'
            )
            # if not ("batch_id" in session and session["batch_id"]):
            #     return {"status": Status.ERROR, "statustext": _("Missing batch id")}
            return {"status": Status.OK, "args": args}

        elif breed == MATERIAL_COMMON:
            # request args: {'state': 'Candidate', 'material_type': 'Place Data', 'batch_id': '2021-10-26.001'}
            session["state"] = args.get("state", State.ROOT_DEFAULT_STATE)
            session["material_type"] = args.get("material_type")
            session["batch_id"] = None
            reset_scope(session, old_params)

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
            return {"status": Status.OK, "args": args}

        return {
            "status": Status.ERROR,
            "statustext": _("Undefined breed of materials"),
            "args": args,
        }

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
