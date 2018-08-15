# coding=UTF-8
# Flask main program for Stk application
# @ Sss 2016
# JMä 29.12.2015

import sys
import os
import importlib

import logging 
import time

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_security import login_required, current_user
from flask import send_from_directory

from flask_babelex import _

from . import bp
    
# --------------------- GEDCOM functions ------------------------

# TODO: move these to config.py
GEDCOM_FOLDER="gedcoms"    
ALLOWED_EXTENSIONS = {"ged"}    
GEDDER="app/bp/gedcom"

def get_gedcom_folder():
    return os.path.join(GEDCOM_FOLDER,current_user.username)

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
    names = sorted([name for name in os.listdir(GEDDER+"/transforms") if name.endswith(".py") and not name.startswith("_")])
    for name in names:
        t = Transform()
        t.name = name
        modname = name[0:-3]
        t.modname = modname
        saved_path = sys.path[:]
        sys.path.append(GEDDER)
        transformer = importlib.import_module("transforms."+modname)
        sys.path = saved_path
        doc = transformer.__doc__
        if doc:
            t.doc = doc
            t.docline = doc.strip().splitlines()[0]
        else:
            t.doc = ""
            t.docline = ""
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
    versions = sorted([name for name in os.listdir(gedcom_folder) if name.startswith(gedcom+".")],key=lambda x: int(x.split(".")[-1]))
    return jsonify(versions)

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
        save_metadata(file.filename, metadata)
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
     
@bp.route('/gedcom/transform/<gedcom>/<transform>', methods=['get','post'])
@login_required
def gedcom_transform(gedcom,transform):
    gedcom_folder = get_gedcom_folder()
    gedcom_filename = os.path.join(gedcom_folder,gedcom)
    gedcom_filename = os.path.abspath(gedcom_filename)
    parser = build_parser(transform,gedcom,gedcom_filename)
    if request.method == 'GET':
        return parser.generate_html()
    else:
        logfile = gedcom_filename + "-log"
        print("logfile:",logfile)
        removefile(logfile)
        args = parser.build_command(request.form.to_dict())
        cmd = "{} {} {} {} {}".format(transform[:-3],gedcom_filename,args,"--logfile", logfile)
        f = os.popen("""cd "{}";{} gedcom_transform.py {}""".format(GEDDER,sys.executable,cmd))
        s = f.read()
        log = open(logfile).read()
        time.sleep(1)  # for testing...
        return cmd + "\n\n" + log + "\n\n" + s

   
def build_parser(filename,gedcom,gedcom_filename):
    modname = filename[:-3]
    saved_path = sys.path[:]
    sys.path.append(GEDDER)
    transformer = importlib.import_module("transforms."+modname)
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
    transformer.add_args(parser)

    return parser

