''' Utilities for processing gedcom data
'''
import importlib
import logging
import os
import traceback

from flask import session
from flask_security import current_user
from flask_babelex import _

from werkzeug.utils import secure_filename

from models import util #, syslog
from bp.gedcom import GEDCOM_DATA, GEDCOM_APP #, APP_ROOT, ALLOWED_EXTENSIONS
from .. import transformer

# Default document server
DOC_SERVER = 'http://mwikitammi.paas.datacenter.fi/index.php'

# --------------------- GEDCOM functions ------------------------

def init_log(logfile): 
    ''' Define log file and save one previous log. '''
    try:
        if os.open(logfile, os.O_RDONLY):
            os.rename(logfile, logfile + '~')
    except:
        pass
    logging.basicConfig(filename=logfile, level=logging.INFO, format='%(levelname)s:%(message)s')

def history_init(gedcom_fname):
    ''' Initialize history file. '''
    history_file_name = gedcom_fname + "-history"
    open(history_file_name,"w").write("{}: Uploaded {}\n".format(util.format_timestamp(),gedcom_fname))
    
def history_append(gedcom_fname,line):
    ''' Add a line to history file. '''
    history_file_name = gedcom_fname + "-history"
    open(history_file_name,"a").write("{}\n".format(line))

def history_append_args(args):
    ''' Add given arguments to history file. '''
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
    ''' Get statistics of given gedcom file. '''
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
    ''' Return all gedcom file rows using default or ISO8859-1 encoding. '''
    try:
        return open(filename).readlines()
    except UnicodeDecodeError:
        return open(filename,encoding="ISO8859-1").readlines()

def get_gedcom_user():
    ''' Return current user name. '''
    return session.get("gedcom_user",current_user.username)

def get_gedcom_folder(username=None):
    ''' Return user's gedcom data directory. '''
    if username is None:
        username = get_gedcom_user()
    return os.path.join(GEDCOM_DATA, username)

def gedcom_fullname(gedcom):
    ''' Return gedcom filename. '''
    return os.path.join(get_gedcom_folder(),secure_filename(gedcom))

def get_metadata(gedcom):
    ''' Return given gedcom metadata from *-meta file. '''
    gedcom_folder = get_gedcom_folder()
    gedcom_fullname = os.path.join(gedcom_folder, secure_filename(gedcom))
    return get_metadata2(gedcom_fullname)

def get_metadata2(gedcom_fullname):
    ''' Return given gedcom file metadata from corresponding meta file. '''
    try:
        metaname = gedcom_fullname + "-meta"
        return eval(open(metaname).read())
    except FileNotFoundError:
        return {}

def save_metadata(gedcom,metadata):
    ''' Save updated or new gedcom metadata. '''
    gedcom_folder = get_gedcom_folder()
    metaname = os.path.join(gedcom_folder, secure_filename(gedcom) + "-meta")
    open(metaname,"w").write(repr(metadata))
    
def get_transforms():
    ''' Search available transformations and return list of their properties. '''
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

        # have to reload because the user may have changed language -> name and docline may change
        importlib.reload(transformer) 

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
        
        doclink = ""
        if hasattr(transformer,"doclinks"):
            lang = session.get('lang',"")
            doclink = transformer.doclinks.get(lang,"")
        if not doclink and hasattr(transformer,"doclink"):
            doclink = transformer.doclink
        if doclink.startswith('/'):
            doclink = DOC_SERVER + doclink
        t.doclink = doclink

        if hasattr(transformer,"name"):
            t.displayname = transformer.name
        else:
            t.displayname = t.modname
            
        t.version = getattr(transformer,"version","")
        transforms.append(t)
        #yield t
    return sorted(transforms,key=lambda t: t.displayname)


def list_gedcoms(username):
    ''' Search transformations and return list of their names and metadata. '''
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
    ''' Remove file. '''
    try:
        os.remove(fname)
    except FileNotFoundError:
        pass

def display_changed_lines(old_lines, new_lines, linenum=None):
    ''' Print diff list of two line sets as html in user language strating from linenum.
    '''
    if old_lines is None: 
        print("<div><b>"+_("Added:")+"</b></div><gedcom-text>", end="")
        for line in new_lines:
            print(line)
        print("</gedcom-text>")
        print("<hr>")  
        return
    if not new_lines: 
        print("<div><b>"+_("Deleted:")+"</b></div><gedcom-replaced>", end="")
        if linenum: 
            print(f"{_('starting from line ')}<a href='#' class='gedcomlink'>{linenum}</a>")
        for line in old_lines:
            print(line)
        print("</gedcom-replaced>")
        print("<hr>")  
        return
    print("<div><b>"+_("Replaced:")+"</b>")
    if linenum: 
        print(f"{_('starting from line ')}<a href='#' class='gedcomlink'>{linenum}</a>")
    print("</div><gedcom-replaced>", end="")
    for line in old_lines:
        print(line)
    print("</gedcom-replaced>")
    print("<div><b>"+_("With:")+"</b></div><gedcom-text>", end="")
    for line in new_lines:
        print(line)
    print("</gedcom-text>")
    print()
    print("<hr>")  

def display_changes(lines, item, linenum=None):
    ''' Print diff list of two line sets as html in user language? 
    '''
    class Out:
        def __init__(self):
            self.lines = []
        def emit(self,line):
            self.lines.append(line)

    out = Out()

    if not item:
        display_changed_lines(lines,None)
    else:
        if isinstance(item, list):
            for it in item:
                it.print_items(out)
        else:
            item.print_items(out)
    
        display_changed_lines(lines, out.lines, linenum)
    
        