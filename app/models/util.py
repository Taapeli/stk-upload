import os
import time

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
    return time.strftime("%a %Y-%m-%d %H:%M:%S", 
                               time.localtime(ts))
