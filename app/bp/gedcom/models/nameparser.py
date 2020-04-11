from pprint import pprint
import sys
import traceback
from types import SimpleNamespace

from bp.gedcom.models.xparser import Parser, Keyword, ParseError
from bp.gedcom.models.xparser import NAME, OTHERWISE, END,CAPWORD
from dataclasses import dataclass

class SurnameParser:

    """
    ---------------
    Kielioppi:
    
    sukunimet   :=   sukunimet_ilman_sulkuja 
                     sukunimet_ilman_sulkuja [erotin] "(" sukunimet_ilman_sulkuja ")"
    
    sukunimet_ilman_sulkuja := sukunimi (erotin sukunimi|tyyppi sukunimi_ilman_tyyppia)*
    
    sukunimi    := [tyyppi] sukunimi_ilman_tyyppia
    
    sukunimi_ilman_tyyppia :=  
                 etuliite* nimi [etuliite] [nimi]

    nimi        := CAPWORD[-CAPWORD]*
    
    etuliite    := von | de | af | ...
    
    tyyppi      := "os." | "o.s." | "s." | "e." | "ent." | "född" | "eli" | "l." | "nyk." | "tai" | ...
    
    erotin      :=  "," | "/"
                
    """
    erottimet = [",","/"]
    type_prefixes1 = ["os.","s.","e.","ent.","l."]
    type_prefixes2 = Keyword(["os","s","ent","e","född","eli"])
    name_prefixes = Keyword(["von","de","la","af","van","der","zu","und","da"])
    
    @dataclass
    class SurnameInfo:
        surname_type: str
        surname_prefix: str
        surname: str

    def parse_sukunimi_ilman_tyyppia(self,p):
        '''
            sukunimi_ilman_tyyppia :=  
                     etuliite* nimi [etuliite] [nimi]
        '''
        surname_prefix = ""
        while p.optional(self.name_prefixes):
            surname_prefix += " " + p.value
        p.parse(NAME,"'t")
        lastname = p.value
        while p.optional(self.name_prefixes):
            lastname += " " + p.value
        if p.optional(NAME,"'t"):
            lastname += " " + p.value
        lastname = lastname.strip()
        surname_prefix = surname_prefix.strip()
        #return self.SurnameInfo(None,surname_prefix=surname_prefix,surname=lastname)
        return SimpleNamespace(surname_prefix=surname_prefix,surname=lastname)
    
    def parse_sukunimi(self,p):
        '''
            sukunimi    := [tyyppi] sukunimi_ilman_tyyppia
        '''
        p.optional(self.type_prefixes1,self.type_prefixes2)
        surname_type = p.value
        res = self.parse_sukunimi_ilman_tyyppia(p)
        res.surname_type = surname_type
        return res

    def parse_sukunimet_ilman_sulkuja(self,p):
        '''
            sukunimet_ilman_sulkuja := sukunimi (erotin sukunimi|tyyppi sukunimi_ilman_tyyppia)*
        '''
        rv = self.parse_sukunimi(p)
        result = [rv]
        while True:
            i = p.optional(self.erottimet,self.type_prefixes1,self.type_prefixes2)
            if i == 1:
                rv2 = self.parse_sukunimi(p)
                result.append(rv2)
            elif i in (2,3):
                surname_type = p.value
                rv2 = self.parse_sukunimi_ilman_tyyppia(p)
                rv2.surname_type = surname_type
                result.append(rv2)
            else:
                break
        return result
    
    def parse_sukunimet(self,name):
        '''
            sukunimet   :=   sukunimet_ilman_sulkuja 
                             sukunimet_ilman_sulkuja [erotin] "(" sukunimet_ilman_sulkuja ")"
        '''
        p = Parser(name)
        result = self.parse_sukunimet_ilman_sulkuja(p)
        p.optional(self.erottimet)
        if p.optional("("):
            rv2 = self.parse_sukunimet_ilman_sulkuja(p)
            result += rv2
            p.parse(")")
        p.parse(END)
        return result

      
    
class NameParser:
    '''
    name := etunimi* "/" sukunimet "/" patronyymi
    
    etunimi := nimi ["*"] | "(" nimi ")"
     
    '''
    def parse_name(self,name):
        i = name.find("/")
        j = name.rfind("/")
        if i >= 0:
            etunimistring = name[:i]
            rv_etunimet = self.parse_etunimet(etunimistring)
        if i+1 < j:
            sukunimet = name[i+1:j]
            p = SurnameParser()
            rv_sukunimet = p.parse_sukunimet(sukunimet)
        patronyymistring = name[j+1].strip()
        p = Parser(patronyymistring)
        p.parse(NAME,END)
        patronyymi = p.value
        return SimpleNamespace(etunimet=rv_etunimet,
                               sukunimet=rv_sukunimet,
                               patronyymi=patronyymi)

    def parse_etunimet(self,etunimistring):
        p = Parser(etunimistring)
        etunimet = []
        while True:
            i = p.parse(NAME,"(",'"',END)
            if i == 1:
                nimi = p.value
                if p.optional("*"):
                    tyyppi = "CALL"
                elif p.optional("."):
                    tyyppi = "PATRO"
                else:
                    tyyppi = ""
            if i == 2:
                p.parse(NAME)
                nimi = p.value
                p.parse(")")
                tyyppi = "NICK"
            if i == 3:
                p.parse(NAME)
                nimi = p.value
                p.parse('"')
                tyyppi = "NICK"
            if i == 4: 
                break
            etunimet.append((tyyppi,nimi))
        return etunimet
                
                
