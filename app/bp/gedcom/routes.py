# coding=UTF-8
# Flask main program for Stk application
# @ Sss 2016
# JMä 29.12.2015

import sys
import os
import importlib
#import time
import subprocess
import traceback

#from re import match
#from collections import defaultdict

from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_security import login_required, current_user, roles_required, roles_accepted
from flask import send_from_directory
from flask_babelex import _

import logging 
from bp.gedcom.models import gedcom_utils
#import string
LOG = logging.getLogger(__name__)

from models import util, syslog

from . import bp
from bp.gedcom import APP_ROOT, GEDCOM_APP, ALLOWED_EXTENSIONS
from .transforms.model.ged_output import Output
from . import transformer

from werkzeug.utils import secure_filename



    
@bp.route('/gedcom', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_list():
    username = gedcom_utils.get_gedcom_user()
    files = gedcom_utils.list_gedcoms(username)
    allowed_extensions = ",".join(["."+ext for ext in ALLOWED_EXTENSIONS])
    return render_template('gedcom_list.html', title=_("Gedcoms"),
                           user=username, 
                           files=files, kpl=len(files),
                           allowed_extensions=allowed_extensions )

@bp.route('/gedcom/versions/<gedcom>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_versions(gedcom):
    gedcom_folder = gedcom_utils.get_gedcom_folder()
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
    history_filename = gedcom_utils.gedcom_fullname(gedcom) + "-history"
    return open(history_filename).read()

@bp.route('/gedcom/compare/<gedcom1>/<gedcom2>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_compare(gedcom1,gedcom2):
    import difflib
    filename1 = gedcom_utils.gedcom_fullname(gedcom1)
    filename2 = gedcom_utils.gedcom_fullname(gedcom2)
    lines1 = gedcom_utils.read_gedcom(filename1)
    lines2 = gedcom_utils.read_gedcom(filename2)
    difftable = difflib.HtmlDiff().make_file(lines1, lines2, context=True, numlines=2,
                                             fromdesc=gedcom1, todesc=gedcom2)
    rsp = dict(diff=difftable)
    return jsonify(rsp)

@bp.route('/gedcom/revert/<gedcom>/<version>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_revert(gedcom,version):
    filename1 = gedcom_utils.gedcom_fullname(gedcom)
    filename2 = gedcom_utils.gedcom_fullname(version)
    newname = util.generate_name(filename1)
    if os.path.exists(filename1) and os.path.exists(filename2):
        os.rename(filename1,newname)
        os.rename(filename2,filename1)
        gedcom_utils.history_append(filename1,"\n{}:".format(util.format_timestamp()))
        gedcom_utils.history_append(filename1,_("File {} saved as {}").format(filename1,newname))
        gedcom_utils.history_append(filename1,_("File {} saved as {}").format(filename2,filename1))
        rsp = dict(newname=os.path.basename(newname))
    else:
        rsp = dict(status="Error")
    return jsonify(rsp) 

@bp.route('/gedcom/save/<gedcom>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_save(gedcom):
    filename1 = gedcom_utils.gedcom_fullname(gedcom)
    filename2 = filename1 + "-temp"
    newname = util.generate_name(filename1)
    os.rename(filename1,newname)
    os.rename(filename2,filename1)
    gedcom_utils.history_append(filename1,"\n{}:".format(util.format_timestamp()))
    gedcom_utils.history_append(filename1,_("File {} saved as {}").format(filename1,newname))
    gedcom_utils.history_append(filename1,_("File {} saved as {}").format(filename2,filename1))
    rsp = dict(newname=os.path.basename(newname))
    return jsonify(rsp) 

@bp.route('/gedcom/check/<gedcom>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_check(gedcom):
    fullname = gedcom_utils.gedcom_fullname(gedcom)
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
    
    gedcom_folder = gedcom_utils.get_gedcom_folder()
    # check if the post request has the file part
    if 'file' not in request.files:
        flash(_('Choose a GEDCOM file to upload'), category='flash_warning')
        return redirect(url_for('.gedcom_list'))
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '': # pragma: no cover
        flash(_('Choose a GEDCOM file to upload'), category='flash_warning')
        return redirect(url_for('.gedcom_list'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(gedcom_folder, exist_ok=True)
        fullname = os.path.join(gedcom_folder, filename)

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
        gedcom_utils.save_metadata(filename, metadata)
        gedcom_utils.history_init(fullname)
        syslog.log(type="uploaded a gedcom",gedcom=file.filename)    
        return redirect(url_for('.gedcom_info',gedcom=filename))
  
@bp.route('/gedcom/download/<gedcom>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_download(gedcom):
    metadata = gedcom_utils.get_metadata(gedcom)
    if gedcom_utils.get_gedcom_user() != current_user.username and not metadata.get("admin_permission"):
        flash(_("You don't have permission to view that GEDCOM"), category='flash_error')
        return redirect(url_for('gedcom.gedcom_list'))
    gedcom_folder = gedcom_utils.get_gedcom_folder()
    gedcom_folder = os.path.abspath(gedcom_folder)
    gedcom = secure_filename(gedcom)
#     filename = os.path.join(gedcom_folder, gedcom)
    return send_from_directory(directory=gedcom_folder, filename=gedcom, as_attachment=True) 

@bp.route('/gedcom/info/<gedcom>', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research','admin')
def gedcom_info(gedcom):
    filename = gedcom_utils.gedcom_fullname(gedcom)
    if not os.path.exists(filename):
        flash(_("That GEDCOM file does not exist on the server"), category='flash_error')
        return redirect(url_for('gedcom.gedcom_list'))
    metadata = gedcom_utils.get_metadata(gedcom)
    transforms = gedcom_utils.get_transforms()
    encoding = metadata.get('encoding','utf-8')
    info = metadata.get('info')
    if gedcom_utils.get_gedcom_user() != current_user.username and not metadata.get("admin_permission"):
        flash(_("You don't have permission to view that GEDCOM"), category='flash_error')
        return redirect(url_for('gedcom.gedcom_list'))
    if info: 
        info = eval(info)
    else: 
        info = gedcom_utils.get_info(filename,encoding)
        metadata['info'] = repr(info.__dict__)
        gedcom_utils.save_metadata(gedcom,metadata) 
    return render_template('gedcom_info.html', 
        user=gedcom_utils.get_gedcom_user(),
        gedcom=gedcom, filename=filename,
        info=info,
        transforms=transforms,
        metadata=metadata,
    )

@bp.route('/gedcom/update_desc/<gedcom>', methods=['POST'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_update_desc(gedcom):
    metadata = gedcom_utils.get_metadata(gedcom)
    desc = request.form['desc']
    metadata['desc'] = desc
    gedcom_utils.save_metadata(gedcom,metadata)
    return "ok"

@bp.route('/gedcom/update_permission/<gedcom>/<permission>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_update_permission(gedcom,permission):
    metadata = gedcom_utils.get_metadata(gedcom)
    metadata['admin_permission'] = (permission == "true")
    gedcom_utils.save_metadata(gedcom,metadata)
    return "ok"

@bp.route('/gedcom/analyze/<gedcom>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_analyze(gedcom):
    filename = gedcom_utils.gedcom_fullname(gedcom)
    metadata = gedcom_utils.get_metadata(gedcom)
    encoding = metadata['encoding']
    rsp = gedcom_utils.analyze(filename,encoding)
    return rsp

@bp.route('/gedcom/get_excerpt/<gedcom>/<int:linenum>')
@login_required
@roles_accepted('gedcom', 'research')
def get_excerpt(gedcom,linenum):
    filename = gedcom_utils.gedcom_fullname(gedcom)
    metadata = gedcom_utils.get_metadata(gedcom)
    encoding = metadata['encoding'] 
    lines = open(filename,encoding=encoding).readlines()
    firstline = linenum-1 
    while not lines[firstline].startswith("0"):
        firstline -= 1
    if firstline < 0: firstline = 0
    html = ""
    for i,line in enumerate(lines[firstline:linenum+9]):
        line = line.strip()
        if i > 0 and firstline+i > linenum-1 and line.startswith("0"): break
        html += f"<br><span class=linenum>{firstline+i+1}</span>: "
        if firstline+i == linenum-1:
            html += f"<span class=current_line>{line}</span>"
        else:    
            html += f"{line}"
    return html

@bp.route('/gedcom/delete/<gedcom>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_delete(gedcom):
    gedcom_folder = gedcom_utils.get_gedcom_folder()
    gedcom_folder = os.path.abspath(gedcom_folder)
    gedcom = secure_filename(gedcom)
    for name in os.listdir(gedcom_folder):
        if name.endswith("-history"): continue # do not remove history
        if (name == gedcom or 
            name.startswith(gedcom+".") or 
            name.startswith(gedcom+"-")
        ):
            filename = os.path.join(gedcom_folder, name)
            gedcom_utils.removefile(filename) 
            logging.info("Deleted:"+filename)
    syslog.log(type="deleted a gedcom",gedcom=gedcom)    
    return redirect(url_for('.gedcom_list'))

@bp.route('/gedcom/delete_old_versions/<gedcom>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_delete_old_versions(gedcom):
    gedcom_folder = gedcom_utils.get_gedcom_folder()
    gedcom_folder = os.path.abspath(gedcom_folder)
    gedcom = secure_filename(gedcom)
    for name in os.listdir(gedcom_folder):
        filename = os.path.join(gedcom_folder, name)
        if name.startswith(gedcom+"."):  
            gedcom_utils.removefile(filename) 
            logging.info("Deleted:"+filename)
    syslog.log(type="deleted old versions for gedcom",gedcom=gedcom)    
    return redirect(url_for('.gedcom_info',gedcom=gedcom))

      
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
             transform_module.name, 
             util.format_timestamp())
    LOG.info("------ {} ------".format(msg))

    import argparse
    import io
#     import traceback
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
    gedcom_utils.history_append(args.input_gedcom,"\n"+msg)
    gedcom_utils.history_append_args(args)
    try:
        gedcom_utils.init_log(args.logfile)
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

            print("<h3>------ {} ------</h3>".format(msg))
            t = transformer.Transformer(transform_module=transform_module,
                                        display_callback=gedcom_utils.display_changes,
                                        options=args)
            g = t.transform_file(args.input_gedcom) 
            g.print_items(out)
            print(_("------ Number of changes:"), t.num_changes)
    except:
        traceback.print_exc()
    finally:
        if old_name: 
            gedcom_utils.history_append(args.input_gedcom,_("File saved as {}").format(args.input_gedcom))
            gedcom_utils.history_append(args.input_gedcom,_("Old file saved as {}").format(old_name))
        else:
            gedcom_utils.history_append(args.input_gedcom,_("File saved as {}").format(args.input_gedcom+"-temp"))
        msg = _("Transform '{}' ended at {}").format(
                 transform_module.name, 
                 util.format_timestamp())
        gedcom_utils.history_append(args.input_gedcom,msg)
        print("<h3>------ {} ------</h3>".format(msg))
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
    if hasattr(transform_module,"output_format") and transform_module.output_format == "plain_text":
        rsp["plain_text"] = True
    return jsonify(rsp)
            
                 
@bp.route('/gedcom/transform/<gedcom>/<transform>', methods=['get','post'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_transform(gedcom,transform):
    gedcom_filename = gedcom_utils.gedcom_fullname(gedcom)
    transform_module,parser = build_parser(transform, gedcom, gedcom_filename)
    if request.method == 'GET':
        rows = parser.generate_option_rows()
        return render_template('gedcom_transform_params.html', 
                               gedcom=gedcom, transform=transform, 
                               transform_name=transform_module.name, rows=rows )
    else:
        logfile = gedcom_filename + "-log"
#         print("#logfile:",logfile)
        gedcom_utils.removefile(logfile)
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

        gedcom_utils.history_append(gedcom_filename,cmd3)

        print("#Doing " + cmd3)
        p = subprocess.Popen(cmd3, shell=True, cwd=gedcom_app,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        s1 = p.stdout.read().decode('UTF-8')
        s2 = p.stderr.read().decode('UTF-8')
        p.wait()
        if s2: gedcom_utils.history_append(gedcom_filename,"\nErrors:\n"+s2)
#         s = "\n" + _("Errors:") + "\n" + s2 + "\n\n" + s1
        try:
            log = open(logfile).read()
        except FileNotFoundError:
            log = "" 
        rsp = dict(stdout=log + "\n" + s1,stderr=s2,oldname="",logfile=logfile,
           diff="",plain_text=True)
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
    
    transform_module.add_args(parser)

    return transform_module,parser

