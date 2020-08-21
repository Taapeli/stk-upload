#!/usr/bin/python
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
        print(f"WARNING: templates.jinja_filters.translate: missing term={term}, var_name={var_name}")
        return "~"
    if var_name == "nt":
        # Name types
        tabl = {
            "Birth Name": _("Birth Name"), #"syntymänimi"
            "Also Known As": _("Also Known As"), #"tunnettu myös"
            "Married Name": _("Married Name"), #"avionimi"
            "Unknown": _("Unknown type"), #"määrittämätön"
            "Aateloitu nimi": _("Aateloitu nimi"), #"Aateloitu nimi"
            "Aatelointinimi" : _("Aatelointinimi ") #"Aatelointinimi"
        }
    elif var_name == "evt":
        # Event types    
        tabl = {
            "Birth": _("Birth"), #"syntymä"
            "Death": _("Death"), #"kuolema"
            "Occupation": _("Occupation"), #"ammatti"
            "Baptism": _("Baptism"), #"kaste"
            "Burial": _("Burial"), #"hautaus"
            "Marriage": _("Marriage"), #"avioliitto"
            "Divorce": _("Divorce"), #"avioero"
            "Residence": _("Residence"), #"asuinpaikka"
            "Cause Of Death": _("Cause Of Death"), #"kuolinsyy"
            "Luottamustoimi": _("Luottamustoimi"), #"luottamustoimi"
            "Lähtömuutto": _("Moved out"), #"lähtömuutto"
            "Tulomuutto": _("Moved to"), #"tulomuutto"
            "Graduation": _("Graduation"), #"valmistuminen"
            "Degree": _("Degree"), #"oppiarvo"
            "Ordination": _("Ordination"), #"palkitseminen"
            "Property": _("Property"), #"omaisuus"
            "Education": _("Education"), #"koulutus"
            "Sota": _("War"), #"sota"
            "Confirmation": _("Confirmation"), #"ripille pääsy"
            "First Communion": _("First Communion"), #"ensimmäinen ehtoollinen"
            "Military Service": _("Military Service"), #"asepalvelus"
            "Käräjöinti": _("Käräjöinti"), #"käräjöinti"
            "Christening": _("Christening"), #"kristillinen kaste"
            "Marriage Banns": _("Marriage Banns"), #"kuulutus avioliittoon"
            "Retirement": _("Retirement"), #"eläkkeelle siirtyminen"
            "Nobility Title": _("Nobility Title"), #"aatelointi"
            "Engagement": _("Engagement"), #"kihlajaiset"
            "Immigration": _("Immigration"), #"maahanmuutto"
            "Ehtoollinen": _("Holy Communion"), #"ehtoollinen"      
            "Family": _("Family") #"ehtoollinen"      
    }
    elif var_name == "role":
        # Event role types or member role in family
        tabl = {
            "Primary": _("Primary"), #"pääosallisena"
            "Family": _("Family"), #"perheenä"
            "Kummi": _("Kummi"), #"kummina"
            "Perillinen": _("Perillinen"), #"perillisenä"
            "kummi": _("kummi"), #"kummina"
            "Clergy": _("Clergy"), #"pappina"
            "Osallinen": _("Osallinen"), #"osallisena"
            "Ostaja": _("Ostaja"), #"ostajana"
            "Perinnönjättäjä": _("Perinnönjättäjä"), #"perinnönjättäjänä"
            "Vihkijä": _("Vihkijä"), #"vihkijänä"
            "Pääosallinen": _("Pääosallinen"), #"pääosallisena"
            "Edunsaaja": _("Edunsaaja"), #"edunsaajana"
            "Myyjä": _("Myyjä"), #"myyjänä"
            "father": _("Father"), 
            "mother": _("Mother"),
            "man": _("Husband"), 
            "wife": _("Wife"),
            "child": _("Child"),     # Role as family member
            "parent": _("Spouse"),   # Role as family member
            "as_child": _("as a child"),   # Role as family member
            "as_parent": _("as spouse"), # Role as family member
            "Unknown": _("Unknown role") #"määräämätön"
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
#     elif var_name == "conf_star":
#         # Confidence level symbols oo, o, *, **, ***
#         tabl = {
#             "0": "oo",   # fa-exclamation-circle [&#xf06a;]
#             "1": "o",
#             "2": "*",    # fa-star [&#xf005;]
#             "3": "**",
#             "4": "***"
#             }
    elif var_name == "notet":
        # Note types
        tabl = {
            "Link": _("See"), #"ks."
            "Cause Of Death": _("Cause Of Death"), #"kuolinsyy"
            "Citation": _("Citation"), #"viite"
            "Event Note": _("Event Note"), #"tapahtuma"
            "Source Note": _("Source Note"), #"lähde"
            "Person Note": _("Person Note"), #"henkilö"
            "Place Note": _("Place Note"), #"paikka"
            "Research": _("Research"), #"tutkimus"
            "Name Note": _("Name Note"), #"nimitieto"
            "To Do": _("To Do"), #"tehtävä/työlistalla"
            "Family Note": _("Family Note"), #"perhe"
            "Repository Note": _("Repository Note"), #"arkisto"
            "Media Reference Note": _("Media Reference Note"), #"mediaviite"
            "Media Note": _("Media Note"), #"media"
            "General": _("General"), #"yleistä"
            "Html code": _("Html code"), #"html-koodi"
            "Citation": _("Citation"), #"lähteen lisätieto"
            "Event Note": _("Event Note"), #"tapahtuman lisätieto"
            "Family Note": _("Family Note"), #"perheen lisätieto"
            "Name Note": _("Name Note"), #"nimen lisätieto"
            "Person Note": _("Person Note"), #"henkilön lisätieto"
            "Place Note": _("Place Note"), #"paikan lisätieto"
            "Repository Note": _("Repository Note"), #"arkiston lisätieto"
            "Source Note": _("Source Note"), #"lähteen lisätieto"
            "Web Search": _("Web Search"), #"Verkosta löytynyt"
            "Web Home": _("Home Page") #"Kotisivu"
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
            "Newspaper": _("Newspaper"), #"lehti"
            'Magazine': _('Magazine'),  #"aikakauslehti"
            'Tombstone': _('Tombstone'), #'hautakivi'
            'Manuscript': _('Manuscript'), #'käsikirjoitus'
            'Photo': _('Photo'),
            "Unknown": _("Unknown"), #"tuntematon"
            }
    elif var_name == "lt":
        # Location types
        tabl = {
            "Alus": _("Vessel"), #"alus"
            "Borough": _("Borough"), #"aluehallintoyksikkö"
            "Building": _("Building"), #"rakennus tai torppa"
            "City": _("City"), #"paikkakunta"
            "Country": _("Country"), #"maa"
            "District": _("District"), #"lääni"
            "Farm": _("Farm"), #"tila"
            "Hamlet": _("Hamlet"), #"talo"
            "Hautausmaa": _("Cemetery"), #"hautausmaa"
            "Kappeliseurakunta": _("Kappeliseurakunta"), #"kappeliseurakunta"
            "Kartano": _("Mansion"), #"kartano"
            "Kuntakeskus": _("Kuntakeskus"), #"kuntakeskus"
            "Kortteli": _("Kortteli"), #"kortteli"
            "Linnoitus": _("Fortress"), #"linnoitus"
            "Locality": _("Locality"), #"kulmakunta"
            "Organisaatio": _("Organisation"), #"organisaatio"
            "Parish": _("Parish"), #"seurakunta"
            "Region": _("Region"), #"alue"
            "State": _("State"), #"valtio"
            "Tila": _("Farm"), #"tila"
            "Tontti": _("Tontti"), #"tontti"
            "Torppa": _("Torppa"), #"torppa"
            "Town": _("Town"), #"kaupunki"
            "Village": _("Village"), #"kylä"
            "srk": _("Parish") #"seurakunta"
        }
    elif var_name == "lt_in":
        # Location types, inessive
        tabl = {
            "Alus": _("on vessel"), #"aluksessa"
            "Borough": _("in the borough of"), #"aluehallintoyksikössä"
            "Building": _("in the building of"), #"rakennuksessa tai torpassa"
            "City": _("in the City"), #"paikassa"
            "Country": _("in the country of"), #"maassa"
            "District": _("in the district of"), #"läänissä"
            "Farm": _("in the farm of"), #"tilalla"
            "Hamlet": _("in the hamlet of"), #"talossa"
            "Hautausmaa": _("Hautausmaalla"), #"hautausmaalla"
            "Kappeliseurakunta": _("Kappeliseurakunnassa"), #"kappeliseurakunnassa"
            "Kartano": _("in the mansion of"), #"kartanossa"
            "Kuntakeskus": _("Kuntakeskuksessa"), #"kuntakeskuksessa"
            "Linnoitus": _("in the fortress"), #"linnoituksessa"
            "Locality": _("at locality of"), #"kulmakuntannassa"
            "Organisaatio": _("in the organisation of"), #"organisaatiossa"
            "Parish": _("in the parish"), #"seurakunnassa"
            "Region": _("in the region"), #"alueella"
            "State": _("Sn the state"), #"valtiossa"
            "Tontti": _("Tontilla"), #"tontilla"
            "Village": _("in the village of"), #"kylässä"
            "srk": _("in the parish of") #"seurakunnassa"
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
