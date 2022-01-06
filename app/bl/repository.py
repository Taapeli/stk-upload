"""
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
"""

# blacked 25.5.2021/JMä
from bl.base import NodeObject
from bl.note import Note

class Repository(NodeObject):
    """Repository / Arkisto.

    Properties:
        uniq_id         int    db native key or None
        handle          str    Gramps handle
        change          int    timestamp
        id              str    esim. "R0001"
        rname           str    arkiston nimi
        type            str    arkiston tyyppi
        medium          str    from Source --> Repository relation.medium
        notes           Note[]
    """

    def __init__(self):
        """ Luo uuden repository-instanssin """
        NodeObject.__init__(self)
        self.type = ""
        self.rname = ""
        self.medium = ""
        self.notes = []  # contains Note instances or Note.uniq_id values

        self.sources = []  # For creating display sets (Not used??)

    def __str__(self):
        return f"{self.id} '{self.rname}' {self.medium}"


