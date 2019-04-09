#!/usr/bin/env python3
'''
Muodostaa yhdistetyistä lähdeviitteistä nimetyt lähteet ja sivunumerot 

Created on 17.2.2017

@author: TimNal

Ohjelman perusteet:

            Kun sukututkimusohjelmalla (esimerkiksi Brothers Keeper) voidaan tallettaa lähde (SOUR), 
            ja muista elementeistå viittaus lähteeseen vaan ei sille lähdeviittauksia (PAGE),
            voidaan tämän muunnoksen avulla täydentää vittaukset GEDCOM-rakenteisiin. 
            Jos lähteiden määrittelyn kommentteihin (NOTE) talletetaan lähdeviittaukset tietyssä muodossa
            puolipisteillä eroteltuna, voidaan tuotetusta gedcom-aineistosta siirtää lähdeviittaukset 
            lähteiden NOTEista elementtien viittauksiin samassa järjestyksessä kuin ne esiintyvät
            viittaavien elementtien määrityksessä.
            
            Lähteiden määrittelyissä on Note-elementteihin kerätty yhden tai useamman lähteen nimet ja 
            mahdollinen sivunumeroviittaukset.
            
            Ohjelman tehtävänä on muodostaa lähteille SOUR-ryhmät siten. että TITLE-rivit rakennetaan 
            ilman sivunumeroa NOTE-elementissä olevista ryhmistä alkuperäinen NOTE-rivi säilyttäen,
            eli siis lisätä gedcomiin omat SOUR-ryhmät NOTE-rivin toiselle ja 
            sitä seuraaville lähdemäärittelyille. Useaan SOUR-ryhmään jaetut lähteet numeroidaan uudelleen 
            konkatenoimalla alkuperäinen numero ja NOTEsta eristetyn tietoryhmän järjestysnumero. 
            Alkuperäiseen lähteeseen viittaukset täydennetään sivunumerolla PAGE lähteen tunniste tarvittaessa vaihtaen.
            
Ohjelman toiminta:

- Phase 1   Gedcom-aineisto käydään läpi ja kerätään lähteen tunnuskohtaisesti 
            (@Snnnn@) rivinumerot, jotka viittaavat lähteeseen.
            Kunkin lähde-elementin TITLE-rivistä jäsennellään puolipistein 
            erotetut osat, joiden kunkin tulkitaan kuvaavan yhtä lähdettä 
            ja mahdollista viittausta siihen. Jos osasta löytyy sivunumeroon 
            viittaus, se lisätään lähdeviittausrivin jälkeiseksi PAGE-riviksi 
            insertions-dictionaryyn.
            Lähdemäärittelyn alkuperäisen Title-rivin ensimmäisestä osasta 
            muodostetaan sivunumeroton Title-rivi, joka lisätään Title-riviksi 
            replaces-dictionaryyn.
            Mahdollisten muiden osien sisällöistä muodostetaan SOUR- ja 
            TITL-rivit alkuperäisen lähteen NOTE-osan jälkeen lisättäviksi 
            insertions-dictionaryyn.
            
-- Phase 2   Gedcom-aineisto käydään läpi ja jos rivinumero on avaimena jossain 
            dictionaryista, suoritetaan arvo-osassa korvaukset ja/tai lisäykset
 
 Lähteen Note-rivillä määriteltävän viittauksen rakenne on
 
        arkistonpitäjän nimi   ( jos samalla rivillä useampia viittauksia, riittää vain ensimmäisessä)
        lähdetyyppi (vaihtoehtoja RK LK vihityt syntyneet kuolleeet pääkirja F/D)
        alkamisvuosi  (4 numwroa)
        '-' loppumisvuosi  (2 tai 4 numeroa, valinnainen
        sivun ilmaisin  (vaihtoehtoja sivu s s. p p. pg pg.
        sivunumero
        lisäteksti (valinnainen) 
            
    Näitä viittauksia voi kirjoittaa samalle riville useampia puolipisteellä eroteltuina              
 
 
 Esimerkkejä: 
 
    Yksittäinen viittaus lähteessä, yksi viittaaja:
    -----------------------------------------------
        
        0 @I001@ INDI                                                     0 @I001@ INDI
        1 BIRT                                                            1 BIRT
        2 SOUR @S001@                                                     2 SOUR @S001@
                                                                          2 PAGE s.360
                                                                ==>  
        0 @S001@ SOUR                                                     0 @S001@ SOUR
        1 TITL Kiika RK 1841-47                                           1 TITL Kiika RK 1841-47
        1 NOTE Kiika RK 1841-47 p.360                                     1 NOTE Kiika RK 1841-47 p.360
  
    Yksittäinen viittaus lähteessä, useita viittaajia:
    --------------------------------------------------
    
        0 @I001@ INDI                                                    0 @I001@ INDI   
        1 BIRT                                                           1 BIRT
        2 SOUR @S001@                                                    2 SOUR @S001@
                                                                         2 PAGE s.360
  
        0 @I002@ INDI                                                    0 @I002@ INDI   
        1 BIRT                                                           1 BIRT
        2 SOUR @S001@                                                    2 SOUR @S001@
                                                                         2 PAGE s.360  
                                                                                                       
                                                                ==>  
        0 @S001@ SOUR                                                    0 @S001@ SOUR
        1 TITL Kiika RK 1841-47                                          1 TITL Kiika RK 1841-47
        1 NOTE Kiika RK 1841-47 p.360                                    1 NOTE Kiika RK 1841-47 p.360
   
    Useita viittauksia lähteessä, useita viittaajia:
    ------------------------------------------------
 
        0 @I001@ INDI                                                    0 @I001@ INDI   
        1 BIRT                                                           1 BIRT
        2 SOUR @S001@                                                    2 SOUR @S001001@
                                                                         2 PAGE s.360
  
        0 @I002@ INDI                                                    0 @I002@ INDI   
        1 BIRT                                                           1 BIRT
        2 SOUR @S001@                                                    2 SOUR @S001002@
                                                                         2 PAGE s.220 ylin  
                                                                                                       
                                                                ==>   
        0 @S001@ SOUR                                                    0 @S001001@ SOUR
        1 TITL Kiika RK 1841-47                                          1 TITL Kiika RK 1841-47
        1 NOTE Kiika RK 1841-47 p.360 ; LK 1801-88 s 220 ylin            1 NOTE Kiika RK 1841-47 p.360  
                                                                         0 @S001002@ SOUR
                                                                         1 TITL Kiika LK 1801-88
                                                                         1 NOTE Kiika LK 1801-88 s 220 ylin                       
'''

from flask_babelex import _

name = _("Citations in notes")
version = "0.9" 
doclink = "http://taapeli.referata.com/wiki/Lähdeviitteiden_ryhmät_-muunnos"
#output_format = "plain_text"

debugging = False

import logging
# LOG = logging.getLogger(__name__)
# LOG.setLevel(logging.DEBUG)

from bp.gedcom import transformer

 
def add_args(parser):
    pass

def initialize( options):
    return Citations()
  
def parseText(textpart):
    import re  
    regexb = "^([A-ZÅÄÖa-zåäö0-9., ]*?)\s*(RK|LK|vihityt|syntyneet|kuolleet|pääkirja|F\/D)\s*([12][0-9]{3})-?([0-9]{0,4})\s*(.*?)(sivu |s\. |s\.|s |s|p |p\. |p\.|p|pg\. |pg\.|pg |pg)?\s*([0-9]{1,5})?\s*(.*)$"       
#        regexb = "^([A-ZÅÄÖa-zåäö0-9., ]*)\s*(RK|LK|vihityt|syntyneet|pääkirja|F/D)\s*([12][0-9]{3})-?([0-9]{0,4})?\s*(sivu |s\. |s\.|s |s|p |p\. |p\.|p|pg\. |pg\.|pg |pg)?\s*([0-9]{1,4})?\s*(.*)?"  
    """ Groups:
            0   archive name, mandatory at the first citation, optional at following if the same
               white space 
            1   source type
               white space
            2   start year  1nnn or 2nnn   
               optional "-"   
            3   optional end year 2 or 4 digits, mandatory if preceding "-"
               optional white space or text?
            4   page indicator
               optional white space
            5   page number
               white space
            6   optional additional text         
              
    """                

#    regexb = "^([A-ZÅÄÖa-zåäö0-9., ]*)\s*(RK|LK|vihityt|syntyneet|pääkirja|F/D)\s*([A-ZÅÄÖa-zåäö0-9.,]*)\s*([12][0-9]{3})-*([0-9]{0,4})*\s*(.*)\s*(sivu |s\. |s\.|s |s|p |p\. |p\.|p|pg\. |pg\.|pg |pg)\s*([0-9]{1,4})\s*(.*)"     
#    regexa = "^(.+);?\s?(.+);?"
#    regexb = "^([A-ZÅÄÖa-zåäö, ]*)(RK|LK|vihityt|syntyneet|pääkirja|F/D)\s*(1[0-9]{3})-*([0-9]{0,4})([A-ZÅÄÖa-zåäö ]*)(s\s|s\.|s\.\s|p\.|p\. p\s|\.\s|pg\.\s)*([0-9]{1,4})*[A-ZÅÄÖa-zåäö!',/: ]*"        
#    regexc = "^([A-Za-z0-9_\s]+)(RK|LK)\s+(1[0-9]{3})-([0-9]{2,4})\s+(.+)\s+(s\.|p\.)([0-9]{1,4}).*"

    textouts = []
    citations = []
    archiver = ''

    line_parts = re.split(';\s*', textpart) 
#    LOG.debug('>>>>', line_parts)
    for lpart in line_parts:
        if len(lpart) > 0:
#            LOG.debug('    >>>>', lpart)
            if re.match(regexb, lpart):                
                src_groups = re.match(regexb, lpart).groups()
                if debugging: 
                    print("    Parsed: {}  >>>>>>> {}|{}|{}|{}|{}|{}|{}|{}"\
                      .format(lpart, src_groups[0], src_groups[1],src_groups[2], src_groups[3], \
                              src_groups[4] if src_groups[4] else "", \
                              str(src_groups[5]) if src_groups[5] else "", \
                              src_groups[6] if src_groups[6] else "", \
                              src_groups[7] if src_groups[7] else ""))
                                                                            
                endYear = ""    
                if archiver == '': 
                    archiver = src_groups[0].strip()
                if not src_groups[3]:
                    endYear = ""
                elif len(src_groups[3]) == 2:
                    endYear = int(src_groups[2][0:2] + src_groups[3])
                    if endYear < int(src_groups[2]):
                        endYear = endYear + 100
                else:
                    endYear =  int(src_groups[3])       
                textout = "{} {} {}{} {}".format(archiver, src_groups[1], \
                                                 src_groups[2], "-" + str(endYear) if endYear else "", \
                                                 src_groups[4] if src_groups[4] else "") 
                textouts.append(textout)    
                cstring = "{} {}".format(("s." + str(src_groups[6]) if src_groups[6] else ""), src_groups[7].strip() if src_groups[7] else "")
                citations.append(cstring)

            else:
                if debugging: print('    textpart-parser match failed', lpart)    
    return textouts, citations

class Citations(transformer.Transformation):
    twophases = True  
     
    def __init__(self):    

        self.references = {}
        self.insertions = {}
        self.replaces = {}
        self.deletes = {}


    def transform(self, item, options, phase):
        """
        Performs a transformation for the given Gedcom "item" (i.e. "line block")
        Returns one of
        - True: keep this item without changes
        - None: remove the item
        - item: use this item as a replacement (can be the same object as input if the contents have been changed)
        - list of items ([item1,item2,...]): replace the original item with these
        
        This is called for every line in the Gedcom so that the "innermost" items are processed first.
        
        Note: If you change the item in this function but still return True, then the changes
        are applied to the Gedcom but they are not displayed with the --display-changes option.
        """
        
        if phase == 1:
#            print("Phase1 input {} {} {} ".format(str(item.linenum), str(item), item.path))
#             for c1 in item.children:
#                 print("       " + str(c1.linenum) + "  " + str(c1) + "  " + c1.path)  
            path = item.path
#            value = item.value
            slevel = item.level
            linenumber = item.linenum

            if item.level > 0 and path.endswith('.SOUR'):    # SOUR referenced by an element
                spointer = path.split('.', 1)[0]
                spointer = item.value
#                print("Phase1  {} {} {}     SOUR {} referenced".format(str(item.linenum), str(item), item.path, spointer))
                if spointer in self.references:
                    self.references[spointer].append([linenumber, slevel])
                else:    
                    self.references[spointer] = [[linenumber, slevel]]
            elif item.level == 0 and path.endswith('SOUR'):
                spointer = path.split('.', 1)[0] 
                slinenumber = item.linenum
#                print("Phase1  {} {} {}   New SOUR declaration {}, referenced by {}"\
#                    .format(str(item.linenum), item, item.path, item.line, self.references[spointer]))
                ntitletexts = []
                ncitations = []
                tlinenumber = None
                ttext = ntext = ""
                nitem = None
                for child in item.children:
                    linenumber = child.linenum
                    if child.path.endswith('.TITL'): 
                        tlinenumber = child.linenum
#                        print("Phase1  " + str(child.linenum) + "  "  + str(child) + "  " + tpath )    
#                         if child.value == ttext:
#                             print("Phase1  " + str(child.linenum) + "  "  + str(child) + "  " + tpath + "    Tuplan poisto")
#                             self.deletes[tlinenumber] = ttext
#                             return(True)
#                        self.slevel = child.level
                        ttext = child.value
                        ttitletexts, tcitations = parseText(ttext)
#                        print("    -TITL ", ttext, " >>>>>>> ", ttitletexts, " ", tcitations)
                    elif  child.path.endswith('.NOTE'):
#                        print("Phase1  " + str(item.linenum) + "  "  + str(child) + "  " + child.path + "  >>>>>>>  Source Note")
                        nitem = child
                        ntext = child.value
                        ntitletexts, ncitations = parseText(ntext)
#                        print("    -NOTE ", ntext, " >>>>>>> ", ntitletexts, " ", ncitations)

#       Source childs processed, Title and Note found an analyzed   
#                print("{} title elements {} and citations {}".format(spointer, len(ttitletexts), len(tcitations))) 
#                print("{}  note elements {} and citations {}".format(spointer, len(ntitletexts), len(ncitations))) 
#                print("referrers {}".format(len(self.references[spointer])))
                if spointer in self.references.keys():
                    referrers = self.references[spointer]
                    if len(ntitletexts) == 1:
#       One entry                
                        title = "1 TITL {}".format(ntitletexts[0])
                        self.replaces[tlinenumber] = [transformer.Item(title)]
                        for ind in range(0, len(referrers)):
                            if ncitations[0] == " ":
                                continue
                            citation = "{} PAGE ".format(str(referrers[ind][1] + 1)) + ncitations[0]
                            self.insertions[referrers[ind][0]] = [transformer.Item(citation)]
#                            print("    Insert lines after {} {}".\
#                            format(referrers[ind][0], self.insertions[referrers[ind][0]]))   
                    elif len(ntitletexts) > 1:                            
#       Several entries  
                        self.replaces[slinenumber] = []                
                        for ind in range(0, len(ntitletexts)):
                            sourceid = spointer[:-1] + str(ind + 1).zfill(3) + "@"
                            source = "0 {} SOUR".format(sourceid)
                            self.replaces[slinenumber].append(transformer.Item(source))
                            title = "1 TITL {}".format(ntitletexts[ind])
                            self.replaces[slinenumber].append(transformer.Item(title))
                            self.replaces[slinenumber].append(nitem)
                            if ind < len(referrers):
                                sourceref = "{} SOUR {}".format(referrers[ind][1], sourceid)
                                citation = "{} PAGE ".format(str(referrers[ind][1] + 1)) + ncitations[0]
                                self.replaces[referrers[ind][0]] = [transformer.Item(sourceref), transformer.Item(citation)]
#           #                    print("    replace line {} with {}".\
    #       #                           format(referrers[ind][0], self.replaces[referrers[ind][0]]))                        
                                                 
            return(True)   
          
        elif phase == 2:  
            linenumber = item.linenum
            if linenumber in self.deletes:
                try:
#                    print("Line {} deleted ".format(linenumber))
                    return(None)
                except Exception as ex:
                    print(ex)

            if linenumber in self.replaces:
                try:
#                    print("Line {} replaced".format(linenumber))
                    return(self.replaces[linenumber])
                except Exception as ex:
                    print(ex)

            elif linenumber in self.insertions:
                try:
#                    print("Line {} inserted ".format(linenumber))
                    return([item] + self.insertions[linenumber])
                except Exception as ex:
                    print(ex)
            else: 
                return(True)                          

