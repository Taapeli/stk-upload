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
Created on 16.1.2017

@author: jm
'''
import logging
from fileinput import lineno
LOG = logging.getLogger(__name__)


class GedcomLine(object):
    '''
    Gedcom line container, which can also carry the lower level gedcom lines.
    
    Example
    - level     2
    - tag       'GIVN'
    - value     'Johan' ...}
    '''
    # Current path elemements
    # See https://docs.python.org/3/faq/programming.html#how-do-i-create-static-class-data-and-static-class-methods
    path_elem = []

    def __init__(self, line, linenum=0):
        '''
        Constructor: Parses and stores a gedcom line
        
        Different constructors:
            GedcomLine("1 GIVN Ville")
            GedcomLine("1 GIVN Ville", 20)
            GedcomLine((1, "GIVN", "Ville"))
            GedcomLine((1, "GIVN", "Ville"), 20)
        '''
        self.path = ""
        self.attributes = {}
        self.linenum = linenum

        if type(line) == str:
            # Parse line
            tkns = line.split(None,2)
            self.line = line
        else:
            tkns = tuple(line)
        try:
            self.level = int(tkns[0])
        except ValueError as e:
            msg = "{} Rivi {} '{}' ei ala kunnon tasonumerolla".\
                        format(self.path, self.linenum, line)
            LOG.error("{}{}".format(self.path, msg))
            self.level = 0
            self.tag = "NOTE"
            self.value = "VIRHE: " + msg
            return
            
        self.tag = tkns[1]
        if len(tkns) > 2:
            if type(line) == str:
                i = line.find(" %s " % self.tag)
                self.value = line[i+len(self.tag)+2:] # preserve leading blanks
            else:
                self.value = tkns[2] 
        else:
            self.value = ""
            self.line = str(self)
        self.set_path(self.level, self.tag)
            

    def __str__(self):
        ''' Get the original line '''
        try:
            ret = "{} {} {}".format(self.level, self.tag, self.value).rstrip()
        except:
            ret = "* Not complete *"
        return ret
    

    def set_path(self, level, tag):
        ''' Update self.path with given tag and level '''
        if level > len(GedcomLine.path_elem):
            raise RuntimeError("{} Invalid level {}: {}".format(self.path, level, self.line))
        if level == len(GedcomLine.path_elem):
            GedcomLine.path_elem.append(tag)
        else:
            GedcomLine.path_elem[level] = tag
            GedcomLine.path_elem = GedcomLine.path_elem[:self.level+1]
        self.path = ".".join(GedcomLine.path_elem)
        return self.path


    def set_attr(self, key, value):
        ''' Optional attributes like name TYPE as a tuple {'TYPE':'marriage'} '''
        self.attributes[key] = value

    
    def get_attr(self, key):
        ''' Get optional attribute value '''
        if key in self.attributes:
            return self.attributes[key]
        return None

    
    def get_year(self):
        '''If value has a four digit last part, the numeric value of it is returned
        '''
        p = self.value.split()
        try:
            if len(p) > 0 and len(p[-1]) == 4:
                return int(p[-1])
        except:
            return None


    def emit(self, f):
        # Print out current line to file f
        f.emit(str(self))

