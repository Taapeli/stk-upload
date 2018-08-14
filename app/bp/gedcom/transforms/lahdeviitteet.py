#!/usr/bin/env python3
'''
Muodostaa yhdistetyistä lähdeviitteistä nimetyt lähteet ja sivunumerot 

Created on 17.2.2017

@author: TimNal

Ohjelman perusteet:

            Brothers Keeper -ohjelmalla tuotetussa gedcom-aineistossa on 
            viittauksia lähteisiin. Lähteiden määrittelyissä on
            Title-elementteihin kerätty yhden tai useamman lähteen nimet ja 
            mahdollinen sivunumeroviittaukset puolipisteillä eroteltuna.
            
            Ohjelman tehtävänä on muodostaa lähteille nimet ilman sivunumeroa 
            ja lisätä gedcomiin omat lähde-elementit Title-rivin toiselle ja 
            sitä seuraaville lähdemäärittelyille.
            
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
            
- Phase 2   Ei toimintaa

- Phase 3   Gedcom-aineisto käydään läpi ja jos rivinumero on avaimena jossain 
            dictionaryista, suoritetaan arvo-osassa korvaukset ja/tai lisäykset
             
'''

#!/usr/bin/python

version = "0.9" 

import re
import logging
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

intag = False
linenumber = 0
xsourcenumber = 1000  
references = {}
spointer = ''
slevel = 0
ttext = ''
ntext = ''                 



def add_args(parser):
    pass

def initialize(run_args):
    pass

regexb = "^([A-ZÅÄÖa-zåäö., ]*)(RK|LK|vihityt|syntyneet|pääkirja|F/D)\s*(1[0-9]{3})-([0-9]{0,4})\s*([A-ZÅÄÖa-zåäö,]*)\s*(sivu |s\. |s\.|s |s|p |p\. |p\.|pg\. |pg\.|pg |pg)([0-9]{1,4})*(.*)"        
#regexb = "^([A-ZÅÄÖa-zåäö, ]*)(RK|LK|vihityt|syntyneet|pääkirja|F/D)\s*(1[0-9]{3})-([0-9]{0,4}) ([A-ZÅÄÖa-zåäö, ]*)(s|s |s\.|s\. |p|p |p\.|p\. |pg |pg\.|pg\. )([0-9]{1,4})*([A-ZÅÄÖa-zåäö0-9!',/: ]*)"        

insertions = {}
replaces = {}
deletes = {}

def parseText(textpart):
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
                print('Parsed: ' + src_groups[0] + '/' + src_groups[1] + '/' \
                      + src_groups[2] + '/' + src_groups[3] + '/' \
                      + src_groups[4] + '/' + src_groups[5] + '/' \
                      + str(src_groups[6]) + '/' + str(src_groups[7]))
                if archiver == '': 
                    archiver = src_groups[0]
                textout = archiver + src_groups[1] + ' ' + src_groups[2] 
                if src_groups[3]:
                    textout = textout + '-' + src_groups[3]
                textouts.append(textout)    
                cstring = 's.' + str(src_groups[6])
                citations.append(cstring)
#                for part in src_groups:
#                    src_parts.append(part)
#                LOG.debug(src_parts)
#                 if len(src_parts[3]) == 2:
#                     endYear = int(src_parts[2][0:2] + src_parts[3])
#                     if endYear < int(src_parts[2]):
#                         endYear = endYear + 100
#                     src_parts[3] =str(endYear)
            else:
                print('    textpart-parser match failed', lpart)    
    return(textouts, citations)

#                
# Phase 1: Process the GEDCOM line
#

def phase1(run_args, gedline):
#    for element in element_list: (gedline)
    global linenumber
    global insertions
    global replaces
    global deletes 
    global ttext
    global spointer
    global slevel
    global xsourcenumber
    path = gedline.path
    value = gedline.value
#    linenumber = gedline.1inenum
    if path.startswith('HEAD'):
        return
    elif gedline.level > 0 and path.endswith('.SOUR'):    # SOUR referenced by an element
        pointer = gedline.value
        slevel = gedline.level
        if pointer in references:
            references[pointer].append(linenumber)
        else:    
            references[pointer] = [linenumber]
#            insertions[linenumber] = [pointer]
    elif gedline.level == 0 and value == 'SOUR':
        spointer = gedline.path 
        print("    New SOUR declaration {}, referenced by {}".\
              format(gedline.line, references[spointer]))
                           
    elif path.startswith('@S') and path.endswith('.TITL'):
        if gedline.value == ttext:
            LOG.debug("    Tuplan poisto", ttext)
            deletes[linenumber] = ttext
        ttext = gedline.value
        referrers = references[spointer]
        result = parseText(ttext)
        textouts = result[0]
        citations = result[1]
        print("    -TITL ", ttext, " ", textouts, " ", citations)
        if textouts:
            replaces[linenumber] = str(gedline.level) + ' ' + gedline.tag \
            + ' ' + gedline.value + ' ' + textouts[0]
        if citations:
            for ind in range(0, len(referrers)):
                citation = "{} PAGE ".format(str(slevel + 1)) + citations[0]
                insertions[referrers[ind]] = [citation]
                print("    Insert lines after {} {}".\
                      format(referrers[ind], insertions[referrers[ind]]))    
        if len(textouts) > 1:
            insertions[linenumber+1] = []
            for ind in range(1, len(textouts)):
                xsourcenumber +=1
                sline = '0  @S{}@ SOUR'.format(xsourcenumber)
                insertions[linenumber+1].append(sline)
                tline = '1 TITL  ' + textouts[ind]
                insertions[linenumber+1].append(tline)
                insertions[linenumber+1].append('1 NOTE  ' + textouts[ind])
                print("    Insert lines after {} {}".\
                      format(linenumber+1, insertions[linenumber+1]))
#            ttext = '' 
 
    elif path.startswith('@S') and path.endswith('.NOTE'):
        ntext = gedline.value
        if ttext != ntext:
            print("-NOTE ", ntext, " ", spointer)
            ntextout, ncitations = parseText(ntext)
            print("    -NOTE ", ntext, " ", ntextout, " ", ncitations, spointer)
        ttext = ''
        ntext = ''
        
    else:
#        spointer = ''
        slevel = 0
        ttext = ''
        ntext = ''    

#                
# Phase 2: None
#

def phase2(run_args):
    global linenumber
    linenumber = 0
    print(references)    

#                
# Phase 3: Build the resulting GEDCOM 
#

def phase3(run_args, gedline, f):
#     path = gedline.path
#     value = gedline.value
 
#     output = open(fout, 'w',  encoding='utf-8-sig')
#     linenumber = 0
#     for element in element_list:
    global linenumber
    global insertions
    global replaces
    global deletes 
    line = gedline.line
    linenumber += 1
    if linenumber in deletes:
        return
    #=======================================================================
    # element_out = str(gedline.level) + ' ' + gedline.tag + ' '
    # if element.pointer() != '':
    #     element_out = element_out + element.pointer() + ' '
    # element_out = element_out + gedline.value
    #=======================================================================
    if linenumber in replaces:
        f.emit(replaces[linenumber])
    else: 
        f.emit(line)
        #===================================================================
        # if gedline.level == 0: 
        #     gedline.emit(str(gedline.level) + ' ' + element.pointer() + ' ' + gedline.tag + ' ' + gedline.value)
        # else:
        #     gedline.emit(str(gedline.level) + ' ' + gedline.tag + ' ' + element.pointer() + ' ' + gedline.value)
        #===================================================================
    if linenumber in insertions:
        for element in insertions[linenumber]:
            f.emit(element)
                   

# if __name__ == '__main__':
#     sys.exit(main(['parsertester', 'C:/Temp/', 'lahtinen_olli_2017-02-14_osa_u_val.ged', 'lahtinen_out.ged']))