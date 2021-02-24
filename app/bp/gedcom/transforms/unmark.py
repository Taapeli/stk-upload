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

#!/usr/bin/env python3
"""
Restores marked tags: <tag>-X -> <tag>
"""

version = "2.0"
#doclink = "http://wiki.isotammi.net/wiki/Gedcom:Gedcom-Marriages-ohjelma"

from flask_babelex import _
name = _("Unmark")
docline = _("Restores marked tags: <tag>-X -> <tag>")
doclinks = {
    'fi': "http://wiki.isotammi.net/wiki/Poista_tag_X_merkinnät", 
}    

from .. import transformer

def add_args(parser):
    pass

def initialize(options):
    return Unmark()

class Unmark(transformer.Transformation):
    def transform(self,item,options,phase):
        # phase 1
        if item.tag.endswith("-X"):
            item.tag = item.tag[0:-2]
            return item
        return True