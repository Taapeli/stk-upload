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
import subprocess
import sys

from collections import defaultdict
from pathlib import Path
from pprint import pprint
from subprocess import PIPE, STDOUT

from bl.gramps.gramps_loader import get_upload_folder
from bl.batch.root import Root

def gramps_run_for_batch(app, toolname, lang, username, batch_id, newfile=None, **args):
    batch = Root.get_batch(username, batch_id)

    upload_folder = get_upload_folder(username) 
    inputfile = os.path.join(upload_folder, batch_id, batch.xmlname)
    inputfile = os.path.realpath(inputfile)

    if newfile:
        export_file = os.path.join(upload_folder, batch_id, newfile)
        export_file = os.path.realpath(export_file)
    else:
        export_file = None

    return gramps_run(app, toolname, lang, username, inputfile, export_file, batch_id=batch_id, **args)


def gramps_run(app, toolname, lang, username, inputfile, export_file=None, **args):
    print("inputfile",inputfile)

    GRAMPS = app.config.get("GRAMPS")   # list, e.g. ["/usr/bin/gramps"] or  ["/usr/bin/gramps", "-q"] or ["python3", "Gramps.py"]
    if not GRAMPS: 
        print("GRAMPS not defined in config.py")
        return []

    GRAMPS_CWD = app.config.get("GRAMPS_CWD")
    GRAMPS_PYTHONPATH = app.config.get("GRAMPS_PYTHONPATH")
    GRAMPS_RESOURCES = app.config.get("GRAMPS_RESOURCES")

    xmlname = os.path.basename(inputfile)

    env = {}
    env.update(os.environ)
    env["LANGUAGE"] = lang

    import neo4j
    print("neo4j:",neo4j.__file__)
    path = str(Path(neo4j.__file__).parent.parent)
    if GRAMPS_PYTHONPATH:
        path += ":" + GRAMPS_PYTHONPATH
    env["PYTHONPATH"] = path

    if GRAMPS_RESOURCES:
        env["GRAMPS_RESOURCES"] = GRAMPS_RESOURCES

    path = Path.home() / (xmlname + ".media")
    print("deleting", path)
    cmd = ["/bin/rm","-rf",  path]
    print(cmd)
    subprocess.run(cmd)

    if export_file:
        print("deleting", export_file)
        cmd = ["/bin/rm","-f",  export_file]
        print(cmd)
        subprocess.run(cmd)

    options = [f"name={toolname}",f"basedir={os.getcwd()}"] + [f"{name}={value}" for (name,value) in args.items()]
    optionstring = ",".join(options)
    cmd = GRAMPS + [ 
           "-q",
           "-i", inputfile,
           "-a", "tool",
           "-p", optionstring
          ]
    if export_file:
        cmd.extend(["-e", export_file])
    print("gramps_run:")
    pprint(cmd)
    #pprint(env)
    p = subprocess.run(cmd, cwd=GRAMPS_CWD, env=env, encoding='utf-8', stdout=PIPE, stderr=STDOUT)

    path = Path.home() / (xmlname + ".media")
    print("deleting", path)
    cmd = ["/bin/rm","-rf",  path]
    print(cmd)
    subprocess.run(cmd)

    return p.stdout.splitlines()



def run_supertool(app, lang, username, batch_id, xmlfile, scriptfile, outputfile):

    lines = gramps_run_for_batch(app, "SuperTool", lang, 
            username, batch_id, script=scriptfile, output=outputfile, args=os.getcwd())
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
    
    
