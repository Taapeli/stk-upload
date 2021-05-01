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
Created on 22.8.2019

@author: jm
"""
#blacked 2021-05-01 JMä
import uuid
import json
import traceback


class Status:
    """Status code values for result dictionary.

    Result dictionary may have
    - item / items    data
    - status          enumarated code
    - statustext      error message
    etc

    example: {"items":events, "status":Status.OK}
    """

    OK = "OK"
    NOT_FOUND = "Not found"
    ERROR = "Error"
    NOT_STARTED = "Not started"
    UPDATED = "Updated"

    @staticmethod
    def has_failed(result: dict, strict=True):
        """Test, if given result dict did not succeed.

        If strict, allow only OK status, else allow any no-error status
        """
        if not isinstance(result, dict):
            traceback.print_exc()
            raise AttributeError(f"bl.base.Status.has_failed")
        st = result.get("status", "undefined")

        if st == Status.ERROR:
            return True  # Error
        if st == Status.OK:
            return False  # Ok
        if strict:
            return True  # Not found or updated etc not allowed
        else:
            return False  # Not found or updated is ok


class StkEncoder(json.JSONEncoder):
    """Returns Stk object hierarchy as a JSON string.

    Usage: json_str = StkEncoder.jsonify(stk_object_struct)
    """

    def default(self, obj):
        if hasattr(obj, "_json_encode"):
            return obj._json_encode()
        else:
            return json.JSONEncoder.default(self, obj)

    @staticmethod
    def jsonify(obj):
        """Convert dictionary with hierarchial stk objects to JSON structure."""
        return json.dumps(obj, cls=StkEncoder)


class NodeObject:
    """
    Class representing Neo4j node type objects
    """

    def __init__(self, uniq_id=None):
        """
        Constructor.

        Optional uniq_id may be uuid identifier (str) or database key (int).
        """
        self.uuid = None  # UUID
        self.uniq_id = None  # Neo4j object id
        self.change = 0  # Object change time
        self.id = ""  # Gedcom object id like "I1234"
        self.handle = ""  # Gramps handle (?)

        self.state = None  # Object state in process path
        # TODO Define constants for values:
        #     candicate, audit_request, auditing, accepted,
        #     mergeing, common, rejected
        self.isotammi_id = None  # Containing
        # - object type id ("I" = Person etc.)
        # - running number in Crockford Base 32 format
        # - ISO 7064 checksum (2 digits)
        if uniq_id:
            if isinstance(uniq_id, int):
                self.uniq_id = uniq_id
            else:
                self.uuid = uniq_id

    def __str__(self):
        uuid = self.uuid if self.uuid else "-"
        return f'(NodeObject {uuid}/{self.uniq_id}/{self.id} date {self.dates})"'

    @classmethod
    def from_node(cls, node):
        """
        Starts Transforming a db node to an undefined type object.

        Call from an inherited class, f.ex. n = Media.from_node(node)
        """
        n = cls()
        n.uniq_id = node.id
        n.id = node["id"]
        n.uuid = node["uuid"]
        if node["handle"]:
            n.handle = node["handle"]
        n.change = node["change"]
        return n

    """
        Compare 
            self.dates <op> other.dates = True?

        See also: bl.dates.DateRange.__lt__()

        - None as other.dates is always considered the 1st in order
        - None as self.dates  is always considered last in order
    """

    def __lt__(self, other):
        if self.dates:
            return self.dates < other.dates
        return True

    def __le__(self, other):
        if self.dates:
            return self.dates <= other.dates
        return True

    def __eq__(self, other):
        if self.dates:
            return self.dates == other.dates
        return False

    def __ge__(self, other):
        if self.dates:
            return self.dates >= other.dates
        return False

    def __gt__(self, other):
        if self.dates:
            return self.dates > other.dates
        return False

    def __ne__(self, other):
        if self.dates:
            return self.dates != other.dates
        return False

    @staticmethod
    def newUuid():
        """Generates a new uuid key.

        See. https://docs.python.org/3/library/uuid.html
        """
        return uuid.uuid4().hex

    def uuid_short(self):
        """ Display uuid in short form. """
        if self.uuid:
            return self.uuid[:6]
        else:
            return ""

    def change_str(self):
        """ Display change time like '28.03.2020 17:34:58'. """
        from datetime import datetime

        try:
            return datetime.fromtimestamp(self.change).strftime("%d.%m.%Y %H:%M:%S")
        except TypeError:
            return ""

    def uuid_str(self):
        """ Display uuid in short form, or show self.uniq_id is missing. """
        if self.uuid:
            return self.uuid[:6]
        else:
            return f"({self.uniq_id})"

    def _json_encode(self):
        """Creates a dictionary of class parameters, if JSON serializable.

        For non serializable classes, define your own _json_encode method.
        Called by `json.dumps(my_stk_object, cls=StkEncoder)`
        """
        return self.__dict__
