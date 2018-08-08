#!/usr/bin/env python3
"""
Korjaa Sukujutut-ohjelman tulostaman gedcomin yleisimpiä virheitä

30. kesäkuuta 2018 klo 20.38 <pekka.valta@kolumbus.fi> kirjoitti:

    Olipa hyvä pläjäys, kiitos Kari. Palautetta muilta, please.

    Olisiko mahdollista lisätä kokonaisuuteen uusi muunnos? Muistanette, että olen korjaillut gedcomien rakennevirheitä Dietrich Hesmerin Conversion-ohjelmalla. Virheet ovat pahimmillaan Sukujuttujen gedcomissa, Grampsin sisäänluku on isoissa ongelmissa ja tietoja katoaa. Tein Ahosen Liisalle Conversion-ohjelmalla ajettavan korjauspaketin, joka eliminoi SJ:n virheet. Kun SJ on  luultavasti sukututkijoiden yleisin ohjelma ja kun Hesmerin ajoa ei saada itsepalveluksi oppimiskynnyksen vuoksi, niin saisiko palvelinohjelmaamme testin, onko gedcomin tuottanut SJ ja tarjota SJ-muunnosta, johon olisi koodattu alla olevat säännöt (tärkein on group 2.1. säännöt).

    Pekka

    ********

    The processing for every record will be performed in the following sequence

    Group: -
       Coding:  original = ANSI -> UTF-8
    Group: 1.1
       Lines with nbr. and missing tag insert tag "_DUMMY"
       Modify lines without nbr. + tag: Concatenate to previous line
       Concatenate CONC to previous line
    Group: 1.2
          Delete orphan records Consolidate multiple identical records
    Group: 2.1
       Delete line blocks ending with ...:
         "1 NOTE"
       Delete line block with text check ...:
         "1 EVEN"
       Delete lines starting with ...:
         "3 SOUR"
         "2 GIVN"
         "2 SURN"
         "3 REFN"
         "1 STAT"
         "3 NOTE"
       Delete lines ending with ...:
         "1 NOTE"
    Group: 2.2
       Delete empty CONC/CONT lines
       Delete spaces at line end
       Delete multiple spaces
       Delete empty DATE + DATE ? lines
       Delete multiple identical lines
    Group: 3.3
       Date BET YYYY AND Y > BET YYYY AND YYYY
       Correct missing year in date range
    Group: 5.1
       "Move text":
         "1 NOTE %1#2 SOUR %2" -> "1 NOTE %1"
         "1 ADDR %1" -> "1 ADDR#2 ADR1 %1"
         "1 EVEN#2 TYPE Ei_julkaista#2 PLAC %1" -> "1 EVEN#2 TYPE Ei_julkaista#2 NOTE %1"
         "1 EMIG" -> "1 RESI"
         "1 EVEN#2 TYPE Kummit#2 PLAC %1" -> "1 EVEN#2 TYPE Kummit#2 NOTE Description: %1"
         "1 EVEN#2 TYPE Tutkijan omat#2 PLAC %1" -> "1 EVEN#2 TYPE Tutkijan omat#2 NOTE %1"
         "1 EVEN#2 TYPE Kolmonen" -> "1 NOTE Kolmonen"
         "1 EVEN#2 TYPE Kaksonen" -> "1 NOTE Kaksonen"

"""

version = "1.0"

ids = set()

def add_args(parser):
    parser.add_argument("--testiparametri")

def initialize(run_args):
    pass

def phase1(run_args, gedline):
    return
    if gedline.path.endswith(".BIRT.PLAC") and gedline.value.startswith("(kastettu)"):
        # @id@.BIRT.PLACE (kastettu) xxx
        parts = gedline.path.split(".")
        indi_id = parts[0]
        ids.add(indi_id)

def phase2(run_args):
    pass

def phase3(run_args, gedline,f):
    if gedline.line.strip() == "": return
    if gedline.line.strip() == "1 NOTE": return
    gedline.emit(f)


