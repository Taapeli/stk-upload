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

class Output:
    def __init__(self, run_args):
        self.run_args = run_args
        if 'nolog' in self.run_args and run_args['nolog']: 
            self.log = False
        else:
            self.log = True
        if 'display_changes' in self.run_args: 
            self.display_changes = run_args['display_changes']
        else:
            self.display_changes = False
        if 'encoding' in self.run_args:
            self.encoding = self.run_args['encoding']
        else:
            self.encoding = 'UTF-8'
        if 'input_gedcom' in self.run_args:
            self.in_name = self.run_args['input_gedcom']
        else:
            self.in_name = None
        if 'output_gedcom' in self.run_args:
            self.out_name = self.run_args['output_gedcom']
        else:
            self.out_name = None
        self.new_name = None

    def __enter__(self):
        if self.out_name:
            self.f = open(self.out_name, "w", encoding=self.encoding)
        else:
            # create tempfile in the same directory so you can rename it later
            tempfile.tempdir = os.path.dirname(self.in_name) 
            self.temp_name = tempfile.mktemp()
            self.new_name = self.generate_name(self.in_name)
            self.f = open(self.temp_name, "w", encoding=self.encoding)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.f.close()
        if 'dryrun' in self.run_args and self.run_args['dryrun']:
            os.remove(self.temp_name) 
            return
        self.save()

    def emit(self, line):
        ''' Process an input line '''
        #if self.display_changes and self.original_line and \
        if self.display_changes:
            if self.original_line == "" and self.saved_line != "":
                print('{:>36} --> {}'.format(self.saved_line, self.saved_line))
                print('{:>36} --> {}'.format(self.original_line, line))
                self.saved_line = ""
            elif line.strip() != self.original_line:
                print('{:>36} --> {}'.format(self.original_line, line))
            else:
                self.saved_line = self.original_line
            self.original_line = ""
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
            datestring = time.strftime("%d %b %Y %H:%M:%S", 
                                       time.localtime(time.time()))
            self.emit("2 CONT _DATE {} {}".format(user, datestring))
            if self.new_name:
                self.emit("2 CONT _SAVEDFILE " + self.new_name)

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

    def generate_name(self,name):
        i = 0
        while True:
            newname = "{}.{}".format(name,i)
            if not os.path.exists(newname): 
                return newname
            i += 1


