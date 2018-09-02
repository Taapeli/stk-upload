# coding=UTF-8
# Flask main program for Stk application
# @ Sss 2016
# JMä 29.12.2015

import sys
import os
import importlib
import datetime
import time
import subprocess

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_security import login_required, current_user
from flask import send_from_directory
from flask_babelex import _

import logging 
LOG = logging.getLogger(__name__)    

from . import bp
from bp.gedcom import APP_ROOT, GEDCOM_DATA, GEDCOM_APP, ALLOWED_EXTENSIONS
from .transforms.model.ged_output import Output
from . import util
from . import transformer

# --------------------- GEDCOM functions ------------------------

def init_log(logfile): 
    ''' Define log file and save one previous log '''
    try:
        if os.open(logfile, os.O_RDONLY):
            os.rename(logfile, logfile + '~')
    except:
        pass
    logging.basicConfig(filename=logfile,level=logging.INFO, format='%(levelname)s:%(message)s')

def read_gedcom(filename):
    try:
        return open(filename).readlines()
    except UnicodeDecodeError:
        return open(filename,encoding="ISO8859-1").readlines()

def get_gedcom_folder():
    return os.path.join(GEDCOM_DATA, current_user.username)

def get_metadata(gedcom):
    gedcom_folder = get_gedcom_folder()
    try:
        metaname = os.path.join(gedcom_folder, gedcom + "-meta")
        return eval(open(metaname).read())
    except FileNotFoundError:
        return {}

def save_metadata(gedcom,metadata):
    gedcom_folder = get_gedcom_folder()
    metaname = os.path.join(gedcom_folder, gedcom + "-meta")
    open(metaname,"w").write(repr(metadata))
    
def get_transforms():
    class Transform: pass
    trans_dir = os.path.join(GEDCOM_APP, "transforms")
    names = sorted([name for name in os.listdir(trans_dir) \
                    if name.endswith(".py") and not name.startswith("_")])
    for name in names:
        t = Transform()
        t.name = name
        t.modname = name[0:-3]
        saved_path = sys.path[:]
        sys.path.append(os.path.join(APP_ROOT, GEDCOM_APP))
        transformer = importlib.import_module("bp.gedcom.transforms."+t.modname)
        sys.path = saved_path
        doc = transformer.__doc__
        if doc:
            t.doc = doc
            t.docline = doc.strip().splitlines()[0]
        else:
            t.doc = ""
            t.docline = ""
        if hasattr(transformer,"doclink"):
            t.doclink = transformer.doclink
        else:
            t.doclink = ""
            
        t.version = getattr(transformer,"version","")
        yield t


@bp.route('/gedcom/list', methods=['GET'])
@login_required
def gedcom_list():
    gedcom_folder = get_gedcom_folder()
    try:
        names = sorted([name for name in os.listdir(gedcom_folder) if name.endswith(".ged")])
    except:
        names = []
    allowed_extensions = ",".join(["."+ext for ext in ALLOWED_EXTENSIONS])
    files = []
    class File: pass
    for name in names:
        f = File()
        f.name = name
        f.metadata = get_metadata(name)
        files.append(f)
    return render_template('gedcom_list.html', title=_("Gedcomit"), 
                           files=files, kpl=len(names),
                           allowed_extensions=allowed_extensions )
    
@bp.route('/gedcom/versions/<gedcom>', methods=['GET'])
@login_required
def gedcom_versions(gedcom):
    gedcom_folder = get_gedcom_folder()
    versions = sorted([name for name in os.listdir(gedcom_folder) \
                       if name.startswith(gedcom+".")],key=lambda x: int(x.split(".")[-1]))
    versions.append(gedcom)
    return jsonify(versions)

@bp.route('/gedcom/compare/<gedcom1>/<gedcom2>', methods=['GET'])
@login_required
def gedcom_compare(gedcom1,gedcom2):
    import difflib
    gedcom_folder = get_gedcom_folder()
    filename1 = os.path.join(gedcom_folder,gedcom1)
    filename2 = os.path.join(gedcom_folder,gedcom2)
    lines1 = read_gedcom(filename1)
    lines2 = read_gedcom(filename2)
    difftable = difflib.HtmlDiff().make_file(lines1, lines2, context=True, numlines=2,
                                             fromdesc=gedcom1, todesc=gedcom2)
    rsp = dict(diff=difftable)
    return jsonify(rsp)

@bp.route('/gedcom/revert/<gedcom>/<version>', methods=['GET'])
@login_required
def gedcom_revert(gedcom,version):
    gedcom_folder = get_gedcom_folder()
    filename1 = os.path.join(gedcom_folder,gedcom)
    filename2 = os.path.join(gedcom_folder,version)
    newname = util.generate_name(filename1)
    os.rename(filename1,newname)
    os.rename(filename2,filename1)
    rsp = dict(newname=os.path.basename(newname))
    return jsonify(rsp)

@bp.route('/gedcom/upload', methods=['POST'])
@login_required
def gedcom_upload():
    # code from: http://flask.pocoo.org/docs/1.0/patterns/fileuploads/
    from werkzeug.utils import secure_filename
    def allowed_file(filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
    gedcom_folder = get_gedcom_folder()
    # check if the post request has the file part
    if 'file' not in request.files:
        flash(_('Valitse ladattava gedcom-tiedosto'), category='flash_warning')
        return redirect(url_for('.gedcom_list'))
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash(_('Valitse ladattava gedcom-tiedosto'), category='flash_warning')
        return redirect(url_for('.gedcom_list'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(gedcom_folder, exist_ok=True)
        file.save(os.path.join(gedcom_folder, filename))

        desc = request.form['desc']
        metadata = {'desc':desc}
        save_metadata(filename, metadata)
        return redirect(url_for('.gedcom_list'))
  
@bp.route('/gedcom/download/<gedcom>')
@login_required
def gedcom_download(gedcom):
    gedcom_folder = get_gedcom_folder()
    gedcom_folder = os.path.abspath(gedcom_folder)
    logging.info(gedcom_folder)
    filename = os.path.join(gedcom_folder, gedcom)
    logging.info(filename)
    return send_from_directory(directory=gedcom_folder, filename=gedcom) 
 
@bp.route('/gedcom/info/<gedcom>', methods=['GET'])
@login_required
def gedcom_info(gedcom):
    gedcom_folder = get_gedcom_folder()
    filename = os.path.join(gedcom_folder,gedcom)
    if not os.path.exists(filename):
        flash(_("Tiedostoa ei ole"), category='flash_error')
        return redirect(url_for('.gedcom_list'))
    metadata = get_metadata(gedcom)
    num_individuals = 666
    transforms = get_transforms()
    return render_template('gedcom_info.html', 
        gedcom=gedcom, filename=filename, 
        num_individuals=num_individuals, 
        transforms=transforms,
        metadata=metadata,
    )


@bp.route('/gedcom/update_desc/<gedcom>', methods=['POST'])
@login_required
def gedcom_update_desc(gedcom):
    metadata = get_metadata(gedcom)
    desc = request.form['desc']
    metadata['desc'] = desc
    save_metadata(gedcom,metadata)
    return "ok"

@bp.route('/gedcom/delete/<gedcom>')
@login_required
def gedcom_delete(gedcom):
    gedcom_folder = get_gedcom_folder()
    gedcom_folder = os.path.abspath(gedcom_folder)
    for name in os.listdir(gedcom_folder):
        filename = os.path.join(gedcom_folder, name)
        if (name == gedcom or 
            name.startswith(gedcom+".") or 
            name.startswith(gedcom+"-")
        ):
            removefile(filename) 
            logging.info("Deleted:"+filename)
    return redirect(url_for('.gedcom_list'))

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
    print("Replaced:")
    for line in lines:
        print(line)
    print("With:")
    item.print_items(Out())
    print()
        
def process_gedcom(cmd, transform_module):
    """Implements another mechanism for Gedcom transforms:

    The transform_module is assumed to contain the following methods:
    - initialize
    - transform: implements the actual transformation for a single line block ("item")
    - fixlines: preprocesses the Gedcom contents (list of lines/strings)
    - add_args: adds the transform-specific arguments (ArgumentParser style)

    See sukujutut.py as an example
    """


    LOG.info("------ Ajo '%s'   alkoi %s ------", \
             transform_module.__name__, \
             datetime.datetime.now().strftime('%a %Y-%m-%d %H:%M:%S'))


    import argparse
    import io
    import traceback
    parser = argparse.ArgumentParser()
#    parser.add_argument('transform', help="Name of the transform (Python module)")
    parser.add_argument('input_gedcom', help="Name of the input GEDCOM file")
    parser.add_argument('--logfile', help="Name of the log file", default="_LOGFILE" )
#    parser.add_argument('--output_gedcom', help="Name of the output GEDCOM file; this file will be created/overwritten" )
    parser.add_argument('--display-changes', action='store_true',
                        help='Display changed rows') 
    parser.add_argument('--dryrun', action='store_true',
                        help='Do not produce an output file')
    parser.add_argument('--nolog', action='store_true',
                        help='Do not produce a log in the output file')
    parser.add_argument('--encoding', type=str, default="utf-8", choices=["UTF-8", "UTF-8-SIG", "ISO8859-1"],
                        help="Input encoding")
    transform_module.add_args(parser)
    args = parser.parse_args(cmd.split())
    run_args = vars(args)
    try:
        init_log(args.logfile)
        transform_module.initialize(args)
        with Output(run_args) as out:
            out.original_line = None
            saved_stdout = sys.stdout
            saved_stderr = sys.stdout
            sys.stdout = io.StringIO()
            sys.stderr = io.StringIO()
            if args.dryrun:
                old_name = ""
            else:
                old_name = out.new_name

            print("------ Ajo '%s'   alkoi   %s ------" % (
                     transform_module.__name__, 
                     datetime.datetime.now().strftime('%a %Y-%m-%d %H:%M:%S')))
            t = transformer.Transformer(transform_module=transform_module,
                                        display_callback=display_changes,
                                        options=args)
            g = t.transform_file(args.input_gedcom) 
            g.print_items(out)
    except:
        traceback.print_exc()
    finally:
        time.sleep(1)  # for testing...
        print("------ Ajo '%s'   päättyi %s ------" % (
                 transform_module.__name__, 
                 datetime.datetime.now().strftime('%a %Y-%m-%d %H:%M:%S')))
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
def gedcom_transform(gedcom,transform):
    gedcom_folder = get_gedcom_folder()
    gedcom_filename = os.path.join(gedcom_folder, gedcom)
    transform_module,parser = build_parser(transform, gedcom, gedcom_filename)
    if request.method == 'GET':
        return parser.generate_html()
    else:
        logfile = gedcom_filename + "-log"
#         print("#logfile:",logfile)
        removefile(logfile)
        args = parser.build_command(request.form.to_dict())

        if hasattr(transform_module,"transform"):
            cmd = "{} {} {} {}".format(gedcom_filename,args,"--logfile", logfile)
            return process_gedcom(cmd, transform_module)
        
        #TODO EI PYTHON EXCECUTABLEN POLKUA, miten korjataan
        python_exe = sys.executable or "/opt/repo/virtenv/bin/python3"
        python_path = ':'.join([os.path.join(APP_ROOT, 'app'), GEDCOM_APP])
        gedcom_app = GEDCOM_APP
        transform_py = os.path.join(GEDCOM_APP, "gedcom_transform.py")
        tr_args = "{} {} {} {} {}".\
                format(transform[:-3], gedcom_filename, args, "--logfile", logfile)
        cmd3 = "cd '{}'; PYTHONPATH='{}' {} {} {}".\
                format(gedcom_app, python_path, python_exe, transform_py, tr_args)
#         cmd3 = "PYTHONPATH='{}' {} {} {}".\
#                 format(python_path, python_exe, transform_py, tr_args)

        print("#Doing " + cmd3)
        p = subprocess.Popen(cmd3, shell=True, cwd=gedcom_app,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        s1 = p.stdout.read().decode('UTF-8')
        s2 = p.stderr.read().decode('UTF-8')
        p.wait()
#         if s2: print("=== Subprocess errors ===\n" + s2) 
        s = "\nErrors:\n" + s2 + "\n\n" + s1
        try:
            log = open(logfile).read()
        except FileNotFoundError:
            log = "" 
        time.sleep(1)  # for testing...
        rsp = dict(stdout=log + "\n" + s1,stderr=s2,oldname="",logfile=logfile,
           diff="")
        return jsonify(rsp)

        return cmd + "\n\n" + log + "\n\n" + s

   
def build_parser(filename,gedcom,gedcom_filename):
    modname = filename[:-3]
    saved_path = sys.path[:]
    sys.path.append(os.path.join(APP_ROOT, GEDCOM_APP))
    transform_module = importlib.import_module("bp.gedcom.transforms."+modname)
    sys.path = saved_path

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
             
        def generate_html(self):
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
                    raise RuntimeError("Unsupported type: ", arg.type )
                rows.append(row)
            return render_template('gedcom_transform_params.html', gedcom=gedcom, transform=filename, rows=rows )

        def build_command(self,argdict):
            args = ""
            for arg in self.args:
                if arg.name in argdict:
                    value = argdict[arg.name].strip()
                    if not value: value = arg.default
                    if value: 
                        if arg.action in {'store_true','store_false'} and value == "on": value = ""
                        if arg.name[0] == "-":
                            args += " %s %s" % (arg.name,value)
                        else:
                            args += ' "%s"' % value
            return args
            
    parser = Parser()
    #parser.add_argument('gedcom-filename', default=gedcom_filename)
    parser.add_argument('--display-changes', action='store_true',
                        help='Display changed rows')
    parser.add_argument('--dryrun', action='store_true',
                        help='Do not produce an output file')
    parser.add_argument('--nolog', action='store_true',
                        help='Do not produce a log in the output file')
    parser.add_argument('--encoding', type=str, default="utf-8", choices=["UTF-8", "UTF-8-SIG", "ISO8859-1"],
                        help="Input encoding")
    transform_module.add_args(parser)

    return transform_module,parser

