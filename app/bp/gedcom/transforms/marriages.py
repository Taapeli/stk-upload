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

version = "2.0"
#doclink = "http://wiki.isotammi.net/wiki/Gedcom:Gedcom-Marriages-ohjelma"
doclinks = {
    'fi': "http://wiki.isotammi.net/wiki/Gedcom:Gedcom-Marriages-ohjelma",
    'sv': "http://wiki.isotammi.net/wiki/Gedcom_verktyg_Marriages",
}    

from flask_babelex import _
name = _("Marriages") 
docline = _('Splitting of data in PLAC of MARR')

from .. import transformer
from .. transformer import Item

from collections import defaultdict 
import re
import logging


def add_args(parser):
    pass


def initialize(options):
    return Marriages()


class Marriages(transformer.Transformation):
    twophases = True
    
    def __init__(self):
        self.resi = defaultdict(list)  # key=@individ-id@ value=[(place,date),...]
        self.test("Pitäjä, (kylä1/kylä2)")
        self.test("Pitäjä,(kylä1/kylä2)")
        self.test("Pitäjä ,(kylä1/kylä2)")
        self.test("Pitäjä (kylä1/kylä2)")
        self.test("Pitäjä , ( kylä1 /  kylä2 )  ")
        self.test("Pitäjä , ( - /  kylä2 )  ")
        self.test("Pitäjä , ( kylä1/ - )  ")
        
    def test(self,place):
        ret = self.match(place)
        #logging.info("'{}' -> {}".format(place,ret))
        
    def match(self,place):
        m = re.match(r"([^,]+),? ?\(([^/]+)/([^/]+)\)", place)
        if not m: return False
        place1 = m.group(1).strip()
        place2 = m.group(2).strip()
        place3 = m.group(3).strip()
        if place2 == "-":
            husb_place = place1
        else:
            husb_place = place2 + ", " + place1
        if place3 == "-":
            wife_place = place1
        else:
            wife_place = place3 + ", " + place1
        return place1, husb_place, wife_place
    
    def transform(self, item, options, phase):
        # phase 1
        if phase == 1 and item.tag == "FAM":
            fam = item.xref  #  @Fxxx@
            place = ""
            date = None
            husb = None
            wife = None
            for c1 in item.children:
                if c1.tag == "MARR":
                    for c2 in c1.children:
                        if c2.tag == "PLAC":
                            place = c2.value
                            place_item = c2
                        if c2.tag == "DATE":
                            date = c2.value
                if c1.tag == "HUSB":  
                    husb = c1.value
                if c1.tag == "WIFE":  
                    wife = c1.value
            if not (husb and wife): return True
            ret = self.match(place)
            if not ret: return True
            place_item.value = ret[0]
            husb_place = ret[1]
            wife_place = ret[2]
            self.resi[husb].append((husb_place, date))
            self.resi[wife].append((wife_place, date))
            return item

        # phase 2
        if phase == 2 and item.tag == "INDI" and item.xref in self.resi:
            for place, date in self.resi[item.xref]:
                c1 = Item("1 RESI")
                c1.children.append(Item("2 TYPE marriage"))
                c1.children.append(Item("2 PLAC " + place))
                if date:
                    c1.children.append(Item("2 DATE " + date))
                item.children.append(c1)
            return item
        return True
    
