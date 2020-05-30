#
# Helper functions for stk statistics module route funtions
#
# Juha Takala 30.05.2020 16:09:40

from flask import flash, request
import re
import os
import shareds


################################################################
#
def build_general_stats():
    """Collect general statistics"""

    ################
    #
    def run_cmd(cmd):
        """Run a shell command."""
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
    def count_files_lines(fpat, line_pattern=None):
        """Count files matching file pattern FPAT, and lines in them.

        Files to work with are searced under application root (see below).
        If optional line pattern LINE_PATTERN given, count only matching lines.
        WARNING: This may be os specific (read: not tested in windows)
        """
        # This is the root directory where the files are searched under:
        code_root = shareds.app.config['APP_ROOT']

        grep = ""
        if line_pattern is not None:
            grep = f" | grep '{line_pattern}'"
        filenames = run_cmd(f"find {code_root} -name '{fpat}'")
        linecount = run_cmd(f"cat {' '.join(filenames)}{grep} | wc -l")
        return (len(filenames), int(linecount[0]))

    (code_files, code_lines) = count_files_lines("*.py")
    (html_files, html_lines) = count_files_lines("*.html")
    (route_files, route_lines) = count_files_lines("routes.py", line_pattern=r"^@.*route")
    commits = int(run_cmd("git log | grep commit | wc -l")[0])
    commits1m = int(run_cmd(f"git log --after '1 month ago' | grep commit | wc -l")[0])
    res = {
        "code_files": code_files,
        "code_lines": code_lines,
        "html_files": html_files,
        "html_lines": html_lines,
        "route_files": route_files,
        "route_lines": route_lines,
        "commits": commits,
        "commits1m": commits1m,
    }
    return res


################################################################
#
def build_options(logdir, logname_template, lookup_table):
    """Create options to do logfile parsing.

    Given LOGDIR and LOGNAME_TEMPLATE, create list of log file name
    (3. return value).

    User options from http GET/POST method are collected (4. return value).

    User's option 'bywhat' is used to decide what logreader class seve_xxx
    method in LOOKUP_TABLE shoud be used to perform log file processing
    (1. and 2. return values).

    """
    ################
    #
    def get_logfiles(log_root, log_files, patterns=""):
        """Get ist of log files matching PATTERNS.

        Empty PATTERNS equals LOG_FILES.  Return matching filenames in
        LOG_ROOT.

        """
        import glob
        if patterns == "":
            patterns = f"{log_files}*"
        files = []
        for pat in re.split(" ", patterns):
            files += list(filter(os.path.isfile, glob.glob(f"{log_root}/{pat}")))
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        files = [ x for x in files if re.search("\.log(_[\d-]+)?$", x)]
        return files

    ################
    #
    def safe_get_request(opt_key, default):
        """Verify that OPT_KEY is valid integer"""
        res = request.args.get(opt_key, default)
        if res == "":
            return default
        try:
            return int(res)
        except ValueError as e:
            flash(f"Bad number for {opt_key} '{res}': {e}; using default {default}",
                  category='warning')
            return default

    ################
    #
    def verify_option_as_valid_regexp(opt_key, default=""):
        """Verify that OPT_KEY compiles as valid regexp."""
        val = request.args.get(opt_key, default)
        if val == "":
            return ""
        try:
            re.compile(re.sub("[, ]+", "|", val))
            return "," . join(re.split("[, ]+", val))
        except Exception as e:
            flash(f"Bad regexp for {opt_key} '{val}': {e}",
                  category='warning')
        return ""


    bycount = request.args.get("bycount", None)
    bywhat  = request.args.get("bywhat", "user")
    logs    = request.args.get("logs", "") # removed selection from UI
    msg     = verify_option_as_valid_regexp("msg")
    period  = request.args.get("period", "daily")
    users   = verify_option_as_valid_regexp("users")
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


