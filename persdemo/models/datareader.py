# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 12.1.2016

import csv
import logging
import time
from models.genealogy import *  # Tietokannan luokat

def _poimi_(row_nro, row, url):
    """ Poimitaan henkilötiedot riviltä ja palautetaan Person-objektina
    """
    person_id = Person.make_id(row_nro)
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

    event_id = u'E%06d' % row_nro
    e = Event(event_id, 'Käräjät')
    e.name = "{0}\t{1}".format(kpaikka, aika)
    e.date = aika
    e.name_orig = row['Käräjät']

    c = Citation()
    c.tyyppi = 'Signum'
    c.id = row['Signum']
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
                
            p = _poimi_(row_nro, row, url)
    
            # Tallettaa Person-olion ja siihen sisältyvät Eventit
            # (Person)-[OSALLISTUU]->(Event)
            p.save()

    message ='Talletettu %d riviä tiedostosta %s' % (row_nro, pathname)
    return message

def lue_henkilot(id=None, names=None):
    """ Lukee tietokannasta Person- ja Event- objektit näytettäväksi
        
        Jos id on annettu, luetaan vain se henkilö, jonka id täsmää
    """
    # TODO: Poista määrän rajoitus max=100
    
    persons = []
    t0 = time.time()
    retList = Person.get_person_events(max=100, pid=id, names=names)
    #print ("Lue_henkilot:\n", retList[0])
    
    for row in retList:
        thisPerson, theseEvents = row
        pid = thisPerson.properties['id']
        p = Person(pid)
        etu = thisPerson.properties['firstname']
        suku = thisPerson.properties['lastname']
        p.name = Name(etu,suku)
        p.name_orig = thisPerson.properties['name_orig']
        p.occupation = thisPerson.properties['occu']
        p.place= thisPerson.properties['place']

        for gotEvent in theseEvents:
            event_id = gotEvent.properties['id']
            e = Event(event_id, 'Käräjät')
            e.name = gotEvent.properties['name']
            e.date = gotEvent.properties['date']
            e.name_orig = gotEvent.properties['name_orig']
            p.events.append(e)    

#            c = Citation()
#            c.tyyppi = 'Signum'
#            c.id = 'Testi3'
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
#   properties={'id': 'R00001', 'name': 'Aabeli', 'type': 'fname'}>
#>>> f
#<Relationship graph='http://localhost:7474/db/data/' ref='relationship/10737' 
#   start='node/24610' end='node/24611' type='REFFIRST' properties={}>
#>>> m
#<Node graph='http://localhost:7474/db/data/' ref='node/24611' labels={'Refname'} 
#   properties={'id': 'R100001', 'name': 'Aapeli', 'type': 'fname'}>

        #logging.debug("n=" + n.__str__())
        #logging.debug("--> m=" + m.__str__())
        rid = n.properties['id']
        r = Refname(rid)
        r.type = n.properties['type']
        r.name = n.properties['name']
        #logging.debug("** name={}, is_ref={}".format(r.name, n.properties['is_ref']))
        r.is_ref = n.properties['is_ref']    # näinkö?
        r.gender = n.properties['gender']
        r.source= n.properties['source']
        
        if f:
            r.reftype = f.type
            r.refname = m.properties['name']
        
        namelist.append(r)

    logging.info("TIME get_refnames {} sek".format(time.time()-t0))

    return (namelist)
