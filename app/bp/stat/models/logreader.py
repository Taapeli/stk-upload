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
def number_to_string(x, w=2):
    """Format our number X, floats to W decimal places (default=2)."""
    if type(x) == int:
        return str(x)
    if type(x) == float:
        return f"{x:.{w}f}"

def is_wanted(target, matcher, want_if_match):
    """Return True if TARGET is matched by MATCER if WANT_IF_MATCH is True.

    If want_if_match is False return True is not matched.
    But if MATCHER is None, return always True.

    """
    if matcher is None:
        return True
    if want_if_match:
        return matcher.match(target)
    else:
        return not matcher.match(target)

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
            "N": 0,             # ...more will come from log files
        }

    ################
    #
    def increment(self, tag="N", incr=1):
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
            self._counters[name] = Counter(name, level=self._level+1, opts=opts)
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
            # Increment own tags with given values
            for (tag_name, incr) in taglist:
                self.increment(tag=tag_name, incr=incr)

        # Are there sub-Counters?
        if inner_specs is None:
            self.increment()    # no, just increment self
            return

        # Go thru all sub-Counters (levels) given in INNER_SPECS.
        # INNER_SPECS is list of tuples: (key, TAGLIST) ...
        cc = self
        for (counter_name, inner_taglist) in inner_specs:
            cc = cc.get_or_create(counter_name)
            cc.update(taglist=inner_taglist)

        return

    ################
    #
    def get_value(self):
        """Get current Counter's _value['N']."""
        return self._values['N']
        # res = 0
        # for counter in self._counters.values():
        #     # counter = self.get_or_create(counter_name, can_create=False)
        #     res += counter.get_value()
        # return res


    ################
    #
    def topn_subcounters(self):
        """Get TOPN first sub-Counter objects.

        Details (bycount?, topN) are in SELF._opts.
        Returns list of Counter objects.
        """
        def counter_value(x, tag):
            return x._values[tag] if tag in x._values else 0

        # use the negative number trick to get numeric sorting
        # reverse & alpa non-reverse (we can't use reverse=True
        # because that woud reverse the alpha sorting too)
        # print(f"{self._name}")
        if self._opts["bycount"] is not None:
            result = sorted(self._counters.values(),
                            key = lambda x: (-counter_value(x, "N"),
                                             -counter_value(x, "n"),
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

        self._opts['maxdepth'] gives the number of sub-Counters to show

        Return value is a tuple (self._name, [dataline, ...],
        Each dataline is list [column, ...], first columns is line number.

        This will finally become one subsection in html template.
        Return value is a tuple (section_name, [line, ...]),
        section_name is 'By_xxx' or some such.
        """

        lines = []              # lines is list of columns
        columns = []

        for _ in range(level-1):
            columns += ["", ""]

        # before sub-Counters, add own level tags
        if level > 0:
            columns += [self._name]
            for tag, value in self._values.items():
                columns.append(f"{tag}")
                val = f"{number_to_string(value)}"
                if tag == "e" or tag == "t":
                    val += " s"
                columns.append(val)
                if tag == "e" and self._values["N"] != 0:
                    columns.append(f"{number_to_string(1000*value/self._values['N'])} ms")
                if tag == "t" and "n" in self._values and self._values["n"] != 0:
                    columns += [f"{number_to_string(1000*value/self._values['n'])} ms"]
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

        if level == 0:
            return self._name, lines
        else:
            return lines


    ################
    #
    def get_report(self):
        """Get the counts of this log.

        Return value is list of nested tuples: (filename, [dataline, ...]).

        This will end as one filesection in html template.

        """

        res = []
        for counter in self._counters.values():
            res.append(counter.get_subreport(level=0))
        files = [ x[x.rindex("/")+1:] for x in self._files ]

        return(", ".join(files), res)


    ################
    #
    def get_regexp_from_opts(self, what):
        """Compile comma separated list of regexp patterns into one.

Return value is tuple (regex, wanted_if_match)
If the list starts with '!', the second retun value is False."""

        if what not in self._opts or self._opts[what] == "":
            return None, True

        want_if_match = True
        pattern = self._opts[what]
        if pattern.startswith("!"):
            pattern = pattern[1:]
            want_if_match = False

        try:
            return re.compile(re.sub("[, ]+", "|", pattern)), want_if_match
        except Exception as e:
            flash(f"Bad regexp for {what} '{self._opts[what]}': {e}",
                  category='warning')
        return None, True


    def save_bymsg(self, tup):
        """Save TUP data by by module | user order."""
        (date, module, user, tuples) = tup
        self.update(inner_specs = [ (module, None), (user, tuples), ] )

    def save_bydate(self, tup):
        """Save TUP data by by date | user order."""
        (date, module, user, tuples) = tup
        self.update(inner_specs = [ (date, None), (user, None), (module, tuples) ] )


    def save_byuser(self, tup):
        """Save TUP data by by user | module | date order."""
        (date, module, user, tuples) = tup
        self.update(inner_specs = [ (user, None), (module, None), (date, tuples) ] )


    def work_with(self, logfile):
        """Call parser to get values from stk upload log files.

        """
        if logfile in self._files:
            flash(f"Already done file {logfile}") # this should not happen
            return
        self._files.append(logfile)  # protect against double processing

        # read date, module, user, tuples from parser
        # call designated counter_xxx to store values
        for tup in self.parser(logfile):
            # print(f"{tup}")
            for saver in self._savers:
                counter = self._savers[saver]
                saver(counter, tup)
        return

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
        return

    """Toistaiseksi olisi 2 mittaria: modulin nimi=käydyt sivut ja
    n=käsitellyt rivit tms.  Raportointia voisi rakentaa käyttäjien
    käyntimääristä kuukausittain (käyttäjittäin monenako päivänä, montako
    eri käyttäjää) ja suosituimmat sivut ja niiden datavolyymit.

    Kuukausittaiset määrät tulee helposti siitä, kun lokit on kuukauden
    lokeja.

        """

    ################
    #
    def parser(self, logfile: str):
        """Parse data from stkserver log LOGFILE.

        Read the file line by line, yield the values found from each line.

        """

        # Format of log messages (see app/__init__.py)
        # '%(asctime)s %(name)s %(levelname)s %(user)s %(message)s'
        #
        # The %(asctime)s part is made of two parts:
        ymd_part = r'\d\d\d\d-\d\d-\d\d'
        hms_part = r'\d\d:\d\d:\d\d,\d\d\d'

        # This shall match each line in log LOGFILE;
        # we don't need the %(name)s part, the other groups we keep
        log_re = re.compile(f'({ymd_part}) ({hms_part})'
                            f' \S+ (\S+) (\S+) (.*)')

        # We are interested only about entries where %(message)s part looks
        # like this:
        arrow_re = re.compile(r"^-> ([^ ]+)(.*)")

        # Additional info in %(message)s part look like x=y
        equals_re = re.compile(r"\b(\S+)=(\S+)\b")

        # some filtering wanted by caller:
        (users_re, want_user)    = self.get_regexp_from_opts("users")
        (msg_re, want_msg) = self.get_regexp_from_opts("msg")

        for line in open(logfile, "r").read().splitlines():
            match = log_re.match(line)
            if not match:
                flash(f"strange log line {line}") # this should not happen
                continue
            (date, _, level, user, message) = match.groups()
            if level != 'INFO':
                continue

            if not is_wanted(user, users_re, want_user):
                continue

            match = arrow_re.match(message)
            if not match:
                continue

            (module, rest) = match.groups()
            if not is_wanted(module, msg_re, want_msg):
                continue

            # Get list of all x=y stuff (if any)
            tuples = equals_re.findall(rest)
            yield date, module, user, tuples

        return


################################################################
#
class StkUploadlog(Counter):
    """Class to handle stk upload log file(s)."""

    def __init__(self, name, level=0, by_what=[], opts=None):
        super().__init__(name, level, opts=opts)
        self._files  = []       # list of files already processed
        self._savers = {}
        (self._want_step_re,
         self._want_step_if_match) = self.get_regexp_from_opts("msg")
        for (name, saver) in by_what:
            self._savers[saver] = self.get_or_create(name)
        return

    ################
    #
    def parser(self, logfile: str) -> None:
        """Parse data from stk upload log LOGFILE.

        1) check that there is line starting with 'TITLE Total time:'; if
        not, the processing was not completed and count this log as
        failure.

        2) If that line was found, do actual counting.

        """
        def fix_date(dmy):
            """Transform DMY in d.m.yyyy format into yyyy-mm-dd format."""
            parts = dmy.split(".")
            parts.reverse()
            for i in range(1,3):
                parts[i] = f"{int(parts[i]):02d}"
            return "-".join(parts)

        def user_from_filename(logfile):
            """Dig the user name from logfile pathname:"""
            last_slash_pos = logfile.rindex("/")
            second_to_last = logfile.rindex("/", 0, last_slash_pos-1)
            user = logfile[second_to_last+1 : last_slash_pos]
            (users_re, want_if_match) = self.get_regexp_from_opts("users")
            if is_wanted(user, users_re, want_if_match):
                return user

        def loading_succesfull(logfile, total_re, ts1_re, ts2_re):
            """Tell if LOGFILE contains data for succesfull loading.

            Judgement is based on TOTAL_RE and TS_RE (must be found in the
            file).  Return value is the timestamp matching TS_RE (or None).

            """
            ymd = "????-??-??"
            for line in open(logfile, "r").read().splitlines():
                if total_re.match(line):
                    return ymd, True
                m = ts1_re.match(line)
                if m:
                    ymd = fix_date(m.group(1))
                    continue
                m = ts2_re.match(line)
                if m:
                    ymd = m.group(1)
                    continue
            return ymd, False

        #### THE PARSER IS UGLY !!!  ( But so are the log files :-( )

        INFO_re = re.compile(
            r"^INFO ([^:]+): "  # step name
            r"(\d+)"            # the first number (int)
            r"(?: *[:/] *)?"    # maybe separator
            r"([\d.]+)?"        # mayme second number (float)
            r"(?: sek)?"        # another optional group
            r" *"               # maybe trailing space
            r"\Z")              # end of txt
        total_re = re.compile(r"^TITLE Total time: +([/:] )?([\d.]+)( sek)?")
        ts1_re = re.compile(r"^(\d\d?\.\d\d?.\d\d\d\d) (?:\d\d:\d\d)")
        ts2_re = re.compile(r"^(?:Sun|Mon|Tue|Wed|Thu|Fri|Sat)"
                            r" (\d\d\d\d-\d\d-\d\d) (?:\d\d:\d\d:\d\d)")
        stored_re = re.compile(r"^Stored the file (.+) from user (.+) to neo4j$")
        storing_re = re.compile(r"^TITLE Storing data from ")
        WARNING_re = re.compile(r"^WARNING (.+)$")
        batchid_re = re.compile(r"^Batch id: (.+)$")
        loaded_re = re.compile(r"^Loaded the file (.+)$")
        INFOloaded_re = re.compile(r"^INFO Loaded file (.+)$")
        log_re = re.compile(r"^Log file: (.+)$")

        user = user_from_filename(logfile)
        if user is None:
            return
        # print(f"u={user}")

        # some filtering wanted by caller:
        (ymd, load_success) = loading_succesfull(logfile, total_re, ts1_re, ts2_re)
        if not load_success:
            step = "Failed"
            if is_wanted(step, self._want_step_re, self._want_step_if_match):
                print(f"** ==> Failed {logfile}")
                yield ymd, step, user, [(logfile, "1")]
                return

        for line in open(logfile, "r").read().splitlines():

            # This is the most intresting kind of line
            m = INFO_re.match(line)
            if m:
                if user is None:
                    flash(f"logfile {logfile} no user found before INFO line")
                    return
                (step, count, time) = m.groups()
                if count == "0":
                    continue
                if not is_wanted(step, self._want_step_re, self._want_step_if_match):
                    continue

                step = step.split(" ")[0]
                if ymd is None or step is None or user is None:
                    print(f"{logfile}: ymd='{ymd}', s='{step}' user='{user}'")
                    continue
                tuples = [ ("n", count) ]
                if time is not None:
                    tuples.append( ("t", time ) )
                yield ymd, step, user, tuples
                continue

            m = total_re.match(line)
            if m:               # has Total time
                time = m.group(1)
                if ymd is None or user is None or time is None:
                    print(f"** --> {logfile}: ymd='{ymd}', s='total_time' user='{user}'")
                    continue
                # print(f"t='{time}'")
                step = "Done"
                if not is_wanted(step, self._want_step_re, self._want_step_if_match):
                    continue
                yield ymd, step, user, [ ("t", time ) ]
                continue

            if ts1_re.match(line): continue # already got at start
            if ts2_re.match(line): continue
            if stored_re.match(line): continue
            if storing_re.match(line): continue
            if WARNING_re.match(line): continue
            if batchid_re.match(line): continue
            if loaded_re.match(line): continue
            if INFOloaded_re.match(line): continue
            if log_re.match(line): continue

            if line != "":
                print(f"Unhandled line: {line}")
                continue
