#!/usr/bin/env python3
"""
Tries to recognize place names and order them correctly
"""

version = "1.0"

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
                        help='Reverse the order of places')
    parser.add_argument('--add-commas', action='store_true',
                        help='Replace spaces with commas')
    parser.add_argument('--ignore-lowercase', action='store_true',
                        help='Ignore lowercase words')
    parser.add_argument('--ignore-digits', action='store_true',
                        help='Ignore numeric words')
    parser.add_argument('--minlen', type=int, default=0,
                        help="Ignore words shorter that minlen")
    parser.add_argument('--auto-order', action='store_true',
                        help='Try to discover correct order...')
    parser.add_argument('--auto-combine', action='store_true',
                        help='Try to combine certain names...')
    parser.add_argument('--match', type=str, action='append',
                        help='Only process places containing any match string')
    parser.add_argument('--display-nonchanges', action='store_true',
                        help='Display unchanged places')
    parser.add_argument('--display-ignored', action='store_true',
                        help='Display ignored places')
    parser.add_argument('--mark-changes', action='store_true',
                        help='Replace changed PLAC tags with PLAC-X')
                        
def initialize(run_args):
    read_parishes("static/seurakunnat.txt")
    read_villages("static/kylat.txt")


def phase2(run_args):
    pass

def phase3(run_args,gedline,f):
    if gedline.tag == "PLAC":
        if not gedline.value: 
            return
        place = gedline.value
        newplace = process_place(run_args, place)
        if newplace != place: 
            #if run_args['display_changes']:
            #    print("'{}' -> '{}'".format(place,newplace))
            gedline.value = newplace  
            if run_args['mark_changes']:
                gedline.tag = "PLAC-X"
        else:
            if run_args['display_nonchanges']:
                print("Not changed: '{}'".format(place))
    gedline.emit(f)
            
ignored = [name.strip() for name in ignored_text.splitlines() if name.strip() != ""]

parishes = set()

countries = {
    "Finland",
    "Suomi",
    "USA",
    "Kanada",
    "Yhdysvallat",
    "Alankomaat",
    "Ruotsi",
    "Australia",
    "Venäjä",
    "Eesti","Viro",
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

def ignore(run_args, names):
    for name in names:
        if len(name) < run_args['minlen']:
            return True
        if name.lower() in ignored:
            return True
        if run_args['ignore_digits'] and numeric(name):
            return True
        if run_args['ignore_lowercase'] and name.islower(): 
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
    
def process_place(run_args, place): 
    orig_place = place
    if run_args['match'] and not stringmatch(place,run_args['match']):
        return place
    if run_args['add_commas'] and "," not in place:
        if run_args['auto_combine']:
            place = auto_combine(place)
        names = place.split()
        if ignore(run_args, names): 
            if run_args['display_ignored']:
                print("ignored: " + orig_place)
            return orig_place
        names = talonumerot(names)
        place = ", ".join(names)
    if "," in place:
        names = [name.strip() for name in place.split(",") if name.strip() != ""]
        if len(names) == 1: 
            if run_args['auto_combine']:
                place = revert_auto_combine(place)
            return place
        do_reverse = False
        if run_args['auto_order']:
            #print(sorted(parishes))
            #print(sorted(villages["helsingin-pitäjä"]))
            #print(names)
            if names[0].lower() in parishes and names[1].lower() in villages[names[0].lower()] and names[-1] not in countries:
                do_reverse = True
            if names[0] in countries:
                do_reverse = True
        if run_args['reverse'] or do_reverse:
            names.reverse()
            place = ", ".join(names)
    if run_args['auto_combine']:
        place = revert_auto_combine(place)
    return place
 


def check(in_file, expected_output, reverse=False, add_commas=False, 
          ignore_lowercase=False, ignore_digits=False):
    class Args: pass
    run_args = {'reverse': reverse,
                'add_commas': add_commas,
                'ignore_lowercase': ignore_lowercase,
                'ignore_digits': ignore_digits,
                'display_ignored': False,
                'auto_order': True,
                'auto_combine': True,
                'min_len': 0,
                'match': None
                }
 
    newplace = process_place(run_args, in_file)
    if newplace != expected_output:
        print("{}: expecting '{}', got '{}'".format(in_file, expected_output, newplace))
        

def test():
    check("Helsingin pitäjä Herttoniemi","Herttoniemi, Helsingin pitäjä",add_commas=True,reverse=False)
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
    
    check("Äyräpää Vuosalmi N:o 4", "Äyräpää, Vuosalmi, N:o, 4",add_commas=True,ignore_digits=False)
    check("Äyräpää Vuosalmi N:o 4", "Äyräpää Vuosalmi N:o 4",add_commas=True,ignore_digits=True)
    check("Kuopio Vehmasmäki 8", "Kuopio, Vehmasmäki, Vehmasmäki 8 ",add_commas=True,ignore_digits=False)
    check("Maaninka Kurolanlahti 6 Viemäki ", "ÄMaaninka, Kurolanlahti, Kurolanlahti 6 Viemäki",add_commas=True,ignore_digits=False)


    
if __name__ == "__main__":
    test()


