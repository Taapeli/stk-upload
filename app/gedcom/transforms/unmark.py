#!/usr/bin/env python3
"""
Restores marked tags: <tag>-X -> <tag>
"""

_VERSION = "1.0"
#from transforms.model.gedcom_line import GedcomLine

def add_args(parser):
    pass

def initialize(run_args):
    pass

def phase3(run_args, gedline, f):
    if gedline.tag.endswith("-X"):
        gedline.tag = gedline.tag[:-2]
#       line = "{} {} {}".format(gedline.level, gedline.tag, gedline.value)
    f.emit(gedline.get_line())
