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

from . import transformer

def initialize(options):
    return InfoParser()

class Info: 
    gedcom_version = None
    submitter = None
    charset = ""
    date = ""
    time = ""
    source_program = None
    source_program_version = None 
    source_program_name = None 
    num_individuals = 0
    num_families = 0
    num_places = 0
    num_notes = 0
    num_sources = 0
    num_citations = 0
    num_repos = 0
    num_multimedia = 0
        
class InfoParser(transformer.Transformation):
    def __init__(self):
        self.info = Info()
        self.places = set()
        self.submitter_xref = None
        
    def transform(self,item,options,phase):
        #print(item.path,item.value)
        if item.level == 0:
            if item.tag == "INDI":
                self.info.num_individuals += 1
            if item.tag == "FAM":
                self.info.num_families += 1
            if item.tag == "NOTE":
                self.info.num_notes += 1
            if item.tag == "SOUR":
                self.info.num_sources += 1
            if item.tag == "REPO":
                self.info.num_repos += 1
            if item.tag == "OBJE":
                self.info.num_multimedia += 1
            return None
        xref = None
        if item.path[0] == '@': xref = item.path.split(".")[0]
        if item.tag == "NOTE":
            self.info.num_notes += 1
        if item.tag == "SOUR" and item.path != "HEAD.SOUR":
            self.info.num_citations += 1
        if item.tag == "PLAC":
            self.places.add(item.value)
            self.info.num_places = len(self.places)
        if item.tag == "OBJE" and item.value == "":
            self.info.num_multimedia += 1
        if item.path == "HEAD.SUBM":
            self.submitter_xref = item.value
        if item.path == "HEAD.CHAR":
            self.info.charset = item.value
        if item.path == "HEAD.DATE":
            self.info.date = item.value
        if item.path == "HEAD.DATE.TIME":
            self.info.time = item.value
        if item.path == "HEAD.GEDC.VERS":
            self.info.gedcom_version = item.value
        if item.path == "HEAD.SOUR":
            self.info.source_program = item.value
        if item.path == "HEAD.SOUR.VERS":
            self.info.source_program_version = item.value
        if item.path == "HEAD.SOUR.NAME":
            self.info.source_program_name = item.value
        if item.path.endswith(".SUBM.NAME") and xref == self.submitter_xref: 
            self.info.submitter = item.value
            
        return None

