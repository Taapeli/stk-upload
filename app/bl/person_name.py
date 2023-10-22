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

    Person Name class

Created on 10.9.2018

@author: jpek@iki.fi
"""
# blacked 2021-05-01 JMä
from sys import stderr
import logging

logger = logging.getLogger("stkserver")

import shareds
from bl.base import NodeObject

class Name(NodeObject):
    """Person name.

    Properties:
            type                str Name type: 'Birth name', ...
            order               int name order of Person etc. (from Gramps xml)
            firstname           str etunimi
            surname             str sukunimi
            prefix              str etuliite
            suffix              str patronyme / patronyymi
            dates               DateRange date expression
            title               str titteli, esim. Sir, Dr.
            # citation_handles[]  str gramps handles for citations
            # citation_ref[]      int uniq_ids of citation nodes
    """

    def __init__(self, givn="", surn="", pref="", suff="", dates="", titl=""):
        """ Luo uuden name-instanssin """
        self.type = ""
        self.order = None
        self.firstname = givn
        self.surname = surn
        self.prefix = pref
        self.suffix = suff
        self.dates = dates
        self.title = titl
        self.attrs = ""
        # # Set in bp.gramps.xml_dom_handler.DOM_handler.handle_people
        # self.citation_handles = []
        # # For person page
        # self.citation_ref = []

    def __str__(self):
        # Gedcom style key
        return "{} /{}/{}/{}/{}".format(
            self.title, self.firstname, self.prefix, self.surname, self.suffix
        )

    def key_surname(self):
        # Standard sort order key "Klick#Brita Helena#Jönsdotter"
        return f"{self.surname}#{self.firstname}#{self.suffix}"


    @staticmethod
    def get_people_with_same_name():
        """ Etsi kaikki henkilöt, joiden nimi on sama"""

        query = """
            MATCH (p1:Person)-[r1:NAME]->(n1:Name)
            MATCH (p2:Person)-[r2:NAME]->(n2:Name) WHERE ID(p1)<ID(p2)
                AND n2.surname = n1.surname AND n2.firstname = n1.firstname
                RETURN COLLECT ([ID(p1), p1.est_birth, p1.est_death,
                n1.firstname, n1.suffix, n1.title, n1.surname,
                ID(p2), p2.est_birth, p2.est_death,
                n2.firstname, n2.suffix, n2.title, n2.surname]) AS ids
            """.format()
        with shareds.driver.session() as session:
            return session.run(query)

    @staticmethod
    def get_clearname(uniq_id=None):  # Not used!
        """Lists all Name versions of this Person as single cleartext"""
        result = Name.get_personnames(None, uniq_id)
        names = []
        for record in result:
            # <Node id=210189 labels={'Name'}
            #    properties={'title': 'Sir', 'firstname': 'Jan Erik', 'type': 'Birth Name',
            #        'suffix': 'Jansson', 'surname': 'Mannerheim', 'order': 0}>
            node = record["name"]
            fn = node.get("firstname", "")
            vn = node.get("prefix", "")
            sn = node.get("surname", "")
            pn = node.get("suffix", "")
            ti = node.get("title", "")
            names.append("{} {} {} {} {}".format(ti, fn, pn, vn, sn))
        return " • ".join(names)

