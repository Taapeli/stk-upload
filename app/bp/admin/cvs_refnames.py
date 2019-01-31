# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 27.1.2016

import csv
import logging
import time

from models.gen.refname import Refname, REFTYPES
from models.gen.user import User
from models.gen.person import Person


def load_refnames(pathname):
    """ Reads reference names from a local csv file. 
        The first row must have the required column names (in any order).
        These column names in the row 1 are:
        - Name
        - Refname
        - Reftype   (REFTYPES: surname / firstname / patronyme / father / mother)
        - Gender    (M = male, N,F = female, empty = undefined)
        - Source    (source name)

        Example file:
            Name,Refname,Reftype,Source,Gender
            Carl,Kalle,firstname,Sibelius-aineisto,male
            Carlsdotter,Carl,father,Sibelius-aineisto,
    """
    row_nro = 0
    empties = 0
    
    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        tx = User.beginTransaction()
        reader=csv.DictReader(f, dialect='excel')
        t0 = time.time()
        for row in reader:
            row_nro += 1
            try:
                nimi=row['Name'].strip()
                if len(nimi) == 0:
                    empties += 1
                    continue # Skip a row without a name

                refname=row['Refname']
                reftype=row['Reftype']
                source=row['Source']
                gd = row['Gender'].upper()
            except KeyError:
                raise KeyError(_('Not valid field names "Name,Refname,Reftype,Source,Gender" {}').\
                               format(row.keys()))

            sex = Person.sex_from_str(gd)

            # Creating Refname
            r = Refname(nimi)
            if (refname != '') and (refname != nimi):
                if reftype in REFTYPES:
                    r.refname = refname
                    r.reftype = reftype
                    logging.debug("cvs_refnames: {0} --> {1}".format(nimi, refname))
                else:
                    logging.warning('cvs_refnames: Invalid reference {} discarded. '.\
                                    format(reftype))
            if sex:
                r.sex = sex
            if source != '':
                r.source = source

            # Saves a Refname object and possibly connection to another Refname
            r.save(tx)

        tx.commit()

    msg = '{}: {} rows, {} skipped. TIME {} sek'.\
        format(pathname, row_nro, empties, time.time()-t0)
    logging.info(msg)
    return (msg)

