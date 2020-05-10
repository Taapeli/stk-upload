#
# Class for reading stk server logs
#

import re
import os

version = "0.1"
timestamp = r'Time-stamp: <10.05.2020 15:38:11 juha@rauta>'

################################################################
#
# '%(asctime)s %(name)s %(levelname)s %(user)s %(message)s'
#
ymd_re = r'\d\d\d\d-\d\d-\d\d'
hms_re = r'\d\d:\d\d:\d\d,\d\d\d'

log_re = re.compile(f'({ymd_re}) ({hms_re})'
                    f' (\S+) (\S+) (\S+) (.*)')


helptext = """
#  To make use of groupings:
#  1) Have groups.py in current (or some other) directory
#  2) set PYTHONPATH=<that other directory> (. not needed)
#  I will continue without...
"""

################################################################
#
def error(msg: str) -> None:
    print(f"*** {msg}")

# def debug_print(level: int, msg: str) -> None:
#     if opts.debug >= level:
#         prefix = "#" * level
#         print(f"{prefix} {msg}")


################################################################
#
class Log():
    """Class to handle stk log file(s).

Methods:
    - work_with(file) - collect log entries from FILE
    - print_counts() - print the counts
    - print_group() - print potential groups

"""
    # _messages = dict()          # key is message, value is count
    # _counts = dict()            # key is message, value is User
    # _opts = ()
    # _files = []
    # _result = []

    def __init__(self, opts={}):
        self._messages = dict()
        self._counts = dict()
        self._opts = opts
        self._files = []
        self._result = []
        try:
            from . import groups
            self._groups = groups.groups
            self._excludes = groups.excludes
        except (ModuleNotFoundError, ImportError):
            self._result.append(helptext)
            self._groups = []
            self._excludes = []

    def result(self):
        return(self._result)

    ################
    #
    def work_with(self, file: str) -> None:
        """Read stkserver log FILE.

Collect counts or potential groups of messages.
        """
        def read_lines(file):
            f = open(file, "r")
            return f.read().splitlines()

        ####
        #
        def collect_counts(self, message, user) -> None:
            """Count occurences of MESSAGE (or group) per USER."""
            # exclude this message?
            for x in self._excludes:
                # (part of) excluded message match current message?
                if x in message:
                    return

            # Grouping this message?
            # this will replace the full message string with the group string
            for gr in self._groups:
                if gr in message:
                    message = gr
                    break

            # ready to update counter
            # new message?
            if message not in self._counts:
                self._counts[message] = dict()

            m = self._counts[message]
            if user in m:
                m[user] += 1
            else:
                m[user] = 1
            return  # from collect_counts()

        ####
        #
        def collect_messages(self, message):
            """Count the occurences of MESSAGE.

Used to help group similar messages together for actual counting.
            """
            if message in self._messages:
                self._messages[message] += 1
            else:
                self._messages[message] = 1
            return  # from collect_messages()

        ####
        #
        def clean_message(message):
            """Tidy the MESSAGE."""
            message = re.sub("^-> ", "", message)
            message = re.sub("(user [^/]+)/[^,]+", "\\1", message)
            return message

        ################ work_with() starts here
        self._files.append(file)
        if "user" in self._opts:
            users = self._opts["user"].split(",")

        # debug_print(2, f"working with {file}")
        for line in read_lines(file):
            match = log_re.match(line)
            if not match:
                error(f"strange line {line}", end='') # this should not happen
                continue
            (ymd, hms, logger, level, user, message) = match.groups()
            # debug_print(4, f"{ymd} {hms} '{logger}' {level} {user} '{message}'")
            if level != 'INFO':
                continue
            if "user" in self._opts and self._opts["user"] not in users:
                continue
            message = clean_message(message)
            if not message: continue
            if "group_level" in self._opts:
                collect_messages(self, message)
            else:
                collect_counts(self, message, user)
        return


    ################
    #
    def print_counts(self):
        """Print observed messages, users and counts"""
        def sum_of(x):
            """Sum of status values' counts"""
            sum = 0
            for count in x.values():
                sum += count
            return sum

        def make_filler(totlen, flen):
            return(" "*(totlen % flen)
                   + (" "*(flen-1) + ".") * (totlen // flen))

        def find_longest_user(counts):
            longest = 0
            if "verbose" in self._opts:
                for message, ulist in counts:
                    for user in ulist:
                        if len(user) > longest:
                            longest = len(user)
            return longest

        ################ start print_counts()
        if "topn" in self._opts:
            # sort by count and keep top N
            countsx = sorted(self._counts.items(),
                             key=lambda k: sum_of(k[1]),
                             reverse=True)
            countsx = countsx[:self._opts["topn"]]
        else:
            # sort alphabetically
            countsx = sorted(self._counts.items())

        n = 0
        longest = find_longest_user(countsx)
        destcol = self._opts["width"] - longest - 6  # room for count + some space
        for message, ulist in countsx:
            n += 1
            before = f"{n:2d} " if "topn" in self._opts else ""
            after = " Group" if (message in self._groups) else ""

            # Truncate too long messages
            if len(message) > destcol - 3 -len(before):
                message = message[:destcol-3-len(before)] + "·"*3

            # Print the message, without newline
            part1 = f"{before}{message}"

            # use filler to make report look nicer
            filler = make_filler(destcol - len(message) - len(before), 3)

            # print the filler and count stuff
            if "verbose" not in self._opts:   #  show individual users' counts?
                self._result.append(f"{part1} {filler}  {sum_of(ulist):4d}{after}")
                continue

            # lines after first line are filled with spaces up to destcol
            for user, count in sorted(ulist.items()):
                self._result.append(f"{part1} {filler} {user:{longest}s} {count:4d}{after}")
                part1 = ""
                filler = " " * destcol

        return  #### from print_counts()

    ################
    #
    def print_groups(self):
        """Print gouped messages."""

        def in_old(message, groups, where):
            """Check if MESSAGE is in GROUPS (and say WHERE if is)."""
            for m in groups:
                if m in message:
                    if "verbose" in self._opts or "debug" in self._opts:
                        self._result.append( f'#    "{message}" in {where} as "{m}"\n')
                    return True
            return False

        def print_one_group(pre, group):
            self._result.append("\n# Old groups\n")
            for m in sorted(group):
                m.replace("\\", "\\\\")
                self._result.append(f'    "{m}",\n')
            self._result.append("]\n")

        #### start print_groups()

        # Build filtered (count > 1) and sorted (by count) list of messages
        smessages = []
        for k,v in self._messages.items():
            if v > 1:
                smessages.append(k)
        # keep top N if so requested ...
        if "topn" in self._opts:
            smessages = [k for k in sorted(smessages,
                                          key=lambda x: self._messages[x],
                                          reverse=True)]
        # ... or sort by alpha
        else:
            smessages = sorted(smessages)

        newgroups = []
        topn = f" (max {self._opts['topn']})" if "topn" in self._opts else ""
        self._result.append(f"# New groups{topn}"
                            f", up to level {self._opts['group_level']}\n")

        group_level_delims = ":,"
        self._result.append("groups = [\n")
        n = 0
        for m in smessages:
            count = self._messages[m]

            # Handle the group length:
            # find the group delimiter positions ...
            positions = [pos for pos,char in enumerate(m) if char in group_level_delims]
            # debug_print(1, f"{count:3d} {positions} {m}")
            # ... and splice to desired length
            if len(positions) >= self._opts["group_level"]:
                m = m[:positions[self._opts["group_level"]-1]+1]

            # we already have this?
            if m in newgroups:
                continue
            # this is in the old groups?
            if in_old(m, self._groups, "old groups"):
                continue
            # this is (old) excluded?
            if in_old(m, self._excludes, "excludes"):
                continue

            # remember this
            newgroups.append(m)
            m.replace("\\", "\\\\")
            self._result.append(f'    "{m}",  # {count}\n')

            # are we done?
            n += 1
            if "topn" in self._opts and n >= self._opts["topn"]:
                break

        # For convinience, add the old groups and excludes in the report, so
        # that this report can be used as new group definition
        self._result.append_one_group("\n# Old groups\n", self._groups)
        self._result.append_one_group("# Old exludes\nexcludes = [", self._excludes)

        return  #### from print_groups()

# Local variables:
# time-stamp-line-limit: 60
# End:
