#
# Class for reading stk server logs
#

import re
import os

from flask import flash

################################################################
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
arrow_re = re.compile(r"^-> ([^ ]+)")



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

def make_filler(totlen, flen):
    return(" "*(totlen % flen)
           + (" "*(flen-1) + ".") * (totlen // flen))


################################################################
#
class Log():
    """Class to handle stk log file(s)."""

    def __init__(self, opts={}):
        self._opts = opts
        self._by_msg = dict()
        self._by_ymd = dict()
        self._files = []        # lis of files already processed


    ################
    #
    def work_with(self, file: str) -> None:
        """Read stkserver log FILE.  Collect counts of messages."""

        """
Toistaiseksi olisi 2 mittaria: modulin nimi=käydyt sivut ja n=käsitellyt
rivit tms.  Raportointia voisi rakentaa käyttäjien käyntimääristä
kuukausittain (käyttäjittäin monenako päivänä, montako eri käyttäjää) ja
suosituimmat sivut ja niiden datavolyymit.

Kuukausittaiset määrät tulee helposti siitä, kun lokit on kuukauden lokeja.

        """

        def update_counters(self, msg, user, ymd):
            """Update counters for MSG, USER"""

            def update_one(outer, k):
                if k not in outer:
                    outer[k] = dict()
                inner = outer[k]
                if user in inner:  inner[user] += 1
                else:              inner[user] = 1
                return

            update_one(self._by_msg, msg)
            update_one(self._by_ymd, ymd)
            return

        if file in self._files:
            flash(f"Already done file {file}") # this should not happen
            return
        self._files.append(file)  # protect against double processing

        users_re = None
        if "users" in self._opts:
            try:
                users_re = re.compile(re.sub(",", "|", self._opts["users"]))
            except Exception as e:
                flash(f"Bad regexp '{self._opts['users']}': {e}", category='warning')

        for line in open(file, "r").read().splitlines():
            match = log_re.match(line)
            if not match:
                flash(f"strange log line {line}") # this should not happen
                continue
            (ymd, hms, logger, level, user, message) = match.groups()
            if level != 'INFO':
                continue

            match = arrow_re.match(message)
            if not match:
                continue
            module = match.group(1)

            if users_re and not users_re.match(user):
                continue

            update_counters(self, module, user, ymd)
        return


    ################
    #
    def get_by_msg_dict(self):
        """Get the counts of messages, maybe per user.  As python (nested) dict."""
        return self._by_msg

    ################
    #
    def get_by_msg_text(self):
        """Get the counts of messages, maybe per user.  As list of text lines."""

        # make the total counts
        for x in self._by_msg.values():
            sum = 0
            for count in x.values():
                sum += count
            x["TOTAL"] = sum

        if "bycount" in self._opts:
            countx = sorted(self._by_msg.items(),
                             key=lambda item: item[1]["TOTAL"],
                             reverse=True)
        else:
            countx = sorted(self._by_msg.items())

        if "topn" in self._opts:
            countx = countx[:self._opts["topn"]]

        n = 0
        longest_user = find_longest(countx, "user")
        longest_message = find_longest(countx, "msg")
        destcol = self._opts["width"] - longest_user - 6  # room for count + some space
        if destcol > longest_message +8:
            destcol = longest_message +8
        if destcol < 10:
            destcol = 10
        # print(f"u={longest_user} m={longest_message} d={destcol}")
        result = []
        for message, ulist in countx:
            n += 1
            before = f"{n:2d} " if "topn" in self._opts else ""

            # Truncate too long messages
            if len(message) > destcol - 3 -len(before):
                message = message[:destcol-3-len(before)] + "·"*3

            # Print the message, without newline
            part1 = f"{before}{message}"

            # use filler to make report look nicer
            filler = make_filler(destcol - len(message) - len(before), 3)

            # print the filler and count stuff
            if "users" not in self._opts:   #  show not users' counts?
                result.append(f"{part1} {filler}  {ulist['TOTAL']:4d}")
                continue

            # lines after first line are filled with spaces up to destcol
            for user, count in sorted(ulist.items()):
                if user == "TOTAL": continue
                result.append(f"{part1} {filler} {user:{longest_user}s} {count:4d}")
                part1 = ""
                filler = " " * destcol

        return(result)
