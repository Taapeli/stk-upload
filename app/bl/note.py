"""
Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

Changed 13.6.2018/JMä: get_notes() result from list(str) to list(Note)

@author: jm
"""

# blacked 25.5.2021/JMä
#from sys import stderr

from bl.base import NodeObject
from pe.dataservice import DataService

class Note(NodeObject):
    """Note / Huomautus
    including eventual web link

    Properties:
            handle          str stats with '_' if comes from Gramps
            change          int timestamp from Gramps
            id              esim. "N0001"
            iid         int database key
            priv            int >0 non-public information
            type            str note type
            text            str note description
            url             str web link
    """

    def __init__(self, iid=None):
        """Creates a Note instance in memory"""
        NodeObject.__init__(self, iid)
        self.type = ""
        self.priv = None
        self.text = ""
        self.url = None

    def __str__(self):
        desc = self.text if len(self.text) < 17 else self.text[:14] + "..."
        url = "" if self.url == None else self.url
        return f"{self.id} {self.type} {desc!r} {url}"


class NoteReader(DataService):
    """
    Data reading class for Note objects. Used with free text search.
    """

    def __init__(self, service_name: str, u_context=None):
        super().__init__(service_name, u_context)

    def note_search(self, args):
        context = self.user_context
        args["use_user"] = self.use_user
        args["fw"] = context.first  # From here forward
        args["limit"] = context.count
        args["batch_id"] = context.material.batch_id
        args["material"] = context.material
        args["state"] = context.material.state
        res = self.dataservice.tx_note_search(args)
        #print(res)
        return res
    
    