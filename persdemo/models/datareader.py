# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 12.1.2016

import csv
import logging
from models.genealogy import *  # Tietokannan luokat

           
def henkilolista(pathname):
    """ Lukee csv-tiedostosta aineiston, ja luo kustakin 
        syöttörivistä Person- ja Event- objektit
    """
    persons = []
    events = {}
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
            person_id = Person.make_id(row_nro)

            # Onko otsikkorivi? Tästä url kaikille seuraaville riveille
            if row['Käräjät'][:4] == 'http':
                url = row['Käräjät']
                #logging.debug('%s: url=%s' % (person_id, url))
                continue

            # Onko henkilörivi?
            suku=row['Sukunimi_vakioitu']
            etu=row['Etunimi_vakioitu']
            if suku == '' and etu == '':
                logging.warning('%s: nimikentät tyhjiä!' % person_id)
                continue

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
            p.ammatti = row['Ammatti_vakioitu']
            p.paikka=row['Paikka_vakioitu']
            event_id = u'E%06d' % row_nro
            p.events.append(event_id)   # Viittaukset tapahtumiin
            
            e = Event(event_id, 'Käräjät')
            e.nimi = kpaikka
            e.aika = aika
            
            c = Citation()
            c.tyyppi = 'Signum'
            c.id = row['Signum']
            c.url = url
            c.source = Source()
            c.source.nimi = kpaikka + ' ' + aika
            e.citation = c
            
            persons.append(p)
            events[event_id] = e

    logging.info(u'%s: %d riviä' % (pathname, row_nro))

    return ((persons, events))

def datastorer(pathname):
    """ Lukee csv-tiedostosta aineiston kantaan
    """
    message = "Pitäisi toteuttaa henkilölistan tapaan, " + \
              "mutta luetut objektit talletetaan kantaan eikä taulukkoihin"
    
    return message

def lue_henkilot():
    """ Lukee tietokannasta Person- ja Event- objektit näytettäväksi
    """
    persons = []
    events = {}
    row_nro = 0
    url = ''

    # Toteutetaan henkilölistan tapaan, mutta objektit luetaan kannasta
    
    return ((persons, events))
