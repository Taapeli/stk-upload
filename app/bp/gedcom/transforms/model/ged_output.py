'''
Generic GEDCOM transformer
Kari Kujansuu, 2016.

'''
import sys
import os
import getpass
import time
import tempfile
import logging
LOG = logging.getLogger(__name__)

sys.path.append("app/bp/gedcom") # otherwise pytest does not work??? 
from models import util

class Output:
    def __init__(self, args):
        self.args = args
        self.in_name = args.input_gedcom
        self.out_name = args.output_gedcom
        self.log = not args.nolog
        self.new_name = None

    def __enter__(self):
        encoding = "UTF-8" # force utf-8 encoding on output
        if self.out_name:
            self.f = open(self.out_name, "w", encoding=encoding)
        else:
            # create tempfile in the same directory so you can rename it later
            #tempfile.tempdir = os.path.dirname(self.in_name) 
            #self.temp_name = tempfile.mktemp()
            self.temp_name = self.in_name + "-temp"
            self.new_name = util.generate_name(self.in_name)
            self.f = open(self.temp_name, "w", encoding=encoding)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.f.close()
        if self.args.dryrun:
            #os.remove(self.temp_name) 
            return
        self.save()

    def emit(self, line):
        ''' Process an input line '''
        #if self.display_changes and self.original_line and \
        if self.args.display_changes and self.original_line is not None:
            if self.original_line == "" and self.saved_line != "":
                print('{:>36} --> {}'.format(self.saved_line, self.saved_line))
                print('{:>36} --> {}'.format(self.original_line, line))
                self.saved_line = ""
            elif line.strip() != self.original_line:
                print('{:>36} --> {}'.format(self.original_line, line))
            else:
                self.saved_line = self.original_line
            self.original_line = ""
        if line.startswith("1 CHAR"): line = "1 CHAR UTF-8" # force utf-8 encoding on output
        self.f.write(line+"\n")

        if self.log:
            #TODO: Should follow a setting from gedder.py
            self.log = False
            args = sys.argv[1:]
            try:
                v = " v." + _VERSION
            except NameError:
                v = ""
            self.emit("1 NOTE _TRANSFORM{} {}".format(v, sys.argv[0]))
            self.emit("2 CONT _COMMAND {} {}".\
                      format(os.path.basename(sys.argv[0]), " ".join(args)))
            user = getpass.getuser()
            if not user:
                user = "Unnamed"
            datestring = util.format_timestamp()
            self.emit("2 CONT _DATE {} {}".format(user, datestring))
            if self.new_name:
                self.emit("2 CONT _SAVEDFILE " + self.new_name)
    write = emit
    
    def save(self):
        if self.out_name:
            msg = "Tulostiedosto '{}'".format(self.out_name)
            print(msg)
            LOG.info(msg)
        else:
            if self.in_name:
                if self.out_name == None:
                    # Only input given
                    os.rename(self.in_name, self.new_name)
                    os.rename(self.temp_name, self.in_name)
                    print("Luettu tiedosto '{}'".format(self.new_name))
                    print("  Uusi tiedosto '{}'".format(self.in_name))
                    LOG.info("Luettu     %s", self.new_name)
                    LOG.info("Tulostettu %s", self.in_name)

