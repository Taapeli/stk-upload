'''
    Nimimuotojen normalisointi (Älä käytä vielä!)

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
logger = logging.getLogger('stkserver')

from ..transforms.model.gedcom_line import GedcomLine
from ..transforms.model.gedcom_record import GedcomRecord
from ..transforms.model.person_name import PersonName

from .. import transformer
from ..transformer import Item
from flask_babelex import _

version = "0.2"
doclink = "http://taapeli.referata.com/wiki/Gedcom-Names-ohjelma"
name = _("Personal names") + " (kesken)"

# Active Indi logical record GedcomRecord
indi_record = None
# state 0 = started, 1 = indi processing, 2 = name processing, 3 = birth processing
state = 0

def initialize(args):
    return PersonNames()

def add_args(parser):
    pass

class PersonNames(transformer.Transformation):

    def transform(self, item, options, phase):
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
        print(f"#Item {item.linenum}: {item} ({len(item.children)} included)")
        if item.path.find('.INDI') < 0:
            return True

        if item.tag == "NAME":
            print(f"## Name {item.value} conversion")
            logger.debug(f"##Item {item.linenum}: {item}")
            n = PersonName(item)
            n.process_name_item(False)
            return n

        if False:   #options.remove_multiple_blanks: # 2.2.3
            if item.tag in ('NAME','PLAC'):
                newtext = "kukkuu"      # remove_multiple_blanks(item.value)
                if newtext != item.value:
                    item.value = newtext
                    return item
    
        if True:        #options.note_to_page:  
            # 1 BIRT
            # 2 DATE 24 APR 1766
            # 2 NOTE Födde 1766 Aprill 24
            # 2 SOUR Kustavi syntyneet 1764-1792 (I C:2)
            # 2 PLAC Kustavi
            # ->
            # 1 BIRT
            # 2 DATE 24 APR 1766
            # 2 SOUR Kustavi syntyneet 1764-1792 (I C:2)
            # 3 PAGE Födde 1766 Aprill 24
            # 2 PLAC Kustavi 
            if item.tag in {"EVEN","BIRT","DEAT","CHR"}:
                note_index = -1
                for i,c in enumerate(item.children):
                    if c.tag == "NOTE" and len(c.children) == 0 and not c.value.startswith("@"): 
                        note_index = i
                    if c.tag == "SOUR" and note_index >= 0:
                        for c2 in c.children:
                            if c2.tag == "PAGE": # PAGE already exists, ignore
                                return True
                        note = item.children[note_index].value
                        del item.children[note_index]
                        newitem = Item("{} PAGE {}".format(item.level+2,note))
                        c.children.append(newitem)
                        return item 
                return True


        return True # no change

