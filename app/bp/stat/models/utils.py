#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta, Juha Takala
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

#
# Helper functions for stk statistics module route funtions
#
# Juha Takala 30.05.2020 16:09:40

from flask import flash, request
import re
import os
import glob
import shareds

################################################################
#
def glob2regexp(glob):
    """Convert (almost) shell wildcard pattern GLOB into python regexp.

    Return value is tuple (regex, wanted_if_match).

    If the list starts with '!', the second retun value is False, meaning: do
    not select objects matching GLOB.

    """
    val = glob
    want_if_match = True

    if val.startswith("!"):
        val = re.sub(r"^!\s*", "", val)
        want_if_match = False

    parts = []
    for part in re.split("[, ]", val):
        parts.append(re
                     .escape(part)
                     .replace(r'\?', '.')
                     .replace(r'\*', '.*?')
        )
    val = "|".join([f"(?:{x})" for x in parts])
    val = "^" + val + "\Z"
    #print(f"val = '{val}'")
    try:
        return re.compile(val), want_if_match
    except Exception as e:
        flash(f"bp.stat.models.utils.glob2regexp: Bad regexp {e}", category='warning')
        #flash(f"Bad regexp for {what} '{self._opts[what]}': {e}", category='warning')
    return None, True


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

        Files to work with are searched under application root (see below).
        If optional line pattern LINE_PATTERN given, count only matching lines.
        WARNING: This may be os specific (read: not tested in windows)
        """
        # This is the root directory where the files are searched under:
        code_root = shareds.app.config['APP_ROOT'] + "/app"
        # Process files by chunks to avoid too long lines
        CHUNK_SIZE = 25    
        total = 0

        filenames = run_cmd(f"find {code_root} -name '{fpat}'")
        if line_pattern:
            grep = f" | grep '{line_pattern}'"
        else:
            grep = ""
        chunks = [ filenames[i:i+CHUNK_SIZE] for i in range(0, len(filenames), CHUNK_SIZE) ]
        for f_names in chunks:
            s = ""
            for fn in f_names:
                if fn:
                    s += " '" + fn + "'"
            res = run_cmd(f"cat {s}{grep} | wc -l")
            # wc returns something like "1437\n", where run_cmd returns ['471', '']
            #print("count_files_lines:",len(f_names),"names",len(s),"chars",res,"cnt")
            if len(res) > 0 and len(res[0]) > 0:
                total += int(res[0])
        return (len(filenames), total)

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
def build_options(logname_template, lookup_table):
    """Create options to do logfile parsing.

    Given LOGNAME_TEMPLATE, create list of log file name (3. return value).

    User options from http GET/POST method are collected (4. return value).

    LOOKUP_TABLE is dict where each key shall match user's option 'pkey',
    and value must be a logreader class save_byxxx method, to be used for
    counting log file entries (1. and 2. return values).

    """
    ################
    #
    def get_logfiles(log_root, logname_template):
        """Get list of log files.

        Potential files are searched under LOG_ROOT (shell glob)
        directory (directories).

        Return filenames mathing LOGNAME_TEMPLATE (shell glob) and ending with
        '.log', + maybe timestamp '_yyyy-mm-dd', sorted by age.

        """

        files = list(filter(os.path.isfile,
                            glob.glob(f"{log_root}/{logname_template}*")))
        # sort by age:
        files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        files = [ x for x in files if re.search("\.log(_[\d-]+)?$", x)]
        return files

    ################
    #
    def get_servers(logname_template):
        """Return list of servers that we have logs for.

        If LOGNAME_TEMPLATE starts with '*', we are to find upload logs, and
        the list has just last component of shareds.app.config['STK_LOGDIR'].

        Else, all sibling directories' last components; e.g. ["omatammi",
        "isotammi", "isotest", "demo"] or some such.

        """
        stk_logdir = shareds.app.config['STK_LOGDIR']
        inx = stk_logdir.rindex("/")
        if logname_template.startswith("*"):
            return [stk_logdir[inx+1:]]
        parent = stk_logdir[:inx]
        dirs = [ d for d in glob.glob(parent + "/*")
                 if os.path.isdir(d) or os.path.ismount(d) ]
        servers = [x[x.rindex("/")+1:] for x in dirs]
        return sorted(servers)

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
        opt_val = request.args.get(opt_key, default)
        if opt_val is None or opt_val == "":
            return ""
        # Verify that it is valid
        (regexp, _) = glob2regexp(opt_val)
        if regexp is None:
            return ""           # it failed, pretend it was empty
        return opt_val          # it works, keep it


    servers = get_servers(logname_template)
    bycount = request.args.get("bycount", None)
    pkey    = request.args.get("pkey", "user")
    server  = request.args.get("server", servers[0])
    msg     = verify_option_as_valid_regexp("msg")
    period  = request.args.get("period", "daily")
    users   = verify_option_as_valid_regexp("users")
    topn    = safe_get_request("topn", 42)

    # opts from html form, they go to logreader and back to html form as next
    # default values
    opts = {
        "bycount": bycount,     # sorting order for log entries: count/text
        "pkey"   : pkey,        # primary key for report ordering: user/date/method
        "server" : server,      # to choose server to process logs for
        "servers": servers,     # ...
        "msg"    : msg,         # str (regexp) to filter log msgs/methods
        "period" : period,      # aggregation period: day/week/month
        "users"  : users,       # str (regexp) to filter log entries by username
        "topn"   : topn,        # integer to limit max count of log entries
    }

    if pkey not in lookup_table:
        if "user" in lookup_table:
            flash(f"Bad primary sort key '{pkey}', trying 'user'")
            pkey = "user"
        else:
            flash("Can not decide primary sort key")
            return None         # this will fail in caller

    if logname_template.startswith("*"):
        logdir = "uploads/*/*"
    else:
        stk_logdir = shareds.app.config['STK_LOGDIR']
        logdir = stk_logdir[:stk_logdir.rindex("/")+1] + server

    logfiles = get_logfiles(logdir, logname_template)

    return pkey, lookup_table[pkey], logfiles, opts


