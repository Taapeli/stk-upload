#
# Class for reading stk server logs
#

import re
#import os

from flask import flash


################################################################
#
# helper funcions
#

################
#
def string_to_number(txt):
    """Try to convert TXT into integer or float (in that order)."""
    try:
        val = int(txt)
        return val
    except ValueError:
        try:
            val = float(txt)
            return val
        except ValueError:
            return None

################
#
def number_to_string(x):
    """Format our numbers, floats to reasonable precision."""
    if type(x) == int:
        return str(x)
    if type(x) == float:
        return f"{x:.3f}"


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


################################################################
#### class definitions

class Counter():
    """Building block class that is used for StkServerlog.

    And maybe for other logreaders also.

    """
    def __init__(self, name, level=0, opts=None):
        """Initialize new Counter with NAME at depth LEVEL."""
        self._opts   = opts
        self._level  = level
        self._name   = name     # name of this (sub)Counter
        self._counters = {}     # dict of subCounter objects
        self._values = {        # values that we keep track at this level
            "call_count": 0,
        }

    ################
    #
    def increment(self, tag="call_count", incr=1):
        """Increment (or create) Counters _values[TAG] by INCR (default=1)."""
        incval = incr
        if type(incr) == str:
            incval = string_to_number(incr)
        if incval is None:
            # print(f"self._values['{tag}'] += {incr}")
            return

        if tag in self._values:
            # The TAG exists, update it...
            self._values[tag] += incval
        else:
            # ... otherewise we create the TAG (with initial value)
            self._values[tag] = incval
        return

    ################
    #
    def get_or_create(self, name, can_create=True, opts=None):
        """Find (or create) existing sub-Counter with NAME."""
        if name in self._counters:
            return self._counters[name]
        if can_create:
            if opts is None:
                opts = self._opts
            self._counters[name] = Counter(name, self._level+1, opts=opts)
            return self._counters[name]
        return None

    ################
    #
    def update(self, taglist=None, inner_specs=None):
        """Update (or create) this and maybe inner Counters.

        Each TAGLIST is list of tuples (tag_name, incr).  If TAGLIST is
        None, use defaults 'n' and 1.

        INNER_SPECS is list of tuples (counter_name, TAGLIST), for nested
        inner counters.

        """

        if taglist is not None:
            # Increment all given tags with given values
            for (tag_name, incr) in taglist:
                self.increment(tag=tag_name, incr=incr)

        # Are there sub-Counters?
        if inner_specs is None:
            self.increment()
            return

        # Go thru all sub-Counters (levels) given in INNER_SPECS.
        # INNER_SPECS is list of tuples: (key, TAGLIST) ...
        for (counter_name, inner_taglist) in inner_specs:
            counter = self.get_or_create(counter_name)
            counter.update(taglist=inner_taglist)

        return

    ################
    #
    def get_value(self, cumul=False):
        """Get current Counter's _value['n'].

        If CUMUL is True, sum up all sublevels and return total count.
        """
        if not cumul or len(self._counters) == 0:
            return self._values["call_count"]

        res = 0
        for counter in self._counters.values():
            # counter = self.get_or_create(counter_name, can_create=False)
            res += counter.get_value(cumul=True)
        return res


    ################
    #
    def topn_subcounters(self):
        """Get TOPN first sub-Counter objects.

        Details (bycount?, cumulative?, topN) are in SELF._opts.
        Returns list of Counter objects.
        """

        # use the negative number trick to get numeric sorting
        # reverse & alpa non-reverse (we can't use reverse=True
        # because that woud reverse the alpha sorting too)
        bycount = self._opts["bycount"] is not None
        if bycount:
            cumulative = self._opts["cumul"] is not None
            result = sorted(self._counters.values(),
                            key = lambda x: (-x.get_value(cumul=cumulative),
                                             x._name) )

        else:
            result = sorted(self._counters.values(),
                            key = lambda x: x._name)

        topn = self._opts["topn"]
        if topn is not None:
            result = result[:topn]
        return result


    ################
    #
    def get_subreport(self, level):
        """Get counts of Counter.

        TOPN limits the length of resulting list (at each level).
        BYCOUNT makes reult sorted by count (default=False).
        LEVEL is current level of Counter.
        MAXLEVELS gives the number of sub-Counters to show

        Return value is a tuple (self._name, [dataline, ...],
        Each dataline is list [column, ...], first columns is line number.
        """
        if level >= self._opts["maxlev"]:
            print(f"too deep {level} >= {self._opts['maxlev']}")
            return()

        lines = []
        columns = []
        # before sub-Counters, add own level tags
        for tag, value in self._values.items():
            txt = self._name if tag == "call_count" else tag
            columns += [f"{txt}", f"{number_to_string(value)}"]
        lines.append(columns)

        # Get list of TOPN sub-Counters
        top_counters = self.topn_subcounters()
        for counter in top_counters:
            sub_res = counter.get_subreport(level+1)
            if sub_res is None:
                continue
            lines += sub_res
            # sub_lines = sub_res[1]
            # for sub_line in sub_lines:
            #     lines.append(line + sub_line)
        return(lines)


    ################
    #
    def get_report(self):
        """Get the counts of this Log.

Return value is list of nested tuples: (filename, [dataline, ...]).
        """

        res = []
        for counter in self._counters.values():
            res.append(counter.get_subreport(level=0))
        files = [ x[x.rindex("/")+1:] for x in self._files ]

        return(", ".join(files), res)


################################################################
#
class StkServerlog(Counter):
    """Top level class to keep event counts found in stkserver log file(s).

Counters are kept in list of Counter objects.
"""

    def __init__(self, name, level=0, by_what=[], opts=None):
        super().__init__(name, level, opts=opts)
        self._files  = []       # list of files already processed
        self._savers = {}
        for (name, saver) in by_what:
            self._savers[saver] = self.get_or_create(name)

        """
Toistaiseksi olisi 2 mittaria: modulin nimi=käydyt sivut ja n=käsitellyt
rivit tms.  Raportointia voisi rakentaa käyttäjien käyntimääristä
kuukausittain (käyttäjittäin monenako päivänä, montako eri käyttäjää) ja
suosituimmat sivut ja niiden datavolyymit.

Kuukausittaiset määrät tulee helposti siitä, kun lokit on kuukauden lokeja.

        """

    def work_with(self, file):
        """Call log_parser to get values, store them useing counter_xxx.

        """
        if file in self._files:
            flash(f"Already done file {file}") # this should not happen
            return
        self._files.append(file)  # protect against double processing

        # read date, module, user, tuples from parser
        # call designated counter_xxx to store values
        for tup in self.parser(file):
            print(f"{tup}")
            for saver in self._savers:
                counter = self._savers[saver]
                saver(counter, tup)
        return


    def saver_bymsg(self, tup):
        (_, module, user, tuples) = tup
        self.update(inner_specs = [ (module, None), (user, tuples), ] )

    def saver_bydate(self, tup):
        (date, _, user, tuples) = tup
        self.update(inner_specs = [ (date, None), (user, tuples) ] )


    ################
    #
    def parser(self, file: str):
        """Read stkserver log FILE.  Collect counts of messages."""


        # Format of log messages (see app/__init__.py)
        # '%(asctime)s %(name)s %(levelname)s %(user)s %(message)s'
        #
        # The %(asctime)s part is made of two parts:
        ymd_part = r'\d\d\d\d-\d\d-\d\d'
        hms_part = r'\d\d:\d\d:\d\d,\d\d\d'

        # This shall match each line in log file;
        # we don't need the %(name)s part, the other groups we keep
        log_re = re.compile(f'({ymd_part}) ({hms_part})'
                            f' \S+ (\S+) (\S+) (.*)')

        # We are interested only about entries where %(message)s part looks
        # like this:
        arrow_re = re.compile(r"^-> ([^ ]+)(.*)")

        # Additional info in %(message)s part look like x=y
        equals_re = re.compile(r"\b(\S+)=(\S+)\b")


        users_re    = get_regexp_from_opts("users", self._opts)
        want_msg_re = get_regexp_from_opts("msg", self._opts)

        for line in open(file, "r").read().splitlines():
            match = log_re.match(line)
            if not match:
                flash(f"strange log line {line}") # this should not happen
                continue
            (date, _, level, user, message) = match.groups()
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
            yield date, module, user, tuples

        return


# ################################################################
# #
# class StkUploadlog():
#     """Class to handle stk upload log file(s)."""

#     def __init__(self, opts={}):
#         self._opts = opts
#         self._by_date = dict()
#         self._by_step = dict()
#         self._by_user = dict()
#         self._files = []        # list of files already processed


#     ################
#     #
#     def work_with(self, logfile: str) -> None:
#         """Read stkserver log FILE.  Collect counts of messages."""

#         if logfile in self._files:
#             flash(f"Already done file {logfile}") # this should not happen
#             return
#         print(f"working with {logfile}")
#         self._files.append(logfile)  # protect against double processing

#         # Dig the user name from logfile pathname:
#         last_slash_pos = logfile.rindex("/")
#         second_to_last = logfile.rindex("/", 0, last_slash_pos-1)
#         user = logfile[second_to_last+1 : last_slash_pos]
#         print(f"u={user}")

#         upload_re1 = re.compile(r"^INFO ([^:]+): (\d+)(?: / ([\d.]+) sek)?$")
#         upload_re2 = re.compile(r"^TITLE Total time: +/ ([\d.]+) sek")
#         upload_re3 = re.compile(r"^(\d\d\.\d\d.\d\d\d\d) (?:\d\d:\d\d)")
#         upload_re4 = re.compile(r"^Stored the file (.+) from user (.+) to neo4j$")

#         ymd = None
#         for line in open(logfile, "r").read().splitlines():
#             m = upload_re1.match(line)
#             if m:               # starts with INFO
#                 if user is None:
#                     flash(f"logfile {logfile} no user found before INFO line")
#                     return
#                 (step, count, time) = m.groups()
#                 step = step.split(" ")[0]
#                 # print(f"INFO: s='{step}' n='{count}' t='{time}'")
#                 if time is None: time = "0.0"
#                 update_counter( self._by_step, step, user,
#                              tuples=[ ("n", count), ("t", time ), ] )
#                 update_counter( self._by_date, ymd, step,
#                              tuples=[ ("n", count), ("t", time ), ] )
#                 continue

#             m = upload_re2.match(line)
#             if m:               # has Total time
#                 time = m.group(1)
#                 print(f"t='{time}'")
#                 update_counter( self._by_user, user, "total_time",
#                              tuples=[ ("n", 1), ("t", time ), ] )
#                 continue

#             m = upload_re3.match(line)
#             if m:               # line has {dmy} ...
#                 dmy = m.group(1)
#                 parts = dmy.split("\.")
#                 parts.reverse()
#                 # just remeber the ymd
#                 ymd = "-".join(parts)
#                 # print(f"ymd='{ymd}'")
#                 continue

#             m = upload_re4.match(line)
#             if m:               # Stored .... from user {user}
#                 # just remember the user
#                 # (datafile, user) = m.groups()
#                 # print(f"Stored f='{datafile}' u='{user}'")
#                 continue

#             if line != "":
#                 print(line)

#         return

#     def get_counts(self, style="text"):
#         res = []
#         res.append(get_section_counts(self._by_step, "By step",
#                                       width     = 6,
#                                       bycount   = "bycount" in self._opts,
#                                       showusers = "users" in self._opts,
#                                       topn      = self._opts["topn"],
#                                       style     = self._opts["style"],
#         ))
#         files = [ x[x.rindex("/")+1:] for x in self._files ]

#         return(", ".join(files), res)

