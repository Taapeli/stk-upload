# Flask routes program for Stk application stat blueprint
#
# Juha Takala 08.05.2020 19:11:31

import logging
logger = logging.getLogger('stkserver')
import time
import re
import os

from flask import flash, render_template, request
from flask_security import roles_accepted, login_required
# from flask_babelex import _

# from ui.user_context import UserContext

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

    Empty PATTERNS equals LOG_FILES.  Return matching filenames in
    LOG_ROOT.

    """
    import glob
    if patterns == "":
        patterns = f"{log_file}*"
    files = []
    for pat in re.split(" ", patterns):
        files += list(filter(os.path.isfile, glob.glob(f"{log_root}/{pat}")))
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    files = [ x for x in files if re.search("\.log(_[\d-]+)?$", x)]
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
        re.compile(re.sub("[, ]+", "|", val))
        return "," . join(re.split("[, ]+", val))
    except Exception as e:
        flash(f"Bad regexp for {what} '{val}': {e}",
              category='warning')
    return ""

################
#
def build_options(logdir, logname_template, lookup_table):

    bycount = request.args.get("bycount", None)
    bywhat  = request.args.get("bywhat", "user")
    logs    = request.args.get("logs", "") # removed selection from UI
    msg     = check_regexp_option("msg")
    period  = request.args.get("period", "daily")
    users   = check_regexp_option("users")
    topn    = safe_get_request("topn", 42)

    # opts from template, they go to logreader and back to template as
    # defaults values
    opts = {
        "bycount": bycount,
        "bywhat" : bywhat,
        "logdir" : logdir,
        "logs"   : logs,        # used before logreader to filter logfiles
        "msg"    : msg,
        "period" : period,
        "users"  : users,
        "topn"   : topn,
    }

    pkey = f"By_{bywhat}"
    if pkey not in lookup_table:
        if "By_user" in lookup_table:
            flash(f"Bad primary sort key '{bywhat}', trying 'user'")
            pkey = "By_user"
        else:
            flash("Can not decide primary sort key")
            return None         # this will fail in caller

    logfiles = get_logfiles(logdir, logname_template, patterns=logs)

    return pkey, lookup_table[pkey], logfiles, opts



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
    logdir = shareds.app.config['STK_LOGDIR']

    t0 = time.time()

    (pkey, parser, logfiles, opts) = build_options(
        logdir, shareds.app.config['STK_LOGFILE'], {
        "By_msg" : logreader.StkServerlog.save_bymsg,
        "By_date": logreader.StkServerlog.save_bydate,
        "By_user": logreader.StkServerlog.save_byuser,
    })

    # res [] could collect results from many logreader invocations, one set
    # from each call (inside loop, as we once did)
    res = []
    # We now have one logreader to read all log files (outside the loop):
    logrdr = logreader.StkServerlog(
        "Top_level",
        by_what = [ (pkey, parser) ],
        opts    = opts,
    )
    for f in logfiles:
        logrdr.work_with(f)
    res.append(logrdr.get_report()) # that will be one filesection

    elapsed = time.time() - t0
    logger.info(f"-> bp.stat.app e={elapsed:.4f}")
    return render_template("/stat/appstat.html",
                           h2      = "Application usage statistics",
                           caller  = "/stat/appstat",
                           title   = "App stats",
                           res     = res,
                           opts    = opts,
                           elapsed = elapsed,
    )


################################################################
#
@bp.route('/stat/uploadstat', methods = ['GET', 'POST'])
@login_required
@roles_accepted('admin')
def stat_upload():
    """Statistics about stk uploads.
    """
    logdir = "uploads/*"

    t0 = time.time()

    (pkey, parser, logfiles, opts) = build_options(
        logdir, "*.log", {
            "By_msg"   :  logreader.StkUploadlog.save_bymsg,
            "By_date"  :  logreader.StkUploadlog.save_bydate,
            "By_user"  :  logreader.StkUploadlog.save_byuser,
        })

    # Create one logreader to read all logfiles
    logrdr = logreader.StkUploadlog(
        "Top_level",
        by_what = [ (pkey, parser) ],
        opts    = opts,
    )
    for f in logfiles:
        logrdr.work_with(f)
    res = [logrdr.get_report()] # that will be one filesection for all
                                    # files in the loop

    elapsed = time.time() - t0
    logger.info(f"-> bp.stat.uploadstat e={elapsed:.4f}")
    return render_template("/stat/appstat.html",
                           h2      = "Data upload statistics",
                           caller  = "/stat/uploadstat",
                           title   = "Upload stats",
                           res     = res,
                           opts    = opts,
                           elapsed = elapsed,
    )

