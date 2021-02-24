#   Isotammi Genealogical Service for combining multiple researchers' results.
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
import datetime
LOG = logging.getLogger(__name__)

from models import util
from .gedcom_line import GedcomLine
from .person_name_v1 import PersonName_v1


class GedcomRecord(GedcomLine):
    '''
    Stores a Gedcom logical record, which includes level 0 record (0 INDI) 
    with all it's lines (with level > 0)

    Methods:
    __init__(...)    An object instance is created using the level 0 line
    add(...)         Other, higher level rows are added
    get_lines()      Returns an iterable containing the lines
    
    The fixes are done mostly from '1 NAME givn/surn/nsfx' row.
    If NAME has significant changes, the original value is also written to 'NOTE orig_'
    
    '''
    def __init__(self, gedline):
        ''' Creates a new instance of gedcom logical record
            which includes a group of gredcom lines starting with a level0 record.
        '''
        self.rows = []
        # optional attributes {'BIRT':1820}
        self.attributes = {}
        # Latest PersonName_v1 index in self.rows
        self.current_index = -1
        # The name found first, userd for default GIVN, _CALL, NICK
        self.name_default = None
        # Store level 0 line
        if not type(gedline) is GedcomLine:
            raise RuntimeError("GedcomLine argument expected")
        self.level = gedline.level
        self.path = gedline.path
        self.value = gedline.value
        self.add_member(gedline)

    
    def __str__(self):
        return "GedcomRecord {} {} ({} riviä)".format(self.path, self.value, len(self.rows))


    def add_member(self, gedline):
        ''' Adds a gedcom line to record set.
            "2 NAME" line is added as a PersonName_v1 object, others as GedcomLine objects
        '''
        if type(gedline) is PersonName_v1:
            # gedline is "1 NAME ...". The first one is the preferred name
            gedline.is_preferred_name = (self.current_index < 0)
#             print("#record row({}) <= {} (name {!r})".format(len(self.rows), gedline.path, gedline.name), file=stderr)
            self.current_index = len(self.rows)
            self.rows.append(gedline)
            if gedline.tag == 'NAME' and self.name_default == None:
                # Save the first NAME occurrence
                self.name_default = self.get_nameobject()
        else:
#             print("#record row({}) <= {} ({!r})".format(len(self.rows), gedline.path, gedline.value), file=stderr)
            self.rows.append(gedline)

 
    def emit(self, f):
        ''' Find the stored data associated to this person and
            writes them as new gedcom lines to file f
        '''
        # Each original NAME row
#         print ("#emit {}:".format(self))
#         i = -1
        for obj in self.rows:
#             i += 1; print ("#{:3}     {}".format(i, obj))
#             j = -1
            if isinstance(obj, PersonName_v1):
                # Each NAME row generated from /surname1, surname2/
                for x in obj.get_person_rows(self.name_default):
#                     j += 1; print ("#{:3}.{:02}  {}".format(i, j, x))
                    f.emit(str(x))
            else:
                # A GedcomLine outside NAME and its descendants
                f.emit(str(obj))


    def store_date(self, year, tag):
        if type(year) == int:
            self.set_attr(tag, year)
        else:
            LOG.warning("{} ERROR: Invalid {} year".format(self.path, tag))


    def get_nameobject(self):
        ''' Returns the latest object of type PersonName_v1 '''
        if self.current_index >= 0:
            return self.rows[self.current_index]


if __name__ == '__main__':
    ''' Test set '''
    from .ged_output import Output

    logging.basicConfig(filename='example.log', level=logging.DEBUG, format='%(levelname)s:%(message)s')
    LOG.info("------ Ajo '%s' alkoi %s", "Testi", util.format_timestamp() + " ------")

    # One person with two NAME lines
    my_record_1 = GedcomRecord(GedcomLine('0 @I1@ INDI'))
    my_name = PersonName_v1(GedcomLine('1 NAME Amalia Saima* (Sanni) Erikint./Raitala os. von Krats/Ericsdr.'))
    my_record_1.add_member(my_name)
    my_name.add_line(GedcomLine(('2','GIVN','Saimi')))
    my_name.add_line(GedcomLine('3 SOUR Äidiltä'))
    my_name.add_line(GedcomLine('2 SURN Raitala'))
    my_name.add_line(GedcomLine('2 NOTE Kummin kaima'))
    my_record_2 = GedcomRecord(GedcomLine('0 @I2@ INDI'))
    my_name = PersonName_v1(GedcomLine('1 NAME vauva//Ericsdr.'))
    my_record_2.add_member(my_name)
    my_record_3 = GedcomRecord(GedcomLine('0 @I3@ INDI'))
    my_name = PersonName_v1(GedcomLine('1 NAME Niilo/Niemelä/Niemeläinen/'))
    my_name.add_line(GedcomLine('2 SOUR Perunkirjoitus'))
    my_record_3.add_member(my_name)
    my_record_4 = GedcomRecord(GedcomLine('0 @I4@ INDI'))
    my_name = PersonName_v1(GedcomLine('1 NAME Janne/Mattila (Matts)/'))
    my_record_4.add_member(my_name)
    my_name = PersonName_v1(GedcomLine('1 NAME /Matiainen/'))
    my_name.add_line(GedcomLine('2 SOUR Kuulopuhe'))
    my_record_4.add_member(my_name)
    my_name = PersonName_v1(GedcomLine('1 NAME Jouto-Janne'))
    my_name.add_line(GedcomLine('2 NOTE _orig_ALIA Jouto-Janne'))
    my_record_4.add_member(my_name)
    run_args = {'nolog': False, 'output_gedcom': '../../out.txt', 'encoding': 'UTF-8', 'dryrun': False}
    with Output(run_args) as f:
        GedcomLine("0 HEAD").emit(f)
        my_record_1.emit(f)
        my_record_2.emit(f)
        my_record_3.emit(f)
        my_record_4.emit(f)
        GedcomLine("0 TRLR").emit(f)

    LOG.info("------ Ajo '%s' päättyi %s", "Testi", util.format_timestamp() + " ------")

