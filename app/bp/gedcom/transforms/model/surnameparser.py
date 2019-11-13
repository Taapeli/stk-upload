import re
import logging 
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger('stkserver')

class Name_types(Enum):
    BIRTH_NAME = 1
    TAKEN_NAME = 2
    MARRIED_NAME = 3
    AKA = 4
    PREVIOUS_NAME = 5

# all these must end in '.'
TYPES = {'os.':Name_types.BIRTH_NAME, 
         'o.s.':Name_types.BIRTH_NAME, 
         's.':Name_types.BIRTH_NAME, 
         'ent.':Name_types.PREVIOUS_NAME, 
         'e.':Name_types.PREVIOUS_NAME, 
}

TYPE_NAMES = {
    Name_types.BIRTH_NAME: "birth", 
    Name_types.TAKEN_NAME: "taken",
    Name_types.MARRIED_NAME: "married",
    Name_types.AKA: "aka",
    Name_types.PREVIOUS_NAME: "entinen",
}

PREFIXES =  {'af','de','der','van','von'}

@dataclass
class SurnameInfo:
    surn:str = ""
    name_type:Name_types = None  
    prefix:str = ""

class ParseError(Exception): pass

class SurnameParser:
    
    def parse_surnames(self,surn):
        """
        Tutkii sukunimi-stringin rakenteen. Paluuarvona on lista SurnameInfo-objekteja.
        """
        if surn.strip() == "":
            return [SurnameInfo("",None,"")]
        try:
            return self._parse_surnames0(surn)
        except ParseError: 
            return [SurnameInfo(surn,None,"")]
        
    def _parse_surnames0(self,surn):
        # ensimmäisenä käsitellään suluissa olevat tiedot: "(Mäkinen)" -> ("aka","Mäkinen")
        i = surn.find("(")
        if i > 0:
            j = surn.find(")",i)
            if j < 0: raise ParseError(f"Expecting ')': '{surn}'")
            if j < i: raise ParseError(f"Expecting ')': '{surn}'")
            ret1 = self._parse_surnames_no_parens(surn[i+1:j])
            for sn in ret1: 
                if sn.name_type is None: sn.name_type = Name_types.AKA
            ret2 = self._parse_surnames0(f"{surn[:i]} {surn[j+1:]}")
            return ret1 + ret2
        else:
            return self._parse_surnames_no_parens(surn)
        
    def _parse_surnames_no_parens(self,surn):
        # 'surn" on merkkijono, joissa ei pitäisi olla sulkumerkkejä
        # Lisätään välilyöntejä, jotta nimityypit ("os." jne) erottuvat.
        # Hajotetaan merkkijono listaksi ja kutsutaan metodia '_parse_surnames_list'
        # Lopuksi tutkitaan metodin palauttamat arvot ja jos sukunimessä on kauttaviiva
        # tai pilkku, hajotetaan ne vielä "aka"-sukunimiksi
        i = surn.find("(")
        if i >= 0: raise ParseError(f"Expected no '(': '{surn}'")
        i = surn.find(")")
        if i >= 0: raise ParseError(f"Expected no ')': '{surn}'")
        for s in TYPES.keys():
            surn = surn.replace(f" {s}",f" {s} ") # separate "os.Mäkinen" -> "os. Mäkinen"
            surn = surn.replace(f",{s}",f" {s} ") # separate "Virtanen,os. Mäkinen" -> "Virtanen, os. Mäkinen"
            surn = surn.replace(f",{s[:-1]} ",f" {s} ") # separate "Virtanen,os Mäkinen" -> "Virtanen, os Mäkinen"
        surnames1 = self._parse_surnames_list(surn.split())
        surnames = []
        for name_type, namelist in surnames1:
            surname = " ".join(namelist)
            names = re.split(r"[/,\\]",surname)
            for name in names:
                name = name.strip()
                parts = name.split()
                if len(parts) > 1 and parts[0] in PREFIXES:
                    prefix_list = []
                    while len(parts) > 1 and parts[0] in PREFIXES:
                        prefix_list.append( parts[0] )
                        name = " ".join(parts[1:])
                        parts = name.split()
                    prefix = " ".join(prefix_list)
                else:
                    prefix = ""
                if name: surnames.append(SurnameInfo(name,name_type,prefix))
                name_type = Name_types.AKA
        return surnames

    def _find_first_type(self,words):
        for i,n in enumerate(words):
            if n in TYPES or n+'.' in TYPES: return i
        return -1

    def _parse_surnames_list(self,words):
        # Käsitellään erillisiksi sanoiksi hajotettu sukunimi.
        # Etsitään ensin ensimmäinen nimen tyyppia osoittava sana (esim. "os.") ja
        # käsitellään rekursiivisesti listan loppuosa.
        # Jos alussa oli jokin nimi (ts. i > 0), liitetään se listan alkuun.
        # Paluuarvo on lista jonka jäsenet ovat tuplia (name_type,surname).
        i = self._find_first_type(words) # the index of first "os." or "ent." etc
        if i == -1: # eg. "Mäkinen Virtanen"
            return [(None,words)]
        n = words[i]
        if i > 0: # eg. "Mäkinen os. Virtanen"
            return [(None,words[0:i])] + self._parse_surnames_list(words[i:])
        else: # i == 0, eg. "os. Mäkinen"
            if n in TYPES:
                name_type = TYPES[n]
            else:
                name_type = TYPES[n+'.']
            names = self._parse_surnames_list(words[i+1:])
            if len(names) > 0: # lisätään tyyppi ensimmäiseen nimeen
                return [(name_type,names[0][1])] + names[1:]
            else:
                # nimi päättyy tyyppiin!
                surname = " ".join(words)
                raise ParseError(f"Invalid surname syntax: '{surname}'")

def __test_surn(surn):
    from pprint import pprint
    pn = SurnameParser()
    x = pn.parse_surnames(surn)
    print()
    print(surn)
    pprint(x)

def __test():

    __test_surn("Mattila")
    __test_surn("Frisk os. Mattila")
    __test_surn("Reipas e. Frisk os. Laine")
    __test_surn("Lehti os. Lampi e. af Damm")
    __test_surn("Mattila (Matts)")
    __test_surn("Hällström (af Hällström)")
    __test_surn("Hällström (af Hällström) e. Hellström, os. Mönkkönen")
    __test_surn("af Hällström (Hällström) e. Hellström, os. Mönkkönen")
    __test_surn("af Hällström (Hällström) ent.Hellström, os.Mönkkönen")
    __test_surn("af Hällström (Hällström) ent.Hellström, s.Mönkkönen")
    __test_surn("af Hällström (Hällström) ent Hellström, os Mönkkönen")
    __test_surn("af Hällström (os. Hällström) ent Hellström")
    __test_surn("Garcia Marquez")
    __test_surn("Heikkilä/Mattila")
    __test_surn("Heikkilä,Mattila")
    __test_surn("von der Goltz")
    __test_surn("de Godzinsky")
    __test_surn(r"Lehti\Lahti\Lehto")
    __test_surn(r"von Mäkinen os.")
            
if __name__ == "__main__":
    __test()