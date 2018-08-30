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

version = "1.0"
doclink = "http://taapeli.referata.com/wiki/Gedcom-Kasteet-ohjelma"

ids = set()

def add_args(parser):
    parser.add_argument("--testiparametri")

def initialize(run_args):
    pass

def phase1(run_args, gedline):
    if gedline.path.endswith(".BIRT.PLAC") and gedline.value.startswith("(kastettu)"):
        # @id@.BIRT.PLACE (kastettu) xxx
        parts = gedline.path.split(".")
        indi_id = parts[0]
        ids.add(indi_id)

def phase2(run_args):
    pass

def phase3(run_args, gedline,f):
    parts = gedline.path.split(".")
    indi_id = parts[0]
    if indi_id in ids:
        if gedline.tag == "BIRT": gedline.tag = "CHR"
        if gedline.tag == "PLAC" and gedline.value.startswith("(kastettu)"): 
            gedline.value = " ".join(gedline.value.split()[1:])
    gedline.emit(f)


