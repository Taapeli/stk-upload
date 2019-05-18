import importlib
import logging
import os
import traceback

from flask import session
from flask_security import current_user
from flask_babelex import _

from werkzeug.utils import secure_filename

from models import util, syslog

from bp.gedcom import APP_ROOT, GEDCOM_DATA, GEDCOM_APP, ALLOWED_EXTENSIONS

from .. import transformer

# --------------------- GEDCOM functions ------------------------

def init_log(logfile): 
    ''' Define log file and save one previous log '''
    try:
        if os.open(logfile, os.O_RDONLY):
            os.rename(logfile, logfile + '~')
    except:
        pass
    logging.basicConfig(filename=logfile,level=logging.INFO, format='%(levelname)s:%(message)s')

def history_init(gedcom_fname):
    history_file_name = gedcom_fname + "-history"
    open(history_file_name,"w").write("{}: Uploaded {}\n".format(util.format_timestamp(),gedcom_fname))
    
def history_append(gedcom_fname,line):
    history_file_name = gedcom_fname + "-history"
    open(history_file_name,"a").write("{}\n".format(line))

def history_append_args(args):
    history_file_name = args.input_gedcom + "-history"
    with open(history_file_name,"a") as f:
        for name,value in sorted(vars(args).items()):
            f.write("- {}={}\n".format(name,value))
        f.write("- User={}\n".format(current_user.username))


def get_info(input_gedcom, enc):
    ''' 
    Read gedcom HEAD info and count level 0 items.
    Uses the transformation framework.
    '''
    class Options:
        display_changes = False
        encoding = enc

    class Nullinfo:
        pass
        
    from .. import gedcom_info_parser
    try:
        t = transformer.Transformer(transform_module=gedcom_info_parser,
                                    display_callback=display_changes,
                                    options=Options())
        t.transform_file(input_gedcom)
        return t.transformation.info 
    except: # pragma: no cover
        traceback.print_exc()
        return Nullinfo()
    
def analyze(input_gedcom, enc):
    class Options:
        display_changes = False
        encoding = enc

    class Nullinfo:
        pass
        
    from .. import gedcom_analyze
    try:
        t = transformer.Transformer(transform_module=gedcom_analyze,
                                    display_callback=display_changes,
                                    options=Options())
        t.transform_file(input_gedcom)
        return t.transformation.info 
    except:
        traceback.print_exc()
        return "error"

def read_gedcom(filename):
    try:
        return open(filename).readlines()
    except UnicodeDecodeError:
        return open(filename,encoding="ISO8859-1").readlines()

def get_gedcom_user():
    return session.get("gedcom_user",current_user.username)

def get_gedcom_folder(username=None):
    if username is None:
        username = get_gedcom_user()
    return os.path.join(GEDCOM_DATA, username)

def gedcom_fullname(gedcom):
    return os.path.join(get_gedcom_folder(),secure_filename(gedcom))

def get_metadata(gedcom):
    gedcom_folder = get_gedcom_folder()
    gedcom_fullname = os.path.join(gedcom_folder, secure_filename(gedcom))
    return get_metadata2(gedcom_fullname)

def get_metadata2(gedcom_fullname):
    try:
        metaname = gedcom_fullname + "-meta"
        return eval(open(metaname).read())
    except FileNotFoundError:
        return {}

def save_metadata(gedcom,metadata):
    gedcom_folder = get_gedcom_folder()
    metaname = os.path.join(gedcom_folder, secure_filename(gedcom) + "-meta")
    open(metaname,"w").write(repr(metadata))
    
def get_transforms():
    class Transform: pass
    trans_dir = os.path.join(GEDCOM_APP, "transforms")
    names = sorted([name for name in os.listdir(trans_dir) \
                    if name.endswith(".py") and not name.startswith("_")])
    
    transforms = []
    for name in names:
        t = Transform()
        t.name = name
        t.modname = name[0:-3]
        transformer = importlib.import_module("bp.gedcom.transforms."+t.modname)
        doc = transformer.__doc__
        if doc:
            t.doc = doc
            t.docline = doc.strip().splitlines()[0]
            t.docline = _(t.docline)
        else:
            t.doc = ""
            t.docline = ""
        if hasattr(transformer,"docline"):
            t.docline = transformer.docline
        if hasattr(transformer,"doclink"):
            t.doclink = transformer.doclink
        else:
            t.doclink = ""

        if hasattr(transformer,"name"):
            t.displayname = transformer.name
        else:
            t.displayname = t.modname
            
        t.version = getattr(transformer,"version","")
        transforms.append(t)
        #yield t
    return sorted(transforms,key=lambda t: t.displayname)


def list_gedcoms(username):
    gedcom_folder = get_gedcom_folder(username)
    try:
        names = sorted([name for name in os.listdir(gedcom_folder) 
                        if name.lower().endswith(".ged")],
                        key=lambda s: s.lower()
                    )
    except:
        names = []
    files = []
    class File: pass
    for name in names:
        f = File()
        f.name = name
        gedcom_fullname = os.path.join(gedcom_folder,name)
        f.metadata = get_metadata2(gedcom_fullname)
        if username == current_user.username or f.metadata.get("admin_permission"):
            files.append(f)
    return files

def removefile(fname): 
    try:
        os.remove(fname)
    except FileNotFoundError:
        pass

def display_changes(lines,item,linenum=None):
    class Out:
        def emit(self,s):
            print(s)

    if not item: 
        print("<b>"+_("Deleted:")+"</b>")
        print("<gedcom-text>")
        for line in lines:
            print(line)
        print("</gedcom-text>")
        print()
        return
    print("<b>"+_("Replaced:")+"</b>")
    if linenum: print("("+_("starting from line ")+f"<a href='#' class='gedcomlink'>{linenum}</a>)")
    print("<gedcom-text>")
    for line in lines:
        print(line)
    print("</gedcom-text>")
    print("<b>"+_("With:")+"</b>")
    print("<gedcom-text>")
    if isinstance(item, list):
        for it in item:
            it.print_items(Out())
    else:
        item.print_items(Out())
    print("</gedcom-text>")
    print()
    print("<br>-----------------------<br>")
