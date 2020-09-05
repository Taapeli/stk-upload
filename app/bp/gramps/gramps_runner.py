'''
Created on Aug 26, 2020

@author: kari
'''
from bp.gramps.gramps_loader import get_upload_folder
import os
import subprocess
from collections import defaultdict

def gramps_verify(username, xmlfile):
    upload_folder = get_upload_folder(username) 
    pathname = os.path.join(upload_folder, xmlfile)
    cmd = f"unset PYTHONPATH;env;"
    cmd += f"rm -rf ~/{xmlfile}.media;"
    cmd += f"/usr/bin/gramps -i {pathname} -a tool -p name=verify" #.split()
    print("cmd:",cmd)
    res = subprocess.run(cmd, shell=True, capture_output=True, encoding="utf-8")
    print(res.stderr)
    lines = res.stdout.splitlines()
    rsp = defaultdict(list)
    for line in lines:
        if line[1:2] == ":":
            msgtype, msg = line.split(",", maxsplit=1)
            rsp[msgtype.strip()] = line
    return rsp


