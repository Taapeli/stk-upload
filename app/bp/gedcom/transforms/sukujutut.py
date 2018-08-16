"""
Sukujutut-muunnos

Kari Kujansuu <kari.kujansuu@gmail.com>
"""
import sys

input_encoding="ISO8859-1"
input_encoding="UTF-8"
output_encoding="UTF-8"


def write(out,s):
    if out == sys.stdout:
        print(s)
    else:
        out.emit(s)
    #out.write(s.encode(output_encoding))
    
def print_lines(lines):
    for line in lines: print(line)
        
class Gedcom: 
    def __init__(self,items):
        self.items = items
    def print_items(self,out):
        for item in self.items:
            item.print_items(out) 
    
class Item:
    def __init__(self,line,children=None):
        if children is None: children = []
        temp = line.split(None,2)
        if len(temp) < 2: raise RuntimeError("Invalid line: " + line)
        self.level= int(temp[0])
        self.tag = temp[1]
        self.line = line
        self.children = children
        i = line.find(" " + self.tag + " ")
        if i > 0:
            self.text = line[i+len(self.tag)+2:] # preserves leading and trailing spaces
        else:
            self.text = ""
            
    def __repr__(self):
        return self.line #+"."+repr(self.children)
    def print_items(self,out):
        #if options.remove_empty_notes and self.tag == "NOTE" and self.children == [] and self.text.strip() == "": return  # drop empty note
        prefix = "%s %s " % (self.level,self.tag)
        if self.text == "":
            write(out,self.line)
        else:
            for line in self.text.splitlines():
                write(out,prefix+line)
                prefix = "%s CONT " % (self.level+1)
        for item in self.children:
            item.print_items(out)

def fixlines(lines,options):
    prevlevel = -1
    for i,line in enumerate(lines):
        #line = line.strip()
        tkns = line.split(None,1)
        
        if not tkns[0].isdigit() and options.add_cont_if_no_level_number: # 1.1.2
            # assume this is a continuation line
            line2 = "%s CONT %s" % (prevlevel+1,line)
            tkns = line2.split(None,1)
            lines[i] = line2
            if options.display_changes:
                print("-----------------------")
                print("Replaced:")
                print(line)
                print("With:")
                print(line2)
        elif len(tkns) == 1 and options.insert_dummy_tags: # 1.1.1
            if options.display_changes:
                print("-----------------------")
                print("Replaced:")
                print(tkns[0])
                print("With:")
                print(tkns[0] + " _DUMMY")
            line = tkns[0] + " _DUMMY"
            tkns = line.split(None,1)
            lines[i] = line
        prevlevel = int(tkns[0])

def parse1(lines,level,options):
    linenums = [] # list of line numbers having the specified level 
    for i,line in enumerate(lines):
        tkns = line.split(None,1)
        if int(tkns[0]) == level:
            linenums.append(i)
    
    items = []
    for i,j in zip(linenums,linenums[1:]+[None]):
        # i and j are line numbers of lines having specified level so that all lines in between have higher line numbers;
        # i.e. they form a substructure
        firstline = lines[i] #.strip()
        item = Item(firstline,parse1(lines[i:j],level+1,options))
        newitem = transform(item,options)
        if newitem == True: # no change
            items.append(item)
            continue
        item = newitem
        if options.display_changes:
            print("-----------------------")
            if item is None: 
                print("Deleted:")
                print_lines(lines[i:j])
            else:
                print("Replaced:")
                print_lines(lines[i:j])
                print("With:")
                if type(item) == list:
                    for it in item:
                        it.print_items(sys.stdout)
                else:
                    item.print_items(sys.stdout)
            print()
            
        if item is None: continue # deleted
        if type(item) == list:
            for it in item:
                items.append(it)
        else:
            items.append(item)
        
    return items

def allempty(items):
    for item in items:
        if item.tag not in ('CONT','CONC') or item.text.strip() != "": return False
    return True

def remove_multiple_blanks(text):
    return " ".join(text.split())

def transform(item,options):
    """
    Performs a transformation for the given Gedcom "item" (i.e. "line block")
    Returns one of
    - True: keep this item without changes
    - None: remove the item
    - item: use this item as a replacement (can be the same object as input if the contents have been changed)
    - list of items ([item1,item2,...]): replace the original item with these
    """
    if options.remove_invalid_marriage_dates:
        if item.line.strip() == "1 MARR":
            # replace
            #     1 MARR
            #     2 DATE AVOLIITTO
            # with
            #     1 MARR
            #     2 TYPE AVOLIITTO
            if len(item.children) > 0 and item.children[0].line.startswith("2 DATE AVOLIITTO"):
                item.children[0] = Item("2 TYPE AVOLIITTO")
                return item
            return True # no change

    if options.remove_invalid_divorce_dates:
        if item.line.strip() == "1 DIV":
            # replace
            #     1 DIV
            #     2 DATE .
            # with
            #     1 DIV Y
            if len(item.children) == 1 and item.children[0].line.startswith("2 DATE ."):
                return Item("1 DIV Y")  # this is not valid GEDCOM but Gramps will fix it

    if options.remove_empty_nameparts: # 2.1.3
        if item.line.strip() in ("2 GIVN","2 SURN"):
            # replace
            #     2 GIVN
            #     3 SOUR xxx
            # with
            #     2 SOUR xxx
            # (same with NOTE instead of SOUR)
            if len(item.children) == 0: return None
            if len(item.children) == 1 and item.children[0].tag in ('SOUR','NOTE'):
                sourline = item.children[0].line
                return Item("2" + sourline[1:])
            return None # empty GIVN/SURN and no subordinate lines => delete
        
    if options.remove_duplicate_sources: # 2.1.3
        if item.line.startswith("1 NAME"):
            prevline = ""
            newchildren = []
            changed = False
            for c in item.children:
                if c.line.startswith("2 SOUR") and c.line == prevline:
                    changed = True
                else:
                    newchildren.append(c)
                prevline = c.line
            item.children = newchildren
            if changed:
                return item
            else:
                pass # fall thru

    if options.insert_dummy_tags:
        if item.tag == "_DUMMY" and len(item.children) == 0: return None

    if options.remove_empty_notes: # 2.1.1
        if item.tag == "NOTE" and item.text.strip() == "" and allempty(item.children): return None

    if options.remove_empty_dates: # 2.2.4
        if item.tag == "DATE" and item.text.strip() in ('','.','?'): return None

    if options.remove_refn: # 2.1.4
        if item.tag == "REFN": return None

    if options.remove_stat: # 2.1.5
        if item.tag == "STAT": return None

    if options.save_level_3_notes: # 2.1.6
        if item.level == 2 and item.tag == 'PLAC' and len(item.children) == 1 and item.children[0].tag == "NOTE":
            # move NOTE from level 3 to level 2 (including possible CONT/CONC lines)
            # 2 PLAC %1#3 NOTE %2 => 2 PLAC %1#2 NOTE %2
            item2 = Item("2 NOTE %s" % item.children[0].text)
            for c in item.children[0].children:
                c.level -= 1
                c.line = "%s %s %s" % (c.level,c.tag,c.text)
                item2.children.append(c)
            item.children = []
            return [item,item2]

    if options.fix_addr: # 5.1.2
        if item.tag == "ADDR" and item.text.strip() != "":
            for c in item.children:
                if c.tag == "ADR1":
                    return True # no change, ADR1 already exists
            item.children.insert(0,Item("2 ADR1 " + item.text))
            item.text = ""
            item.line = "1 ADDR"
            return item

    if options.fix_events: # 5.1.4
        if (item.tag == "EVEN" and len(item.children) == 2):
            c1 = item.children[0]
            c2 = item.children[1]
            if c1.tag == "TYPE" and c1.text in ('Ei_julkaista','Kummit','Tutkijan omat') and c2.tag == 'PLAC':
                c2.tag = "NOTE"
                if c1.text == "Kummit": c2.text = "Description: " + c2.text
                c2.line = "%s %s %s" % (c2.level,c2.tag,c2.text)
                return item

    if options.fix_events_kaksonen: # 5.1.5
        if (item.tag == "EVEN" and len(item.children) == 1):
            c1 = item.children[0]
            if c1.tag == "TYPE" and c1.text in ('Kaksonen','Kolmonen'):
                c1.tag = "NOTE"
                c1.line = "%s %s %s" % (c1.level,c1.tag,c1.text)
                return item

    if options.remove_multiple_blanks: # 2.2.3
        if item.tag in ('NAME','PLAC'):
            newtext = remove_multiple_blanks(item.text)
            if newtext != item.text:
                item.text = newtext
                item.line = "%s %s %s" % (item.level,item.tag,item.text)
                return item

    return True # no change
    
    

def add_args(parser):
    #parser.add_argument('--concatenate_lines', action='store_true',
    #                    help='Combine all CONT and CONC lines')
    
    parser.add_argument('--add_cont_if_no_level_number', action='store_true',
                        help='Add a CONT line if there is no level number')
    parser.add_argument('--insert_dummy_tags', action='store_true',
                        help='Insert s _DUMMY tag if a tag is missing')
    parser.add_argument('--remove_empty_dates', action='store_true',
                        help='Remove invalid DATE tags')
    parser.add_argument('--remove_empty_notes', action='store_true',
                        help='Remove empty NOTE tags')
    parser.add_argument('--remove_invalid_marriage_dates', action='store_true',
                        help='Remove DATE AVOLIITTO tags')
    parser.add_argument('--remove_invalid_divorce_dates', action='store_true',
                        help='Remove invalid DATEs for DIV tags')
    parser.add_argument('--remove_empty_nameparts', action='store_true',
                        help='Remove empty GIVN and SURN tags')
    parser.add_argument('--remove_duplicate_sources', action='store_true',
                        help='Remove duplicate SOUR lines under NAME')
    parser.add_argument('--remove_refn', action='store_true',
                        help='Remove REFN tags')
    parser.add_argument('--remove_stat', action='store_true',
                        help='Remove STAT tags')
    parser.add_argument('--save_level_3_notes', action='store_true',
                        help='Move level 3 NOTEs to level 2 to save them')
    parser.add_argument('--fix_addr', action='store_true',
                        help='Insert ADR1 tags under ADDR')
    parser.add_argument('--fix_events', action='store_true',
                        help='Change PLAC tags to NOTEs under certain events')
    parser.add_argument('--fix_events_kaksonen', action='store_true',
                        help='Change event types "Kaksonen" and "Kolmonen" to NOTEs')
    parser.add_argument('--remove_multiple_blanks', action='store_true',
                        help='Remove _multiple consecutive spaces in person and place names')
     
def initialize(run_args):
    pass

def process(run_args,output):
    class Options: pass
    options = Options()
    options.__dict__= run_args
    lines = []
    input_gedcom = options.input_gedcom
    input_encoding = options.encoding
    lines = open(input_gedcom,encoding=input_encoding).readlines()
    lines = [line[:-1] for line in lines]
    fixlines(lines,options)
    items = parse1(lines,level=0,options=options)
    g = Gedcom(items)
    output.original_line = None
    g.print_items(output)
        
if __name__ == "__main__":
    fname = sys.argv[1]
    g = parse_gedcom_from_file(fname,encoding=input_encoding)
    #out = open("liisa","wb")
    #g.print_items(out)
    g.print_items(sys.stdout)


