import difflib
import importlib
import json
import os
import pprint
import sys
import logging

from pprint import pprint
from types import SimpleNamespace
from lxml import etree

import pytest

from bp.gedcom.transformer import Transformer

logging.basicConfig(level=logging.INFO)

testdata_dir = "testdata"

class Out:
    def __init__(self):
        self.lines = []
    def emit(self,line):
        self.lines.append(line)


def load_options(fname):
    options_fname = fname.replace(".ged","_options.json")
    if os.path.exists(options_fname): 
        options_string = open(options_fname).read()
        options_data = json.loads(options_string)
    else:
        options_data = {}
    options = SimpleNamespace(**options_data)
    options.encoding = 'utf-8'
    options.display_changes = False
    return options

def find_subdirs():
    for name in os.listdir(testdata_dir):
        subdirname = os.path.join(testdata_dir,name)
        if not os.path.isdir(subdirname): continue
        if not os.path.exists("app/bp/gedcom/transforms/"+name+".py"): continue
        transform_module = importlib.import_module("bp.gedcom.transforms."+name)
        yield subdirname,transform_module


def printlines(lines):
    for line in lines:
        print(line)
        
def is_header(line):
    return line.startswith("[")

def splitlist(input_list,func):
    indexes = [i for i,line in enumerate(input_list) if func(line)]
    resultlist = [input_list[i:j] for (i,j) in zip(indexes,indexes[1:]+[None])]
    return resultlist

def yieldsections(input_list):
    sections = splitlist(input_list, is_header)  
    for sectlines in sections:
        section_name = sectlines[0].strip()[1:-1]
        lines = sectlines[1:]
        lines = [line.replace("\n","") for line in lines if line.strip() != ""]
        yield section_name,lines

def load_options(lines):
    options = {}
    for line in lines:
        if line.strip() == "": continue
        if line.strip().startswith("#"): continue
        key,value = line.split("=", maxsplit=1)
        key = key.strip()
        value = value.strip()
        if value.lower() == "true": 
            value = True
        elif value.lower() == "false": 
            value = False
        options[key] = value
    return options

def load_testdata(fname):
    lines = open(fname).readlines()
    options = {} #SimpleNamespace()
    for section_name,section_lines in yieldsections(lines):
        if section_name == "description":
            continue  
        if section_name == "options":
            options = load_options(section_lines)  
        if section_name == "original":
            lines_orig = section_lines  
        if section_name == "expected":
            lines_expected = section_lines  
    #options.encoding = 'utf-8'
    #options.display_changes = False
    return options,lines_orig,lines_expected  

class Options_parser:
    def __init__(self):
        self.options = SimpleNamespace()
        self.options_dict = dict(
            encoding = 'utf-8',
            display_changes = False
        )
        
    def add_argument(self, name, name2=None, action='store', 
                     type=str,  # @ReservedAssignment
                     default=None, 
                     help=None, # @ReservedAssignment
                     nargs=0,   # @UnusedVariable 
                     choices=None):
        if name.startswith("--"): name = name[2:]
        if type == str:
            self.options_dict[name] = ""  
        if type == bool:
            self.options_dict[name] = False  
        if type == int:
            self.options_dict[name] = default  
        #print(name,default)
        self.options_dict[name] = default  

def scan_subdir(dirname,transform_module):
    for name in sorted(os.listdir(dirname)):
        if not name.endswith(".test"): continue
        yield dirname,name

def scan_all_gedcoms():
    res = []
    for subdirname,transformer in find_subdirs():
        for dirname,name in scan_subdir(subdirname,transformer):
            res.append( (dirname,name,transformer) )
    return res
            
tests = scan_all_gedcoms()

using_pytest = True

@pytest.mark.parametrize('dirname,name,transform_module', tests )
def test_gedcom(dirname,name,transform_module):  
        print(name)      
        fname = os.path.join(dirname,name)
        transformed_name = name.replace(".test","_transformed.ged")
        expected_name = name.replace(".test","_expected.txt")
        expected_fname = os.path.join(dirname,expected_name)
        #if not os.path.exists(expected_fname): continue
        options_parser = Options_parser()            
        transform_module.add_args(options_parser)
        options,lines_orig,lines_expected = load_testdata(fname)
        options_parser.options_dict.update(options)
        options = SimpleNamespace(**options_parser.options_dict)

        trace = False
        if trace:
            print("options:")
            pprint(options_parser.options_dict)
            print("lines_orig:")
            pprint(lines_orig)
            pprint("lines_expected:")
            pprint(lines_expected)
        transformer = Transformer(options,transform_module,None)
        gedcom = transformer.transform_lines(lines_orig)
        out = Out()
        gedcom.print_items(out)
        if trace:
            print("lines_transformed:")
            pprint(out.lines)
        #pprint.pprint(out.lines)
        #if not os.path.exists(expected_fname): 
        #    open(expected_fname,"w").writelines(out.lines)
        diff = list(difflib.context_diff(out.lines,lines_expected,
                fromfile=transformed_name, tofile=expected_name))
        printlines(diff)
        #sys.stdout.writelines(diff)
        if using_pytest:
            assert len(diff) == 0

if __name__ == "__main__":
    using_pytest = False
    for dirname,name,transform_module in tests:
        test_gedcom(dirname,name,transform_module)
    
    
    
    