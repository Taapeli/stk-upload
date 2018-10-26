'''
    Gives service to collect citation references, and display the reference links
    and Sources list, where the links point to.

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
from models.gen.source import Source

class Footnotes():
    ''' A structure for organizing footnotes for source citations '''

    def __init__(self):
        '''
        List fns members are SourceFootnotes
        '''
        fns = []

    def add(self, obj):
        ''' Adds the obj to Sources list 
        
            1.  Selvitetään, onko sama SourceFootnote jo talletettu.
                Jos on, käytetään sitä viitettä
            2.  Muuten viitteelle generoidaan uusi nimi (kuten "2b") ja
                talletetaan se
        '''
        for o in self.fns:
            if o.source_title == obj.source_title:
                return o
        # Add a new object
        self.fns.append(obj)
        return self.fns[-1]
    

class SourceFootnote(Source):
    '''
    A structure for creating footnotes for source citations:
    
    '''

    def __init__(self, params):
        '''
        Constructor
        '''
        ref_text = ''       # str like "1a"
        source_title = ''
        citations = []      # Citation objects
        repocitory = None   # Repocitory object

