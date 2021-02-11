#   Isotammi Geneological Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
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
VERSION = "0.1"

#sys.path.append("app/bp/gedcom") # otherwise pytest does not work??? 
from models import util

class Output:
    def __init__(self, args):
        self.args = args
        self.in_name = args.input_gedcom
        self.out_name = args.output_gedcom
        self.log = not args.nolog
        self.new_name = None

    def __enter__(self):
        input_encoding = self.args.encoding
        if input_encoding in {"UTF-8","UTF-8-SIG"}:
            self.output_encoding = "UTF-8"
        elif input_encoding == "ISO8859-1":
            self.output_encoding = input_encoding
        else:
            self.output_encoding = input_encoding
        if self.out_name:
            self.f = open(self.out_name, "w", encoding=self.output_encoding)
        else:
            # create tempfile in the same directory so you can rename it later
            self.temp_name = self.in_name + "-temp"
            self.new_name = util.generate_name(self.in_name)
            self.f = open(self.temp_name, "w", encoding=self.output_encoding)
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
        if line.startswith("1 CHAR"): 
            # this is probably unnecessary because the result should always be 
            # the same as in the input file, i.e. the line is not modified
            if self.output_encoding == "UTF-8":
                line = "1 CHAR UTF-8"
            elif self.output_encoding == "ISO8859-1":
                line = "1 CHAR ANSI"
            else:
                line = "1 CHAR {}".format(self.output_encoding)
        self.f.write(line+"\n")

        if self.log:
            #TODO: Should follow a setting from gedder.py
            self.log = False
            args = sys.argv[1:]
            try:
                v = " v." + VERSION
            except NameError:
                v = ""
            self.emit("1 NOTE _TRANSFORM{} {}".format(v, self.transform_name))
            self.emit("2 CONT args:")
            for name,value in vars(self.args).items():
                self.emit("1 CONT - {}={}".format(name,value))
            self.emit("2 CONT _COMMAND {} {}".\
                      format(os.path.basename(sys.argv[0]), " ".join(args)))
            user = getpass.getuser()
            if not user:
                user = "Unnamed"
            datestring = util.format_timestamp()
            self.emit("2 CONT _USER {}".format(user))
            self.emit("2 CONT _DATE {}".format(datestring))
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

