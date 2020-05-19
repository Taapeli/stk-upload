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
                    f' \S+ (\S+) (\S+) (.*)')

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
        if type(tup[1]) != dict:
            return 1
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
def update_dict(dicti, key1, key2=None, incr=1, tuples=None):
    """Update (or create) the counters in dict DICTI.

If KEY2 is not None, initialize inner dict as DICTI[KEY1][KEY2] with
{'TOTAL': incr}.

TUPLES contains additional (key, value) into the inner dict.

    """
    if key1 not in dicti:
        dicti[key1] = dict()
        dicti[key1]["TOTAL"] = 0
    dicti2 = dicti[key1]
    dicti2["TOTAL"] += 1

    if key2 is None:
        return

    if key2 not in dicti2:
        dicti2[key2] = dict()
        dicti2[key2]["TOTAL"] = 0
    dicti3 = dicti2[key2]
    dicti3["TOTAL"] += incr

    if tuples is None:
        return

    for tup in tuples:
        val = string_to_number(tup[1])
        if val is None:
            # what to do with these?
            # print(f"got {module} {user} {tup[0]}={tup[1]}")
            continue
        # print(f" -> {key1}, {key2}, {incr}, {tuples} --> {key2}, {tup[0]}, {val}")
        if tup[0] in dicti3:
            dicti3[tup[0]] += val
        else:
            dicti3[tup[0]] = val
    return

################
#
def get_topn(dicti, bycount, topn=None):
    # use the negative number trick to get numeric sorting
    # reverse & alpa non-reverse (we can't use reverse=True
    # because that woud reverse the alpha sorting too)
    if bycount:
        result = sorted(dicti.items(),
                        key=lambda x:
                        (-x[1] if type(x[1]) == int else -x[1]["TOTAL"],
                         x[0]))
    else:
        # print(f"{dicti}")
        result = sorted(dicti.items())

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

################
#
def get_section_counts(dicti, heading,
                       topn=None, bycount=False, showusers=False, style="table"):
    """Get counts of section DICTI.

Return value is a tuple (HEADING, [dataline, ...]).
    """

    countx = get_topn(dicti, bycount, topn=topn)
    len_user = find_longest(countx, "user")
    len_msg = find_longest(countx, "msg")
    destcol = len_msg + 1
    destcol = max(destcol, 10)
    # print(f"u={len_user} m={len_msg} d={destcol}")
    lines = []
    n = 0
    for message, ulist in countx:
        n += 1
        before = f"{n:2d}"

        # Truncate too long messages
        if len(message) >= destcol:
            message = message[:destcol-3] + "·"*3

        # The message and filler to make report look nicer
        part1 = f"{before} {message}"
        filler = make_filler(destcol - len(message), 3)

        # add them and count stuff
        if showusers:   #  show not users' counts?
            cnt = format_count(ulist)
            if style == "text":
                lines.append(f"{part1} {filler}  {cnt}")
            if style == "table":
                lines.append([before, message, cnt])
            continue

        # lines after first line are filled with spaces up to destcol
        for user, count in get_topn(ulist, bycount, topn=topn):
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
            (ymd, hms, level, user, message) = match.groups()
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

            update_dict(self._by_msg, module, key2=user)
            update_dict(self._by_ymd, ymd,    key2=user, tuples=tuples)

        return

    ################
    #
    def get_counts(self, style="text"):
        """Get the counts of this Log, maybe per user.

Return value is list of nested tuples: (heading, [dataline, ...]).
        """

        res = []
        res.append(get_section_counts(self._by_msg, "By msg:",
                                      bycount   = "bycount" in self._opts,
                                      showusers = "users" in self._opts,
                                      topn      = self._opts["topn"],
                                      style     = self._opts["style"],
        ))
        res.append(get_section_counts(self._by_ymd, "By date:",
                                      bycount   = "bycount" in self._opts,
                                      showusers = "users" in self._opts,
                                      topn      = self._opts["topn"],
                                      style     = self._opts["style"],
        ))
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
        upload_re3 = re.compile(r"^(\d\d\.\d\d.\d\d\d\d) (\d\d:\d\d)")
        upload_re4 = re.compile(r"^Stored the file (.+) from user (.+) to neo4j$")
        for line in open(file, "r").read().splitlines():
            m = upload_re1.match(line)
            if m:               # starts with INFO
                (step, count, time) = m.groups()
                step = step.split(" ")[0]
                print(f"INFO: s='{step}' n='{count}' t='{time}'")
                if time is None: time = "0.0"
                update_dict( self._by_step, step, user,
                             tuples=[
                                 ("n", count),
                                 ("t", time ),
                            ]
                )
                continue

            m = upload_re2.match(line)
            if m:               # starts with TITLE
                (title, time) = m.groups()
                print(f"TITLE: '{title}' t='{time}'")
                if "Storing" in title:
                    continue
                #  update_dict( self._by_step, user, "total_time", incr = time )
                continue

            m = upload_re3.match(line)
            if m:               # line has {dmy} {hm}
                (dmy, hm) = m.groups()
                print(f"dmy='{dmy}' hm='{hm}'")
                continue

            m = upload_re4.match(line)
            if m:               # Stored {file} from user {user}
                (datafile, user) = m.groups()
                print(f"Stored f='{datafile}' u='{user}'")
                continue

            if line != "":
                print(line)

            #update_dict(self._by_step, ymd, user, tuples=tuples)

        return

    def get_counts(self, style="text"):
        res = []
        res.append(get_section_counts(self._by_step, "By user",
                                      bycount   = "bycount" in self._opts,
                                      showusers = "users" in self._opts,
                                      topn      = self._opts["topn"],
                                      style     = self._opts["style"],
        ))
        files = [ x[x.rindex("/")+1:] for x in self._files ]

        return(", ".join(files), res)


