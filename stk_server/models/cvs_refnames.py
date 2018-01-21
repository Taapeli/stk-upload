# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 27.1.2016

import csv
import logging

from models.gen.refname import Refname  # Tietokannan kaikki luokat

def referenssinimet(pathname, colA=None, colB=None, maxrows=0):
    """ Lukee csv-tiedostosta referenssinimet. 
        Ensimmäisellä rivillä pitää olla sarakkeiden nimet 'Nimi', 'RefNimi', 
        'On_itse_refnimi', 'Lähde', 'Sukupuoli' (halutussa järjestyksessä).
        Kenttä On_itse_refnimi ei ole käytössä.

        Jos colA on määrittelemättä, lataisi vain tiedoston alun niin että 
        voidaan esittää käyttäjälle sarakkeiden valintasivu
        
        Syötteen 1. rivi: ['Nimi', 'RefNimi', 'Reftype', 'Lähde', 'Sukupuoli']
                            0       1          2          3        4 ('M'/'N'/'')
    """
    # TODO: miksi otettaisiin colA ja colB käyttöön?
    if colA:
        # Luetaan cvs-tiedoston kaikki kentät, maxrows maxrows riviä
        maxrows=50
        return list()
    
    row_nro = 0
    tyhjia = 0
    
    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        reader=csv.DictReader(f, dialect='excel')
        for row in reader:
            row_nro += 1
            if maxrows > 0 and row_nro > maxrows:
                break
            nimi=row['Nimi'].strip()
            if len(nimi) == 0:
                tyhjia += 1
                continue # Tyhjä nimi ohitetaan

            try:
                refname=row['RefNimi']
                reftype=row['Reftype']
            except KeyError:
                raise

            source=row['Lähde']
            if row['Sukupuoli'].lower().startswith('m'):
                sp = 'M'
            elif row['Sukupuoli'].lower().startswith('n'):
                sp = 'F'
            else:
                sp = ''

            # Luodaan Refname
            r = Refname(nimi)
            if (refname != '') and (refname != nimi):
                # Tullaan viittaamaan tähän nimeen
                #r.mark_reference(refname, 'REFFIRST')
                # Laitetaan muistiin, että self viittaa refname'een
                if reftype in r.REFTYPES:
                    r.refname = refname
                    r.reftype = reftype
                    logging.debug("cvs_refnames: {0} <-- {1}".format(nimi, refname))
                else:
                    logging.warning('cvs_refnames: Referenssinimen viittaus {} hylätty. '.format(reftype))
            if sp != '':
                r.gender = sp
            if source != '':
                r.source = source

            """
            Tallettaa Refname-olion ja mahdollisen yhteyden referenssinimeen:
            
            (a:Refname {nimi='Nimi'}) -[r:Reftype]-> (b:Refname {nimi='RefNimi'})
            """
            r.save()

    msg = '{0}: {1} riviä, {2} ohitettu'.format(pathname, row_nro, tyhjia)
    if maxrows > 0 and row_nro > maxrows:
        msg = msg + ". KATKAISTU {0} nimen kohdalta".format(maxrows)
    logging.info(msg)
    return (msg)

