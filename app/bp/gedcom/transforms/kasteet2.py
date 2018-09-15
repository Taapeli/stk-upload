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

version = "2.0"
doclink = "http://taapeli.referata.com/wiki/Gedcom-Kasteet-ohjelma"

def add_args(parser):
    pass

def initialize(run_args):
    pass

def fixlines(lines,options):
    pass

def transform(item,options):
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

