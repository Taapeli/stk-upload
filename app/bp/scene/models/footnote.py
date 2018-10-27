'''
    Gives service to collect citation references, and display the reference links
    and Sources list, where the links point to.
    
    Use case plan:
        ref = Foornotes()
        ref.add(SourceFootNote.from_citation_objs(citation, objs))

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

    def add(self, new):
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
                    return (o.keystr(), i)
                else:
                    # Add to fnotes and incement 2nd part of key
                    new.key[0] = o.key[0]
                    new.key[1] = o.key[1] + 1
                    self.fnotes.append(new)
                    return (new.keystr(), i + 1)

        # A new item to fnotes list. Wirdt key number is incremented,
        # The letter numbering is started from begin
        new.key[0] = self.fnotes[-1].key[0] + 1
        return (new.keystr(), len(self.fnotes) - 1)


class SourceFootnote():
    '''
    A structure for creating footnotes for source citations:
    '''
                                #
    def __init__(self):
        '''
        Constructor
        '''
        self.cit = None         # Citation object
        self.source = None      # Source object
        self.repo = None        # Repocitory object
        self.ind = [0,0,0]      # key = uniq_ids of Repocitory, Source, Citation
        self.key = [0, 0]       # corrsponding "0a"

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
        if not ( isinstance(cit, Citation) and isinstance(objs, list) ):
            raise TypeError("SourceFootnote: Invalid arguments {}".format(cit))

        n = cls()
        n.cite = cit
        n.source = objs[n.cite.source]
        n.repo = objs[n.source.repocitory_id]
        n.ind = [n.cite.uniq_id, n.source.uniq_id, n.repo.uniq_id]
        return n


    def keystr(self):
        # Returns key as a string "1a"
        letters = "abcdefghijklmnopqrstuvxyzåäö*"
        letterno = self.key[1]
        if letterno >= len(letters):
            letterno = len(letters) - 1
        return "{}{}".format(self.key[0], letters[len(letters)-1])


#         ''' Create citation references for foot notes '''
#         sl = "{} '{}'".format(source.uniq_id, source.stitle)
#         print("lähde {} / {} '{}'".format(sl, cit.uniq_id, cit.page))
