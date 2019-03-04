# coding=UTF-8
# Flask main program for Stk application
# @ Sss 2016
# JMä 29.12.2015

import sys
import os
import importlib
import time
import subprocess
import traceback

from re import match
from collections import defaultdict

from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_security import login_required, current_user, roles_required, roles_accepted
from flask import send_from_directory
from flask_babelex import _

import logging 
LOG = logging.getLogger(__name__)

from models import util

from . import bp
from bp.gedcom import APP_ROOT, GEDCOM_DATA, GEDCOM_APP, ALLOWED_EXTENSIONS
from .transforms.model.ged_output import Output
from . import transformer

from werkzeug.utils import secure_filename

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
    #open(history_file_name,"a").write("{}: {}\n".format(util.format_timestamp(),line))
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
        
    from . import gedcom_info_parser
    try:
        t = transformer.Transformer(transform_module=gedcom_info_parser,
                                    display_callback=display_changes,
                                    options=Options())
        t.transform_file(input_gedcom)
        return t.transformation.info 
    except:
        traceback.print_exc()
        return Nullinfo()
    
def analyze(input_gedcom, enc):
    class Options:
        display_changes = False
        encoding = enc

    class Nullinfo:
        pass
        
    from . import gedcom_analyze
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

def get_gedcom_folder():
    user = get_gedcom_user()
    return os.path.join(GEDCOM_DATA, user)

def gedcom_fullname(gedcom):
    return os.path.join(get_gedcom_folder(),secure_filename(gedcom))

def get_metadata(gedcom):
    gedcom_folder = get_gedcom_folder()
    try:
        metaname = os.path.join(gedcom_folder, secure_filename(gedcom) + "-meta")
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


@bp.route('/gedcom', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_list():
    gedcom_folder = get_gedcom_folder()
    user = get_gedcom_user()
    try:
        names = sorted([name for name in os.listdir(gedcom_folder) if name.lower().endswith(".ged")])
    except:
        names = []
    allowed_extensions = ",".join(["."+ext for ext in ALLOWED_EXTENSIONS])
    files = []
    class File: pass
    for name in names:
        f = File()
        f.name = name
        f.metadata = get_metadata(name)
        
        if user == current_user.username or f.metadata.get("admin_permission"):
            files.append(f)
    return render_template('gedcom_list.html', title=_("Gedcoms"),
                           user=get_gedcom_user(), 
                           files=files, kpl=len(files),
                           allowed_extensions=allowed_extensions )
    
@bp.route('/gedcom/versions/<gedcom>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_versions(gedcom):
    gedcom_folder = get_gedcom_folder()
    gedcom = secure_filename(gedcom)
    versions = [] 
    for name in os.listdir(gedcom_folder):
        if name.startswith(gedcom+"."):
            fullname = os.path.join(gedcom_folder,name)
            modtime = util.format_date(os.stat(fullname).st_mtime)
            version_number = int(name.split(".")[-1])
            displayname = f"v.{version_number}" 
            versions.append((version_number,name,displayname,modtime))
    versions.sort()
    fullname = os.path.join(gedcom_folder,gedcom)
    versions.append((-1,gedcom,_("Current file"),util.format_date(os.stat(fullname).st_mtime)))
    return jsonify(versions)

@bp.route('/gedcom/history/<gedcom>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_history(gedcom):
    history_filename = gedcom_fullname(gedcom) + "-history"
    return open(history_filename).read()

@bp.route('/gedcom/compare/<gedcom1>/<gedcom2>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_compare(gedcom1,gedcom2):
    import difflib
    filename1 = gedcom_fullname(gedcom1)
    filename2 = gedcom_fullname(gedcom2)
    lines1 = read_gedcom(filename1)
    lines2 = read_gedcom(filename2)
    difftable = difflib.HtmlDiff().make_file(lines1, lines2, context=True, numlines=2,
                                             fromdesc=gedcom1, todesc=gedcom2)
    rsp = dict(diff=difftable)
    return jsonify(rsp)

@bp.route('/gedcom/revert/<gedcom>/<version>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_revert(gedcom,version):
    filename1 = gedcom_fullname(gedcom)
    filename2 = gedcom_fullname(version)
    newname = util.generate_name(filename1)
    if os.path.exists(filename1) and os.path.exists(filename2):
        os.rename(filename1,newname)
        os.rename(filename2,filename1)
        history_append(filename1,"\n{}:".format(util.format_timestamp()))
        history_append(filename1,_("File {} saved as {}").format(filename1,newname))
        history_append(filename1,_("File {} saved as {}").format(filename2,filename1))
        rsp = dict(newname=os.path.basename(newname))
    else:
        rsp = dict(status="Error")
    return jsonify(rsp) 

@bp.route('/gedcom/save/<gedcom>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_save(gedcom):
    filename1 = gedcom_fullname(gedcom)
    filename2 = filename1 + "-temp"
    newname = util.generate_name(filename1)
    os.rename(filename1,newname)
    os.rename(filename2,filename1)
    history_append(filename1,"\n{}:".format(util.format_timestamp()))
    history_append(filename1,_("File {} saved as {}").format(filename1,newname))
    history_append(filename1,_("File {} saved as {}").format(filename2,filename1))
    rsp = dict(newname=os.path.basename(newname))
    return jsonify(rsp) 

@bp.route('/gedcom/check/<gedcom>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_check(gedcom):
    fullname = gedcom_fullname(gedcom)
    logging.info("fullname2: "+fullname)
    if os.path.exists(fullname):
        return "exists"
    else:
        return "does not exist"
    
@bp.route('/gedcom/upload', methods=['POST'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_upload():
    # code from: http://flask.pocoo.org/docs/1.0/patterns/fileuploads/
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    gedcom_folder = get_gedcom_folder()
    # check if the post request has the file part
    if 'file' not in request.files:
        flash(_('Choose a GEDCOM file to upload'), category='flash_warning')
        return redirect(url_for('.gedcom_list'))
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash(_('Choose a GEDCOM file to upload'), category='flash_warning')
        return redirect(url_for('.gedcom_list'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(gedcom_folder, exist_ok=True)
        fullname = os.path.join(gedcom_folder, filename)

        logging.info("fullname1: "+fullname)
        if os.path.exists(fullname):
            flash(_('This GEDCOM file already exists'), category='flash_error')
            return redirect(url_for('.gedcom_list'))
            
        file.save(fullname)

        desc = request.form['desc']
        encoding = util.guess_encoding(fullname)
        metadata = {
            'desc':desc,
            'encoding':encoding,
            'upload_time':util.format_timestamp(),
            'size':os.stat(fullname).st_size,
        }
        save_metadata(filename, metadata)
        history_init(fullname)
        return redirect(url_for('.gedcom_info',gedcom=filename))
  
@bp.route('/gedcom/download/<gedcom>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_download(gedcom):
    gedcom_folder = get_gedcom_folder()
    gedcom_folder = os.path.abspath(gedcom_folder)
    gedcom = secure_filename(gedcom)
    logging.info(gedcom_folder)
    filename = os.path.join(gedcom_folder, gedcom)
    logging.info(filename)
    return send_from_directory(directory=gedcom_folder, filename=gedcom, as_attachment=True) 

@bp.route('/gedcom/info/<gedcom>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_info(gedcom):
    filename = gedcom_fullname(gedcom)
    if not os.path.exists(filename):
        flash(_("That GEDCOM file does not exist on the server"), category='flash_error')
        return redirect(url_for('.gedcom_list'))
    metadata = get_metadata(gedcom)
    transforms = get_transforms()
    encoding = metadata.get('encoding','utf-8')
    info = metadata.get('info')
    if info: 
        info = eval(info)
    else: 
        info = get_info(filename,encoding)
        metadata['info'] = repr(info.__dict__)
        save_metadata(gedcom,metadata) 
    return render_template('gedcom_info.html', 
        user=get_gedcom_user(),
        gedcom=gedcom, filename=filename,
        info=info,
        transforms=transforms,
        metadata=metadata,
    )

@bp.route('/gedcom/update_desc/<gedcom>', methods=['POST'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_update_desc(gedcom):
    metadata = get_metadata(gedcom)
    desc = request.form['desc']
    metadata['desc'] = desc
    save_metadata(gedcom,metadata)
    return "ok"

@bp.route('/gedcom/update_permission/<gedcom>/<permission>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_update_permission(gedcom,permission):
    metadata = get_metadata(gedcom)
    metadata['admin_permission'] = (permission == "true")
    save_metadata(gedcom,metadata)
    return "ok"

@bp.route('/gedcom/analyze/<gedcom>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_analyze(gedcom):
    filename = gedcom_fullname(gedcom)
    metadata = get_metadata(gedcom)
    encoding = metadata['encoding']
    rsp = analyze(filename,encoding)
    return rsp

@bp.route('/gedcom/delete/<gedcom>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_delete(gedcom):
    gedcom_folder = get_gedcom_folder()
    gedcom_folder = os.path.abspath(gedcom_folder)
    gedcom = secure_filename(gedcom)
    for name in os.listdir(gedcom_folder):
        if name.endswith("-history"): continue # do not remove history
        if (name == gedcom or 
            name.startswith(gedcom+".") or 
            name.startswith(gedcom+"-")
        ):
            filename = os.path.join(gedcom_folder, name)
            removefile(filename) 
            logging.info("Deleted:"+filename)
    return redirect(url_for('.gedcom_list'))

@bp.route('/gedcom/delete_old_versions/<gedcom>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_delete_old_versions(gedcom):
    gedcom_folder = get_gedcom_folder()
    gedcom_folder = os.path.abspath(gedcom_folder)
    gedcom = secure_filename(gedcom)
    for name in os.listdir(gedcom_folder):
        filename = os.path.join(gedcom_folder, name)
        if name.startswith(gedcom+"."):  
            removefile(filename) 
            logging.info("Deleted:"+filename)
    return redirect(url_for('.gedcom_info',gedcom=gedcom))

def removefile(fname): 
    try:
        os.remove(fname)
    except FileNotFoundError:
        pass

def display_changes(lines,item):
    class Out:
        def emit(self,s):
            print(s)

    print("-----------------------")
    if not item: 
        print(_("Deleted:"))
        for line in lines:
            print(line)
        print()
        return
    print(_("Replaced:"))
    for line in lines:
        print(line)
    print(_("With:"))
    if isinstance(item, list):
        for it in item:
            it.print_items(Out())
    else:
        item.print_items(Out())
    print()
        
def process_gedcom(arglist, transform_module):
    """Implements another mechanism for Gedcom transforms:

    The transform_module is assumed to contain the following methods:
    - initialize
    - transform: implements the actual transformation for a single line block ("item")
    - fixlines: preprocesses the Gedcom contents (list of lines/strings)
    - add_args: adds the transform-specific arguments (ArgumentParser style)

    See sukujutut.py as an example
    """

    msg = _("Transform '{}' started at {}").format(
             transform_module.__name__, 
             util.format_timestamp())
    LOG.info("------ {} ------".format(msg))

    import argparse
    import io
    import traceback
    parser = argparse.ArgumentParser()
#    parser.add_argument('transform', help="Name of the transform (Python module)")
    parser.add_argument('input_gedcom', help=_("Name of the input GEDCOM file"))
    parser.add_argument('--logfile', help=_("Name of the log file"), default="_LOGFILE" )
#    parser.add_argument('--output_gedcom', help="Name of the output GEDCOM file; this file will be created/overwritten" )
    parser.add_argument('--display-changes', action='store_true',
                        help=_('Display changed rows'))
    parser.add_argument('--dryrun', action='store_true',
                        help=_('Do not produce an output file'))
    parser.add_argument('--nolog', action='store_true',
                        help=_('Do not produce a log in the output file'))
    parser.add_argument('--encoding', type=str, default="UTF-8", choices=["UTF-8", "UTF-8-SIG", "ISO8859-1"],
                        help=_("Encoding of the input GEDCOM"))
    transform_module.add_args(parser)
    args = parser.parse_args(arglist)
    args.output_gedcom = None
    args.nolog = True # replaced by history file
    history_append(args.input_gedcom,"\n"+msg)
    history_append_args(args)
    try:
        init_log(args.logfile)
        with Output(args) as out:
            out.original_line = None
            out.transform_name = transform_module.__name__
            saved_stdout = sys.stdout
            saved_stderr = sys.stdout
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            if args.dryrun:
                old_name = ""
            else:
                old_name = out.new_name

            print("------ {} ------".format(msg))
            t = transformer.Transformer(transform_module=transform_module,
                                        display_callback=display_changes,
                                        options=args)
            g = t.transform_file(args.input_gedcom) 
            g.print_items(out)
    except:
        traceback.print_exc()
    finally:
        if old_name: 
            history_append(args.input_gedcom,_("File saved as {}").format(args.input_gedcom))
            history_append(args.input_gedcom,_("Old file saved as {}").format(old_name))
        else:
            #history_append(args.input_gedcom,_("File was not saved"))
            history_append(args.input_gedcom,_("File saved as {}").format(args.input_gedcom+"-temp"))
        msg = _("Transform '{}' ended at {}").format(
                 transform_module.__name__, 
                 util.format_timestamp())
        history_append(args.input_gedcom,msg)
        print("------ {} ------".format(msg))
        output = sys.stdout.getvalue()
        errors = sys.stderr.getvalue()
        sys.stdout = saved_stdout
        sys.stderr = saved_stderr
    if old_name:
        old_basename = os.path.basename(old_name)
    else:
        old_basename = ""
    if errors and old_basename:
        os.rename(old_name,args.input_gedcom)
        old_basename = "" 
    rsp = dict(stdout=output,stderr=errors,oldname=old_basename,logfile=args.logfile)
    return jsonify(rsp)
            
                 
@bp.route('/gedcom/transform/<gedcom>/<transform>', methods=['get','post'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_transform(gedcom,transform):
    gedcom_filename = gedcom_fullname(gedcom)
    transform_module,parser = build_parser(transform, gedcom, gedcom_filename)
    if request.method == 'GET':
        rows = parser.generate_option_rows()
        return render_template('gedcom_transform_params.html', 
                               gedcom=gedcom, transform=transform, 
                               transform_name=transform_module.name, rows=rows )
    else:
        logfile = gedcom_filename + "-log"
#         print("#logfile:",logfile)
        removefile(logfile)
        args = parser.build_command(request.form.to_dict())
        encoding = util.guess_encoding(gedcom_filename)
        logging.info("Guessed encoding {} for {}".format(encoding,gedcom_filename))
        args += " --encoding {}".format(encoding)
        if hasattr(transform_module,"transformer"):
            command_args = parser.build_command_args(request.form.to_dict())
            arglist = [gedcom_filename] + command_args 
            arglist += ["--logfile",logfile]
            arglist += ["--encoding",encoding]
            return process_gedcom(arglist, transform_module)
        
        #TODO EI PYTHON EXCECUTABLEN POLKUA, miten korjataan
        python_exe = sys.executable or "/opt/jelastic-python37/bin/python3"
        python_path = ':'.join([os.path.join(APP_ROOT, 'app'), GEDCOM_APP])
        gedcom_app = GEDCOM_APP
        transform_py = os.path.join(GEDCOM_APP, "gedcom_transform.py")
        tr_args = "{} {} {} {} {}".\
                format(transform[:-3], gedcom_filename, args, "--logfile", logfile)
        cmd3 = "cd '{}'; PYTHONPATH='{}' {} {} {}".\
                format(gedcom_app, python_path, python_exe, transform_py, tr_args)
#         cmd3 = "PYTHONPATH='{}' {} {} {}".\
#                 format(python_path, python_exe, transform_py, tr_args)

        history_append(gedcom_filename,cmd3)

        print("#Doing " + cmd3)
        p = subprocess.Popen(cmd3, shell=True, cwd=gedcom_app,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        s1 = p.stdout.read().decode('UTF-8')
        s2 = p.stderr.read().decode('UTF-8')
        p.wait()
#         if s2: print("=== Subprocess errors ===\n" + s2) 
        if s2: history_append(gedcom_filename,"\nErrors:\n"+s2)
        s = "\n" + _("Errors:") + "\n" + s2 + "\n\n" + s1
        try:
            log = open(logfile).read()
        except FileNotFoundError:
            log = "" 
        time.sleep(1)  # for testing...
        rsp = dict(stdout=log + "\n" + s1,stderr=s2,oldname="",logfile=logfile,
           diff="")
        return jsonify(rsp)

def build_parser(filename,gedcom,gedcom_filename):
    modname = filename[:-3]
    transform_module = importlib.import_module("bp.gedcom.transforms."+modname)

    class Arg:
        def __init__(self,name,name2,action,type,choices,default,help):
            self.name = name
            self.name2 = name2
            self.action = action
            self.type = type
            self.choices = choices
            self.default = default
            self.help = help

    class Parser:
        def __init__(self):
            self.args = []
        def add_argument(self,name,name2=None,action='store',type=str,default=None,help=None,nargs=0,choices=None):
            self.args.append(Arg(name,name2,action,type,choices,default,help))
             
        def generate_option_rows(self):
            rows = []
            class Row: pass
            for arg in self.args:
                row = Row()
                row.name = arg.name
                row.action = arg.action
                row.help = arg.help
                row.checked = ""
                if arg.action == 'store_true':
                    row.type = "checkbox"
                    if row.name == "--dryrun": row.checked = "checked"
                    if row.name == "--display-changes": row.checked = "checked"
                elif arg.action == 'store_false':
                    row.type = "checkbox"
                elif arg.action == 'store_const':
                    row.type = "checkbox"
                elif arg.choices:
                    row.type = "select"
                    row.choices = arg.choices
                elif arg.action == 'store' or arg.action is None:
                    row.type = 'text'
                    if arg.type == int:
                        row.type = 'number'
                elif arg.action == 'append':
                    row.type = 'text'
                elif arg.type == str:
                    row.type = 'text'
                elif arg.type == int:
                    row.type = 'number'
                else:
                    raise RuntimeError(_("Unsupported type: "), arg.type )
                rows.append(row)
            return rows

        def build_command(self,argdict):
            return " ".join(self.build_command_args(argdict))
            
        def build_command_args(self,argdict):
            args = []
            for arg in self.args:
                if arg.name in argdict:
                    value = argdict[arg.name].rstrip()
                    if not value: value = arg.default
                    if value: 
                        if arg.action in {'store_true','store_false'} and value == "on": value = ""
                        if arg.name[0] == "-":
                            args.append(arg.name)
                            if value: args.append(value)
                        else:
                            args.append(value)
            args.append("--dryrun")
            args.append("--nolog")
            return args

    parser = Parser()

    parser.add_argument('--display-changes', action='store_true',
                        help=_('Display changed rows'))
    #parser.add_argument('--dryrun', action='store_true',
    #                    help=_('Do not produce an output file'))
    #parser.add_argument('--nolog', action='store_true',
    #                    help=_('Do not produce a log in the output file'))
#    parser.add_argument('--encoding', type=str, default="utf-8", choices=["UTF-8", "UTF-8-SIG", "ISO8859-1"],
#                        help=_("Encoding of the input GEDCOM"))
    
    transform_module.add_args(parser)

    return transform_module,parser

