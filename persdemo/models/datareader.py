# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 12.1.2016

import csv
import logging
import time
from models.genealogy import *  # Tietokannan luokat

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
    p.name = Name(etu, suku)
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
            row_nro += 1
    
            # Onko otsikkorivi? Tästä url kaikille seuraaville riveille
            if row['Käräjät'][:4] == 'http':
                url = row['Käräjät']
                #logging.debug('%s: url=%s' % (person_id, url))
                continue

            # Onko henkilörivi?
            if row['Sukunimi_vakioitu'] == '' and row['Etunimi_vakioitu'] == '':
                logging.warning('%s: nimikentät tyhjiä!' % person_id)
                continue
                            
            p = _poimi_(row_nro, row, url)
            persons.append(p)

    logging.info(u'%s: %d riviä' % (pathname, row_nro))
    return (persons)


def datastorer(pathname):
    """ Lukee csv-tiedostosta aineiston, ja tallettaa kustakin 
        syöttörivistä Person-objektit
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
            row_nro += 1
    
            # Onko otsikkorivi? Tästä url kaikille seuraaville riveille
            if row['Käräjät'][:4] == 'http':
                url = row['Käräjät']
                #logging.debug('%s: url=%s' % (person_id, url))
                continue

            # Onko henkilörivi?
            if row['Sukunimi_vakioitu'] == '' and row['Etunimi_vakioitu'] == '':
                logging.warning('%s: nimikentät tyhjiä!' % person_id)
                continue
                
            person_id = get_new_oid()
            event_id = get_new_oid()
            
            p = _poimi_(person_id,  event_id, row, url)
    
            # Tallettaa Person-olion ja siihen sisältyvät Eventit
            # (Person)-[OSALLISTUU]->(Event)
            p.save()

    message ='Talletettu %d riviä tiedostosta %s' % (row_nro, pathname)
    return message

def lue_henkilot(oid=None, names=None, max=1000):
    """ Lukee tietokannasta Person- ja Event- objektit näytettäväksi
        
        Jos oid on annettu, luetaan vain se henkilö, jonka oid täsmää
    """    
    persons = []
    t0 = time.time()
    retList = Person.get_person_events(max=max, pid=oid, names=names)
    if len(retList.records) == 0:
        logging.warning("lue_henkilot: ei ketään oid={}, names={}".format(oid, names))
    else:
        logging.info("lue_henkilot: {} henkiloä".format(len(retList.records)))
        #print ("Lue_henkilot:\n", retList[0])
    
    for row in retList:
        # Saatu Person ja collection(Event)
        thisPerson, theseEvents = row
        pid = thisPerson.properties['oid']
        p = Person(pid)
        etu = thisPerson.properties['firstname']
        suku = thisPerson.properties['lastname']
        p.name = Name(etu,suku)
        p.name_orig = thisPerson.properties['name_orig']
        p.occupation = thisPerson.properties['occu']
        p.place= thisPerson.properties['place']

#        logging.info("lue_henkilot: Person {}, {} tapahtumaa".format(pid, 
#            len(theseEvents)))
        for gotEvent in theseEvents:
            event_id = gotEvent.properties['oid']
            e = Event(event_id, 'Käräjät')
            e.name = gotEvent.properties['name']
            e.date = gotEvent.properties['date']
            e.name_orig = gotEvent.properties['name_orig']
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

    logging.debug("TIME lue_henkilot {} sek".format(time.time()-t0))

    return (persons)


def lue_refnames():
    """ Lukee tietokannasta Refname- objektit näytettäväksi
    """
    namelist = []
    t0 = time.time()
    v_names = Refname.getrefnames()
    
    for n,f,m in v_names:
#>>> n
#<Node graph='http://localhost:7474/db/data/' ref='node/24610' labels={'Refname'} 
#   properties={'oid': 123, 'name': 'Aabeli'}>
#>>> f
#<Relationship graph='http://localhost:7474/db/data/' ref='relationship/10737' 
#   start='node/24610' end='node/24611' kind='REFFIRST' properties={}>
#>>> m
#<Node graph='http://localhost:7474/db/data/' ref='node/24611' labels={'Refname'} 
#   properties={'oid': 124, 'name': 'Aapeli'}>

        logging.debug("n=" + str(n) + "--> m=" + str(m))
        r = Refname(n.properties['name'])
        r.oid = n.properties['oid']
        r.gender = n.properties['gender']
        r.source= n.properties['source']
        
        if f:
            r.reftype = f.type
            r.refname = m.properties['name']
        
        namelist.append(r)

    logging.info("TIME get_refnames {} sek".format(time.time()-t0))

    return (namelist)

def lue_typed_refnames(reftype):
    """ Lukee tietokannasta Refname- objektit näytettäväksi
    """
    namelist = []
    t0 = time.time()
    if not (reftype and reftype != ""):
        raise AttributeError("Mitä referenssityyppiä halutaan?")
    
    v_names = Refname.get_typed_refnames(reftype)
    
    for oid, name, gender, source, names in v_names:
#        logging.debug("lue_typed_refnames: oid={}, name='{}', names={}".format(oid, name, names))
        r = Refname(name)
        r.oid = oid
        if gender:
            r.gender = gender
        if source:
            r.source= source        
        namelist.append((r,names))
    
    logging.info("TIME get_named_refnames {} sek".format(time.time()-t0))

    return (namelist)
