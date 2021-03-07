#!/usr/bin/python

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

'''
  Filter methods for _Jinja2 filters
  Methods are called from stk_server.setups()

Created on 4.1.2018
@author: jm
'''
from urllib.parse import urlparse
from flask_babelex import _
from models.gen.person import SEX_FEMALE, SEX_MALE, SEX_UNKOWN


def translate(term, var_name):
    """ Given term is translated depending of var_name name.
        The lang parameter is not used

        'nt'   = Name types
        'evt'  = Event types
        'role' = Event role
        'lt'   = Location types
        'lt_in' = Location types, inessive form
        'notet' = note type
        'rept' = repository types
        'medium' = media types
        'marr' = marriage types
        'child' = child relations
    """
#     print("# {}[{}]".format(var_name, term))
    if not term:
        print(f"WARNING: ui.jinja_filters.translate: missing term={term}, var_name={var_name}")
        return "~"
    if var_name == "nt":
        # Name types
        tabl = {
            "Aatelointinimi" : _("Noble Name "), #"Aatelointinimi"
            "Aateloitu nimi": _("Noble Name"), #"Aateloitu nimi"
            "Also Known As": _("Also Known As"), #"tunnettu myös"
            "Birth Name": _("Birth Name"), #"syntymänimi"
            "Married Name": _("Married Name"), #"avionimi"
            "Sotilasnimi": _("Soldier name"), #"Sotilasnimi
            "Taitelijanimi": _("Artist name"), #"Taiteilijanimi
            "Vaihdettu nimi": _("Changed name"), #"Vaihdettu nimi
            "Unknown": _("Unknown type") #"määrittämätön"
        }
    elif var_name == "evt":
        # Event types    
        tabl = {
            "Baptism": _("Baptism"), #"kaste"
            "Birth": _("Birth"), #"syntymä"
            "Burial": _("Burial"), #"hautaus"
            "Cause Of Death": _("Cause Of Death"), #"kuolinsyy"
            "Christening": _("Christening"), #"kristillinen kaste"
            "Confirmation": _("Confirmation"), #"ripille pääsy"
            "Death": _("Death"), #"kuolema"
            "Degree": _("Degree"), #"oppiarvo"
            "Divorce": _("Divorce"), #"avioero"
            "Education": _("Education"), #"koulutus"
            "Ehtoollinen": _("Holy Communion"), #"ehtoollinen"      
            "Engagement": _("Engagement"), #"kihlajaiset"
#           "Family": _("Family"), #"Family event marriage etc. Not displayed"      
            "First Communion": _("First Communion"), #"ensimmäinen ehtoollinen"
            "Graduation": _("Graduation"), #"valmistuminen"
            "Immigration": _("Immigration"), #"maahanmuutto"
            "Käräjöinti": _("Käräjöinti"), #"käräjöinti"
            "Luottamustoimi": _("Luottamustoimi"), #"luottamustoimi"
            "Lähtömuutto": _("Moved out"), #"lähtömuutto"
            "Marriage Banns": _("Marriage Banns"), #"kuulutus avioliittoon"
            "Marriage": _("Marriage"), #"avioliitto"
            "Military Service": _("Military Service"), #"asepalvelus"
            "Nobility Title": _("Nobility Title"), #"aatelointi"
            "Occupation": _("Occupation"), #"ammatti"
            "Ordination": _("Ordination"), #"palkitseminen"
            "Property": _("Property"), #"omaisuus"
            "Residence": _("Residence"), #"asuinpaikka"
            "Retirement": _("Retirement"), #"eläkkeelle siirtyminen"
            "Sota": _("War"), #"sota"
            "Tulomuutto": _("Moved to") #"tulomuutto"
    }
    elif var_name == "role":
        # Event role types or member role in family
        tabl = {
            "As_child": _("as a child"),   # Role as family member
            "As_parent": _("as spouse"), # Role as family member
# Child roles does not exist?
#             "child": _("Child"),     # Role as family member
#             "Adoptio": _("Adoption"),     # Adoptiolapsi
#             "Kasvatus": _("Foster-child"), # Kasvatuslapsi
            "Clergy": _("Clergy"), #"pappi"
            "Edunsaaja": _("Edunsaaja"),
            "Family": _("Family"), #"perhe" ?
            "father": _("Father"), 
            "Kohde": _("Concerned"),
            "kummi": _("kummi"), #"kummina"
            "Kummi": _("kummi"), #"kummina"
            "man": _("Husband"), 
            "mother": _("Mother"),
            "Myyjä": _("Myyjä"), #"myyjänä"
            "Opettaja": _("Teacher"),
            "Osallinen": _("Osallinen"), #"osallisena"
            "Ostaja": _("Ostaja"), #"ostajana"
            "parent": _("Spouse"),   # Role as family member
            "Perillinen": _("Perillinen"), #"perillisenä"
            "Perinnönjättäjä": _("Perinnönjättäjä"), #"perinnönjättäjänä"
            "Primary": _("Primary"), #"pääosallisena"
            "Pääosallinen": _("Pääosallinen"), #"pääosallisena"
            "Unknown": _("Unknown"), #"määräämätön"
            "Vihkijä": _("Vihkijä"), #"vihkijänä"
            "wife": _("Wife")
        }
    elif var_name == "conf":
        # Confidence levels
        tabl = {
            "0": _("confidence 0/4"), #"erittäin matala"
            "1": _("confidence 1/4"), #"alhainen"
            "2": _("confidence 2/4"), #"normaali"
            "3": _("confidence 3/4"), #"korkea"
            "4": _("confidence 4/4")  #"erittäin korkea"
        }
    elif var_name == "notet":
        # Note types
        tabl = {
            "Cause Of Death": _("Cause Of Death"), #"kuolinsyy"
            "Citation": _("Citation"), #"viitteen lisätieto"
            "Event Note": _("Event Note"), #"tapahtuman lisätieto"
            "Family Note": _("Family Note"), #"perheen lisätieto"
            "General": _("General"), #"yleistä"
            "Html code": _("Html code"), #"html-koodi"
            "Link": _("See"), #"ks."
            "Media Note": _("Media Note"), #"media"
            "Media Reference Note": _("Media Reference Note"), #"mediaviite"
            "Name Note": _("Name Note"), #"nimen lisätieto"
            "Person Note": _("Person Note"), #"henkilön lisätieto"
            "Place Note": _("Place Note"), #"paikan lisätieto"
            "Repository Note": _("Repository Note"), #"arkiston lisätieto"
            "Research": _("Research"), #"tutkimus"
            "Source Note": _("Source Note"), #"lähteen lisätieto"
            "To Do": _("To Do"), #"tehtävä/työlistalla"
            "Transcript": _("Transcript"), #"kirjoituskopio"
            "Web Home": _("Home Page"), #"Kotisivu"
            "Web Search": _("Web Search") #"Verkosta löytynyt"
        }
    elif var_name == "rept":
        # Repository types
        tabl = {
            "Album": _("Album"), #"albumi"
            "Archive": _("Archive"), #"arkisto"
            "Collection": _("Collection"), #"kokoelma"
            "Library": _("Library"), #"kirjasto"
            "Unknown": _("Unknown type"), #"tuntematon"
            "Web site": _("Web site") #"verkkopalvelu"
        }
    elif var_name == "medium":
        # Madium types
        tabl = {
            "Asiakirja": _("Document"), #"asiakirja"
            "Book": _("Book"), #"kirja"
            "Electronic": _("Electronic"), #"sähköinen"
            "Magazine": _("Magazine"),  #"aikakauslehti"
            "Manuscript": _("Manuscript"), #"käsikirjoitus"
            "Newspaper": _("Newspaper"), #"lehti"
            "Photo": _("Photo"), #valokuva
            "Tombstone": _("Tombstone"), #"hautakivi"
            "Unknown": _("Unknown") #"tuntematon"
        }
    elif var_name == "lt":
        # Location (place) types
        tabl = {
            "Alue": _("Region"),
            "Alus": _("Vessel"),
            "Borough": _("Borough"), #"aluehallintoyksikkö"
            "Building": _("Building"), #"rakennus tai torppa"
            "City": _("City"), #"paikkakunta"
            "Country": _("Country"), #"maa"
            "Department": _("Department"), #
            "District": _("District"), #"lääni"
            "Farm": _("Farm"), #"tila"
            "Talo": _("Farm"), #"tila" !
            "Hamlet": _("Hamlet"), #"taloryhmä"
            "Hautapaikka": _("Burial Site"),
            "Hautausmaa": _("Cemetery"), #"hautausmaa"
            "Kappeliseurakunta": _("Chappel Parish"), #"kappeliseurakunta"
            "Kartano": _("Mansion"), #"kartano"
            "Katuosoite": _("Street Address"),
            "Kortteli": _("Kortteli"), #"kortteli"
            "Kuntakeskus": _("Kuntakeskus"), #"kuntakeskus"
            "Linnoitus": _("Fortress"), #"linnoitus"
            "Locality": _("Locality"), #"kulmakunta"
            "Luonnonpaikka": _("Natural Place"),
            "Municipality": _("Municipality"),
            "Oppilaitos": _("Learning Institution"), #"oppilaitos"
            "Organisaatio": _("Organisation"), #"organisaatio"
            "Parish": _("Parish"), #"seurakunta"
            "Region": _("Region"), #"alue"
            "srk": _("Parish"), #"seurakunta"
            "State": _("State"), #"valtio"
            "Tila": _("Farm"), #"tila"
            "Tontti": _("Tontti"), #"tontti"
            "Torppa": _("Torppa"), #"torppa"
            "Town": _("Town"), #"kaupunki"
            "Village": _("Village"), #"kylä"
            "Unknown": _("Unknown") #"tuntematon"
        }
    elif var_name == "lt_in":
        # Location types, inessive
        tabl = {
            "Alue": _("in the region"), #"alueella"
            "Alus": _("on vessel"), #"aluksessa"
            "Borough": _("in the borough of"), #"aluehallintoyksikössä"
            "Building": _("in the building of"), #"rakennuksessa tai torpassa"
            "City": _("in the City"), #"paikassa"
            "Country": _("in the country of"), #"maassa"
            "Department": _("in the department of"), #"
            "District": _("in the district of"), #"läänissä"
            "Farm": _("in the farm of"), #"tilalla"
            "Hamlet": _("in the hamlet of"), #"talossa"
            "Hautapaikka": _("in a burial site of"),
            "Hautausmaa": _("in the cemetery"), #"hautausmaalla"
            "Kappeliseurakunta": _("in chapel parish"), #"kappeliseurakunnassa"
            "Kartano": _("in the mansion of"), #"kartanossa"
            "Kuntakeskus": _("Kuntakeskuksessa"), #"kuntakeskuksessa"
            "Linnoitus": _("in the fortress"), #"linnoituksessa"
            "Locality": _("at locality of"), #"kulmakuntannassa"
            "Luonnonpaikka": _("in a natural place of"),
            "Municipality": _("in the municipality of"),
            "Oppilaitos": _("in the learning lnstitution"), #"oppilaitos"
            "Organisaatio": _("in the organisation of"), #"organisaatiossa"
            "Parish": _("in the parish"), #"seurakunnassa"
            "Region": _("in the region"), #"alueella"
            "srk": _("in the parish of"), #"seurakunnassa"
            "State": _("In the state"), #"valtiossa"
            "Tontti": _("Tontilla"), #"tontilla"
            "Village": _("in the village of") #"kylässä"
        }
        try:    
            return tabl[term]
        except:
            return term + ":ssa"

    elif var_name == "marr":
        # Marriage types
        tabl = {
            "Married": _("Married"),
            "Unknown": _("Unknown relation")
        }

    elif var_name == "child":
        # Child relations to family
        tabl = {
            SEX_FEMALE: _("Daughter"),
            SEX_MALE: _("Son"),
            SEX_UNKOWN: _("Child")
        }

    elif var_name == "handle":
        # Shows handle '_dd3d7f7206c3ca3408c9daf6c58' in short format '_d…f6c58'"
        if len(term) > 8:
            return term[:2] + '…' + term[-5:]
        return term
    elif var_name == "urldomain":
        # Pick domain part of url 
        return urlparse(term).hostname

    try:
        if term:
            return tabl[term]
        else:
            return ''
    except:
        return "'" + term + "'"
