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
Created on 22.11.2016

    Converted from bp.gedcom.transforms.model.person_name_v1.PersonName_v1

@author: jm 4.6.2019
'''

import re
import logging 
from dataclasses import dataclass
from bp.gedcom.transforms.model.surnameparser import SurnameParser
logger = logging.getLogger('stkserver')

_NONAME = 'N'            # Marker for missing name part
_CHGTAG = "NOTE _orig_"  # Comment: original format

_UNNAMED = ['nimetön', 'tuntematon', 'N.N.', '?']
_PATRONYME = {'poika':'poika', 'p.':'poika', 'p':'poika',
              'sson':'sson', 'ss.':'sson', 's.':'son',
             'tytär':'tytär', 't.':'tytär', 'tr':'tytär', 
             'dotter':'dotter', 'dr.':'dotter' }
_LATIN_PATRONYME = [
       "Æschilli", "Aeschilli", "Eschilli", "Adami", "Andreæ",
       "Andreae", "Algothi", "Arvidi", "Axelii", "Bartholdi",
       "Benedicti", "Christierni", "Danielis", "Erici", "Erlandi",
       "Esaiæ", "Esaiae", "Fabiani", "Georgii", "Gustavi",
       "Henrici", "Hezekielis", "Haqvini", "Isaaci", "Jacobi",
       "Jeremiae", "Johannis", "Johannis", "Justi", "Laurentii",
       "Marci", "Magni", "Matthiae", "Nicolai", "Olai",
       "Petri", "Pauli", "Reginaldi", "Samueli", "Sigfridi",
       "Stephani", "Svenonis", "Thomæ", "Thomae"
    ]
_SURN = {'os.':'avionimi', 'o.s.':'avionimi', 'ent.':'otettu nimi', 'e.':'otettu nimi', \
         '/':'tunnettu myös', ',':'tunnettu myös'}

# all these must end in '.'
TYPES = {'os.':'syntymänimi', 
         'o.s.':'syntymänimi', 
         's.':'syntymänimi', 
         'ent.':'otettu nimi', 
         'e.':'otettu nimi', 
}

#_VON = ['von', 'af', 'de', 'la']
_BABY = {"vauva":"U", "poikavauva":"M", "tyttövauva":"F", 
         "poikalapsi":"M", "tyttölapsi":"F", "lapsi":"U",
         "fröken":"F", "junfru":"F", "herr":"M", 
         "neiti":"F", "rouva":"F", "herra":"M", 
         "(vauva)":"U", "(poikavauva)":"M", "(tyttövauva)":"F", "tyttö":"N",
         "(poikalapsi)":"M", "(tyttölapsi)":"F", "(lapsi)":"U","poika":"M",
         "barn":"U", "son":"M", "gåsse":"M", 
         "dotter":"F", "flicke":"F", "fl.barn":"U", "dödf.barn":"U",
         "(barn)":"U", "(son)":"M", "(gåsse)":"M", 
         "(dotter)":"F", "(flicke)":"F", "(fl.barn)":"U", "(dödf.barn)":"U" }

class NameParts:
    givn = None
    surn = None
    nsfx = None
    sex = None
    call_name = None
    nick_name = None
    changed = False
    patronymic_conflict = False 

@dataclass
class ParseResult:
    name_parts:NameParts 
    surnames:str

class ParseError(Exception): pass

class PersonName:
    '''
    Stores and fixes Gedcom individual name information.

    The preferred source of information is the '1 NAME givn/surn/nsfx' row.
    If NAME has significant changes, the original value is also written to 
    a 'NOTE _orig_' row.
    
    1. A patronyme in givn part is moved to nsfx part and a new NSFX row is created,
       if needed
    
    2. A missing givn or surn is replaced with noname mark 'N'
    
    3. If surname part has multiple surnames, a new "1 NAME" group is generated
       from each of them
    '''

    def process_NAME(self, value):
        ''' Analyze and fix a NAME Item.
        
            First NAME and then the descendant Items included in the level hierarchy.

            Attribute name_default may be an NAME Item, who's given name is used
            in place of a missing givn.

            The rules about merging original and generated values are applied here.
            
            #TODO: If there is no '/', don't output givn, surn, ... lines ??
        '''

        ''' 1) Full name parts like 'givn/surn/nsfx' will be isolated and analyzed ''' 
        name_parts = value.split("/")
        if len(name_parts) < 3: 
            print("Illegal name:", value)
            return None # no change

        s1 = value.find('/')
        s2 = value.rfind('/')
        if s1 >= 0 and s2 >= 0 and s1 != s2: 
            # Contains '.../Surname/...' or even '.../Surname1/Surname2/...' etc
            givn = value[:s1].strip()
            surn = value[s1+1:s2].strip()
            nsfx = value[s2+1:].strip()
        else:
            print("Illegal name:", value)
            return None # should not come here

        ''' 1.1) GIVN given name part rules '''
        name_parts = self._evaluate_givn(givn)
        if name_parts.nsfx and nsfx and name_parts.nsfx != nsfx:
            pass # conflict..
            name_parts.patronymic_conflict = True 
        if not name_parts.nsfx: name_parts.nsfx = nsfx
        surnameparser = SurnameParser()
        surnames = surnameparser.parse_surnames(surn)
        
        return ParseResult(name_parts,surnames)
    
    def _evaluate_givn(self, givn):
        ''' Process given name part of NAME record '''

        def _match_patronyme(nm):
            ''' Returns full patronyme name, if matches, else None
            '''
            if nm in _LATIN_PATRONYME:
                # Any of Latin patronymes is accepted as is
                return nm;
            for short, full in _PATRONYME.items():
                # Has ending as short, but short is not the whole name
                if nm.endswith(short) and not short == nm:
                    # 'Matinp.' --> 'Matinpoika'
                    return nm[:-len(short)] + full
            return None


        name_parts = NameParts()
        name_parts.givn = givn
        
        gnames = givn.split()
        
        # 1.1a) Find if last givn is actually a patronyme; mark it as new nsfx 
       
        if len(gnames) > 1:
            nm = gnames[-1]
            pn = _match_patronyme(nm)
            if pn is not None:
                name_parts.nsfx = pn
                name_parts.givn = ' '.join(gnames[0:-1])
                name_parts.changed = True

        # 1.1b) A generic baby name replaced as no name
        if givn in _BABY:
            # A unnamed baby
            name_parts.givn = _NONAME
            name_parts.sex = _BABY[givn]
            name_parts.changed = True
            return name_parts

        gnames = name_parts.givn.split()
        parts = []
        for nm in gnames:
            # Name has a star '*'
            if nm.endswith('*'):
                # Remove star
                nm = nm[:-1]
                name_parts.call_name = nm
                parts.append(nm)
                name_parts.changed = True
            # Nick name in parenthesis "(Jussi)"
            elif re.match(r"\(.*\)", nm) != None:
                name_parts.nick_name = nm[1:-1]
                name_parts.changed = True
            else:
                parts.append(nm)
        name_parts.givn = " ".join(parts)
        if name_parts.givn == "": name_parts.givn = "N"
        return name_parts
                


given_names = []
surnames = []    

def __test_givn(givn):
    from pprint import pprint
    pn = PersonName(None)
    x = pn._evaluate_givn(givn)
    print()
    print(givn)
    pprint(x.__dict__)
    given_names.append(givn)


def __test():
    from pprint import pprint
    pn = PersonName(None)
    __test_givn("Matti")
    __test_givn("Matti Pekka")
    __test_givn("Matti*")
    __test_givn("Matti Pekka*")
    __test_givn("Matti* Pekka")
    __test_givn("Matti (Pekka)")
    __test_givn("(Matti) Pekka")
    __test_givn("(Matti)")
    __test_givn("Matti Pekanpoika")
    __test_givn("poikalapsi")
    __test_givn("Johan Henrici")

if __name__ == "__main__":
    __test()