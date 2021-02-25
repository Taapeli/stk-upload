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

"""
Gedcom transformer

Kari Kujansuu <kari.kujansuu@gmail.com>

Each transformation module should implement:
    1. Function initialize
       Returns an instance of the class Transformation
    2. Function add_args
       Adds the transformation specific arguments (Argparse style)
    3. Attribute name
    4. Attribute docline
    5. Attribute doclink
    6. Attribute twophases

The Transformation object should implement the methods transform and finish. 
Optionally it can implement the initializer (__init__) and the method finish().    
    
Class Transformer parses a file or a list of lines into a hierarchical structure of "Item" objects. 
For each item the method 'transform' is called and its return value can replace the original
value.

Finally the top level object is returned: this is a Gedcom object 
which contains a list of top level (level 0) Gedcom records (as Items). 

"""
import sys
# import os
# from subprocess import call
# import logging 
# logger = logging.getLogger('stkserver')

from flask_babelex import _
from .models import  gedcom_utils

def write(out,s):
    out.emit(s)

def fixlines(lines,options):
    """ Clean Gedcom lines from line feed marks and fix CONT.
    """
    prevlevel = -1
    line = ""
    for i,line in enumerate(lines):
        #line = line.strip()

        if i == 0 and line and line[0] == "\ufeff":  # remove Byte Order Mark (BOM) 
            line = line[1:]        
            lines[i] = line        

        tkns = line.split(None,1)
        
        if (len(tkns) == 0 or not tkns[0].isdigit()):
            # assume this is a continuation line
            newline = "%s CONT %s" % (prevlevel+1,line)
            tkns = newline.split(None,1)
            lines[i] = newline
            if options.display_changes:
                gedcom_utils.display_changed_lines([line],[newline],i+1)
        elif len(tkns) == 1:
            newline = tkns[0] + " _DUMMY"
            if options.display_changes:
                gedcom_utils.display_changed_lines([line],[newline],i+1)
            line = newline
            tkns = line.split(None,1)
            lines[i] = line
        tag = lines[i].split()[1]
        if tag not in {"CONT","CONC"}: prevlevel = int(tkns[0])
    if line.strip() != "0 TRLR":
        newline = "0 TRLR"
        lines.append(newline)
        if options.display_changes:
            gedcom_utils.display_changed_lines(None,[newline],None)

class Transformation:
    """ Base class for different transformation objects.
    
        Class Transformer parses a file or a list of lines into a hierarchical 
        structure of "Item" objects. 
        
        The Transformation object should implement the methods transform and finish. 
        Optionally it can implement the initializer (__init__) and the method finish.    
    """
    twophases = False
    
    def transform(self,item,options):
        """
        Performs a transformation for a given Gedcom "item" ("line block").

        Returns one of
        - True: keep this item without changes
        - None: remove the item
        - item: use this item as a replacement (can be the same object as input
          if the contents have been changed)
        - list of items ([item1,item2,...]): replace the original item with these
       
        This is called for every line in the Gedcom so that the "innermost" items
        are processed first.
       
        Note: If you change the item in this function but still return True, 
              then the changes are applied to the Gedcom but they are not 
              displayed with the --display-changes option.
    
        The method can manipulate the input "item", for example it can add or 
        remove "children", i.e. the next level items contained in the item. 
        It can change the item's tag or value but it cannot change the level number.
        The attribute item.line contains the Gedcom line as a string - it should not 
        be changed directly - it is actually a computed property. 
        The method can create new items if needed by calling the constructor 
        Item("<gedcom line>").
        """
        pass

    def finish(self,options):
        pass
        
class Gedcom: 
    def __init__(self,items):
        self.items = items
    def print_items(self,out):
        for item in self.items:
            item.print_items(out) 
    
class Item:
    """ A gedcom line with all its included descendants.
    
        Examples:
            0 @I2@ INDI
            1 SEX F

        Data fields:
        - linenum       int    source line number
        - level         int    gedcom level number 0, 1, ...
        - xref          str    gedcom reference "@I001@" etc
        - tag           str    Gedcom tag "INDI", "SEX", ...
        - children[]    Item   included Items (with next higher level)
        - value         str    text following tag "F" etc
                        int    x
    """
    def __init__(self, line, children=None, lines=None, linenum=None):
        if children is None: 
            children = []
        self.linenum = linenum
        parts = line.split()
        if len(parts) < 2: 
            raise RuntimeError(_("Invalid line: ") + line)
        self.level = int(parts[0])
        if self.level == 0 and parts[1][0] == '@':
            self.xref = parts[1]
            self.tag = parts[2]
        else:
            self.xref = ""
            self.tag = parts[1]
        self._line = line
        self.children = children
        self.lines = lines
        i = line.find(" " + self.tag + " ")
        if i > 0:
            self.value = line[i+len(self.tag)+2:] # preserves leading and trailing spaces
        else:
            self.value = ""

    @property
    def line(self):
        s = str(self.level)
        if self.xref:
            s += " " + self.xref
        s += " " + self.tag
        if not self.value and self._line.strip() == s.strip(): 
            return self._line
        if self.value or self.tag == "CONT": 
            s += " " + self.value
        return s

    def __repr__(self):
        """ Return current line.  """
        return self.line 
    
    def list(self, show_children=True):
        """ Display item, optionally with included inner level items. """
        if show_children:
            if len(self.children) > 6:
                return f"{self.line} {self.children[:5]} ..."
            else:
                return f"{self.line} {self.children}"
        else:
            return self.line

    def print_items(self, out):
        """ Print item with included inner level items.
        """
        write(out,self.line)
        for item in self.children:
            item.print_items(out)

class Transformer:
    def __init__(self,options,transform_module,display_callback):
        self.options = options
        self.transform_module = transform_module
        self.display_callback = display_callback
        self.transformation = transform_module.initialize(options)
        self.num_changes = 0

    def build_items(self,lines,level,linenum=1):
        if len(lines) == 0: return []
        linenums = [] # list of line numbers having the specified level 
        for i,line in enumerate(lines):
            tkns = line.split(None,1)
            if int(tkns[0]) == level:
                linenums.append(i)
            elif int(tkns[0]) < level:
                raise RuntimeError(_("Invalid GEDCOM at line: {}").format(line))
    
        if len(linenums) == 0:    
            raise RuntimeError(_("Invalid GEDCOM; no level %s lines") % level)
        items = []
        for i,j in zip(linenums,linenums[1:]+[None]):
            # i and j are line numbers of lines having specified level so that all lines in between have higher line numbers;
            # i.e. they form a substructure
            firstline = lines[i] 
            item = Item(firstline,
                        children=self.build_items(lines[i+1:j],level+1,linenum+i+1),
                        lines=lines[i:j],
                        linenum=linenum+i
                        )
            items.append(item)
            
        return items
    
    def transform_items(self, items, path="", phase=1):
        """ Do transformation for a list of Items.
        
            This is called recursive for inner level Items.
        """
        newitems = []
#         if items:
#             print(f"# Processing {items[:5]} ..." if len(items) > 6 else f"# Processing {items}<br>")

        for item in items:
            if path:        item.path = path + "." + item.tag
            elif item.xref: item.path = item.xref + "." + item.tag
            else:           item.path = item.tag
            # Process the children (lines with next higher level numbers)
            item.children = self.transform_items(item.children, path=item.path, phase=phase)
            # Process current type transformation for this Item
            newitem = self.transformation.transform(item, self.options,phase)
            #print(f"# {item.line[:6]} – {len(item.children)} children")
            if newitem == True: # no change
                newitems.append(item)
                continue
            self.num_changes += 1
            if self.options.display_changes:
                self.display_callback(item.lines, newitem, item.linenum)
            if newitem is None: continue # delete item
            if type(newitem) == list:
                for it in newitem:
                    newitems.append(it)
            else:
                newitems.append(newitem)

        return newitems
        
    
    def transform_lines(self, lines):    
        """ Creates Items from lines and runs the transformation.
        
            Returns the fixed lines after transformation
        """
        fixlines(lines, self.options)
        items = self.build_items(lines,level=0)
        # Transformation
        items = self.transform_items(items)
        if self.transformation.twophases:
            items = self.transform_items(items,phase=2)
        self.transformation.finish(self.options)
        # Return the resulting lines out of Items
        return Gedcom(items)
    
    def transform_file(self,fname):
        """ Reads and cleans the input gedcom file and returns processed lines.
        """
        #lines = []
        lines = open(fname,encoding=self.options.encoding).readlines()
        lines = [line[:-1] for line in lines]
        # Do transforming
        return self.transform_lines(lines)
    
    

    


if __name__ == "__main__":
    import textwrap
    text = """
    0 HEAD
    0 @I1@ INDI
    1 NAME Antti A
    0 @I2@ INDI
    1 NAME Antti B
    1 BIRT
    2 PLAC Finland
    0 TRLR
    """
    text = textwrap.dedent(text)

    class Options: pass
    
    class Out:
        def emit(self,s):
            print(s)
            
    def transform(item,options):
        #if item.tag == "@I1@": return None
        if item.value == "Antti B": 
            item.value = ""
            return item
        if item.tag == "BIRT":
            item.children.append(Item("2 DATE 2000"))
            return item
        return True

    def display(lines,item):
        print("--------------------")
        print("Replaced:")
        for line in lines:
            print(line)
        print("With:")
        item.print_items(Out())
        print()

    lines = [line for line in text.splitlines() if line.strip() != ""]
    
    print(lines)
    
    options = Options()
    options.display_changes = True
    transformer = Transformer(transform_callback=transform,options=options,display_callback=display)
    g = transformer.transform_lines(lines)
    
    print(g)
    g.print_items(Out())
    
