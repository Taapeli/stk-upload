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
Fix Sukuohjelmisto 2004 problems
"""
from flask_babelex import _

from .. import transformer
from ..transformer import Item
from collections import defaultdict

version = "1.0"
name = _("Suku2004")
doclink = "http://wiki.isotammi.net/wiki/Gedcom:Gedcom-Suku2004-ohjelma"
docline = _('Fixes problems in Sukuohjelmisto 2004 Gedcoms')

custom_tags = {
        "_EXTR",
        "_OCCU",
        "_ROTE",
        "_SPEC",
        "_UNKN",
}

def add_args(parser):
    parser.add_argument('--change_custom_tags_to_even', action='store_true',
                        help=_('Change custom tags to EVENs'))
    parser.add_argument('--change_photo_to_obje', action='store_true',
                        help=_('Change _PHOTO tags to OBJEs'))
    parser.add_argument('--change_marr_to_marb', action='store_true',
                        help=_('Change MARR to MARB if TYPE=Kuulutus'))
    parser.add_argument('--compress_sours', action='store_true',
                        help=_('Remove empty CONT lines under SOUR'))
    parser.add_argument('--combine_plac_and_addr', action='store_true',
                        help=_('Combine PLAC and ADDR'))

def initialize(options):
    return Suku2004()


def count_tags(items):
    res = defaultdict(int)
    for item in items:
        res[item.tag] += 1
    return res


class Suku2004(transformer.Transformation):
    def transform(self,item,options,phase):
        """
        Performs a transformation for the given Gedcom "item" (i.e. "line block")
        Returns one of
        - True: keep this item without changes
        - None: remove the item
        - item: use this item as a replacement (can be the same object as input if the contents have been changed)
        - list of items ([item1,item2,...]): replace the original item with these
        
        This is called for every line in the Gedcom so that the "innermost" items are processed first.
        
        Note: If you change the item in this function but still return True, then the changes
        are applied to the Gedcom but they are not displayed with the --display-changes option.
        """
        if options.change_custom_tags_to_even:
            if item.tag in custom_tags:
                item.tag = "EVEN"
                if len(item.children) == 0: return None  #empty _UNKN tag, remove
                return item

        if options.change_photo_to_obje:
            # 1 _PHOTO
            # 2 OBJE
            # 3 FORM gif
            # 3 FILE KUVAT\Paimio_Rukkijoki.gif
            if item.tag in {"_PHOT","_PHOTO"} and item.level == 1:
                obje = item.children[0]
                item2 = Item("1 OBJE")
                for c in obje.children:
                    c2 = Item("2 {} {}".format(c.tag,c.value))
                    item2.children.append(c2)
                return item2

        if options.change_marr_to_marb:
            if item.tag == "MARR":
                if len(item.children) > 0 and (
                    item.children[0].tag == "TYPE" and
                    item.children[0].value.lower() in {"kuulutus","kuulutettu"}
                ):
                    item.tag = "MARB"
                    return item

        if options.compress_sours:
            if item.level > 0 and item.tag == "SOUR" and item.value == "" and len(item.children) > 0:
                newitems = []
                # 2 SOUR 
                # 3 CONT 
                # 3 CONT 
                # 3 CONT 
                # 3 CONT VA SSS 5, Vehkalahden syntyneet 1794-1800, sivu 196
                # 3 CONT 
                # 3 CONT VA SSS 10, Vehkalahden kuolleet 1790-1804, sivu 488
                for c in item.children:
                    if c.tag == "CONT" and c.value != "":
                        newline = "{} SOUR {}".format(item.level,c.value)
                        newitem = Item(newline)
                        newitems.append(newitem)
                    if c.tag == "CONC":
                        newitem.value += c.value
                return newitems

        if options.combine_plac_and_addr:
            if item.tag in {"BIRT","DEAT"}:
                counts = count_tags(item.children)
                if counts["PLAC"] == 1 and counts["ADDR"] == 1:
                    newitems = []
                    # 1 BIRT
                    # 2 DATE 7 MAY 1998
                    # 2 PLAC California
                    # 2 ADDR San Jose
                    # 3 CONT USA 
                    # ->
                    # 1 BIRT
                    # 2 DATE 7 MAY 1998
                    # 2 PLAC California
                    # 3 CONC , San Jose
                    # 3 CONC , USA 
    
                    for c in item.children:
                        if c.tag == "ADDR":
                            c.tag = "CONC"
                            c.value = ", " + c.value
                            c.level += 1
                            for c2 in c.children:
                                if c2.tag == "CONT":
                                    c2.tag = "CONC"
                                    c2.value = ", " + c2.value
                    return item

        return True
