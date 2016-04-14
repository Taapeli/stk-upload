# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 27.1.2016

import csv
import logging

from models.genealogy import *  # Tietokannan kaikki luokat ja apuluokkia

def referenssinimet(pathname, colA=None, colB=None, max=0):
    """ Lukee csv-tiedostosta referenssinimet
        Jos colA on määrittelemättä, lataa vain tiedoston alun niin että 
        voidaan esittää käyttäjälle sarakkeiden valintasivu
        
        Syötteen 1. rivi: ['Nimi', 'RefNimi', 'On_itse_refnimi', 'Lähde', 'Sukupuoli']
                            0       1          2 boolean          3        4 ('M'/'N'/'')
    """
    # TODO: colA ja colB käyttöön!
    if colA:
        # Luetaan cvs-tiedoston kaikki kentät, max maxrows riviä
        maxrows=50
        return list()
    
    row_nro = 0
    tyhjia = 0
    
    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        reader=csv.DictReader(f, dialect='excel')
        
#        if row.__len__ != 5 and row[1] != "RefNimi":
#            raise KeyError('Väärät sarakeotsikot: ' + str(row))

        for row in reader:
            row_nro += 1
            if max > 0 and row_nro > max:
                break
            nimi=row['Nimi'].strip()
            if nimi.__len__() == 0:
                tyhjia += 1
                continue # Tyhjä nimi ohitetaan

            try:
                ref_name=row['RefNimi']
            except KeyError:
                raise

            on_ref=(row['On_itse_refnimi'].lower().startswith('k'))
            source=row['Lähde']
            if row['Sukupuoli'].startswith('m'):
                sp = 'M'
            elif row['Sukupuoli'].startswith('n'):
                sp = 'F'
            else:
                sp = ''

            # Luodaan Refname
            r = Refname(nimi)
            if ref_name != '':
                # Tullaan viittaamaan tähän nimeen
                r.mark_reference(ref_name, 'REFFIRST')
            if sp != '':
                r.gender = sp
            if sp != '':
                r.source = source
                
            # Tallettaa Refname-olion ja mahdollisen yhteyden referenssinimeen
            # (a:Refname {nimi='Nimi'})
            #   -[r:Reftype]->
            #   (b:Refname {nimi='RefNimi'})
            r.save()

    msg = '{0}: {1} riviä, {2} ohitettu'.format(pathname, row_nro, tyhjia)
    if max > 0:
        msg = msg + ". KATKAISTU {0} nimen kohdalta".format(max)
    logging.info(msg)
    return (msg)

