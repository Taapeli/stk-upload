#!/usr/bin/env python3
"""
Hiski-lähdeviitteiden tulkinta (?)

@author: ?
"""
#import collections
import urllib.request

version = "1.0"

sourceids = set()  # set of sources ids (@Sxxxx@) to be processed
maxnotenum = 0
notes = []        # list of (notenum,link)


class Container:
    nextnum = 0
    def __init__(self):
        self.itemnum = -1
        self.items = {}
        self.map = {}
    def add(self,item):
        if item in self.map:
            return self.map[item]
        self.itemnum += 1
        self.items[self.itemnum] = item
        self.map[item] = self.itemnum
        return self.itemnum
#repos = Container()

class Repo:
    nextnum = 0
    def __init__(self,name):
        self.sources = set()
        self.name = name
        self.num = Repo.nextnum
        Repo.nextnum += 1
    def addsource(self,source):
        self.sources.add(source)
    def __repr__(self):
        return "Repo<%s>: %s sources" % (self.name,len(self.sources))
       
class Source:
    nextnum = 0
    def __init__(self,name,repo):
        self.name = name
        self.repo = repo
        repo.addsource(self)
        self.num = Source.nextnum
        Source.nextnum += 1
    def __repr__(self):
        return "Source<%s,%s>" % (self.name,self.repo)
   
class HiskiCitations:
    nextnum = 0
    def __init__(self):
        self.sources = {}  # name -> Source
        self.repos = {}  # name -> Repo
        self.citations = {} # link -> Source
        self.original_sour_to_source = {} # @Sxxxx@ -> Source
    def add(self,sour,sourcename,reponame,link):
        if reponame not in self.repos:
            self.repos[reponame] = Repo(reponame)
        repo = self.repos[reponame]
        if sourcename not in self.sources:
            source = Source(sourcename,repo)
            self.sources[sourcename] = source
            repo.addsource(source)
       
        source = self.sources[sourcename]
        self.citations[link] = source
        self.original_sour_to_source[sour] = (source,link)

citations = HiskiCitations()
    
def text_content(s,tag):
    txt = None
    starttag = b"<%s>" % tag
    endtag = b"</%s>" % tag
    i = s.find(starttag)
    if i > 0:
        j = s.find(endtag,i)
        txt = s[i+4:j]
    return txt.decode("iso8859-1")

def get_hiski_info(link):
#     srk = None
#     kirja = None
    s = urllib.request.urlopen(link).read()
    srk = text_content(s, b"H2")
    kirja = text_content(s, b"H3")
    return srk,kirja

def add_args(parser):
    pass

def initialize(run_args):
    pass

def phase1(run_args, gedline):
    global maxnotenum
     
    # The following two if statements process the GEDCOM lines like
    #   0 @S0000@ SOUR
    #   1 TITL http://hiski.genealogia.fi/...
    # and store the citations in 'citations'
    if gedline.value == "SOUR" and gedline.level == 0: # 0 @Sxxxx@ SOUR
        sourceids.add(gedline.tag)  
    if (gedline.tag == "TITL" and
        gedline.level == 1 and  
        gedline.value.startswith("http://hiski.genealogia.fi/")):
        sourceid = gedline.path.split(".")[0]
        if sourceid in sourceids:
            link = gedline.value
            srk,kirja = get_hiski_info(link)
            sourcename = "HisKi %s %s" % (srk,kirja)
            reponame = "%s srk arkisto" % srk
            citations.add(sourceid,sourcename,reponame,link)
        
    if 0 and gedline.path.endswith(".NOTE"):
        noteid = gedline.path.split(".")[0]  # @Nxxxx@
        n = int(noteid[1:-1])
        if n >= maxnotenum: maxnotenum = n

def phase2(run_args):
    pass

def phase3(run_args, gedline, f):
    global maxnotenum
    indi_id = gedline.path.split(".")[0]
    if gedline.path.endswith(".SOUR"):  # n SOUR @Sxxxx@ 
        #indi = gedline.path.split(".")[0]
        sour = gedline.value
        if sour in citations.original_sour_to_source:
            source,link = citations.original_sour_to_source[sour]
            gedline.value = "@XS%4.4d@" % source.num
            gedline.emit(f) # emit original "2 SOUR @sour@" line, but with new id
            f.emit("%d PAGE %s" % (gedline.level+1,link))
            f.emit("%d NOTE %s" % (gedline.level+1,link))
            #maxnotenum += 1
            #f.emit("3 NOTE @N%s@" % maxnotenum)
            #notes.append((maxnotenum,link))
            return
    if indi_id in citations.original_sour_to_source:
        return # remove original sources

    gedline.emit(f)


def phase4(run_args, f):
    for source in citations.sources.values():
        f.emit("0 @XS%4.4d@ SOUR" % source.num)
        f.emit("1 TITL %s" % source.name)
        f.emit("1 REPO @XR%4.4d@" % source.repo.num)
    """
    0 @R0000@ REPO
    1 NAME Vanajan srk arkisto
    """
    for repo in citations.repos.values():
        f.emit("0 @XR%4.4d@ REPO" % repo.num)
        f.emit("1 NAME %s" % repo.name)
