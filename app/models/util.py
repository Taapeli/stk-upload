#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu,
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import time
#from pprint import pprint
import ast
import _ast
import traceback

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
    """Converts timestamp (seconds since the Epoch) to string like '23.05.2021 15:10'.
       Returns current time, is no ts is given.
    """
    if ts is None: ts = time.time()
    return time.strftime("%d.%m.%Y %H:%M", time.localtime(ts))

def format_ms_timestamp(ts_ms=None, opt="m"):
    """Converts timestamp (ms since the Epoch) to string (by 'm' minute or 'd' day)
       Returns "", is no ts is given.

        Example '23.5.2021 15:10' or '23.5.2021'.
    """
    if ts_ms:
        ts = float(ts_ms) / 1000.
        if opt == "d":
            return time.strftime("%-d.%-m.%Y", time.localtime(ts))
        else:
            return time.strftime("%-d.%-m.%Y %H:%M", time.localtime(ts))
    return ""

def format_date(ts=None):
    """Converts the ts (seconds since the Epoch) to ISO date string like '2021-05-23'.
    """
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
            _s = open(fname,encoding=encoding).read()
            return encoding
        except UnicodeDecodeError:
            pass
    return None

from dataclasses import dataclass


def scan_endpoints_for_file(fname):    
    print(f"models.util.scan_endpoints_for_file: '{fname}'")
    endpoints = {}
    source = open(fname, encoding="utf-8").read()
    try:
        root = ast.parse(source)
    except SyntaxError as _e:
        traceback.print_exc()
        return endpoints

    @dataclass
    class Info: 
        name: str
        urls: list = None
        login_required: bool = False
        roles_accepted: str = None
        roles_required: str = None

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
                    if decorator_name == 'route':
                        arglist = [arg.s for arg in call.args]
                        #args = ",".join(arglist)
                        if len(arglist) != 1:
                            raise RuntimeError("Invalid route "+ arglist[0])
                        if info.urls is None: info.urls = []
                        info.urls.append(arglist[0])
                    if decorator_name == 'roles_accepted':
                        arglist = [arg.s for arg in call.args]
                        info.roles_accepted = arglist
                    if decorator_name == 'roles_required':
                        arglist = [arg.s for arg in call.args]
                        info.roles_required = arglist
            if info.urls is not None:
                for url in info.urls:
                    endpoints[url] = info
    return endpoints

def scan_endpoints():
    endpoints = {}
    for dirname, _dirs, files in os.walk("app"):
        for file in files:
            if file.endswith(".py"):
                fname = os.path.join(dirname,file)
                endpoints1 = scan_endpoints_for_file(fname)
                #pprint(endpoints)   
                endpoints.update(endpoints1)     
    return endpoints



