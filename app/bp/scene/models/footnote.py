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
#from models.gen.source import Source
from models.gen.citation import Citation
#from models.gen.repository import Repository

class Footnotes():
    ''' A structure for organizing footnotes for source citations '''

    def __init__(self):
        '''
        List fns members are SourceFootnotes
        '''
        self.fnotes = []

    def merge(self, new):
        ''' Adds the new SourceFootnote to Sources list. 
            Returns the matching reference id like "1a" and 
            an index to fnotes list
        
            1.  Selvitetään, onko sama SourceFootnote jo talletettu.
                Jos on, käytetään sitä viitettä
            2.  Muuten viitteelle generoidaan uusi nimi (kuten "2b") ja
                talletetaan se
        '''
        for i in range(len(self.fnotes)):
            o = self.fnotes[i]
            if o.ind[0] == new.ind[0] and o.ind[1] == new.ind[1]:
                # Found matcing Repocitory & Source key
                if o.ind[2] == new.ind[2]:
                    # Found matching Citation, too
                    return (o.mark_id, i)
                else:
                    # Add to fnotes and incement 2nd part of mark
                    new.setmark(o.mark[0], o.mark[1] + 1)
                    self.fnotes.append(new)
                    return (new.mark_id, i + 1)

        # A new item to fnotes list. 
        # Default number and letter are (0,0) ~ "1a"
        if self.fnotes:
            # Next number, default letter
            new.setmark(self.fnotes[-1].mark[0] + 1, 0)
        self.fnotes.append(new)
        return (new.mark_id, len(self.fnotes) - 1)

    def getNotes(self):
        lst = []
        for n in self.fnotes:
            lst.append([n.mark_id] + n.ind)
        return lst


class SourceFootnote():
    '''
    A structure for creating footnotes for source citations:
    '''
                                #
    def __init__(self):
        '''
        Constructor
        '''
        self.cite = None        # Citation object
        self.source = None      # Source object
        self.repo = None        # Repocitory object
        self.ind = [0,0,0]      # key = uniq_ids of Repocitory, Source, Citation
        self.mark = [0, 0]       # corrsponding "0a"
        self.mark_id = '1a'

    def __str__(self):
        return "{}: {} / {} / {}".format(self.mark_id, self.repo, self.source, self.cite)


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
        n.cite = cit
        if n.cite.source_id in objs:
            n.source = objs[n.cite.source_id]
            s_id = n.source.uniq_id
        else:
            s_id = -1
        if n.source.repocitory_id in objs:
            n.repo = objs[n.source.repocitory_id]
            r_id = n.repo.uniq_id
        else:
            r_id = -1
        n.ind = [n.cite.uniq_id, s_id, r_id]
        #print("- ind={}".format(n.ind))
        return n

    def setmark(self, mark1, mark2):
        # Sets mark[] indexes and mark_id as a string "1a"
        letters = "abcdefghijklmnopqrstuvxyzåäö*"
        self.mark[0] = mark1
        self.mark[1] = mark2
        letterno = self.mark[1]
        if letterno >= len(letters):
            letterno = len(letters) - 1
        self.mark_id = "{}{}".format(self.mark[0] + 1, letters[letterno])
