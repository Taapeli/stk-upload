#!/usr/bin/env python3
"""
Tries to recognize place names and order them correctly
"""
import sys
import os

from flask_babelex import _

version = "1.0"
doclink = "http://taapeli.referata.com/wiki/Gedcom-Places-ohjelma"
docline = _("Tries to recognize place names and order them correctly")

from collections import defaultdict 

ignored_text = """
mlk
msrk
ksrk
tksrk
maalaiskunta
maaseurakunta
kaupunkiseurakunta
tuomiokirkkoseurakunta
rykmentti
pitäjä
kylä

hl
tl
ol
ul
vpl
vl

tai

de
las

"""


def add_args(parser):
    parser.add_argument('--reverse', action='store_true',
                        help=_('Reverse the order of places'))
    parser.add_argument('--add-commas', action='store_true',
                        help=_('Replace spaces with commas'))
    parser.add_argument('--ignore-lowercase', action='store_true',
                        help=_('Ignore lowercase words'))
    parser.add_argument('--ignore-digits', action='store_true',
                        help=_('Ignore numeric words'))
    parser.add_argument('--minlen', type=int, default=0,
                        help=_("Ignore words shorter that minlen"))
    parser.add_argument('--auto-order', action='store_true',
                        help=_('Try to discover correct order...'))
    parser.add_argument('--auto-combine', action='store_true',
                        help=_('Try to combine certain names...'))
    parser.add_argument('--match', type=str, action='append',
                        help=_('Only process places containing any match string'))
    parser.add_argument('--display-nonchanges', action='store_true',
                        help=_('Display unchanged places'))
    parser.add_argument('--display-ignored', action='store_true',
                        help=_('Display ignored places'))
    parser.add_argument('--mark-changes', action='store_true',
                        help=_('Replace changed PLAC tags with PLAC-X'))
                        
def initialize(options):
    read_parishes("app/static/seurakunnat.txt")
    read_villages("app/static/kylat.txt")


def fixlines(lines,options):
    pass

def transform(item,options):
    if item.tag != "PLAC":  return True
    if not item.value: return True
    place = item.value
    newplace = process_place(options, place)
    if newplace != place: 
        item.value = newplace  
        if options.mark_changes:
            item.tag = "PLAC-X"
        return item
    else:
        if options.display_nonchanges:
            print(_("Not changed: '{}'").format(place))
        return True
    raise RuntimeError(_("Internal error"))

ignored = [name.strip() for name in ignored_text.splitlines() if name.strip() != ""]

parishes = set()

countries = {
    "Finland","Suomi",
    "Kanada","Canada",
    "Yhdysvallat","USA","United States",
    "Alankomaat","Hollanti","Netherlands"
    "Ruotsi","Sverige","Sweden",
    "Australia",
    "Venäjä","Russia",
    "Eesti","Viro","Estland",
    "Norja","Norge","Norway",
}

villages = defaultdict(set)

def numeric(s):
    return s.replace(".","").isdigit()

def read_parishes(parishfile):
    for line in open(parishfile,encoding="utf-8"):
        line = line.strip()
        if line == "":
            continue
        _num, name = line.split(None,1)
        for x in name.split("-"):
            name2 = x.strip().lower()
            parishes.add(auto_combine(name2))
         
def read_villages(villagefile):
    for line in open(villagefile,encoding="utf-8"):
        line = line.strip()
        if not ":" in line:
            continue
        parish,village = line.split(":",1)
        parish = parish.strip().lower()
        village = village.strip().lower()
        villages[auto_combine(parish)].add(village)

def ignore(options, names):
    for name in names:
        if len(name) < options.minlen:
            return True
        if name.lower() in ignored:
            return True
        if options.ignore_digits and numeric(name):
            return True
        if options.ignore_lowercase and name.islower(): 
            return True
    return False

auto_combines = [
    "n pitäjä",
    "n srk",
    "n seurakunta",
    "n maalaiskunta",
    "n maaseurakunta",
    "n kaupunkiseurakunta",
    "n tuomiokirkkoseurakunta",
    "n rykmentti",
    "n kylä",
    "n mlk",
    "n msrk",
    "n ksrk",
]


def talonumerot(names):
    """
    Yritetään hoitaa seuraavanlaiset tapaukset niin että talonnumero tulee yhdistettyä kylän nimeen, esim.
        Kuopio Vehmasmäki 8 -> Kuopio, Vehmasmäki, Vehmasmäki 8
        Maaninka Kurolanlahti 6 Viemäki -> Maaninka, Kurolanlahti, Kurolanlahti 6 Viemäki
        Maaninka Kurolanlahti N:o 6 Viemäki -> Maaninka, Kurolanlahti, Kurolanlahti N:o 6 Viemäki
    Tässä inputtina kuitenkin jo listaksi hajotettu paikka esim.
        ["Kuopio","Vehmasmäki","8"] -> ["Kuopio", "Vehmasmäki", "Vehmasmäki 8"]
        ["Maaninka","Kurolanlahti","6","Viemäki"] -> ["Maaninka", "Kurolanlahti", "Kurolanlahti 6 Viemäki"]
    """
    def find_digit(names):
        for i, name in enumerate(names):
            if name.isdigit() and int(name) > 0 and int(name) < 1000: return i
        return None
    i = find_digit(names)
    if i is None: return names
    if i == 0: return names
    if i > 1 and names[i-1].lower() == "n:o": # yhdistetaan ["n:o","9"] -> ["n:o 9"]
        names[i-1] = "%s %s" % (names[i-1],names[i])
        del names[i]
        i = i-1
    numero = names[i]
    kyla = names[i-1]
    if i < len(names)-1:
        talo = names[i+1]
        names[i] = "%s %s %s" % (kyla,numero,talo)
        del names[i+1]
    else:
        names[i] = "%s %s" % (kyla,numero)
    return names


def auto_combine(place):
    for s in auto_combines:
        place = place.replace(s,s.replace(" ","-"))
    return place
    
def revert_auto_combine(place):
    for s in auto_combines:
        place = place.replace(s.replace(" ","-"),s)
    return place

def stringmatch(place,matches):
    for match in matches:
        if place.find(match) >= 0: return True
    return False
    
def process_place(options, place): 
    orig_place = place
    if options.match and not stringmatch(place,options.match):
        return place
    if options.add_commas and "," not in place:
        if options.auto_combine:
            place = auto_combine(place)
        names = place.split()
        if ignore(options, names): 
            if options.display_ignored:
                print(_("ignored: ") + orig_place)
            return orig_place
        names = talonumerot(names)
        place = ", ".join(names)
    if "," in place:
        names = [name.strip() for name in place.split(",") if name.strip() != ""]
        if len(names) == 1: 
            if options.auto_combine:
                place = revert_auto_combine(place)
            return place
        do_reverse = False
        if options.auto_order:
            #print(sorted(parishes))
            #print(sorted(villages["helsingin-pitäjä"]))
            #print(names)
            if names[0].lower() in parishes and names[1].lower() in villages[names[0].lower()] and names[-1] not in countries:
                do_reverse = True
            if names[0] in countries:
                do_reverse = True
        if options.reverse or do_reverse:
            names.reverse()
            place = ", ".join(names)
    if options.auto_combine:
        place = revert_auto_combine(place)
    return place
 


def check(in_file, expected_output, **kwargs):
    class Options: pass
    options = Options()
    options.reverse = False
    options.add_commas = False
    options.ignore_lowercase = False
    options.ignore_digits = False
    options.display_ignored = False
    options.auto_order = True
    options.auto_combine = True
    options.minlen = 0
    options.match = None
    options.__dict__.update(kwargs)
    
    newplace = process_place(options, in_file)
    if newplace != expected_output:
        print("{}: expecting '{}', got '{}'".format(in_file, expected_output, newplace),file=sys.stderr)
        

def test():
    check("Helsingin pitäjä Herttoniemi","Herttoniemi, Helsingin pitäjä",add_commas=True,reverse=True)
    check("Rättölä, Heinjoki","Heinjoki, Rättölä",reverse=True)
    check("Rättölä Heinjoki","Rättölä, Heinjoki",add_commas=True)
    check("Rättölä Heinjoki","Heinjoki, Rättölä",add_commas=True,reverse=True)
    check("Rättölä, Heinjoki","Rättölä, Heinjoki",add_commas=True)
    check("Viipurin mlk","Viipurin mlk",add_commas=True)
    check("Viipurin msrk","Viipurin msrk",add_commas=True)
    check("Koski tl","Koski tl",add_commas=True)
    check("Koski TL","Koski TL",add_commas=True)
    check("Koski","Koski",add_commas=True)
    check("Koski","Koski",reverse=True)

    check("Koski förs","Koski, förs",add_commas=True,ignore_lowercase=False)
    check("Koski förs","Koski förs",add_commas=True,ignore_lowercase=True)

    #check("Rio de Janeiro","Rio, de, Janeiro",add_commas=True,ignore_lowercase=False)
    check("Rio de Janeiro","Rio de Janeiro",add_commas=True,ignore_lowercase=True)

    check("Stratford upon Avon","Stratford, upon, Avon",add_commas=True,ignore_lowercase=False)
    check("Stratford upon Avon","Stratford upon Avon",add_commas=True,ignore_lowercase=True)
    
    check("Äyräpää Vuosalmi N:o 4", "Äyräpää, Vuosalmi, Vuosalmi N:o 4",add_commas=True,ignore_digits=False)
    check("Äyräpää Vuosalmi N:o 4", "Äyräpää Vuosalmi N:o 4",add_commas=True,ignore_digits=True)
    check("Kuopio Vehmasmäki 8", "Kuopio, Vehmasmäki, Vehmasmäki 8",add_commas=True,ignore_digits=False)
    check("Maaninka Kurolanlahti 6 Viemäki ", "Maaninka, Kurolanlahti, Kurolanlahti 6 Viemäki",add_commas=True,ignore_digits=False)


    
if __name__ == "__main__":
    test()


