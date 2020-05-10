# Flask routes program for Stk application stat blueprint
#
# Juha Takala 08.05.2020 19:11:31

import logging
logger = logging.getLogger('stkserver')
import time
import re

from flask import render_template, request, redirect, url_for, jsonify
from flask_security import roles_accepted, login_required
from flask_babelex import _

import shareds

from . import bp


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


@bp.route('/stat')
@login_required
@roles_accepted('admin')
def stat_home():
    """Statistiikkaa palvelimelta.
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

    elapsed = time.time() - t0
    logger.info(f"-> bp.stat, {elapsed:.4f}")
    return render_template("/stat/stat.html",
                           code_files = code_files,
                           code_lines = code_lines,
                           html_files = html_files,
                           html_lines = html_lines,
                           route_files = route_files,
                           route_lines = route_lines,
                           commits = int(commits[0]),
                           elapsed = elapsed,
    )


@bp.route('/stat/appstat')
@login_required
@roles_accepted('admin')
def stat_app():
    """Statistiikkaa palvelimelta.
    """
    t0 = time.time()

    log_root = shareds.app.config['STK_LOGDIR']
    log_file = shareds.app.config['STK_LOGFILE']
    from .models import logreader
    opts = {
        "topn": 99,
        "width": 80,
    }

    log = logreader.Log(opts)
    log.work_with(f"{log_root}/{log_file}")
    log.print_counts()
    lines = log.result()
    # log.clear()

    elapsed = time.time() - t0
    logger.info(f"-> bp.stat.app, {elapsed:.4f}")
    return render_template("/stat/appstat.html",
                           lines = lines,
                           elapsed = elapsed )

