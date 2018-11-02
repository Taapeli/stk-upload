#!/usr/bin/env python3
"""
Sukuohjelmisto 2004 problems
"""
from flask_babelex import _

from .. import transformer
from ..transformer import Item

version = "2.0"
doclink = "http://taapeli.referata.com/wiki/Gedcom-Suku2004-ohjelma"
docline = _('Fixes problems in Sukuohjelmisto 2004 Gedcoms')

def add_args(parser):
    parser.add_argument('--change_unkn_to_even', action='store_true',
                        help=_('Change _UNKN tags to EVENs'))
    parser.add_argument('--change_photo_to_obje', action='store_true',
                        help=_('Change _PHOTO tags to OBJEs'))

def initialize(options):
    return Suku2004()

class Suku2004(transformer.Transformation):
    def transform(self,item,options,phase):
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
        if options.change_unkn_to_even:
            if item.tag == "_UNKN":
                item.tag = "EVEN"
                if len(item.children) == 0: return None  #empty _UNKN tag, remove
                return item
        """
1 _PHOTO
2 OBJE
3 FORM gif
3 FILE KUVAT\Paimio_Rukkijoki.gif
"""

        if options.change_photo_to_obje:
            if item.tag in {"_PHOT","_PHOTO"} and item.level == 1:
                obje = item.children[0]
                item2 = Item("1 OBJE")
                for c in obje.children:
                    c2 = Item("2 {} {}".format(c.tag,c.value))
                    item2.children.append(c2)
                return item2

        return True
