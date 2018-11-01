'''
    Gives service to collect citation references, and display the reference links
    and Sources list, where the links point to.
    
    Use case plan:
        ref = Foornotes()
        ref.merge(SourceFootNote.from_citation_objs(citation, objs))

    Sivulla person_pg esiintyvät sitaatit kootaan listaan cits kutsulla

        macro.link_cite(person.citation_ref, obj, cits)

    Makron tulee
        1) muodostaa viite_src "1a", "1b", "2a" ... jossa parit
           (Repository_id, Source_id) vastavat numeroita ja 
           Citation_id:t kirjaimia
           - jos viite on jo taulukossa cits, käytetään sitä
           - muuten luodaan uusi:
        2) tallettaa listaan cits[] tuplet 
           esim. cits[0] = ((100269,91355), ("1a", 92125))
           - avain i = (Repository_id, Source_id)
           - arvo j = (viite_str, Citation_id)
        3) palauttaa sivun esiintymispaikkaan linkin
            <a href="viite_str" title="Source_name">viite_str</a>

    Lähteet-osiossa kelataan viitteet läpi ja muodostetaan 2-tasoinen
    lista (linkkeineen ym.) mallia:

        1. Source.stitle, Repository.rname
            a. Citation.page

Created on 23.10.2018

@author: jm
'''
from models.gen.citation import Citation

class Footnotes():
    ''' A structure for organizing footnotes for source citations '''

    def __init__(self):
        '''
        List fns members are SourceFootnotes
        '''
        self.fnotes = []


    def merge(self, new):
        ''' Adds the new SourceFootnote to fnotes list, if not there.
 
            Returns for ex. ('1a', 0, 0): the matching citation mark and 
            indexes to fnotes[i].citation[j]
                '''
        if not self.fnotes:
            # a) Add the first SourceFootnote item to fnotes list. 
            self.fnotes.append(new)
            new.setmark(0, 0)
            return (new.mark, 0, 0)
            
        for i in range(len(self.fnotes)):
            o = self.fnotes[i]
            if o.is_sameSource(new):
                j = o.has_sameCitation(new)
                if j >= 0:
                    # b) Found a reference to same Citation
                    o.setmark(i, j)
                    return (o.cites[j].mark, i, j)
                else:
                    # c) Append a new Citation to this SourceFootnote 
                    j = len(o.cites)
                    new.setmark(i, j)
                    self.fnotes[i].cites.append(new.cites[0])
                    return (new.mark, i, j)

        # d) A new SourceFootnote item (with 1 Citation)
        i1 = len(self.fnotes)
        new.setmark(i1, 0)
        self.fnotes.append(new)
        return (new.mark, i1, 0)


    def getNotes(self):
        lst = []
        for n in self.fnotes:
            for c in n.cites:
                lst.append(CitationMark(c.mark, c.ids))
        return lst


class CitationMark():
    def __init__(self, mark=None, ids=[-1, -1, -1]):
        self.mark = mark
        self.r_id = ids[0]
        self.s_id = ids[1]
        self.c_id = ids[2]

    def __str__(self):
        return "{}: r={},s={},c={}".format(self.mark, self.r_id, self.s_id, self.c_id)

class SourceFootnote():
    '''
    A structure for creating footnotes for sources and citations:

        (cite:Citation) -[*]-> (source:Source) -[1]-> (repo:Repocitory)

        self ~ Source reference
            .source             Source object
            .repo               Repocitory object covering this Source
            .cites[]            Citation objects pointing this Source
            .source.uniq_id     int ~ index1 (Source)
            .cites[j].uniq_id   int ~ index2 (Citation)
            .mark               str '1a'
    '''
    def __init__(self):
        '''
        SourceFootnote constructor
        '''
        self.source = None      # Source object (this)
        self.repo = None        # Repocitory object
        self.cites = []         # Citation objects
        self.mark = '1a'


    def __str__(self):
        clist = []
        for c in self.cites:
            clist.append(str(c))
        return "{}: {} | {} | {}".format(self.mark, self.repo, self.source, ", ".join(clist))


    def is_sameSource(self, other):
        ''' Return True, if SourceFootnote other refers to same Source 
        '''
        if not self.source:
            return False
        if other.source and other.source.uniq_id == self.source.uniq_id:
            return True
        return False


    def has_sameCitation(self, other):
        ''' Return citation index, if 1st Citation in SourceFootnote other 
            refers to same Citation in this Source.
        '''
        if not self.cites:
            return -1
        for i in range(len(self.cites)):
            if other.cites and other.cites[0].uniq_id == self.cites[i].uniq_id:
                return i
        return -1


    @classmethod
    def from_citation_objs(cls, cit, objs):
        ''' Creates a SourceFootnote from Citation structure components
            using objects from dictionary objs

            cit                 Citation object ~ from objs[cref]
            - cit.page          str     Citation page text
            source              Source object ~ from objs[cit.source]
            - source.stitle     str     Source title
                                source href="#sref{{ source.uniq_id }}"
            repo                Repocitory object ~ from objs[source.repocitory_id]
            - repo.rname        str     Repocitory name"
        '''
        if not ( isinstance(cit, Citation) and isinstance(objs, dict) ):
            raise TypeError("SourceFootnote: Invalid arguments {}".format(cit))

        n = cls()
        n.cites.append(cit)
        if cit.source_id in objs:
            n.source = objs[cit.source_id]
            s_id = n.source.uniq_id
        else:
            s_id = -1

        if n.source and n.source.repocitory_id in objs:
            n.repo = objs[n.source.repocitory_id]
            r_id = n.repo.uniq_id
        else:
            r_id = -1
        n.cites[0].ids = [r_id, s_id, n.cites[0].uniq_id]
        print("- ind=(r,s,c)={}".format(n.cites[0].ids))
        return n


    def setmark(self, i, j):
        ''' Sets mark by indexes i, j as a string "1a 
            for this SourceFootnote and .cites[-1]"
        '''
        letters = "abcdefghijklmnopqrstizåäö*"
        #self.cites[-1].mark2 = j
        mark2 = j
        if mark2 >= len(letters):
            mark2 = len(letters) - 1
        self.mark = "{}{}".format(i + 1, letters[mark2])
        self.cites[-1].mark = self.mark
