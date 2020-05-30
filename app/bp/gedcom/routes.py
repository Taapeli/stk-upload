# coding=UTF-8
# Flask main program for Stk application
# @ Sss 2016
# JMä 29.12.2015

import sys
import os
import subprocess

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_security import login_required, current_user, roles_accepted
from flask import send_from_directory
from flask_babelex import _
from werkzeug.utils import secure_filename
from difflib import HtmlDiff

import shareds

import logging 
#LOG = logging.getLogger(__name__)
logger = logging.getLogger('stkserver')

from . import bp
from models import util, syslog
from bp.gedcom import APP_ROOT, GEDCOM_APP, ALLOWED_EXTENSIONS
from bp.gedcom.models import gedcom_utils
from .models.processor import build_parser, process_gedcom

    
@bp.route('/gedcom', methods=['GET'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_list():
    username = gedcom_utils.get_gedcom_user()
    files = gedcom_utils.list_gedcoms(username)
    allowed_extensions = ",".join(["."+ext for ext in ALLOWED_EXTENSIONS])
    logger.info(f'-> bp.gedcom.routes.gedcom_list n={len(files)}')
    return render_template('gedcom_list.html', title=_("Gedcoms"),
                           user=username, 
                           files=files, kpl=len(files),
                           allowed_extensions=allowed_extensions,
                           maxsize=shareds.app.config.get("MAX_CONTENT_LENGTH") )

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
    filename1 = gedcom_utils.gedcom_fullname(gedcom1)
    filename2 = gedcom_utils.gedcom_fullname(gedcom2)
    lines1 = gedcom_utils.read_gedcom(filename1)
    lines2 = gedcom_utils.read_gedcom(filename2)

    difftable = HtmlDiff().make_file(lines1, lines2, context=True, numlines=2,
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
    logger.info(f'-> bp.gedcom.routes.gedcom_save f="{os.path.basename(newname)}"')
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
        logger.info(f'-> bp.gedcom.routes.gedcom_upload n={os.stat(fullname).st_size/1024.}kb')
        return redirect(url_for('.gedcom_info',gedcom=filename))

@bp.route('/gedcom/download/<gedcom>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_download(gedcom):
    parts = gedcom.rsplit(".",maxsplit=1)
    if len(parts) == 2 and parts[1].isdigit():
        base_gedcom = parts[0]  # remove version number
    else:
        base_gedcom = gedcom
    metadata = gedcom_utils.get_metadata(base_gedcom)
    if gedcom_utils.get_gedcom_user() != current_user.username and not metadata.get("admin_permission"):
        flash(_("You don't have permission to view that GEDCOM"), category='flash_error')
        return redirect(url_for('gedcom.gedcom_list'))
    gedcom_folder = gedcom_utils.get_gedcom_folder()
    gedcom_folder = os.path.abspath(gedcom_folder)
    gedcom = secure_filename(gedcom)
#     filename = os.path.join(gedcom_folder, gedcom)
    logger.info(f'-> bp.gedcom.routes.gedcom_download f="{gedcom}"')
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
    logger.info(f'-> bp.gedcom.routes.gedcom_info f="{gedcom}"')
    return render_template('gedcom_info.html', 
                           user=gedcom_utils.get_gedcom_user(), gedcom=gedcom, 
                           filename=filename, info=info, transforms=transforms, 
                           maxsize=shareds.app.config.get("MAX_CONTENT_LENGTH"),
                           metadata=metadata)

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
    logger.info(f'-> bp.gedcom.routes.gedcom_update_permission/{permission} f="{gedcom}"')
    return "ok"

@bp.route('/gedcom/analyze/<gedcom>')
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_analyze(gedcom):
    filename = gedcom_utils.gedcom_fullname(gedcom)
    metadata = gedcom_utils.get_metadata(gedcom)
    encoding = metadata['encoding']
    logger.info(f'-> bp.gedcom.routes.gedcom_analyze f="{gedcom}"')
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
    logger.info(f'-> bp.gedcom.routes.gedcom_delete f="{gedcom}"')
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


@bp.route('/gedcom/transform/<gedcom>/<transform>', methods=['get','post'])
@login_required
@roles_accepted('gedcom', 'research')
def gedcom_transform(gedcom,transform):
    """ Execute the pre-defined transformation.
    """
    gedcom_filename = gedcom_utils.gedcom_fullname(gedcom)
    transform_module, parser = build_parser(transform, gedcom, gedcom_filename)
    if request.method == 'GET':
        """ (1) Shows transformation parameter page
        """
        rows = parser.generate_option_rows()
        return render_template('gedcom_transform_params.html', 
                               gedcom=gedcom, transform=transform, 
                               transform_name=transform_module.name, rows=rows)
    else:
        """ (2) Starts the transformation with parameters from (1).
        """
        logfile = gedcom_filename + "-log"
#         print("#logfile:",logfile)
        gedcom_utils.removefile(logfile)
        args = parser.build_command(request.form.to_dict())
        encoding = util.guess_encoding(gedcom_filename)
        logging.info(f"Guessed encoding {encoding} for {gedcom_filename}")
        args += f" --encoding {encoding}"
        if hasattr(transform_module, "transformer"):
            """ (2a) Runs Gedcom transformation
                     using bp.gedcom.models.processor.process_gedcom
            """
            command_args = parser.build_command_args(request.form.to_dict())
            arglist = [gedcom_filename] + command_args 
            arglist += ["--logfile",logfile]
            arglist += ["--encoding",encoding]

            module_name = transform_module.__name__.split('.')[-1]
            logger.info(f'-> bp.gedcom.routes.gedcom_transform/{module_name}')
            rsp = process_gedcom(arglist, transform_module)
            return jsonify(rsp)
        
        """ (2b) Runs Gedcom transformation by obsolete stand alone program emulation.

            Used only for older bp.gedcom.transforms.names,
            to be replaced by   bp.gedcom.transforms.person_names
        """
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

