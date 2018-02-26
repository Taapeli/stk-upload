#!/usr/bin/python
'''
  Filter methods for _Jinja2 filters
  Methods are called from stk_server.setups()

Created on 4.1.2018
@author: jm
'''

def translate(term, var_name, lang="fi"):
    """ Given term is translated depending of var_name name.
        No language selection yet.
        
        'nt'   = Name types
        'evt'  = Event types
        'role' = Event role
        'lt'   = Location types
        'lt_in' = Location types, inessive form
        'notet' = note type
        'urlt' = web page type
        'rept' = repository types
        'medium' = media types
    """
#     print("# {}[{}]".format(var_name, term))
    if var_name == "nt":
        # Name types
        tabl = {
            "Also Known As": "tunnettu myös",
            "Birth Name": "syntymänimi",
            "Married Name": "avionimi"
        }
    if var_name == "evt":
        # Event types    
        tabl = {
            "Residence": "asuinpaikka",
            "Occupation": "ammatti",
            "Birth": "syntymä",
            "Death": "kuolema",
            "Luottamustoimi": "luottamustoimi",
            "Graduation": "valmistuminen",
            "Marriage": "avioliitto",
            "Baptism": "kaste",
            "Burial": "hautaus",
            "Cause Of Death": "kuolinsyy",
            "Education": "koulutus",
            "Degree": "oppiarvo",
            "Christening": "kristillinen kaste",
            "Military Service": "asepalvelus",
            "Confirmation": "ripille pääsy",
            "Ordination": "palkitseminen",
            "Sota": "sota"
        }
    elif var_name == "role":
        # Name types
        tabl = {
            "Kummi": "kummina",
            "Clergy": "pappina"
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
            "Citation":"viitteen lisätieto",
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
            "Linnoitus": "linnoitus",
            "Locality": "kulmakunta",
            "Organisaatio": "organisaatio",
            "Parish": "seurakunta",
            "Region": "alue",
            "State": "valtio",
            "Tontti": "tontti",
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

    try:
        return tabl[term]
    except:
        return term + '?'