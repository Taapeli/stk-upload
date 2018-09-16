#!/usr/bin/env python3

"""
Avio-PLAC:n hajoittaminen
5.11.2016 16.48 
	
Moi,
vilkaisin gedcomista, miltä näyttää avioliitto, jossa on paikan nimeen lykätty myös sulhasen ja morsiamen kotipaikat. Tämä tapahan on itse asiassa hyvin tehokas ja ainoa mahdollinen, jos sukututkimusohjelma ei tue asuinpaikka-tapahtumia. Sen voisi jopa antaa suosituksena, jos näin kirjattu tieto kyettäisiin purkamaan.

0 @F0712@ FAM
1 HUSB @I33884@
1 WIFE @I33885@
1 MARR
2 DATE 1 APR 1839
2 PLAC Pielavesi, (Säviä 8/Taipale 10)
2 ADDR
3 CTRY Pielavesi, (Säviä 8/Taipale 10)

Grampsista varmistin, että henkilöiden ID:t olivat samat kuin gedcomissa.

Nyt seuraa tiiseri teille ohjelmointitaitoisille:

Päättelisin Grampsin (uuden) erillistyökalun logiikaksi sen, että sen jälkeen kun gedcom on luettu Grampsiin, luetaan työkalulla gedcomia uudelleen ja kun MARR-tietoryhmässä kohdataan PLAC teksti a (b/c),
muodostetaan ja päivitetään kantaan
- henkilölle HUSB RESI b,a , jossa DATE=FAM DATE date
- henkilölle WIFE RESI c,a , jossa DATE=FAM DATE date
- MARR PLAC < a

Jos oikein hienostelisi, niin ottaisi huomioon lisätapaukset, jossa on kylän lisäksi talokin
(Säviä Vuorimäki/Sulkavanjärvi Petäjämäki)

Mallia sorsapohjaksi löytynee Data Entry Grampletista, jonka kautta voi syöttää syntymä/kuolintapahtumia.


"""
from flask_babelex import _
docline = _("Avio-PLAC:n hajoittaminen")

version = "2.0"
doclink = "http://taapeli.referata.com/wiki/Gedcom-Marriages-ohjelma"

from collections import defaultdict 
import re

from transformer import Item

class FamInfo:
    husb = None
    wife = None
    date = None
    place = ""
   
class Place:
    def __init__(self,place,date):
        self.place = place
        self.date = date
    def __repr__(self):
        pass

twophases = True

def add_args(parser):
    pass

def initialize(options):
    options.resi = defaultdict(list) # key=@individ-id@ value=[(place,date),...]
    options.fams = defaultdict(FamInfo) # key=@fam@, value=FamInfo
    options.fixedfams = {} # key=@fam@ value=place

def fixlines(lines,options):
    pass

def transform(item,options):
    # phase 1
    if item.value == "FAM":
        fam = item.tag #  @Fxxx@
        faminfo = FamInfo()
        for c1 in item.children:
            if c1.tag == "MARR":
                for c2 in c1.children:
                    if c2.tag == "PLAC":
                        faminfo.place = c2.value
                        place_item = c2
                    if c2.tag == "DATE":
                        faminfo.date = c2.value
            if c1.tag == "HUSB":  
                husb = c1.value
                faminfo.husb = c1.value
            if c1.tag == "WIFE":  
                husb = c1.value
                faminfo.wife = c1.value
        m = re.match(r"([^,]+), \(([^/]+)/([^/]+)\)",faminfo.place)
        if m:
            options.fams[fam] = faminfo
            husb_place = m.group(2)+", "+m.group(1)
            wife_place = m.group(3)+", "+m.group(1)
            options.resi[faminfo.husb].append((husb_place,faminfo.date))
            options.resi[faminfo.wife].append((wife_place,faminfo.date))
            place_item.value = m.group(1)
            return item
    # phase 2
    if item.value == "INDI" and item.tag in options.resi:
        for place,date in options.resi[item.tag]:
            c1 = Item("1 RESI")
            c1.children.append(Item("2 TYPE marriage"))
            c1.children.append(Item("2 PLAC " + place))
            if date:
                c1.children.append(Item("2 DATE " + date))
            item.children.append(c1)
        return item
    return True


