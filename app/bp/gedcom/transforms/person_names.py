'''
    Nimimuotojen normalisointi (Kehityksen alla!)

    Processes gedcom Items trying to fix problems of individual name tags

    The input flow of Item objects have the following process:
      1. When an INDI line is found, a new GedcomRecord is created
        - The following lines associated to this person are stored in a list in the GedcomRecord:
          - When a "1 NAME" line is found, a new PersonName object is created and the following
            lines associated to this name are stored as a list in the PersonName
          - When all lines of current INDI record (0 INDI and all lower level rows)
            the transformed lines are written to output using GedcomRecord.emit() method.
      2. The other input records (HEAD, FAM etc.) are written out immediately line by line

Created on 26.11.2016 – 2.6.2019

    Converted from bp.gedcom.transforms.names

@author: JMä
'''
#     Input example (originally no indent):
#         0 @I0149@ INDI
#           1 NAME Johan Johanpoika /Sihvola/
#             2 TYPE aka
#             2 GIVN Johan Johanpoika
#             2 SURN Sihvola
#           1 NAME Johan /Johansson/
#             2 GIVN Johan
#             2 SURN Johansson
#             2 SOUR @S0015@
#               3 PAGE Aukeama 451, Kuva 289 Sihvola
#               3 DATA
#                 4 DATE 28 JAN 2015
#             3 NOTE @N0175@
#           1 SEX M
#             ...
import logging 
from ..transforms.model import surnameparser
logger = logging.getLogger('stkserver')

#from ..transforms.model.gedcom_line import GedcomLine
#from ..transforms.model.gedcom_record import GedcomRecord
from ..transforms.model.person_name_v2 import PersonName

from .. import transformer
from ..transformer import Item 
from flask_babelex import _

version = "0.3kku"
doclink = "http://taapeli.referata.com/wiki/Gedcom-Names-ohjelma"
name = _("Personal names") + ' ' + version

# Active Indi logical record GedcomRecord
indi_record = None
# state 0 = started, 1 = indi processing, 2 = name processing, 3 = birth processing
state = 0

def initialize(_args):
    return PersonNames()

def add_args(parser):
    parser.add_argument('--missing_name_part', action='store_true',
                        help=_('Mark missing name parts as "N"'))
#     parser.add_argument('--child_as_firstname', action='store_true',
#                         help=_('Handle "child" expressions'))
    parser.add_argument('--patronyme_in_given_name', action='store_true',
                        help=_('Recognize_patronymes'))
    parser.add_argument('--call_names', action='store_true',
                        help=_('Call names and aliases'))
    parser.add_argument('--create_surname_history', action='store_true',
                        help=_('Create surname history from multiple names'))
    parser.add_argument('--aliases', action='store_true',
                        help=_("Process_nonstd_ALIA_lines"))


class PersonNames(transformer.Transformation):

    def transform(self, item, _options, _phase):
        """
        Performs a transformation for the given Gedcom "item" (i.e. "line block")
        Returns one of
        - True: keep this item without changes
        - None: remove the item
        - item: use this item as a replacement (can be the same object as input if the contents have been changed)
        - list of items ([item1,item2,...]): replace the original item with these
        
        This is called for every line in the Gedcom so that the "innermost" items are processed first.
        
        Note: If you change the item in this function but still return True, then the changes
        are applied to the Gedcom but they are not displayed with the --display-changes option.
        """
        #print(f"#Item {item.linenum}: {item.list()}<br>")
        if item.path.find('.INDI') < 0:
            return True

        if item.tag == "NAME":
            pn = PersonName(item)
            n,surnames = pn.process_NAME(False)
            newitems = []
            first = True
            for pn in sorted(surnames,key=self.surname_sortkey):
                #logger.debug('#' + str(pn)) # Merge original and new rows
                #print(f"{n.givn}/{nm}/{n.nsfx}")
                if pn.prefix:
                    surname = f"{pn.prefix} {pn.surn}"
                else:
                    surname = pn.surn
                item = Item(f"{item.level} NAME {n.givn}/{surname}/{n.nsfx}")
                if pn.name_type:
                    typename = surnameparser.TYPE_NAMES.get(pn.name_type,"unknown")
                    typeitem = Item(f"{item.level+1} TYPE {typename}")
                    item.children.append(typeitem)
                newitems.append(item)
                if first:
                    if n.call_name:
                        item2 = Item(f"{item.level+1} CALL {n.call_name}")
                        item.children.append(item2)
                    if n.nick_name:
                        item2 = Item(f"{item.level+1} NICK {n.nick_name}")
                        item.children.append(item2)
                first = False
            return newitems

        return True
    
        # ---- TEKEMÄTTÄ: ----
        #2. If there is SURN.NOTE etc without any name, move their Notes and  
        #   Sources to NAME level
        if item.tag in ["NPFX", "GIVN", "NICK", "SPFX", "SURN", "NSFX"] \
           and item.value == "" \
           and item.children:
            print(f"##   {item} – TODO move child nodes with children to self<br>")
            logger.debug(f"##Item {item.linenum}: {item.list()}")
            new_items = []
            for c in item.children:
                it = Item(c.line, c.children, c.linenum)
                it.level += -1
                new_items.append(it)
            return new_items

        return True # no change

    def surname_sortkey(self,surnameinfo):
        # Sort birth names first
        if surnameinfo.name_type == surnameparser.Name_types.BIRTH_NAME: return 0
        if surnameinfo.name_type is None: return 1
        return 2



