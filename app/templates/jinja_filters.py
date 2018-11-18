#!/usr/bin/python
'''
  Filter methods for _Jinja2 filters
  Methods are called from stk_server.setups()

Created on 4.1.2018
@author: jm
'''
from urllib.parse import urlparse

def translate(term, var_name, lang="fi"):
    """ Given term is translated depending of var_name name.
        No language selection yet.
        
        'nt'   = Name types
        'evt'  = Event types
        'role' = Event role
        'lt'   = Location types
        'lt_in' = Location types, inessive form
        'notet' = note type
        #'urlt' = web page type
        'rept' = repository types
        'medium' = media types
    """
#     print("# {}[{}]".format(var_name, term))
    if var_name == "nt":
        # Name types
        tabl = {
            "Birth Name": "syntymänimi",
            "Also Known As": "tunnettu myös",
            "Married Name": "avionimi",
            "Unknown": "määrittämätön",
            "Aateloitu nimi": "Aateloitu nimi",
            "Aatelointinimi" : "Aatelointinimi"
#             "Also Known As": "tunnettu myös",
#             "Birth Name": "syntymänimi",
#             "Married Name": "avionimi"
        }
    if var_name == "evt":
        # Event types    
        tabl = {
            "Birth": "syntymä",
            "Death": "kuolema",
            "Occupation": "ammatti",
            "Baptism": "kaste",
            "Burial": "hautaus",
            "Marriage": "avioliitto",
            "Residence": "asuinpaikka",
            "Cause Of Death": "kuolinsyy",
            "Luottamustoimi": "luottamustoimi",
            "Lähtömuutto": "lähtömuutto",
            "Tulomuutto": "tulomuutto",
            "Graduation": "valmistuminen",
            "Degree": "oppiarvo",
            "Ordination": "palkitseminen",
            "Property": "omaisuus",
            "Education": "koulutus",
            "Sota": "sota",
            "Confirmation": "ripille pääsy",
            "First Communion": "ensimmäinen ehtoollinen",
            "Military Service": "asepalvelus",
            "Käräjöinti": "käräjöinti",
            "Christening": "kristillinen kaste",
            "Marriage Banns": "kuulutus avioliittoon",
            "Retirement": "eläkkeelle siirtyminen",
            "Nobility Title": "aatelointi",
            "Engagement": "kihlajaiset",
            "Immigration": "maahanmuutto",
            "Ehtoollinen": "ehtoollinen"      
#             "Residence": "asuinpaikka",
#             "Occupation": "ammatti",
#             "Birth": "syntymä",
#             "Death": "kuolema",
#             "Luottamustoimi": "luottamustoimi",
#             "Graduation": "valmistuminen",
#             "Marriage": "avioliitto",
#             "Baptism": "kaste",
#             "Burial": "hautaus",
#             "Cause Of Death": "kuolinsyy",
#             "Education": "koulutus",
#             "Degree": "oppiarvo",
#             "Christening": "kristillinen kaste",
#             "Military Service": "asepalvelus",
#             "Confirmation": "ripille pääsy",
#             "Ordination": "palkitseminen",
#             "Sota": "sota",
    }
    elif var_name == "role":
        # Name types
        tabl = {
            "Primary": "pääosallisena",
            "Family": "perheenä",
            "Kummi": "kummina",
            "Perillinen": "perillisenä",
            "kummi": "kummina",
            "Clergy": "pappina",
            "Osallinen": "osallisena",
            "Ostaja": "ostajana",
            "Perinnönjättäjä": "perinnönjättäjänä",
            "Vihkijä": "vihkijänä",
            "Pääosallinen": "pääosallisena",
            "Edunsaaja": "edunsaajana",
            "Myyjä": "myyjänä",
            "Unknown": "määräämätön"
#             "Kummi": "kummina",
#             "Clergy": "pappina",
        }
    elif var_name == "conf":
        # Confidence levels
        tabl = {
            "0":"erittäin matala",
            "1":"alhainen",
            "2":"normaali",
            "3":"korkea",
            "4":"erittäin korkea"
            }
    elif var_name == "conf_star":
        # Confidence level symbols oo, o, *, **, ***
        tabl = {
            "0":"oo",   # fa-exclamation-circle [&#xf06a;]
            "1":"o",
            "2":"*",    # fa-star [&#xf005;]
            "3":"**",
            "4":"***"
            }
    elif var_name == "notet":
        # Note types
        tabl = {
            "Link":"ks.",
            "Cause Of Death":"kuolinsyy",
            "Citation":"viite",
            "Event Note":"tapahtuma",
            "Source Note":"lähde",
            "Person Note":"henkilö",
            "Place Note":"paikka",
            "Research":"tutkimus",
            "Name Note":"nimitieto",
            "To Do":"tehtävä",
            "Family Note":"perhe",
            "Repository Note":"arkisto",
            "Media Reference Note":"mediaviite",
            "Media Note":"media",
            "General":"yleistä",
            "Html code":"html-koodi",
            "Citation":"lähteen lisätieto",
            "Event Note":"tapahtuman lisätieto",
            "Family Note":"perheen lisätieto",
            "Name Note":"nimen lisätieto",
            "Person Note":"henkilön lisätieto",
            "Place Note":"paikan lisätieto",
            "Repository Note":"arkiston lisätieto",
            "Source Note":"lähteen lisätieto",
            "To Do":"työlistalla"
            }
    elif var_name == "rept":
        # Repository types
        tabl = {
            "Album":"albumi",
            "Archive":"arkisto",
            "Collection":"kokoelma",
            "Library":"kirjasto",
            "Unknown":"tuntematon",
            "Web site":"verkkopalvelu"
            }
    elif var_name == "medium":
        # Madium types
        tabl = {
            "Asiakirja":"asiakirja",
            "Book":"kirja",
            "Electronic":"sähköinen",
            "Newspaper":"lehti",
            "Unknown":"tuntematon",
            }
    elif var_name == "lt":
        # Location types
        tabl = {
            "Alus": "alus",
            "Borough": "aluehallintoyksikkö",
            "Building": "rakennus tai torppa",  #"rakennus",
            "City": "paikkakunta",              # "kaupunki",
            "Country": "maa",
            "District": "lääni",
            "Farm": "tila",
            "Hamlet": "talo",
            "Hautausmaa": "hautausmaa",
            "Kappeliseurakunta": "kappeliseurakunta",
            "Kartano": "kartano",
            "Kuntakeskus": "kuntakeskus",
            "Kortteli": "kortteli",
            "Linnoitus": "linnoitus",
            "Locality": "kulmakunta",
            "Organisaatio": "organisaatio",
            "Parish": "seurakunta",
            "Region": "alue",
            "State": "valtio",
            "Tila": "tila",
            "Tontti": "tontti",
            "Torppa": "torppa",
            "Town": "kaupunki",
            "Village": "kylä",
            "srk": "seurakunta"
        }
    elif var_name == "lt_in":
        # Location types, inessive
        tabl = {
            "Alus": "aluksessa",
            "Borough": "aluehallintoyksikössä",
            "Building": "rakennuksessa tai torpassa",   #"rakennuksessa",
            "City": "paikassa",                         # "kaupungissa",
            "Country": "maassa",
            "District": "läänissä",
            "Farm": "tilalla",
            "Hamlet": "talossa",
            "Hautausmaa": "hautausmaalla",
            "Kappeliseurakunta": "kappeliseurakunnassa",
            "Kartano": "kartanossa",
            "Kuntakeskus": "kuntakeskuksessa",
            "Linnoitus": "linnoituksessa",
            "Locality": "kulmakuntannassa",
            "Organisaatio": "organisaatiossa",
            "Parish": "seurakunnassa",
            "Region": "alueella",
            "State": "valtiossa",
            "Tontti": "tontilla",
            "Village": "kylässä",
            "srk": "seurakunnassa"
        }
        try:    
            return tabl[term]
        except:
            return term + ":ssa"

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
