# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 27.1.2016

import csv
import logging

from models.gen.refname import Refname  # Tietokannan kaikki luokat

def load_refnames(pathname):
    """ Reads reference names from a local csv file. 
        The first row must have the required column names (in any order).
        These column names in the row 1 are:
        - Name
        - Refname
        - Reftype    (surname / firstname / patronyme)
        - Gender    (M = male, N,F = female, empty = undefined)
        - Source    (source name)
    """
    row_nro = 0
    empties = 0
    
    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        reader=csv.DictReader(f, dialect='excel')
        for row in reader:
            row_nro += 1
            try:
                nimi=row['Name'].strip()
                if len(nimi) == 0:
                    empties += 1
                    continue # Skip a row without name

                refname=row['Refname']
                reftype=row['Reftype']
                source=row['Source']
                gd = row['Gender'].lower()
            except KeyError:
                raise KeyError('Not valid fields {}'.format(row.keys()))

            if gd.startswith('m'):
                sex = 'M'
            elif gd.startswith('n') or  gd.startswith('f'):
                sex = 'F'
            else:
                sex = ''

            # Luodaan Refname
            r = Refname(nimi)
            if (refname != '') and (refname != nimi):
                # Tullaan viittaamaan tähän nimeen
                #r.mark_reference(refname, 'REFFIRST')
                # Laitetaan muistiin, että self viittaa refname'een
                if reftype in r.REFTYPES:
                    r.refname = refname
                    r.reftype = reftype
                    logging.debug("cvs_refnames: {0} --> {1}".format(nimi, refname))
                else:
                    logging.warning('cvs_refnames: Invalid reference {} discarded. '.\
                                    format(reftype))
            if sex != '':
                r.gender = sex
            if source != '':
                r.source = source

            """
            Saves a Refname object and possible connection to another reference name:
            (a:Refname {name:'Name'}) -[r:Reftype]-> (b:Refname {name:'Refname'})
            """
            r.save()

    msg = '{0}: {1} rows, {2} skipped'.format(pathname, row_nro, empties)
    logging.info(msg)
    return (msg)

