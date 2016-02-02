# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 27.1.2016

import csv
import logging

from models.genealogy import *  # Tietokannan kaikki luokat ja apuluokkia

def referenssinimet(pathname):
    """ Lukee csv-tiedostosta referenssinimet
        Syötteen 1. rivi: ['Nimi', 'RefNimi', 'On_itse_refnimi', 'Lähde', 'Sukupuoli']
                            0       1          2 boolean          3        4 ('M'/'N'/'')
    """
    rivit = []
    row_nro = 0
    tyhjia = 0
    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        reader=csv.DictReader(f, dialect='excel')
        
#        if row.__len__ != 5 and row[1] != "RefNimi":
#            raise KeyError('Väärät sarakeotsikot: ' + str(row))

        for row in reader:
            row_nro += 1
            rid = make_id('R', row_nro)
            nimi=row['Nimi'].strip()
            if nimi.__len__() == 0:
                tyhjia += 1
                continue # Tyhjä nimi ohitetaan

            try:
                ref=row['RefNimi']
            except KeyError as e:
                raise

            on_ref=(row['On_itse_refnimi'].lower().startswith('k'))
            source=row['Lähde']
            if row['Sukupuoli'].startswith('m'):
                sp = 'M'
            else:
                if row['Sukupuoli'].startswith('n'):
                    sp = 'F'
                else:
                    sp = ''

            # Luodaan Refname
            inst = Refname(rid, 'fname', nimi)
            if ref != '':
                inst.setref(ref, 'refname')
            inst.is_ref = on_ref
            if sp != '':
                inst.gender = sp
            if sp != '':
                inst.source = source
                
            rivit.append(inst)

    logging.info(u'%s: %d riviä, %d tyhjää' % (pathname, row_nro, tyhjia))
    return (rivit)


# Testaa referenssinimet
# python3 models/datareader.py tiedosto.csv > lst

import sys
if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Käyttö: " + sys.argv[0] + " tiedosto.csv", file=sys.stderr)
        exit(1)
    
    try:
        rivit = referenssinimet(sys.argv[1])
        for r in rivit:
            print("{0}: {1:20s}{2:20s}{3} {4:1s} ({5:s})".format( r['id'],
                r['nimi'], r['refnimi'], r['onref'], r['sp'], r['source']) )
    except KeyError as e:
        print ("Väärät sarakeotsikot, tämä puuttuu: " + str(e))
