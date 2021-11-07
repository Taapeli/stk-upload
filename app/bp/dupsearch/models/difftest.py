from difflib import SequenceMatcher, _mdiff
import xml.dom.minidom
from pprint import pprint

a = "siirtolaisuusinstituutti"
b = "siirtolaisinstituutti"

a = [
    ("syntymä","12.10.1800","Turku"),
    ("kaste","12.10.1800","Turku"),
]
b = [
    ("syntymä","12.10.1800","Turku"),
    ("kaste","12.11.1800","Turku"),
    ("kuolema","12.11.1888","Turku"),
]

# m = SequenceMatcher(a=a,b=b)
# for x in m.get_matching_blocks():
#     print(x)

SEP = "###"
a2 = [SEP.join(x) for x in a]    
b2 = [SEP.join(x) for x in b]    
table = "<table>"
for x in _mdiff(a2,b2):
    print(x)

def getText(node):
    rc = []
    for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE:
            rc.append(child.data)
    return ''.join(rc)

def fixtable(table):
    table = table.replace("ä","a")
    print("zz",table)
    dom = xml.dom.minidom.parseString(table)
    print("doc",dom)
    for span in dom.getElementsByTagName("span"):
        text = getText(span)
        print("span",span, text)
        parts = text.split(SEP)
        if len(parts) > 1:
            print("found",parts)
            #pprint(dir(span))
            #span.childNodes[0].data = "aaa"
            textNode = dom.createTextNode('Some textual content.')
            span.removeChild(span.firstChild)
            parent = span.parentNode
            parent.removeChild(span)
            for part in parts:
                spanNode = dom.createElement("span")
                textNode = dom.createTextNode(part)
                spanNode.appendChild(textNode)
                parent.appendChild(spanNode)
    return dom.toxml()

STARTADD = "$$$0"             
STARTSUB = "$$$1"             
STARTCHG = "$$$2"             
END = "$$$3"             

def fixline1(line):
    line = line.strip()
    line = line.replace('\0+',STARTADD). \
                 replace('\0-',STARTSUB). \
                 replace('\0^',STARTCHG). \
                 replace('\1',END). \
                 replace('\t','&nbsp;')
    spans = line.split("$$$")
    print(spans)
    return line

def fixline(line):
    line = line.strip()
    print("line:",line)
    KEYS = ['\0+','\0-','\0^']
    for key in KEYS:
        i = 0
        while True:
            i = line.find(key, i)
            if i < 0:
                break
            j = line.find('\1',i)
            span = line[i+2:j]
            span2 = span.replace(SEP,'\1'+SEP+key)
            line = line[0:i+2] + span2 + line[j:]
            i = i+2+len(span2)
    print("line2:",line)
    return line

for (linenum1,line1),(linenum2,line2),flag in _mdiff(a2,b2):
    line = "<tr><td>" + fixline(line1) + "</td><td>" + fixline(line2) + "</td></tr>\n"
    #line = "<tr><td>" + line1.strip() + SEP + line2.strip() + "</td></tr>\n"
    #line = fixline(line)
    table += line
#    x = x.replace(r'\x00','<span class=a>')
table += "</table>"
    
table = table.replace('\0+','<span class="diff_add">'). \
             replace('\0-','<span class="diff_sub">'). \
             replace('\0^','<span class="diff_chg">'). \
             replace('\1','</span>'). \
             replace('\t','&nbsp;')
             
STARTADD = "$$$0"             
STARTSUB = "$$$1"             
STARTCHG = "$$$2"             
END = "$$$3"             
table1 = table.replace('\0+',STARTADD). \
             replace('\0-',STARTSUB). \
             replace('\0^',STARTCHG). \
             replace('\1',END). \
             replace('\t','&nbsp;')
#table = fixtable(table)
table = table.replace(SEP,"<td>")

print(table)    