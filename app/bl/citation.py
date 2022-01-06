"""
    Citation class for handling Citation nodes and relations and
    NodeRef class to store data of referring nodes and Source

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
"""

# blacked 25.5.2021/JMä
from sys import stderr
import logging
from bl.dates import DateRange

logger = logging.getLogger("stkserver")

from bl.base import NodeObject

class Citation(NodeObject):
    """Lähdeviittaus

    Properties:
            handle           str
            change           int
            id               esim. "C0001"
            dates            DateRange date
            page             str page description
            confidence       str confidence 0.0 - 5.0 (?)
            note_ref         int huomautuksen osoite (ent. note_handles str)
            source_handle    str handle of source   _or_
            source_id        int uniq_id of a Source object
            citators         NodeRef nodes referring this citation
    """

    def __init__(self):
        """ Creates a Citation instance """

        NodeObject.__init__(self)
        self.dates = None
        self.page = ""
        self.confidence = ""
        self.mark = ""  # citation mark display references
        self.mark_sorter = 0  # citation grouping by source variable

        self.note_handles = []  # Gramps handle
        self.source_handle = ""

        # For displaying citations in person.html
        self.source_id = None

        self.citators = []  # Lähde-sivulle
        self.note_ref = []

    def __str__(self):
        return f"{self.mark} {self.id} '{self.page}'"

