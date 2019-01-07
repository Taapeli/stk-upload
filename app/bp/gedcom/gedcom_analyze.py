import io
import re
import sys
import time
from collections import Counter, defaultdict

import transformer
from flask_babelex import _

name = _("GEDCOM Analyzer")

def initialize(options):
    return Analyzer()

def add_args(parser):
    pass

class Info: pass 

def read_allowed_paths():
    allowed = set()
    from gedcom_grammar_data import paths
    for line in paths.splitlines():
        if line.strip() != "":
            allowed.add(line.strip())
    return allowed

def valid_date(datestring):
    # date checker, not perfect
    parts = datestring.split(maxsplit=1)
    if len(parts) < 1: return False

    if parts[0] in {"ABT","EST","CAL"}:
        return valid_date(parts[1])

    m = re.match("BET (.+?) AND (.+)",datestring)
    if m:
        return valid_date(m.group(1)) and valid_date(m.group(2))

    m = re.match("FROM (.+) TO (.+)",datestring)
    if m:
        return valid_date(m.group(1)) and valid_date(m.group(2))

    if parts[0] in {"FROM","TO","BEF","AFT"}:
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

class LineCounter:
    def __init__(self,title):
        self.title = title
        self.values = defaultdict(list)
    def add(self,key,item):
        self.values[key].append(item)
    def display(self):
        if len(self.values) == 0: return
        print()
        print(self.title) 
        for key,itemlist in sorted(self.values.items()):
            linenums = [str(item.linenum) for item in itemlist]
            if len(linenums) > 10:
                linenums = linenums[0:10] 
                linenums.append("...")
            print("- {:25} (count={:5}, lines {})".format(key,len(itemlist),",".join(linenums)))   
            #print("- {:25} (count={:5})".format(key,len(itemlist)))   
        
class Analyzer(transformer.Transformation):
    def __init__(self):
        self.info = Info()
        self.allowed_paths = read_allowed_paths()
        self.illegal_paths = LineCounter(_("Illegal paths:"))
        self.novalues = LineCounter(_("No value:"))
        self.invalid_dates = LineCounter(_("Invalid dates:"))
        self.mandatory_paths = {
            "HEAD.SOUR",
            "HEAD.GEDC",
            "HEAD.GEDC.VERS",
            "HEAD.GEDC.FORM",
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
        
        if item.value == "" and len(item.children) == 0 and item.tag not in {"TRLR","CONT"}:
            self.novalues.add(item.line,item)         
            
        if item.tag == "DATE":
            if not valid_date(item.value.strip()):
                self.invalid_dates.add(item.value,item)

        if path in self.mandatory_paths: self.mandatory_paths.remove(path)     
        
        return True

    def finish(self,options):
        saved_stdout = sys.stdout
        saved_stderr = sys.stdout
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        self.illegal_paths.display()
        self.novalues.display()
        self.invalid_dates.display()
        
        if len(self.mandatory_paths) > 0:
            print()
            print("Missing paths:")
            for path in sorted(self.mandatory_paths):
                print("-",path)
            
        self.info = sys.stdout.getvalue()
        errors = sys.stderr.getvalue()
        sys.stdout = saved_stdout
        sys.stderr = saved_stderr

            
            
            