# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 12.1.2016

import csv
import logging
import time
from models.dbutil import Date
from models.gen.person import Person, Name
from models.gen.event import Event
from models.gen.source_citation import Source, Citation
from models.gen.refname import Refname


def _poimi_(person_id, event_id, row, url):
    """ Poimitaan henkilötiedot riviltä ja palautetaan Person-objektina
    """

    suku=row['Sukunimi_vakioitu']
    etu=row['Etunimi_vakioitu']

    """ Käräjät-tieto on yhdessä sarakkeessa muodossa 'Tiurala 1666.02.20-22'
        Paikka erotetaan ja aika muunnetaan muotoon '1666-02-20 … 22'
        Päivämäärän korjaus tehdään jos kentässä on väli+numero.
        - TODO Pelkää vuosiluku käräjäpaikkana pitäisi siirtää alkuajaksi
     """
    if ' 1' in row['Käräjät']:
        kpaikka, aika = row['Käräjät'].split(' 1')
        aika = Date.range_str('1' + aika)
    else:
        kpaikka, aika = (row['Käräjät'], '')

    # Luodaan henkilö ja käräjätapahtuma

    p = Person(person_id)
    n = Name(etu, suku)
    p.name.append(n)
    p.name_orig = "{0} /{1}/".format(etu, suku)
    p.occupation = row['Ammatti_vakioitu']
    p.place=row['Paikka_vakioitu']

    e = Event(event_id, 'Käräjät')
    e.name = kpaikka
    e.date = aika
    e.name_orig = row['Käräjät']

    c = Citation()
    c.tyyppi = 'Signum'
    c.oid = row['Signum']
    c.url = url
    c.name_orig = row['Signum']
    c.source = Source()
    c.source.nimi = kpaikka + ' ' + aika
    e.citation = c

    p.events.append(e)
    return p


def henkilolista(pathname):
    """ Lukee csv-tiedostosta aineiston, ja luo kustakin 
        syöttörivistä Person-objektit
    """
    persons = []
    row_nro = 0
    url = ''

    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, dialect='excel')

        for row in reader:
            if row_nro == 0:
                logging.debug("Tiedosto " + pathname + ", sarakkeet: " + str(reader.fieldnames))
                if not "Käräjät" in reader.fieldnames:
                    raise KeyError('Sarake "Käräjät" puuttuu: ' + str(reader.fieldnames))
            row_nro += 2
            person_id = row_nro
    
            # Onko otsikkorivi? Tästä url kaikille seuraaville riveille
            if row['Käräjät'][:4] == 'http':
                url = row['Käräjät']
                #logging.debug('%s: url=%s' % (person_id, url))
                continue

            # Onko henkilörivi?
            if row['Sukunimi_vakioitu'] == '' and row['Etunimi_vakioitu'] == '':
                logging.warning('%s: nimikentät tyhjiä!' % person_id)
                continue
                            
            p = _poimi_(row_nro, row_nro+1, row, url)
            persons.append(p)

    logging.info(u'%s: %d riviä' % (pathname, row_nro))
    return (persons)


def datastorer(pathname):
    """ Lukee csv-tiedostosta aineiston, ja tallettaa kustakin syöttörivistä
         Person-objektit sisältäen käräjä-Eventit, Citation-viittaukset ja
         Place-paikat
    """
    row_nro = 0
    url = ''

    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, dialect='excel')

        for row in reader:
            if row_nro == 0:
                logging.debug("Tiedosto " + pathname + ", sarakkeet: " + str(reader.fieldnames))
                if not "Käräjät" in reader.fieldnames:
                    raise KeyError('Sarake "Käräjät" puuttuu: ' + str(reader.fieldnames))
            row_nro += 2
            person_id = row_nro
    
            # Onko otsikkorivi? Tästä url kaikille seuraaville riveille
            if row['Käräjät'][:4] == 'http':
                url = row['Käräjät']
                #logging.debug('%s: url=%s' % (person_id, url))
                continue

            # Onko henkilörivi?
            if row['Sukunimi_vakioitu'] == '' and row['Etunimi_vakioitu'] == '':
                logging.warning('%s: nimikentät tyhjiä!' % person_id)
                continue
                
            p = _poimi_(row_nro, row_nro+1, row, url)
    
            # Tallettaa Person-olion ja siihen sisältyvät Eventit
            # (Person)-[OSALLISTUU]->(Event)
            p.save("User100")

    message ='Talletettu %d riviä tiedostosta %s' % (row_nro, pathname)
    return message


def lue_henkilot(oid=None, names=None, nmax=1000):
    """ Lukee tietokannasta Person- ja Event- objektit näytettäväksi
        
        Palauttaa riveillä listan muuttujia: henkilön tiedot ja lista
        käräjätapahtuman muuttujalistoja
    """
    
    persons = []
    t0 = time.time()
    recs = Person.get_person_events(nmax=nmax, pid=oid, names=names)
    nro = 0
    for rec in recs:
        nro = nro + 1
        # Saatu Person ja collection(Event)
        #Palauttaa riveillä listan muuttujia:
        #n.oid, n.firstname, n.lastname, n.occu, n.place, type(r), events
        #  0      1            2           3       4      5        6
        # 146    Bengt       Bengtsson   soldat   null    OSALLISTUI [[...]]	

        pid = rec['n.id']
        p = Person(pid)
        etu = ""
        suku = ""
        if rec['k.firstname']:
            etu = rec['k.firstname']
        if rec['k.surname']:
            suku = rec['k.surname']
        p.name.append(Name(etu,suku))
#        if rec['n.name_orig']:
#            p.name_orig = rec['n.name_orig']
#         if rec['n.occu']:
#             p.occupation = rec['n.occu']
#         if rec['n.place']:
#             p.place= rec['n.place']

        for ev in rec['events']:
            # 'events' on lista käräjiä, jonka jäseninä on lista muuttujia:
            #[[e.oid, e.kind,  e.name,  e.date,          e.name_orig]...]
            #    0      1        2        3                4
            #[[ 147,  Käräjät, Sakkola, 1669-03-22 … 23, Sakkola 1669.03.22-23]]

            event_id = ev[0]
            if event_id:
                e = Event(event_id, ev[1])
    #             e.name = ev[2]
    #             e.date = ev[3]
    #             e.name_orig = ev[4]
                p.events.append(e)    
    #            logging.info("lue_henkilot: Tapahtuma {}".format(e))

#            c = Citation()
#            c.tyyppi = 'Signum'
#            c.oid = 'Testi3'
#            c.url = url
#            c.source = Source()
#            c.source.nimi = 'Testi3'
#            e.citation = c

        persons.append(p)

    if nro == 0:
        logging.warning("lue_henkilot: ei ketään oid={}, names={}".format(oid, names))
    else:
        logging.info("lue_henkilot: {} henkiloä".format(nro))
        #print ("Lue_henkilot:\n", retList[0])
    logging.debug("TIME lue_henkilot {} sek".format(time.time()-t0))

    return (persons)


def lue_refnames():
    """ Lukee tietokannasta Refname- objektit näytettäväksi
        (n:Refname)-[r]->(m)
    """
    namelist = []
    t0 = time.time()
    recs = Refname.getrefnames()
    for rec in recs:
        namelist.append(rec)

    logging.info("TIME get_refnames {} sek".format(time.time()-t0))

    return (namelist)


def lue_typed_refnames(reftype):
    """ Lukee tietokannasta Refname- objektit näytettäväksi
    """
    namelist = []
    t0 = time.time()
    if not (reftype and reftype != ""):
        raise AttributeError("Mitä referenssityyppiä halutaan?")
    
    recs = Refname.get_typed_refnames(reftype)
# Esimerkki:
# >>> for x in v_names: print(x)
# <Record a.oid=3 a.name='Aabi' a.gender=None a.source='harvinainen' 
#         base=[[2, 'Aapeli', None]] other=[[None, None, None]]>
# <Record a.oid=5 a.name='Aabraham' a.gender='M' a.source='Pojat 1990-luvulla' 
#         base=[[None, None, None]] other=[[None, None, None]]>
# <Record a.oid=6 a.name='Aabrahami' a.gender=None a.source='harvinainen' 
#         base=[[7, 'Aappo', None]] other=[[None, None, None]]>
# >>> for x in v_names: print(x[1])
# Aabrahami
# Aabrami
# Aaca

#a.oid  a.name  a.gender  a.source   base                 other
#                                     [oid, name, gender]  [oid, name, gender]
#-----  ------  --------  --------   ----                 -----
#3493   Aake	F	  Messu- ja  [[null, null, null], [[3495, Aakke, null],
#                         kalenteri   [null, null, null],  [3660, Acatius, null],
#                                     [null, null, null],  [3662, Achat, null],
#                                     [null, null, null],  [3664, Achatius, M],
#                                     [null, null, null],  [3973, Akatius, null],
#                                     [null, null, null],  [3975, Ake, null],
#                                     [null, null, null]]  [3990, Akke, null]]
#3495   Aakke   null     harvinainen [[3493, Aake, F]]    [[null, null, null]]

    for rec in recs:
#        logging.debug("oid={}, name={}, gender={}, source={}, base={}, other={}".\
#               format( rec[0], rec[1],  rec[2],    rec[3],    rec[4],  rec[5]))
        # Luodaan nimi
        r = Refname(rec['a.name'])
        r.oid = rec['a.id']
        if rec['a.gender']:
            r.gender = rec['a.gender']
        if rec['a.source']:
            r.source= rec['a.source']

        # Luodaan mahdollinen kantanimi, johon tämä viittaa (yksi?)
        baselist = []
        for fld in rec['base']:
            if fld[0]:
                b = Refname(fld[1])
                b.oid = fld[0]
                if fld[2]:
                    b.gender = fld[2]
                baselist.append(b)

        # Luodaan lista muista nimistä, joihin tämä viittaa
        otherlist = []
        for fld in rec['other']:
            if fld[0]:
                o = Refname(fld[1])
                o.oid = fld[0]
                if fld[2]:
                    o.gender = fld[2]
                otherlist.append(o)

        namelist.append((r,baselist,otherlist))
    
    logging.info("TIME get_named_refnames {} sek".format(time.time()-t0))

    return (namelist)


def get_people_by_surname(surname):
    people = []
    result = Name.get_people_with_surname(surname)
    for record in result:
        handle = record['handle']
        p = Person()
        p.handle = handle
        p.get_person_and_name_data()
        people.append(p)
        
    return (people)
        
        
