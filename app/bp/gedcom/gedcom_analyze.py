import io
import re
import time
from collections import defaultdict
from contextlib import redirect_stdout

from . import transformer
from flask_babelex import _, ngettext

name = _("GEDCOM Analyzer")

def initialize(options):
    return Analyzer()

class Info: pass 

from . import gedcom_grammar_data2


events = """
INDI
FAM
FAM.ANUL
FAM.CENS
FAM.DIVF
FAM.DIV
FAM.ENGA
FAM.EVEN
FAM.MARB
FAM.MARC
FAM.MARL
FAM.MARR
FAM.MARS
FAM.RESI
FAM.SLGS
INDI.ADOP
INDI.ASSO
INDI.BAPL
INDI.BAPM
INDI.BARM
INDI.BASM
INDI.BIRT
INDI.BLES
INDI.BURI
INDI.CAST
INDI.CENS
INDI.CHRA
INDI.CHR
INDI.CONF
INDI.CONL
INDI.CREM
INDI.DEAT
INDI.DSCR
INDI.EDUC
INDI.EMIG
INDI.ENDL
INDI.EVEN
INDI.FACT
INDI.FCOM
INDI.GRAD
INDI.IDNO
INDI.IMMI
INDI.NAME.FONE
INDI.NAME.ROMN
INDI.NAME
INDI.NATI
INDI.NATU
INDI.NCHI
INDI.NMR
INDI.OCCU
INDI.ORDN
INDI.PROB
INDI.PROP
INDI.RELI
INDI.RESI
INDI.RETI
INDI.SLGC
INDI.SSN
INDI.TITL
INDI.WILL
"""

events = set(events.splitlines())

def read_allowed_paths():
    allowed = set()
    from . import gedcom_grammar_data 
    for line in gedcom_grammar_data.paths.splitlines():
        if line.strip() != "":
            allowed.add(line.strip())
    return allowed

def valid_date(datestring):
    # date checker, not perfect
    datestring = datestring.upper()
    parts = datestring.split(maxsplit=1)
    if len(parts) < 1: return False

    if len(parts) > 1 and parts[0] in {"ABT","EST","CAL"}:
        return valid_date(parts[1])

    m = re.match("BET (.+?) AND (.+)",datestring)
    if m:
        return valid_date(m.group(1)) and valid_date(m.group(2))

    m = re.match("FROM (.+) TO (.+)",datestring)
    if m:
        return valid_date(m.group(1)) and valid_date(m.group(2))

    if len(parts) > 1 and parts[0] in {"FROM","TO","BEF","AFT"}:
        return valid_date(parts[1])
    
    try:
        if time.strptime(datestring, "%Y"): return True
    except:
        pass

    try:
        if time.strptime(datestring, "%b %Y"): return True
    except:
        pass

    try:
        if time.strptime(datestring, "%d %b %Y"): return True
    except:
        pass
        
    return False

def printheader(title):
    print("<div class=results-box>")
    print(f"<h3 class=results-title>{title}</h3>")
    print("<table class=results>")

def printtrailer():
    print("</table>")
    print("</div>")

def printitem(item):
    print(f"<tr><td>{item}")

class LineCounter:
    def __init__(self,title=None):
        self.title = title
        self.values = defaultdict(list)
    def add(self,key,item):
        self.values[key].append(item)
    def display(self,count=None):
        if len(self.values) == 0: return
        print()
        printheader(self.title) 
        for key,itemlist in sorted(self.values.items()):
            linenums = [str(item.linenum) for item in itemlist]
            if len(linenums) > 10:
                linenums = linenums[0:10] 
            links = [f"<a href='#' class='gedcomlink'>{linenum}</a>" for linenum in linenums]
            txt = ngettext(
                "count=%(num)d, line %(lines)s",
                "count=%(num)d, lines %(lines)s",
                 num=len(itemlist), lines=', '.join(links))
            if len(itemlist) > len(linenums): txt += ",..."
            printitem(f"<b>{key:25}</b><td>({txt})")
        if count is not None:
            if count > len(self.values): printitem(f"<b>...")
            printitem(f"<b>Count: {count}")
        printtrailer() 
                


class Analyzer(transformer.Transformation):
    def __init__(self):
        self.info = Info()
        self.individuals = 0
        self.allowed_paths = read_allowed_paths()
        self.illegal_paths = LineCounter(_("Invalid tag hierarchy"))
        self.novalues = LineCounter(_("No value"))
        self.invalid_dates = LineCounter(_("Invalid dates"))
        self.too_many = LineCounter(_("Too many child tags"))
        self.submitter_refs = LineCounter(_("Records for submitters"))
        self.family_with_no_parents = LineCounter(_("Families with no parents"))
        self.submitters = dict()
        self.submitter_emails = dict()
        self.records = {}
        self.xrefs = {}
        self.types = defaultdict(LineCounter)

        self.with_sources = LineCounter(_("With sources"))
        self.without_sources = LineCounter(_("Without sources"))
        
        self.genders = defaultdict(int)
        self.invalid_pointers = []
        self.mandatory_paths = {
            "HEAD",
            "HEAD.SOUR",
            "HEAD.GEDC",
            "HEAD.GEDC.VERS",
            "HEAD.GEDC.FORM",
            "HEAD.CHAR",
            "HEAD.SUBM",
            "TRLR",
        }

    def transform(self,item,options,phase):
        if 0:
            print("line:",item.line)
            print("tag:",item.tag)
            print("path:",item.path)
            print("value:",item.value)
        path = item.path
        if path[0] == '@': path = path.split(".",maxsplit=1)[1]
        if item.tag != "CONC" and path not in self.allowed_paths:
            self.illegal_paths.add(path,item)
        
        if item.tag == "INDI":
            self.individuals += 1

        if item.value == "" and len(item.children) == 0 and item.tag not in {"TRLR","CONT"}:
            self.novalues.add(item.line,item)         
            
        if item.tag == "SEX":
            self.genders[item.value] += 1
            
        if item.tag == "DATE":
            if not valid_date(item.value.strip()):
                self.invalid_dates.add(item.value,item)

        if path in self.mandatory_paths: self.mandatory_paths.remove(path)     
        
        taglist = gedcom_grammar_data2.data.get(path)
        if taglist:
            for (tag,(mincount,maxcount)) in taglist:
                count = 0
                for c in item.children:
                    if c.tag == tag: count += 1
                if maxcount and count > maxcount:
                    self.too_many.add( "{} {} tags under {} - should be at most {}".format(count,tag,path,maxcount), item )     
        
        if item.path.endswith("SUBM.NAME"):
            xref = item.path.split(".")[0]
            self.submitters[xref] = item.value 
        if item.path.endswith("SUBM.EMAIL"):
            xref = item.path.split(".")[0]
            self.submitter_emails[xref] = item.value 
        if item.level == 1 and item.tag == "SUBM":
            self.submitter_refs.add(item.value,item) 
        if item.level == 0 and item.xref:
            self.records[item.xref] = item
        if item.level > 0 and item.value.startswith("@") and not item.value.startswith("@#"):
            self.xrefs[item.value] = item
            if (not item.value.startswith("@@") and 
                not item.tag in {"SOUR","REPO","SUBM","NOTE",
                                "FAMC","FAMS","CHIL","HUSB","WIFE",
                                "OBJE","SUBN"}):
                self.invalid_pointers.append(item.line)
            
        if item.tag == "TYPE": # classify types
            parts = item.path.split(".")
            if parts[0][0] == "@":
                parent_path = ".".join(parts[1:-1])
            else: 
                parent_path = ".".join(parts[0:-1])
            self.types[parent_path].add(item.value,item)
            
        if item.tag == "FAM":
            husb = None
            wife = None
            for c1 in item.children:
                if c1.tag == "HUSB":  
                    husb = c1.value
                if c1.tag == "WIFE":  
                    wife = c1.value
            if husb is None and wife is None:
                self.family_with_no_parents.add("",item)

        if path in events:
            for c in item.children:
                if c.tag == "SOUR":
                    self.with_sources.add(path,item)
                    break
            else:  
                self.without_sources.add(path,item)
        
        return True

    def finish(self,options):
        with io.StringIO() as buf, redirect_stdout(buf):
            self.display_results(options)
            self.info = buf.getvalue()

            
    def display_results(self,options):
        printheader(_("Genders"))
        
        total = 0
        for sex,count in sorted(self.genders.items()):
            printitem(f"<b>{sex}</b><td>{count:5}")
            total += count
        if self.individuals > total:
            printitem(f"<td>{self.individuals-total:5}")
        printtrailer()
                    
        self.illegal_paths.display()

        self.with_sources.display()
        self.without_sources.display()

        self.invalid_dates.display()
        self.novalues.display()
        self.too_many.display()
        self.family_with_no_parents.display()
        
        self.submitter_refs2 = LineCounter(_("Submitters"))
        for xref,itemlist in self.submitter_refs.values.items():
            name = self.submitters.get(xref,xref)
            if name == xref: name = self.submitter_emails.get(xref,xref)
            self.submitter_refs2.values[name] = itemlist
        self.submitter_refs2.display()
             
        if len(self.mandatory_paths) > 0:
            printheader(_("Missing paths"))
            for path in sorted(self.mandatory_paths):
                printitem(f"<b>{path}</b>")
            printtrailer()

        for parent_path,typeinfo in self.types.items():
            typeinfo.title = _("TYPEs for %(parent_path)s",parent_path=parent_path)
            typeinfo.display()

        if len(self.invalid_pointers) > 0:
            printheader(_("Invalid pointers"))
            for line in self.invalid_pointers:
                printitem(line)
            printtrailer()
            
        xrefs = self.xrefs.keys() - self.records.keys()
        count = len(xrefs) 
        if count > 0: 
            missing = LineCounter(_("Missing records"))
            for xref in list(xrefs)[:10]:          
                missing.add(xref,self.xrefs[xref])          
            missing.display(count)

        xrefs = self.records.keys() - self.xrefs.keys()
        count = len(xrefs) 
        if count > 0: 
            unused = LineCounter(_("Unused records"))
            for xref in list(xrefs)[:10]:          
                unused.add(xref,self.records[xref])
            unused.display(count)


            
            