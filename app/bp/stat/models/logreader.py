#
# Class for reading stk server logs
#

import re
import os

from flask import flash


################
#
# Format of log messages (see app/__init__.py)
# '%(asctime)s %(name)s %(levelname)s %(user)s %(message)s'
#
ymd_re = r'\d\d\d\d-\d\d-\d\d'
hms_re = r'\d\d:\d\d:\d\d,\d\d\d'

# This shall match each line in log file
log_re = re.compile(f'({ymd_re}) ({hms_re})'
                    f' (\S+) (\S+) (\S+) (.*)')

# We are interested only about entries where %(message)s part looks like this:
arrow_re = re.compile(r"^-> ([^ ]+)(.*)")

# Additional info in %(message)s part look like this:
equals_re = re.compile(r"\b(\S+)=(\S+)\b")


################
#
def find_longest(list_of_tuples, what):
    longest = 0
    for tup in list_of_tuples:
        if what == "msg":
            if len(tup[0]) > longest:
                longest = len(tup[0])
            continue
        for u in tup[1].keys():
            if len(u) > longest:
                longest = len(u)
    return longest

################
#
def make_filler(totlen, flen):
    return(" "*(totlen % flen)
           + (" "*(flen-1) + ".") * (totlen // flen))

################
#
def string_to_number(txt):
    """Try to convert TXT into integer or float (in that order)."""
    try:
        val = int(txt)
        return val
    except ValueError:
        pass
    try:
        val = float(txt)
        return val
    except ValueError:
        return None

################
#
def get_regexp_from_opts(what, opts):
    """Compile comma separated regexp patterns into one."""
    if what not in opts or opts[what] == "":
        return None
    try:
        return re.compile( re.sub("[, ]+", "|", opts[what]) )
    except Exception as e:
        flash(f"Bad regexp for {what} '{opts[what]}': {e}",
              category='warning')
    return None

################
#
def update_one_counter(dicti, outer_key, inner_key, incr=1, tuples=None):
    """Update (or create) the dict OUTER[KEY]"""
    if outer_key not in dicti:
        dicti[outer_key] = dict()
        dicti[outer_key]["TOTAL"] = 0

    inner_dicti = dicti[outer_key]
    if tuples is None:
        # Update these only after recursion?
        print(f" -> {outer_key}, {inner_key}, {inner_dicti['TOTAL']}, {incr}, {tuples}")
        inner_dicti["TOTAL"] += 1
        if inner_key in inner_dicti:
            inner_dicti[inner_key] += incr
        else:
            inner_dicti[inner_key] = incr
        return

    # Recursive call to process TUPLES
    # update_one_counter (inner_dicti, inner_key, "TOTAL")
    for tup in tuples:
        val = string_to_number(tup[1])
        if val is not None:
            update_one_counter(inner_dicti, inner_key, tup[0], incr=val)
        else:
            # what to do with these?
            # print(f"got {module} {user} {tup[0]}={tup[1]}")
            continue
    return

################
#
def get_topn(tuples, topn=None, by_count=False):
    # use the negative number trick to get numeric sorting
    # reverse & alpa non-reverse (we can't use reverse=True
    # because that woud reverse the alpha sorting too)
    if by_count:
        result = sorted(tuples.items(),
                        key=lambda x:
                        (-x[1] if type(x[1]) == int else -x[1]["TOTAL"],
                         x[0]))
    else:
        result = sorted(tuples.items())

    if topn is not None:
        result = result[:topn]
    return result

################
#
def format_count(count_or_dict):
    if type(count_or_dict) == int:
        return f"{count_or_dict:4d}"
    elif type(count_or_dict) == dict:
        return f"{count_or_dict['TOTAL']:4d}"
    else:
        return "???"


################################################################
#### class definitions below

################################################################
#
class StkServerlog ():
    """Class to handle stkserver log file(s)."""

    def __init__(self, opts={}):
        self._opts = opts
        self._by_msg = dict()
        self._by_ymd = dict()
        self._files = []        # list of files already processed

        """
Toistaiseksi olisi 2 mittaria: modulin nimi=käydyt sivut ja n=käsitellyt
rivit tms.  Raportointia voisi rakentaa käyttäjien käyntimääristä
kuukausittain (käyttäjittäin monenako päivänä, montako eri käyttäjää) ja
suosituimmat sivut ja niiden datavolyymit.

Kuukausittaiset määrät tulee helposti siitä, kun lokit on kuukauden lokeja.

        """


    ################
    #
    def work_with(self, file: str) -> None:
        """Read stkserver log FILE.  Collect counts of messages."""

        if file in self._files:
            flash(f"Already done file {file}") # this should not happen
            return
        self._files.append(file)  # protect against double processing

        users_re    = get_regexp_from_opts("users", self._opts)
        want_msg_re = get_regexp_from_opts("msg", self._opts)

        for line in open(file, "r").read().splitlines():
            match = log_re.match(line)
            if not match:
                flash(f"strange log line {line}") # this should not happen
                continue
            (ymd, hms, logger, level, user, message) = match.groups()
            if level != 'INFO':
                continue

            if users_re and not users_re.match(user):
                continue

            match = arrow_re.match(message)
            if not match:
                continue

            (module, rest) = match.groups()
            if want_msg_re and not want_msg_re.match(module):
                continue

            # Get list of all x=y stuff (if any)
            tuples = equals_re.findall(rest)

            update_one_counter(self._by_msg, module, user)
            update_one_counter(self._by_ymd, ymd, user, tuples=tuples)

        return

    ################
    #
    def get_counts(self, style="text"):
        """Get the counts of this Log, maybe per user.

Return value is list of nested tuples: (heading, data-tuple).
        """
        def get_section_counts(outer, heading):
            """Get counts of one section.

Return value is a tuple (HEADING, data-list).
            """

            countx = get_topn(outer, self._opts["topn"])
            len_user = find_longest(countx, "user")
            len_msg = find_longest(countx, "msg")
            destcol = min(self._opts["width"], len_msg+1)
            destcol = max(destcol, 10)
            # print(f"u={len_user} m={len_msg} d={destcol}")
            lines = []
            n = 0
            for message, ulist in countx:
                n += 1
                before = f"{n:2d}" if "topn" in self._opts else ""

                # Truncate too long messages
                if len(message) >= destcol:
                    message = message[:destcol-3] + "·"*3

                # The message and filler to make report look nicer
                part1 = f"{before} {message}"
                filler = make_filler(destcol - len(message), 3)

                # add them and count stuff
                if "users" not in self._opts:   #  show not users' counts?
                    if style == "text":
                        lines.append(f"{part1} {filler}  {ulist['TOTAL']:4d}")
                    if style == "table":
                        lines.append([before, message, ulist["TOTAL"]])
                    continue

                # lines after first line are filled with spaces up to destcol
                for user, count in get_topn(ulist):
                    # For just one user, don't show the TOTAL, unless explicit request
                    if user == "TOTAL" and len(ulist) < 3:
                        continue
                    cnt = format_count(count)
                    if style == "text":
                        lines.append(f"{part1} {filler} {user:{len_user}s} {cnt}")
                        filler = " " * (destcol + len(before) +1)
                    if style == "table":
                        lines.append([before, message, user, cnt])
                        before = ""
                        message = ""
                    part1 = ""

            return(heading, lines)

        res = []
        res.append(get_section_counts(self._by_msg, "By msg:"))
        res.append(get_section_counts(self._by_ymd, "By date:"))
        files = [ x[x.rindex("/")+1:] for x in self._files ]

        return(", ".join(files), res)


################################################################
#
class StkUploadlog():
    """Class to handle stk upload log file(s)."""

    def __init__(self, opts={}):
        self._opts = opts
        self._by_step = dict()
        self._files = []        # list of files already processed


    ################
    #
    def work_with(self, file: str) -> None:
        """Read stkserver log FILE.  Collect counts of messages."""

        if file in self._files:
            flash(f"Already done file {file}") # this should not happen
            return
        print(f"working with {file}")
        self._files.append(file)  # protect against double processing
        upload_re1 = re.compile(r"^INFO ([^:]+): (\d+)(?: / ([\d.]+) sek)?$")
        upload_re2 = re.compile(r"^TITLE ([^:]+):(?:  / ([\d.]+) sek)? *$")
        upload_re3 = re.compile(r"^([^:]+):(.*)$")
        upload_re4 = re.compile(r"^Stored the file (.+) from user (.+) to neo4j$")
        for line in open(file, "r").read().splitlines():
            m = upload_re1.match(line)
            if m:               # starts with INFO
                (step, count, time) = m.groups()
                step = step.split(" ")[0]
                if time is None: time = "0.0"
                print(f"INFO: s='{step}' n='{count}' t='{time}'")
                update_one_counter(self._by_step, "INFO", step,
                                   tuples=[ ("n", count),
                                            ("t", time ), ])
                continue

            m = upload_re2.match(line)
            if m:               # starts with TITLE
                print(f"got 2 meta {m.groups()}")
                continue

            m = upload_re3.match(line)
            if m:               # line has :
                print(f"got 3 timestamp {m.groups()}")
                continue

            m = upload_re4.match(line)
            if m:               # other lines
                print(f"got 4 total {m.groups()}")
                continue

            if line != "":
                print(line)

            #update_one_counter(self._by_step, ymd, user, tuples=tuples)

        return

    def get_counts(self, style="text"):
        for step, count in self._by_step.items():
            print(f"{step} {format_count(count)}")
            for k,v in count.items():
                print(f"  {k}  {format_count(v)}")
        return
