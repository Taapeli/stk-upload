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

version = "0.4kku"
doclink = "http://wiki.isotammi.net/wiki/Gedcom:Gedcom-Names-ohjelma"
name = _("Personal names") + ' ' + version

# Active Indi logical record GedcomRecord
indi_record = None
# state 0 = started, 1 = indi processing, 2 = name processing, 3 = birth processing
state = 0

NO_CHANGE = True
DELETE = None

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


def normalize(namestring):
    return namestring.replace(" /","/").replace("/ ","/")

<<<<<<< Upstream, based on branch 'master' of https://github.com/Taapeli/stk-upload.git
NO_CHANGE = True
DELETE = None
=======
def capitalize(name):
    return " ".join(n.capitalize() for n in name.split())
>>>>>>> 6da04f3 Person names transformation v0.4

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
        if item.tag != "INDI": return NO_CHANGE
        subitems = []
        changed = False
        name_changed = False
        saved_givn = None
        saved_nsfx = None
        for subitem in item.children:
            if subitem.tag != "NAME": 
                subitems.append(subitem)
                continue
            pn = PersonName()
            orig_name = subitem.value
            parseresult = pn.process_NAME(subitem.value)
            if parseresult is None: return True
            n = parseresult.name_parts
            print(n.givn,saved_givn)
            if n.givn and saved_givn is None:
                saved_givn = n.givn
            if n.givn == "" and saved_givn is not None:
                n.givn = saved_givn 
            first = True
            if len(parseresult.surnames) > 1: changed = True
            for pn in sorted(parseresult.surnames,key=self.surname_sortkey):
<<<<<<< Upstream, based on branch 'master' of https://github.com/Taapeli/stk-upload.git
                if pn.prefix:
                    #surname = f"{pn.prefix} {pn.surn}"
                    surname = pn.surn
                else:
                    surname = pn.surn
                namestring = f"{n.givn}/{surname}/{n.nsfx}"
                if normalize(namestring) != normalize(subitem.value): 
                    name_changed = True
=======
                surname = capitalize(pn.surn)
                namestring = f"{capitalize(n.givn)}/{surname}/{n.nsfx}"
                if normalize(namestring) != normalize(subitem.value): 
                    name_changed = True
                    changed = True
>>>>>>> 6da04f3 Person names transformation v0.4
                    item2 = Item(f"{subitem.level+1} NOTE _orig_NAME {orig_name}")
                    #subitem.children.append(item2)
                newitem = Item(f"{subitem.level} NAME {namestring}")
                newitem.children = subitem.children
                subitem.children = []
                if pn.name_type:
                    typename = surnameparser.TYPE_NAMES.get(pn.name_type,"unknown")
                    typeitem = Item(f"{subitem.level+1} TYPE {typename}")
                    newitem.children.append(typeitem)
                    changed = True
                if first:
                    if n.call_name:
<<<<<<< Upstream, based on branch 'master' of https://github.com/Taapeli/stk-upload.git
                        item2 = Item(f"{subitem.level+1} CALL {n.call_name}")
=======
                        item2 = Item(f"{subitem.level+1} NOTE _CALL {n.call_name}")
>>>>>>> 6da04f3 Person names transformation v0.4
                        newitem.children.append(item2)
                        changed = True
                    if n.nick_name:
                        item2 = Item(f"{subitem.level+1} NICK {n.nick_name}")
                        newitem.children.append(item2)
                        changed = True
                    if n.nsfx:
                        item2 = Item(f"{subitem.level+1} NSFX {n.nsfx}")
                        newitem.children.append(item2)
                        changed = True
                if pn.prefix:
                    item2 = Item(f"{subitem.level+1} SPFX {pn.prefix}")
                    newitem.children.append(item2)
                    changed = True
                subitems.append(newitem)
                first = False
        if name_changed:
            item2 = Item(f"{subitem.level+1} NOTE _orig_NAME {orig_name}")
            subitems[0].children.insert(0,item2)
        if changed:
            item.children = subitems 
            return item

        return NO_CHANGE

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



