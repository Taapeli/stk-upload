import re
from pprint import pprint
import sys
import traceback
from types import SimpleNamespace
import itertools

#RE_WORD = "^([a-zA-ZäåöÄÅÖüÜéÉŝŜ-]+)"

RE_WORD = r"^([\w-]+)"
RE_DIGITS = "^([0-9]+)"
RE_NUMBER = "^([+-]?[0-9]+)"
RE_STRING = r'^(\"[^"]*\")'

class ParseError(RuntimeError): 
    def __init__(self,parser,msg=""):
        self.input = parser.input
        self.pos = len(parser.input) - len(parser.s)
        self.args = parser.args
        self.msg = msg
    def __put(self,*args):
        print(*args,file=sys.stderr)
    def printerr(self):
        if self.msg: self.__put(self.msg)
        self.__put(self.input)
        self.__put(" "*self.pos+"^")
        self.__put("Expecting one of:")
        for arg in self.args:
            self.__put(arg)

class Arg:
    def __init__(self, title, regex, testfunc=None, valuefunc=None):
        self.title = title
        self.regex = regex
        self.testfunc = testfunc
        self.valuefunc = valuefunc
    def match(self,s):
        m = re.match(self.regex,s)  
        if m:
            text = m.group(1)
            if self.testfunc:
                if not self.testfunc(text):
                    return None
            if self.valuefunc:
                value = self.valuefunc(text)
            else:
                value = text
            return Match(text, value)
        return None
    def __repr__(self):
        return self.title

class Name(Arg):
    def __init__(self, title):
        self.title = title
    def match(self,s):
        if s[0].isupper():
            i = 1
            while i < len(s) and s[i].isalpha(): i += 1
            text = s[:i]
            return Match(text)
        return None
    def __repr__(self):
        return self.title

class Word(Arg):
    def __init__(self, title):
        self.title = title
    def match(self,s):
        if s[0].isalpha():
            i = 1
            while i < len(s) and s[i].isalpha(): i += 1
            text = s[:i]
            return Match(text)
        return None
    def __repr__(self):
        return self.title

class Keyword(Arg):
    def __init__(self, keywords, case_sensitive=True, space_separated=False):
        self.keywords = keywords
        self.case_sensitive = case_sensitive
        self.space_separated = space_separated
        if not self.case_sensitive:
            self.keywords_lower = [s.lower() for s in keywords]
    def match(self,s):
        if self.space_separated:
            text = s.split()[0]
        else:
            m = re.match(RE_WORD,s)  
            if m:
                text = m.group(1)
            else:
                return None
        if not self.case_sensitive:
            if text.lower() in self.keywords_lower:
                index = self.keywords_lower.index(text.lower())
                return Match(self.keywords[index])
            else:
                return None
        if text in self.keywords:
            return Match(text)
        else:
            return None
    def __repr__(self):
        return "One of: " + ",".join(self.keywords)

class Special:
    def __init__(self, title):
        self.title = title
    def __repr__(self):
        return self.title
    
def is_capitalized(s):
    try:
        return s[0].isupper() and s[1:].islower()
    except:
        return False

def is_name(s):
    if s.find(" ") > 0: return False
    parts = s.split("-")
    if len(parts) > 2: return False
    if not is_capitalized(parts[0]): return False
    if len(parts) == 2 and not (
        is_capitalized(parts[1]) or parts[1].islower()): return False
    return True

WORD = Arg("word",RE_WORD)
WORD = Word("word2")
LCWORD = Arg("lower case word",RE_WORD,testfunc=str.islower)
UCWORD = Arg("upper case word",RE_WORD,testfunc=str.isupper)
CAPWORD = Arg("capitalized word",RE_WORD,testfunc=is_capitalized)
NUMBER = Arg("number",RE_NUMBER,valuefunc=int)
DIGITS = Arg("number",RE_DIGITS,valuefunc=int)
STRING = Arg("quoted string",RE_STRING,valuefunc=eval)
NAME = Arg("name",RE_WORD,testfunc=is_name)
#NAME = Name("name2")

END = Special("end")
OTHERWISE = Special("otherwise")

class Match(object):
    def __init__(self, text, value=None):
        #print("text:",text)
        self.text = text
        self.value= value
        if value is None: self.value = text


class Parser:
    def __init__(self,s,return_zero=False, loop_limit=50):
        self.input = s
        self.s = s
        self.value = None
        self.text = None
        self.return_zero = return_zero
        self.prev = None
        self.counter = 0
        self.loop_limit = loop_limit
        
    def __repr__(self):
        return f"Parser: remaining string: '{self.s}'"
    
    def end(self):
        return self.s.strip() == ""
    
    def peek(self,*args):
        """
        Parses the next 'token' in the input string (self.s). The accepted
        tokens are defined by the arg parameters.
        Checks all args in order and stops when the first one matches.
        Each call to 'parse' 'consumes' the input, i.e. removes the matching text 
        from the front of the input string but calls to 'peek' does not advance.
        Leading spaces are ignored.
        Returns the position number of the matching arg (first one is 1).
        The matching text is stored in self.text and self.value. The difference
        is that self.text is always a string but self.value may
        be a value of another type, e.g. for numeric matches it is an integer. 
        For case-insensitive keyword matches self.value is
        the matching keyword in the keyword list, not the matching string in the input.
        If no arg matches raises an exception unless return_zero is True - then
        parse will return zero.
        Each arg may be
        1. A string: then the match is a literal string match at the start of the input string.
           The comparison in case-sensitive.
        2. List of strings. Matches if any of the string matches the start of the input string.
           Return value is the same for any match (ie. the position of the list) 
        3. An object of type Arg. Then the match method of arg is called,
        4. END. Then there is a match only if the whole string s is empty.
        5. OTHERWISE. Anything matches. OTHERWISE must be the last choice.
        There are these predefined arg objects:
        1. WORD - matches any alphabetic string
        2. LCWORD - matches any lower case alphabetic string
        3. UCWORD - matches any upper case alphabetic string
        4. CAPWORD - matches any alphabetic string that starts with an upper case
           character and is otherwise lower case (may be a single upper case character)
        5. DIGITS - matches any numeric string (containing only digits)
        6. NUMBER - matches any integer (containing only digits + optional sign in the front)
        7. Keyword([word,word,...]) - matches any of the given words (strings)
           - Keyword() accepts two additional arguments
             - case_sensitive (True or False, default True)
             - space_separated (True or False, default False)
        8. STRING - matches a quoted string (text within double quotes)
        Other types can be easily defined.
        """
        self.value = None
        self.text = None
        self.args = args
        self.s = self.s.lstrip()
        if self.s == self.prev:
            if self.counter > self.loop_limit:
                raise ParseError(self,"Parser in infinite loop")
                #raise RuntimeError("Parser in infinite loop")
            self.counter += 1
        else:
            self.counter = 0
        self.prev = self.s
            
        for i,arg in enumerate(args):
            m = self.match(self.s,arg)
            if m:
                self.text = m.text
                self.value = m.value
                return i+1
        if self.return_zero:
            return 0
        #print(self.s)
        #print("Expecting one of:")
        #for arg in args:
        #    print(arg)
        raise ParseError(self)

    def parse(self,*args):
        """
        Parses the next token and advances the pointer. Returns
        the position number of the matching arg. See 'peek'.
        """
        i = self.peek(*args)
        if i > 0:
            self.s = self.s[len(self.text):]
        return i

    def optional(self,*args):
        """
        If any arg matches then consumes the token and returns True.
        If no match is found then returns False.
        The position number is lost but the matching text is in self.text 
        and self.value.
        """
        i = self.peek(*args,OTHERWISE)
        if i > 0:
            self.s = self.s[len(self.text):]
        return i < len(args)+1

    def match(self,s,arg):
        """
        Returns a Match object if the string s starts with a substring
        matching the argument arg. Return None otherwise.
        Argument arg can be:
        1. A string: then the match is a literal string match.
        2. An object of type Arg. Then the match method of arg is called which will
           return a Match object or None.
        3. END. Then there is a match only if the whole string s is empty.
        4. OTHERWISE. Anything matches. OTHERWISE must be the last choice.
        """
        if arg is OTHERWISE:
            return Match("")
        if arg is END:
            if s == "":
                return Match("")
            else:
                return None
        if s == "": return None
        if isinstance(arg, Arg):
            m = arg.match(s)  
            if m:
                return m
            else:
                return None
        if isinstance(arg, str):
            if s.startswith(arg):  
                return Match(arg)
            else:
                return None
        if isinstance(arg, list):
            for tkn in arg:
                if s.startswith(tkn):  
                    return Match(tkn)
            return None
        raise RuntimeError(f"unknown arg type: {arg}")
        return None
    
def test():
    s = " abc/ 123"
    p = Parser(s)

    i = p.parse(WORD)
    assert(i==1)
    assert(p.value == "abc")
        
    i = p.parse("/")    
    assert(i==1)

    i = p.parse(NUMBER)        
    assert(i==1)
    assert(p.text == "123")
    assert(p.value == 123)

    i = p.parse(END)        
    assert(i==1)

#--------------------

    p = Parser("  123  ")
    i = p.parse(WORD,OTHERWISE)
    assert(i==2)
    i = p.parse(NUMBER,OTHERWISE)
    assert(i==1)
    assert(p.text == "123")
    assert(p.value == 123)
    i = p.parse(END)        
    assert(i==1)
    

#--------------------

    p = Parser(" -123")
    i = p.parse(NUMBER)
    assert(i==1)
    assert(p.text == "-123")
    assert(p.value == -123)

#--------------------

    p = Parser("123",return_zero=True)
    i = p.parse(WORD)
    assert(i==0)

#--------------------
    p = Parser("language=python")
    i = p.parse(Keyword(["language","country"]))
    assert(i==1)
    assert(p.value == "language")

#--------------------
    p = Parser("Language=python")
    i = p.parse(Keyword(["language","country"],case_sensitive=False))
    assert(i==1)
    assert(p.value == "language")

#--------------------
    p = Parser("country=sweden")
    i = p.parse(NUMBER,Keyword(["language","country"]))
    assert(i==2)
    assert(p.value == "country")

    i = p.parse("+","=")
    assert(i==2)
    assert(p.value == "=")

    i = p.parse(NUMBER,Keyword(["finland","sweden"]))
    assert(i==2)
    assert(p.value == "sweden")

#--------------------
    p = Parser("Country=sweden")
    i = p.parse(LCWORD,UCWORD,CAPWORD)
    assert(i==3)
    assert(p.value == "Country")

#--------------------
    p = Parser("country=sweden")
    i = p.parse(LCWORD,UCWORD,CAPWORD)
    assert(i==1)
    assert(p.value == "country")

#--------------------
    p = Parser("COUNTRY=sweden")
    i = p.parse(LCWORD,UCWORD,CAPWORD)
    assert(i==2)
    assert(p.value == "COUNTRY")

#--------------------
    p = Parser('country="sweden or finland";')
    i = p.parse(NUMBER,Keyword(["language","country"]))
    assert(i==2)
    assert(p.value == "country")

    i = p.parse("+","=")
    assert(i==2)
    assert(p.value == "=")

    i = p.parse(STRING)
    assert(i==1)
    assert(p.value == "sweden or finland")
    assert(p.text == '"sweden or finland"')

    i = p.parse(";")
    i = p.parse(END)


test()    


    
