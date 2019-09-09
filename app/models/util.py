import os
import time
from pprint import pprint
import ast
import _ast

def generate_name(name):
    """
    Generates a new file name for a new version of a gedcom file
    
    Input: the base gedcom name with full path; e.g.
        gedcoms/kku/test-gedcom.ged
    Output: the name for an nonexistent file with format name.<n> where <n> is a sequence number. E.g.
        gedcoms/kku/test-gedcom.ged.4
        (if the largest used version number is currently 3) 
    """
    dirname = os.path.dirname(name)
    gedcomname = os.path.basename(name)
    maxnum = -1
    for name in os.listdir(dirname):
        if name.startswith(gedcomname+"."):
            num = int(name.split(".")[-1])
            if num > maxnum: maxnum = num
    newname = "{}.{}".format(gedcomname,maxnum+1)
    return os.path.join(dirname,newname)

def format_timestamp(ts=None):
    if ts is None: ts = time.time()
    return time.strftime("%-d.%-m.%Y %-H:%M", time.localtime(ts))

def format_date(ts=None):
    if ts is None: ts = time.time()
    return time.strftime("%Y-%m-%d", time.localtime(ts))

def guess_encoding(fname):
    encodings = [
        "UTF-8",
        "UTF-8-SIG",
        "ISO8859-1",
    ]
    for encoding in encodings:
        try:
            s = open(fname,encoding=encoding).read()
            return encoding
        except UnicodeDecodeError:
            pass
    return None

from dataclasses import dataclass


def scan_endpoints_for_file(fname):    
    source = open(fname).read()
    root = ast.parse(source)

    @dataclass
    class Info: 
        name: str
        urls: list = None
        login_required: bool = False
        roles_accepted: str = None
        roles_required: str = None

    endpoints = {}
    for node in ast.iter_child_nodes(root):
        if hasattr(node,'decorator_list'):
            #print(node.name,node.decorator_list)
            info = Info(node.name)
            
            for call in node.decorator_list:
                if isinstance(call,_ast.Name):
                    if call.id == "login_required":
                        info.login_required = True
                if isinstance(call,_ast.Call):
                    if isinstance(call.func,_ast.Attribute):
                        decorator_name = call.func.attr
                    if isinstance(call.func,_ast.Name):
                        decorator_name = call.func.id
                    arglist = [arg.s for arg in call.args]
                    args = ",".join(arglist)
                    if decorator_name == 'route':
                        if len(arglist) != 1:
                            raise RuntimeError("Invalid route "+ arglist[0])
                        if info.urls is None: info.urls = []
                        info.urls.append(arglist[0])
                    if decorator_name == 'roles_accepted':
                        info.roles_accepted = arglist
                    if decorator_name == 'roles_required':
                        info.roles_required = arglist
            if info.urls is not None:
                for url in info.urls:
                    endpoints[url] = info
    return endpoints

def scan_endpoints():
    endpoints = {}
    for dirname,dirs,files in os.walk("app"):
        for file in files:
            if file.endswith(".py"):
                fname = os.path.join(dirname,file)
                endpoints1 = scan_endpoints_for_file(fname)
                #pprint(endpoints)   
                endpoints.update(endpoints1)     
    return endpoints



