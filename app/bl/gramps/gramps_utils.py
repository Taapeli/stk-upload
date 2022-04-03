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

'''
Created on Aug 26, 2020

@author: kari
'''
from bl.gramps.gramps_loader import get_upload_folder
import os
import subprocess
from collections import defaultdict

test_output = None

def gramps_verify(gramps_runner, lang, username, batch_id, xmlfile, newfile):
    if test_output:
        lines = test_output.splitlines()
        import time
        time.sleep(3)
    else:
        upload_folder = get_upload_folder(username) 
        pathname = os.path.join(upload_folder, batch_id, xmlfile)
        export_file = os.path.join(upload_folder, batch_id, newfile)
        #cmd = f"unset PYTHONPATH;env;"
        #cmd += f"rm -rf ~/{xmlfile}.media;"
        #cmd += f"/usr/bin/gramps -i {pathname} -a tool -p name=verify" #.split()
        cmd = [gramps_runner, lang, xmlfile, pathname]
        cmd = f"{gramps_runner} '{lang}' '{xmlfile}' '{pathname}' '{export_file}'"
        print("cmd:",cmd)
        res = subprocess.run(cmd, shell=True, capture_output=True, encoding="utf-8")
        print(res.stderr)
        lines = res.stdout.splitlines()
    rsp = defaultdict(list)
    for line in lines:
        if line[1:2] == ":":
            msgtype, _msg = line.split(",", maxsplit=1)
            rsp[msgtype.strip()].append(line)
    return rsp


def run_supertool(supertool_runner, lang, username, batch_id, xmlfile, scriptfile, outputfile):
    upload_folder = get_upload_folder(username) 
    pathname = os.path.join(upload_folder, batch_id)
    supertool_runner = os.path.abspath(supertool_runner)
    scriptfile_full = os.path.abspath(scriptfile)
    cmd = f"{supertool_runner} '{lang}' '{xmlfile}' '{scriptfile_full}' '{outputfile}' '{os.getcwd()}'"
    print("cmd:",cmd)
    res = subprocess.run(cmd, shell=True, cwd=pathname, capture_output=True, encoding="utf-8")
    print(res.stderr)
    lines = res.stdout.splitlines()
    return lines


def get_nonstandard_types(username,batch_id):
    upload_folder = get_upload_folder(username) 
    pathname = os.path.join(upload_folder, batch_id, "nonstandard-types.csv")
    import csv
    if os.path.exists(pathname):
        rows = list(csv.reader(open(pathname)))
    else:
        rows = []
    return rows
    
    
