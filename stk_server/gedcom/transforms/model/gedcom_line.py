'''
Created on 16.1.2017

@author: jm
'''

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
        self.level = int(tkns[0])
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

