#!/usr/bin/env python3
import datetime
from flask_babelex import _

from .. import transformer

import re

version = "1.0"
name = _("Dates")
docline = _('Correct some invalid date formats')

#doclink = "http://taapeli.referata.com/wiki/Gedcom-Dates-ohjelma"

def add_args(parser):
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


def initialize(options):
    return Dates()

def fmtdate(y,m,d):
    try:
        dt = datetime.date(int(y),int(m),int(d))
        return dt.strftime("%d %b %Y").upper()
    except:
        return None


oneortwodigits = r"\d{1,2}"
twodigits = r"\d{2}"
fourdigits = r"\d{4}"
dash = r"-"
sep = "[\.,-/]"

def p(**kwargs):
    ret = ""
    for name,pat in kwargs.items():
        ret += f"(?P<{name}>{pat})"
    return ret
    
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
    def transform(self,item,options,phase):
        """
        Fix dates of the forms:
        
        31.12.1888 -> 31 DEC 1888
        31,12,1888 -> 31 DEC 1888
        31-12-1888 -> 31 DEC 1888
        31/12/1888 -> 31 DEC 1888
        .12.1888   ->    DEC 1888
        12.1888    ->    DEC 1888
        12/1888    ->    DEC 1888
        12-1888    ->    DEC 1888
        0.12.1888   ->    DEC 1888
        00.12.1888   ->    DEC 1888
        00.00.1888   ->    1888
        00 JAN 1888   ->    JAN 1888
        """
        if item.tag == "DATE":
            value = item.value.strip()

            if options.handle_dd_mm_yyyy:
                    # 31.12.1888 -> 31 DEC 1888
                    # 31,12,1888 -> 31 DEC 1888
                    # 31-12-1888 -> 31 DEC 1888
                    # 31/12/1888 -> 31 DEC 1888
                    r = re.match(r"(?P<dd>\d{1,2})" +
                                 sep +
                                 r"(?P<mm>\d{1,2})" +
                                 sep +
                                 r"(?P<yyyy>\d{4})",value)
                    if r:
                        y = r.group('yyyy')
                        m = r.group('mm')
                        d = r.group('dd')
                        val = fmtdate(y,m,d)
                        if val:
                            item.value = val
                            return item
    
            if options.handle_zeros:
                # 0.0.1888 -> 1888
                # 00.00.1888 -> 1888
                r = re.match(r"0{1,2}\.0{1,2}\." +
                             r"(?P<yyyy>\d{4})",value)
                if r:
                    item.value = r.group('yyyy')
                    return item
            
                # 00.12.1888 -> DEC 1888
                # .12.1888 -> DEC 1888
                #  12.1888 -> DEC 1888
                r = re.match(r"(0{0,2}\.)?" +
                             r"(?P<mm>\d{1,2})" +
                             sep +
                             r"(?P<yyyy>\d{4})",value)
                if r:
                    y = r.group('yyyy')
                    m = r.group('mm')
                    d = 1
                    val = fmtdate(y,m,d)
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
                    century = r.y1[0:2]
                    item.value = f"FROM {r.y1} TO {century}{r.y2}"
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
                r = match(value,y=fourdigits,sep1=dash,m=twodigits,sep2=dash,d=twodigits)
                if r:
                    val = fmtdate(r.y,r.m,1)
                    if val:
                        item.value = val[3:]
                        return item

        return True

