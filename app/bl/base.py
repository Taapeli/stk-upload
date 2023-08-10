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
#import uuid
import json
import traceback
from datetime import datetime
#import base32_lib as base32

# Privacy rule: how many years after death
PRIVACY_LIMIT = 0

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
    Class representing Neo4j Node type objects.
    """
    STR_DELIM = "⁋" # Used for storing a string array to a staring

    def __init__(self, uniq_id:int=None):
        """
        Constructor.

        Optional uniq_id may be database key (int).
        """
        #self.uuid = None 
        self.uniq_id = uniq_id  # Neo4j object id
        self.change = 0  # Object change time
        self.id = ""  # Gedcom object id like "I1234"
        self.handle = ""  # Gramps handle (?)

        self.state = None  # Object state in process path
        # TODO Define constants for values:
        #     candicate, audit_requested, auditing, accepted,
        #     mergeing, common, rejected
        self.iid = None  # Containing
        # - object type id ("H" = Human person etc.)
        # - running number in Crockford Base 32 format
        # - ISO 7064 checksum (2 digits)

        # if uniq_id:
        #     if isinstance(uniq_id, int):
        #         self.uniq_id = uniq_id
        #     else:
        #         self.uuid = uniq_id

    def __str__(self):
        #uuid = self.uuid if self.uuid else "-"
        return f'(NodeObject {self.iid}/{self.uniq_id}/{self.id} date {self.dates})"'

    def timestamp_str(self):
        """ My timestamp to display format. """
        if hasattr(self, "timestamp") and self.timestamp:
            t = float(self.timestamp) / 1000.0
            return datetime.fromtimestamp(t).strftime("%d.%m.%Y %H:%M")
        else:
            return ""


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

    # @staticmethod
    # def split_with_hyphen(id_str): # -> pe.neo4j.util.IsotammiId.get_one.format_iid
    #     """Inserts a hyphen into the id string."""
    #     """Examples: H-1, H-1234, H1-2345, H1234-5678."""
    #
    #     return id_str[:max(1, len(id_str)-4)] + "-" + id_str[max(1, len(id_str)-4):]

    def change_str(self):
        """ Display change time like '28.03.2020 17:34:58'. """
        try:
            return datetime.fromtimestamp(self.change).strftime("%d.%m.%Y %H:%M:%S")
        except TypeError:
            return ""

    def _json_encode(self):
        """Creates a dictionary of class parameters, if JSON serializable.

        For non serializable classes, define your own _json_encode method.
        Called by `json.dumps(my_stk_object, cls=StkEncoder)`
        """
        return self.__dict__

    def extra_attrs(self):
        """ Return Gramps object attributes from xml as a list of parameters
            to be saved to db.

            Input:  obj.attr__dict a pre-defined dictionary
                                  created by xml_dom_handler.DOM_handler._extract_base 
            Output: obj.attr_<key> = <values_string> for each dictionary items

            The values are joined using STR_DELIM symbol as separator. String also
            starts with 

            Example: 
            - from  obj.attr__dict = {'Id Code': 'malli',
                                      "Copyright":"Helmet"
                                      "Copyright":"Kaupunginkirjasto"} 
            - to    {"attr_id_code": ["malli"],
                     "attr_copyright": ["Helmet", "Kaupunginkirjasto"]}
        """
        dl = {}
        ret = {}
        if hasattr(self, "attr__dict") and isinstance(self.attr__dict, dict):
            for key, value in self.attr__dict.items():
                keyvar = "attr_" + "".join([c if c.isalnum() else "_" for c in key]).lower()
                if keyvar in dl.keys():
                    dl[keyvar].append(value)
                else:
                    dl[keyvar] = [value]
            for keyvar in dl.keys():
                values = dl[keyvar]
                ret[keyvar] = self.STR_DELIM + self.STR_DELIM.join(values) + self.STR_DELIM
                print(f"# Attribute {type(self).__name__}({self.id}).{keyvar} = {ret[keyvar]}")
        return ret


class IsotammiException(BaseException):
    def __init__(self, msg, **kwargs):
        Exception.__init__(self, msg)
        self.kwargs = kwargs
        