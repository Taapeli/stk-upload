"""
Gedcom-transformer

Kari Kujansuu <kari.kujansuu@gmail.com>

Class Transformer parses a file or a list of lines into a hierarchical structure of "Item" objects. 
For each item the function 'callback' is called and its return value can replace the original
value.

Finally the top level object is returned: this is a Gedcom object 
which contains a list of top level (level 0) Gedcom records (as Items). 

"""
import sys
import os
from subprocess import call

def write(out,s):
    out.emit(s)        

class Gedcom: 
    def __init__(self,items):
        self.items = items
    def print_items(self,out):
        for item in self.items:
            item.print_items(out) 
    
class Item:
    def __init__(self,line,children=None,lines=None):
        if children is None: children = []
        temp = line.split(None,2)
        if len(temp) < 2: raise RuntimeError("Invalid line: " + line)
        self.level= int(temp[0])
        self.tag = temp[1]
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
        if self.value == "":
            return "{} {}".format(self.level,self.tag)
        else:
            return "{} {} {}".format(self.level,self.tag,self.value)
                
    def __repr__(self):
        return self.line 
    
    def print_items(self,out):
        prefix = "%s %s " % (self.level,self.tag)
        if self.value == "":
            write(out,self.line.strip())
        else:
            for line in self.value.splitlines():
                write(out,prefix+line)
                prefix = "%s CONT " % (self.level+1)
        for item in self.children:
            item.print_items(out)

class Transformer:
    def __init__(self,options,transform_module,display_callback):
        self.options = options
        self.transform_module = transform_module
        self.display_callback = display_callback


    def build_items(self,lines,level):
        if len(lines) == 0: return []
        linenums = [] # list of line numbers having the specified level 
        for i,line in enumerate(lines):
            tkns = line.split(None,1)
            if int(tkns[0]) == level:
                linenums.append(i)
            elif int(tkns[0]) < level:
                raise RuntimeError("Invalid GEDCOM at line: %s" % line)
    
        if len(linenums) == 0:    
            raise RuntimeError("Invalid GEDCOM; no level %s lines" % level)
        items = []
        for i,j in zip(linenums,linenums[1:]+[None]):
            # i and j are line numbers of lines having specified level so that all lines in between have higher line numbers;
            # i.e. they form a substructure
            firstline = lines[i] 
            item = Item(firstline,children=self.build_items(lines[i+1:j],level+1),lines=lines[i:j])
            items.append(item)
            
        return items
    
    def transform_items(self,items):
        if self.transform_module.transform is None: return items 
        newitems = []
        for item in items:
            item.children = self.transform_items(item.children)
            newitem = self.transform_module.transform(item,self.options)
            if newitem == True: # no change
                newitems.append(item)
                continue
            if self.options.display_changes: self.display_callback(item.lines,newitem)
            if newitem is None: continue # delete item
            if type(newitem) == list:
                for it in newitem:
                    newitems.append(it)
            else:
                newitems.append(newitem)
            
        return newitems
        
    
    def transform_lines(self,lines):    
        self.transform_module.fixlines(lines,self.options)
        items = self.build_items(lines,level=0)
        items = self.transform_items(items)
        return Gedcom(items)
    
    def transform_file(self,fname):
        lines = []
        lines = open(fname,encoding=self.options.encoding).readlines()
        lines = [line[:-1] for line in lines]
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
    
