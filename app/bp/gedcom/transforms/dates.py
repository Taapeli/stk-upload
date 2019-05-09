#!/usr/bin/env python3
import datetime
from flask_babelex import _

from .. import transformer
from .. import gedcom_analyze


import re
import sys
from _collections import defaultdict

version = "1.0"
name = _("Dates")
docline = _('Correct some invalid date formats')

#doclink = "http://taapeli.referata.com/wiki/Gedcom-Dates-ohjelma"

def add_args(parser):
    parser.add_argument('--display_invalid_dates', action='store_true',
                        help=_('Display invalid dates'))
    parser.add_argument('--handle_dd_mm_yyyy', action='store_true',
                        help=_('Change 31.12.1999 to 31 DEC 1999'))
    parser.add_argument('--handle_yyyy_mm_dd', action='store_true',
                        help=_('Change 1999-12-31 to 31 DEC 1999'))
    parser.add_argument('--handle_yyyy_mm', action='store_true',
                        help=_('Change 1999-12 to DEC 1999'))
    parser.add_argument('--handle_zeros', action='store_true',
                        help=_('Change [00.]12.1999 to DEC 1999'))
    parser.add_argument('--handle_zeros2', action='store_true',
                        help=_('Change 00 DEC 1999 to DEC 1999'))
    parser.add_argument('--handle_intervals', action='store_true',
                        help=_('Change 1950-[19]59 to FROM 1950 TO 1959'))
    parser.add_argument('--handle_intervals2', action='store_true',
                        help=_('Change 1950-/>1950 to FROM/AFT 1950'))
    parser.add_argument('--handle_intervals3', action='store_true',
                        help=_('Change -1950/<1950 to TO/BEF 1950'))


def initialize(options):
    return Dates()

def fmtdate(y,m,d):
    try:
        dt = datetime.date(int(y),int(m),int(d))
        return dt.strftime("%d %b %Y").upper()
    except:
        return None


zerototwozeros = r"0{0,2}"
oneortwodigits = r"\d{1,2}"
twodigits = r"\d{2}"
fourdigits = r"\d{4}"
dot = r"\."
dash = r"-"
sep = "[\.,-/]"
gt = "\>"
lt = "\<"

# regex helpers
def p(**kwargs):
    ret = ""
    for name,pat in kwargs.items():
        ret += f"(?P<{name}>{pat})"
    return ret

def optional(pat):
    return f"({pat})?"    

def match(s,**kwargs):    
    pat = p(**kwargs)
    flags = re.VERBOSE
    r = re.fullmatch(pat,s,flags)
    if r is None: return None
    class Ret: pass
    ret = Ret()
    ret.__dict__ = r.groupdict()
    return ret

class Dates(transformer.Transformation):
    def __init__(self):
        self.invalid_dates = defaultdict(list)
        
    def finish(self,options):
        if self.invalid_dates:
            print("<p><b>",_("Invalid dates:"),"</b><p>")
            for date in sorted(self.invalid_dates):
                linenums = self.invalid_dates[date]
                links = []
                for linenum in linenums:
                    link = f"<a href=# class=gedcomlink>{linenum}</a>"
                    links.append(link)
                if len(links) > 10: links = links[0:10] + ["..."]
                linkstr = ", ".join(links)
                print("",_("%(date)s (line %(linkstr)s)<br>",date=date,linkstr=linkstr))

    def transform(self,item,options,phase):
        """
        Fix dates of the forms:
        
        31.12.1888    -> 31 DEC 1888
        31,12,1888    -> 31 DEC 1888
        31-12-1888    -> 31 DEC 1888
        31/12/1888    -> 31 DEC 1888
        1888-12-31    -> 31 DEC 1888
        .12.1888      ->    DEC 1888
        12.1888       ->    DEC 1888
        12/1888       ->    DEC 1888
        12-1888       ->    DEC 1888
        0.12.1888     ->    DEC 1888
        00.12.1888    ->    DEC 1888
        00.00.1888    ->    1888
        00 JAN 1888   ->    JAN 1888
        1950-[19]59   -> FROM 1950 TO 1959
        1950-         -> FROM 1950 
        >1950         -> FROM 1950 
        -1950         -> TO 1950 
        <1950         -> TO 1950 
        """
        self.options = options

        if item.tag == "DATE":
            value = item.value.strip()


            if options.display_invalid_dates:
                valid = gedcom_analyze.valid_date(value)
                if not valid:
                    self.invalid_dates[value].append(item.linenum)

            if options.handle_dd_mm_yyyy:
                    # 31.12.1888 -> 31 DEC 1888
                    # 31,12,1888 -> 31 DEC 1888
                    # 31-12-1888 -> 31 DEC 1888
                    # 31/12/1888 -> 31 DEC 1888
                    r = match(value,
                              d=oneortwodigits,sep1=sep,
                              m=oneortwodigits,sep2=sep,
                              y=fourdigits)
                    if r:
                        val = fmtdate(r.y,r.m,r.d)
                        if val:
                            item.value = val
                            return item
    
            if options.handle_zeros:
                # 0.0.1888 -> 1888
                # 00.00.1888 -> 1888
                r = match(value,z1=zerototwozeros,dot=dot,z2=zerototwozeros,y=fourdigits)
                if r:
                    item.value = r.y
                    return item
            
                # 00.12.1888 -> DEC 1888
                # .12.1888 -> DEC 1888
                #  12.1888 -> DEC 1888
                r = match(value,z=zerototwozeros,dot1=dot,m=oneortwodigits,dot2=dot,y=fourdigits)
                if not r:
                    r = match(value,m=oneortwodigits,dot=dot,y=fourdigits)
                if r:
                    val = fmtdate(r.y,r.m,1)
                    if val:
                        item.value = val[3:]
                        return item

            if options.handle_zeros2:
                # 0 JAN 1888   ->    JAN 1888
                if value.startswith("0 "):
                    item.value = item.value[2:]
                    return item
                
                # 00 JAN 1888   ->    JAN 1888
                if value.startswith("00 "):
                    item.value = item.value[3:]
                    return item
    
    
            if options.handle_intervals:
                # 1888-1899 
                r = match(value,y1=fourdigits,sep=dash,y2=fourdigits)
                if r:
                    century = r.y1[0:2]
                    item.value = f"FROM {r.y1} TO {r.y2}"
                    return item
    
                # 1888-99
                r = match(value,y1=fourdigits,sep=dash,y2=twodigits)
                if r:
                    if int(r.y2) > int(r.y1[2:]): 
                        century = r.y1[0:2]
                        item.value = f"FROM {r.y1} TO {century}{r.y2}"
                        return item
                    
            if options.handle_intervals2:
                # 1888-, >1888
                tag = item.path.split(".")[-2]
                kw = "AFT"
                if tag in ('RESI','OCCU'): kw = "FROM"
                r = match(value,y=fourdigits,sep=dash)
                if r:
                    item.value = f"{kw} {r.y}"  
                    return item
                r = match(value,sep=gt,y=fourdigits)
                if r:
                    item.value = f"{kw} {r.y}"  
                    return item
    
            if options.handle_intervals3:
                # -1888, <1888
                tag = item.path.split(".")[-2]
                kw = "BEF"
                if tag in ('RESI','OCCU'): kw = "TO"
                r = match(value,sep=dash,y=fourdigits)
                if r:
                    item.value = f"{kw} {r.y}" 
                    return item
                r = match(value,sep=lt,y=fourdigits)
                if r:
                    item.value = f"{kw} {r.y}"  
                    return item
    
            if options.handle_yyyy_mm_dd:
                # 1888-12-31
                r = match(value,y=fourdigits,sep=dash,m=twodigits,sep2=dash,d=twodigits)
                if r:
                    val = fmtdate(r.y,r.m,r.d)
                    if val:
                        item.value = val
                        return item
    
            if options.handle_yyyy_mm:
                # 1888-12
                r = match(value,y=fourdigits,sep1=dash,m=twodigits)
                if r:
                    val = fmtdate(r.y,r.m,1)
                    if val:
                        item.value = val[3:]
                        return item

        return True

