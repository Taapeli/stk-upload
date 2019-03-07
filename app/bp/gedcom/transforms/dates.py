#!/usr/bin/env python3
import datetime
from flask_babelex import _

from .. import transformer

import re

version = "1.0"
name = _("Dates")

#doclink = "http://taapeli.referata.com/wiki/Gedcom-Dates-ohjelma"

def add_args(parser):
    pass

def initialize(options):
    return Dates()

def fmtdate(y,m,d):
    try:
        dt = datetime.date(y,m,d)
        return dt.strftime("%d %b %Y").upper()
    except:
        return None

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
        sep = "[\.,-/]"
        if item.tag == "DATE":
            # 31.12.1888 -> 31 DEC 1888
            # 31,12,1888 -> 31 DEC 1888
            # 31-12-1888 -> 31 DEC 1888
            # 31/12/1888 -> 31 DEC 1888
            r = re.match(r"(?P<dd>\d{1,2})" +
                         sep +
                         r"(?P<mm>\d{1,2})" +
                         sep +
                         r"(?P<yyyy>\d{4})",item.value.strip())
            if r:
                y = int(r.group('yyyy'))
                m = int(r.group('mm'))
                d = int(r.group('dd'))
                val = fmtdate(y,m,d)
                if val:
                    item.value = val
                    return item

            # 0.0.1888 -> 1888
            # 00.00.1888 -> 1888
            r = re.match(r"0{1,2}\.0{1,2}\." +
                         r"(?P<yyyy>\d{4})",item.value.strip())
            if r:
                item.value = r.group('yyyy')
                return item
        
            # 00.12.1888 -> DEC 1888
            # .12.1888 -> DEC 1888
            #  12.1888 -> DEC 1888
            r = re.match(r"(0{0,2}\.)?" +
                         r"(?P<mm>\d{1,2})" +
                         sep +
                         r"(?P<yyyy>\d{4})",item.value.strip())
            if r:
                y = int(r.group('yyyy'))
                m = int(r.group('mm'))
                d = 1
                val = fmtdate(y,m,d)
                if val:
                    item.value = val[3:]
                    return item

            # 0 JAN 1888   ->    JAN 1888
            if item.value.startswith("0 "):
                item.value = item.value[2:]
                return item
            
            # 00 JAN 1888   ->    JAN 1888
            if item.value.startswith("00 "):
                item.value = item.value[3:]
                return item

        return True

