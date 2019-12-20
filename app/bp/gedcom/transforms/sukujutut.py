"""
Sukujutut-muunnos

Kari Kujansuu <kari.kujansuu@gmail.com>

The notation "# 1.1.2" etc. refer to notation in the discussion about this transformation in August 2018. 
The numbering was originally based on Diedrich Hesmer's Gedcom Conversion program.
"""
# import sys
# import os

from .. import transformer
from ..transformer import Item
from flask_babelex import _

name = _("Sukujutut")
version = "1.0"
doclink = "/Sukujutut-muunnos"
docline = _("Sukujutut transformations")

def initialize(_args):
    return Sukujutut()

def allempty(items):
    for item in items:
        if item.tag not in ('CONT','CONC') or item.value.strip() != "": return False
    return True

def remove_multiple_blanks(text):
    return " ".join(text.split())

class Sukujutut(transformer.Transformation):
    def transform(self, item, options, _phase):
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
        if options.remove_invalid_marriage_dates:
            if item.line.strip() == "1 MARR":
                # replace
                #     1 MARR
                #     2 DATE AVOLIITTO
                # with
                #     1 MARR
                #     2 TYPE AVOLIITTO
                if len(item.children) > 0 and item.children[0].line.startswith("2 DATE AVOLIITTO"):
                    item.children[0] = Item("2 TYPE AVOLIITTO")
                    return item
                return True # no change
    
        if options.remove_invalid_divorce_dates:
            if item.line.strip() == "1 DIV":
                # replace
                #     1 DIV
                #     2 DATE .
                # with
                #     1 DIV Y
                if len(item.children) == 1 and item.children[0].line.startswith("2 DATE ."):
                    return Item("1 DIV Y")  # this is not valid GEDCOM but Gramps will fix it
    
        if options.remove_empty_nameparts: # 2.1.3
            if item.line.strip() in {"2 GIVN","2 SURN"}:
                # replace
                #     2 GIVN
                #     3 SOUR xxx
                # with
                #     2 SOUR xxx
                # (same with NOTE instead of SOUR)
                if len(item.children) == 0: return None
                if len(item.children) == 1 and item.children[0].tag in {'SOUR','NOTE'}:
                    sourline = item.children[0].line
                    return Item("2" + sourline[1:])
                return None # empty GIVN/SURN and no subordinate lines => delete
            
        if options.remove_duplicate_sources: # 2.1.3
            if item.line.startswith("1 NAME"):
                prevline = ""
                newchildren = []
                changed = False
                for c in item.children:
                    if c.line.startswith("2 SOUR") and c.line == prevline:
                        changed = True
                    else:
                        newchildren.append(c)
                    prevline = c.line
                item.children = newchildren
                if changed:
                    return item
                else:
                    pass # fall thru
    
        if options.remove_empty_notes: # 2.1.1
            if item.tag == "NOTE" and item.value.strip() == "" and allempty(item.children): return None
    
        if options.remove_empty_dates: # 2.2.4
            if item.tag == "DATE" and item.value.strip() in ('','.','?'): return None
    
        if options.remove_refn: # 2.1.4
            if item.tag == "REFN": return None
    
        if options.remove_stat: # 2.1.5
            if item.tag == "STAT": return None
    
        if options.save_level_3_notes: # 2.1.6
            if item.level == 2 and item.tag == 'PLAC' and len(item.children) == 1 and item.children[0].tag == "NOTE":
                # move NOTE from level 3 to level 2 (including possible CONT/CONC lines)
                # 2 PLAC %1#3 NOTE %2 => 2 PLAC %1#2 NOTE %2
                item2 = Item("2 NOTE %s" % item.children[0].value)
                for c in item.children[0].children:
                    c.level -= 1
                    item2.children.append(c)
                item.children = []
                return [item,item2]
    
        if options.fix_addr: # 5.1.2
            if item.tag == "ADDR" and item.value.strip() != "":
                for c in item.children:
                    if c.tag == "ADR1":
                        return True # no change, ADR1 already exists
                item.children.insert(0,Item("%s ADR1 %s" % (item.level+1,item.value)))
                item.value = ""
                return item
    
        if options.fix_events: # 5.1.4
            if (item.tag == "EVEN" and len(item.children) == 2):
                c1 = item.children[0]
                c2 = item.children[1]
                if c1.tag == "TYPE" and c1.value in ('Ei_julkaista','Kummit','Tutkijan omat') and c2.tag == 'PLAC':
                    c2.tag = "NOTE"
                    if c1.value == "Kummit": c2.value = "Description: " + c2.value
                    return item
    
        if options.fix_events_kaksonen: # 5.1.5
            if (item.tag == "EVEN" and len(item.children) == 1):
                c1 = item.children[0]
                if c1.tag == "TYPE" and c1.value in ('Kaksonen','Kolmonen'):
                    c1.tag = "NOTE"
                    return item
    
        if options.remove_multiple_blanks: # 2.2.3
            if item.tag in ('NAME','PLAC'):
                newtext = remove_multiple_blanks(item.value)
                if newtext != item.value:
                    item.value = newtext
                    return item
    
        if options.emig_to_resi: # 5.1.3
            if item.line.strip() == "1 EMIG":
                item.tag = "RESI"
                return item
    
        if options.note_to_page:  
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

        if options.sour_under_note:  
            if item.tag == "NOTE": # nested NOTEs with SOUR
                # 1 NOTE Kaurissalon Pukkilasta lampuodin tytär. Oli 1754-1755
                # 2 CONC Kalannissa. Vihittäessä 1756 Saara oli piika Kivimaalla.Torpparin
                # 2 CONC vaimo Kustavin Pleikilässä. Leskenä lastensa kanssa vuodesta 1787
                # 2 CONC Pleikilän rantatorpassa, vuodesta 1792 Westan torpassa. Oli siellä
                # 2 CONC vuoteen 1800, rippikirjan mukaan ei enää 1801.
                # 2 NOTE Bleknäs torpare
                # 2 SOUR Kustavi rippikirja 1784-1789 (I Aa:10)
                # ->
                # 1 NOTE Kaurissalon Pukkilasta lampuodin tytär. Oli 1754-1755
                # 2 CONC Kalannissa. Vihittäessä 1756 Saara oli piika Kivimaalla.Torpparin
                # 2 CONC vaimo Kustavin Pleikilässä. Leskenä lastensa kanssa vuodesta 1787
                # 2 CONC Pleikilän rantatorpassa, vuodesta 1792 Westan torpassa. Oli siellä
                # 2 CONC vuoteen 1800, rippikirjan mukaan ei enää 1801.
                # 1 SOUR Kustavi rippikirja 1784-1789 (I Aa:10)
                # 2 PAGE Bleknäs torpare
                note_index = -1
                for i,c in enumerate(item.children):
                    if c.tag == "NOTE" and len(c.children) == 0: 
                        note_index = i
                    if c.tag == "SOUR" and len(c.children) == 0:
                        sour = c.value
                        del item.children[i]
                        newitem = Item("{} SOUR {}".format(item.level,sour))
                        if note_index >= 0: 
                            note = item.children[note_index].value
                            del item.children[note_index]
                            newitem2 = Item("{} PAGE {}".format(item.level+1,note))
                            newitem.children.append(newitem2)
                        return [item,newitem] 
                return True

        return True # no change
    
    

def add_args(parser):
    #parser.add_argument('--concatenate_lines', action='store_true',
    #                    help=_('Combine all CONT and CONC lines'))
    
    parser.add_argument('--remove_empty_dates', action='store_true',
                        help=_('Remove invalid DATE tags'))
    parser.add_argument('--remove_empty_notes', action='store_true',
                        help=_('Remove empty NOTE tags'))
    parser.add_argument('--remove_invalid_marriage_dates', action='store_true',
                        help=_('Remove DATE AVOLIITTO tags'))
    parser.add_argument('--remove_invalid_divorce_dates', action='store_true',
                        help=_('Remove invalid DATEs for DIV tags'))
    parser.add_argument('--remove_empty_nameparts', action='store_true',
                        help=_('Remove empty GIVN and SURN tags'))
    parser.add_argument('--remove_duplicate_sources', action='store_true',
                        help=_('Remove duplicate SOUR lines under NAME'))
    parser.add_argument('--remove_refn', action='store_true',
                        help=_('Remove REFN tags'))
    parser.add_argument('--remove_stat', action='store_true',
                        help=_('Remove STAT tags'))
    parser.add_argument('--save_level_3_notes', action='store_true',
                        help=_('Move level 3 NOTEs to level 2 to save them'))
    parser.add_argument('--fix_addr', action='store_true',
                        help=_('Insert ADR1 tags under ADDR'))
    parser.add_argument('--fix_events', action='store_true',
                        help=_('Change PLAC tags to NOTEs under certain events'))
    parser.add_argument('--fix_events_kaksonen', action='store_true',
                        help=_('Change event types "Kaksonen" and "Kolmonen" to NOTEs'))
    parser.add_argument('--remove_multiple_blanks', action='store_true',
                        help=_('Remove trailing and multiple consecutive spaces in person and place names'))
    parser.add_argument('--emig_to_resi', action='store_true',
                        help=_('Change EMIG to RESI'))
    parser.add_argument('--note_to_page', action='store_true',
                        help=_('Move an event NOTE to citation PAGE'))
    parser.add_argument('--sour_under_note', action='store_true',
                        help=_('Move a SOUR under NOTE to upper level'))
     


        


