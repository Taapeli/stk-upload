# Flask routes program for Stk application stat blueprint
#
# Juha Takala 08.05.2020 19:11:31

import logging
logger = logging.getLogger('stkserver')
import time
import re
import os

from flask import flash, render_template, request, redirect, url_for, session as user_session
from flask_security import current_user, roles_accepted, login_required
from flask_babelex import _

from ui.user_context import UserContext

import shareds

from . import bp
from .models import logreader

################ helper fuctions ################

################
#
def run_cmd(cmd):
    import subprocess
    # see https://docs.python.org/3.3/library/subprocess.html
    proc = subprocess.Popen(cmd, shell=True,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
    )
    (stdout, stderr) = proc.communicate()
    if stderr:
        print(f"{cmd}: {stderr}")
    output = stdout.decode("utf-8") # bytes to string
    lines = [x.rstrip() for x in output.split("\n")]
    return (lines)

################
#
def get_logfiles(log_root, log_file, patterns=""):
    """Get ist of log files matching PATTERNS.

Empty PATTERNS equals LOG_FILES.  Return matching filenames in LOG_ROOT."""
    import glob
    if patterns == "":
        patterns = f"{log_file}*"
    files = []
    for pat in re.split(" ", patterns):
        files += list(filter(os.path.isfile, glob.glob(f"{log_root}/{pat}")))
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files

################
#
def safe_get_request(what, default):
    res = request.args.get(what, default)
    if res == "":
        return default
    try:
        return int(res)
    except ValueError as e:
        flash(f"Bad number for {what} '{res}': {e}; using default {default}",
              category='warning')
        return default

################
#
def check_regexp_option(what, default=""):
    val = request.args.get(what, default)
    if val == "":
        return ""
    try:
        re.compile( re.sub("[, ]+", "|", val) )
        return "," . join(re.split("[, ]+", val))
    except Exception as e:
        flash(f"Bad regexp for {what} '{val}': {e}",
              category='warning')
    return ""


################################################################
#### @route funtions below

################################################################
#
@bp.route('/stat')
@login_required
@roles_accepted('admin')
def stat_home():
    """Statistics from stk server.
    """
    import shareds
    code_root = shareds.app.config['APP_ROOT']

    def count_files_lines(fpat, lpat=None):
        """Count files matching file pattern FPAT, and lines in them.

        If optional line pattern LPAT given, count only matching lines.
        """
        grep = ""
        if lpat is not None:
            grep = f" | grep '{lpat}'"
        files = run_cmd(f"find {code_root} -name '{fpat}'")
        lines = run_cmd(f"cat {' '.join(files)}{grep} | wc -l")
        return (len(files), int(lines[0]))

    t0 = time.time()
    (code_files, code_lines) = count_files_lines("*.py")
    (html_files, html_lines) = count_files_lines("*.html")
    (route_files, route_lines) = count_files_lines("routes.py", lpat=r"^@.*route")
    commits = run_cmd("git log | grep commit | wc -l")
    commits1m = run_cmd(f"git log --after '1 month ago' | grep commit | wc -l")
    elapsed = time.time() - t0
    logger.info(f"-> bp.stat e={elapsed:.4f}")
    return render_template("/stat/stat.html",
                           code_files = code_files,
                           code_lines = code_lines,
                           html_files = html_files,
                           html_lines = html_lines,
                           route_files = route_files,
                           route_lines = route_lines,
                           commits = int(commits[0]),
                           commits1m = int(commits1m[0]),
                           elapsed = elapsed,
    )

################################################################
#
@bp.route('/stat/appstat', methods = ['GET', 'POST'])
@login_required
@roles_accepted('admin')
def stat_app():
    """Statistics about stk application usage.
    """

    t0 = time.time()
    users   = check_regexp_option("users")
    msg     = check_regexp_option("msg")     # ...took the place of width in UI
    width   = safe_get_request("width", 70) # no way to set this in UI...
    topn    = safe_get_request("topn", 42)
    bycount = request.args.get("bycount", None)
    style   = request.args.get("style", "text")
    logs    = request.args.get("logs", "")

    opts = {
        "topn"   : topn,
        "width"  : width,
        "style"  : style,
    }
    # Absense/precense of these in opts matters:
    if bycount is not None: opts["bycount"] = 1
    for k,v in { "msg"  : msg,
                 "users": users }.items():
        if v != "":
            opts[k] = v

    # lines[] will collect results from all log files
    lines = []
    for f in get_logfiles(shareds.app.config['STK_LOGDIR'],
                          shareds.app.config['STK_LOGFILE'],
                          patterns = logs):
        log = logreader.StkServerlog(opts) # each file needs own Log
        log.work_with(f)
        lines.append(log.get_counts(style=style))

    elapsed = time.time() - t0
    logger.info(f"-> bp.stat.app e={elapsed:.4f}")
    return render_template("/stat/appstat.html",
                           topn    = topn,
                           width   = width,
                           bycount = bycount,
                           logs    = logs,
                           style   = style,
                           users   = users,
                           msg     = msg,
                           lines   = lines,
                           elapsed = elapsed )


################################################################
#
@bp.route('/stat/uploadstat', methods = ['GET', 'POST'])
@login_required
@roles_accepted('admin')
def stat_upload():
    """Statistics about material uploading.
    """

    t0 = time.time()

    users   = check_regexp_option("users")
    msg     = check_regexp_option("msg")     # ...took the place of width in UI
    width   = safe_get_request("width", 70) # no way to set this in UI...
    topn    = safe_get_request("topn", 42)
    bycount = request.args.get("bycount", None)
    style   = request.args.get("style", "text")
    logs    = request.args.get("logs", "")

    opts = {
        "topn"   : topn,
        "width"  : width,
        "style"  : style,
    }
    # Absense/precense of these in opts matters:
    if bycount is not None: opts["bycount"] = 1
    for k,v in { "msg"  : msg,
                 "users": users }.items():
        if v != "":
            opts[k] = v

    log = logreader.StkUploadlog(opts)
    for f in get_logfiles("/home/juha/projs/Taapeli/stk-upload/uploads",
                          "*/*.log",
                          ""):
        log.work_with(f)
    log.get_counts()

    lines = []
    elapsed = time.time() - t0
    logger.info(f"-> bp.stat.app e={elapsed:.4f}")
    return render_template("/stat/uploadstat.html",
                           lines   = lines,
                           elapsed = elapsed )
