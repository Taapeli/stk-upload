"""
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
"""

# blacked 25.5.2021/JMä
from bl.base import NodeObject
from bl.base import Status
from pe.dataservice import DataService


class Repository(NodeObject):
    """Repository / Arkisto.

    Properties:
        iid         int    db native key or None
        handle          str    Gramps handle
        change          int    timestamp
        id              str    esim. "R0001"
        rname           str    arkiston nimi
        type            str    arkiston tyyppi
        medium          str    from Source --> Repository relation.medium
        notes           Note[]
        
        For gramps_loader:
            note_handles[]   str lisätiedon handle
    """

    def __init__(self, iid=None):
        """ Luo uuden repository-instanssin """
        NodeObject.__init__(self, iid)
        self.type = ""
        self.rname = ""
        self.medium = ""
        self.notes = []  # contains Note instances or Note.iid values
        self.note_handles = [] # contains noterefs of Note instances

        self.sources = []  # For creating display sets (Not used??)

    def __str__(self):
        return f"{self.id} '{self.rname}' {self.medium}"



class RepositoryReader(DataService):
    """
    Data reading class for Repository objects with associated data.
    """

    def __init__(self, service_name: str, u_context=None):
        """Create a reader object with db driver and user context."""
        super().__init__(service_name, u_context)
        if u_context:
            # For reader only; writer has no context?
            self.user_context = u_context
            self.username = u_context.user
            if u_context.is_common():
                self.use_user = None
            else:
                self.use_user = u_context.user

    def get_repo_list(self):
        """Get junk of Repository objects for Repositories list."""
        context = self.user_context
        fw = context.first  # From here forward
        use_user = context.batch_user()
        args = {"user": use_user, "fw": fw, "count": context.count}
        args['material'] = context.material
        try:
            repos = self.dataservice.dr_get_repo_list_fw(args)
            # results = {'sources':sources,'status':Status.OK}

            # Update the page scope according to items really found
            if repos:
                context.update_session_scope(
                    "source_scope",
                    repos[0].rname,
                    repos[-1].rname,
                    context.count,
                    len(repos),
                )
            else:
                return {"items": [], "status": Status.NOT_FOUND}

            results = {"items": repos, "status": Status.OK}
        except Exception as e:
            results = {"status": Status.ERROR, "statustext": f"Repository list: {e}"}
        return results

    def get_repository_sources(self, iid, u_context):
        """Read the repository and referencing sources.

        Returns a dictionary, where items = Source object.
        - item.repositories Repositories
        - item.notes        Notes connected to Repository
        - item.sources      Souorce objects
        """
        use_user = self.user_context.batch_user()
        res = self.dataservice.dr_get_repository(use_user, 
                                                 u_context.material, 
                                                 iid)
        if Status.has_failed(res):
            return res
        repo = res.get("item")
        if not repo:
            res.statustext = f"no Repository with iid={iid!r}"

        return res
