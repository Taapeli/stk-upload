# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 12.1.2016

import csv
import logging
from models.genealogy import *  # Tietokannan luokat

def dateformatter(aika):
    """ Aika esim. '1666.02.20-22' muunnetaan muotoon '1666-02-20 … 22':
        * Tekstin jakaminen sarakkeisiin käyttäen välimerkkiä ”-” 
          tai ”,” (kentät tekstimuotoiltuna)
        * Päivämäärän muotoilu ISO-muotoon vaihtamalla erottimet 
          ”.” viivaksi
     """
    t = '1' + aika.replace('-','|').replace(',','|') 
    if '|' in t:
        osat = t.split('|')
        # osat[0] olkoon tapahtuman 'virallinen' päivämäärä
        t = '%s … %s' % (osat[0], osat[-1])
        if len(osat) > 2:
            logging.warning('%s: aika korjattu (%s) -> %s' % \
                (person_id, row['Käräjät'], t))

    t = t.replace('.', '-')
    return t;
    
            
def henkilolista(pathname):
    """ Lukee csv-tiedostosta aineiston listaan, niin että kustakin 
        syöttörivistä talletetaan dictionary listaan
    """
    rivit = []
    row_nro = 0;
    url = '';

    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, dialect='excel')
        if not "Käräjät" in reader.fieldnames:
            raise KeyError('sarake "Käräjät" puuttuu: ' + str(reader.fieldnames))

        for row in reader:
            row_nro += 1
            person_id = (u'P%06d' % row_nro)

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

            if etu == '': etu = 'N'
            if suku == '': suku = 'N'

            """ Käräjät-tieto on yhdessä sarakkeessa muodossa 'Tiurala 1666.02.20-22'
                Paikka erotetaan ja aika muunnetaan muotoon '1666-02-20 … 22'
                Päivämäärän korjaus tehdään jos kentässä on väli+numero.
                - TODO Pelkää vuosiluku käräjäpaikkana pitäisi siirtää alkuajaksi
             """
            if ' 1' in row['Käräjät']:
                kpaikka, aika = row['Käräjät'].split(' 1')
                aika = dateformatter(aika)
            else:
                kpaikka, aika = (row['Käräjät'], '')

            # Luodaan rivitieto tulostettavaksi
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


def referenssinimet(pathname):
    """ Lukee csv-tiedostosta referenssinimet
        Syöte: ['Nimi', 'RefNimi', 'On_itse_refnimi', 'Lähde', 'Sukupuoli']
    """
    rivit = []
    row_nro = 0
    tyhjia = 0

    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        hei='vaan'
        reader=csv.reader(f, dialect='excel')
        # Tarkastetaan ja ohitetaan otsikkorivi
        row = reader.__next__()
        if row.__len__ != 5 and row[1] != "RefNimi":
            raise KeyError('Väärät sarakeotsikot: ' + str(row))
       
        for row in reader:
            row_nro += 1
            rid = (u'R%04d' % row_nro)
            nimi=row[0].strip()
            if row[0].__len__() == 0:
                tyhjia += 1
                continue # Tyhjä nimi ohitetaan
            
            ref=row[1]
            on_ref=(row[2].lower().startswith('k'))
            source=row[3]
            if row[4].startswith('m'):
                sp = 'M'
            else:
                if row[4].startswith('n'):
                    sp = 'F'
                else:
                    sp = ''

            # Luodaan rivitieto tulostettavaksi
            rivi = dict( \
                id=rid, \
                nimi=nimi, \
                refnimi=ref, \
                onref=on_ref, \
                source=source, \
                sp=sp )
            rivit.append(rivi)
    
    logging.info(u'%s: %d riviä, %d tyhjää' % (pathname, row_nro, tyhjia))
    return (rivit)

# Testaa referenssinimet
# python3 models/datareader.py tiedosto.csv > lst

import sys
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Käyttö: " + sys.argv[0] + " tiedosto.csv", file=sys.stderr)
        exit(1)
        
    rivit = referenssinimet(sys.argv[1])
    n=0
    for r in rivit:
        print("{0}: {1:20s}{2:20s}{3} {4:1s} ({5:s})".format( r['id'],
            r['nimi'], r['refnimi'], r['onref'], r['sp'], r['source']) )
