#   Isotammi Geneological Service for combining multiple researchers' results.
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
"BIRT.PLAC (kastettu) place" -> "CHR.PLAC place"

Lähettäjä: <pekka.valta@kolumbus.fi>
Päiväys: 12. marraskuuta 2016 klo 17.26
Aihe: Kastettu paikan korjaus
Vastaanottaja: "Kujansuu, Kari" <kari.kujansuu@gmail.com>
Kopio: Juha Mäkeläinen <juha.makelainen@iki.fi>


Moi,
yhdessä gedcomissa oli runsaasti syntymäpaikkoja muodossa "(kastettu) Oulu". Ilmeisesti sukututkimusohjelma ei ole tukenut kastetiedon kunnon rekisteröintiä.

Voisitko lisätä paikkojen käsittelyyn säännön, että jos

1 BIRT
2 PLAC (kastettu) xxx

niin muutetaan muotoon

1 CHR
2 PLAC xxx

t.
Pekka

"""
from flask_babelex import _

from .. import transformer

version = "2.0"
name = _("Baptisms")

doclink = "http://wiki.isotammi.net/wiki/Gedcom:Gedcom-Kasteet-ohjelma"

def add_args(parser):
    pass

def initialize(options):
    return Kasteet()

class Kasteet(transformer.Transformation):
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
        if item.tag == "BIRT":
            for c in item.children:
                if c.tag == "PLAC" and c.value.startswith("(kastettu)"):
                    item.tag = "CHR"
                    c.value = " ".join(c.value.split()[1:])
                    return item
        return True

