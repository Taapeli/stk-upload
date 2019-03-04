#!/usr/bin/env python3

from flask_babelex import _

from .. import transformer

version = "1.0"
name = _("Dates")

#doclink = "http://taapeli.referata.com/wiki/Gedcom-Dates-ohjelma"

def add_args(parser):
    pass

def initialize(options):
    return Dates()

class Dates(transformer.Transformation):
    def transform(self,item,options,phase):
        """
        Fix dates of the forms:
        
        31.12.1888 -> 31 DEC 1888
        """
        if item.tag == "DATE":
            pass
        return True

