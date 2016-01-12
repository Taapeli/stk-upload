# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 12.1.2016

import csv
import logging

def henkilolista(pathname):
    """ Lukee csv-tiedostosta aineiston listaan, niin että kustakin 
        syöttörivistä talletetaan dictionary
    """
    rivit = []
    row_nro = 0;
    url = '';

    with open(pathname, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_nro += 1
            person_id = (u'P%06d' % row_nro)

            # Onko otsikkorivi? Tästä url kaikille seuraaville riveille
            if row['Käräjät'][:4] == 'http':
                url = row['Käräjät']
                logging.debug('%s: url=%s' % (person_id, url))
                continue

            # Onko henkilörivi?
            suku=row['Sukunimi_vakioitu']
            etu=row['Etunimi_vakioitu']
            if suku == '' and etu == '':
                continue

            if etu == '': etu = 'N'
            if suku == '': suku = 'N'

            """ Käräjät-tieto on yhdessä sarakkeessa muodossa 'Tiurala 1666.02.20-22'
                Paikka erotetaan ja aika muunnetaan muotoon '1666-02-20 … 22'
            """
            if ' 1' in row['Käräjät']:
                kpaikka, aika = row['Käräjät'].split(' 1')
                aika = '1' + aika.replace('-','|').replace(',','|') 
                if '|' in aika:
                    osat = aika.split('|')
                    # osat[0] olkoon tapahtuman 'virallinen' päivämäärä
                    aika = '%s … %s' % (osat[0], osat[-1])
                    if len(osat) > 2:
                        logging.warning('%s: aika korjattu (%s) -> %s' % \
                            (person_id, row['Käräjät'], aika))
  
                aika = aika.replace('.', '-')
            else:
                kpaikka, aika = (row['Käräjät'], '')

            rivi = dict( \
                id=person_id, \
                etunimi=etu, \
                sukunimi=suku, \
                ammatti=row['Ammatti_vakioitu'], \
                paikka=row['Paikka_vakioitu'], \
                kpaikka=kpaikka, \
                kaika=aika, \
                signum=row['Signum'],
                url=url \
            )
            rivit.append(rivi)
    
    logging.info(u'%s: %d riviä' % (pathname, row_nro))

    return (rivit)
