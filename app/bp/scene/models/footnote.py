'''
    Gives service to collect citation references, and display the reference links
    and Sources list, where the links point to.
    
    USED ONLY in bp.scene.scene_reader.get_a_person_for_display_apoc
    
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


    def getFootnotes(self):
        lst = []
        for n in self.fnotes:
            for c in n.cites:
                lst.append(CitationMark(c.mark, c.ids))
        return lst


class SourceFootnote():
    '''
    A structure for creating footnotes for sources and citations:

        (cite:Citation) -[*]-> (source:Source) -[1]-> (repo:Repository)

        self ~ Source reference
            .source             Source object
            .repo               Repository object covering this Source
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
        self.repo = None        # Repository object
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
    def from_citation_objs(cls, citation_obj, objs):
        ''' Creates a SourceFootnote from Citation structure components
            using objects from dictionary objs

            citation_obj        Citation object ~ from objs[cref]
            - citation_obj.page str     Citation page text
            source              Source object ~ from objs[citation_obj.source]
            - source.stitle     str     Source title
                                source href="#sref{{ source.uniq_id }}"
            repo                Repository object ~ from objs[source.repositories[]]
            - repo.rname        str     Repository name"
        '''
        if not ( isinstance(citation_obj, Citation) and isinstance(objs, dict) ):
            raise TypeError(f"SourceFootnote: Invalid arguments {citation_obj}")

        n = cls()
        n.cites.append(citation_obj)
        if citation_obj.source_id in objs:
            n.source = objs[citation_obj.source_id]
            s_id = n.source.uniq_id
        else:
            s_id = -1

        r_ids = []
        if n.source:
            for rep in n.source.repositories:
                if rep in objs:
                    n.repo = objs[rep]
                    r_ids.append(n.repo.uniq_id)
        n.cites[0].ids = [r_ids, s_id, n.cites[0].uniq_id]
        #print("- ind=(r,s,c)={}".format(n.cites[0].ids))
        return n


    def setmark(self, i, j):
        ''' Sets mark by indexes i, j as a string " 1a"
            for this SourceFootnote and .cites[-1]
        '''
        letters = "abcdefghijklmnopqrstizåäö*"
        #self.cites[-1].mark2 = j
        mark2 = j
        if mark2 >= len(letters):
            mark2 = len(letters) - 1
        self.mark = f"{i + 1:2d}{letters[mark2]}"
        self.cites[-1].mark = self.mark


class CitationMark():
    """ Object representing a citation mark '1a', for Footnote.
    
        Moved here from models.gen.citation / JMä 15.11.2019
    """
    def __init__(self, mark=None, ids=[-1, -1, -1]):
        self.mark = mark
        self.repository_ids = ids[0]
        self.source_id = ids[1]
        self.citation_id = ids[2]
 
    def __str__(self):
        return "{}: r={},s={},c={}".format(self.mark, self.repository_ids, self.source_id, self.citation_id)

