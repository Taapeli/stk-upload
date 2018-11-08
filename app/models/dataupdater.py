# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 11.4.2016

import logging
import time

from bp.gramps.batchlogger import Batch, Log
from models.gen.user import User
from models.gen.person import Person
from models.gen.person_name import Name
from models.gen.refname import Refname
from models.gen.person_combo import Person_combo


def set_confidence_value(tx, uniq_id=None, batch_logger=None):
    """ Sets a quality rate for one or all Persons
        Asettaa henkilölle laatuarvion
        
        Person.confidence is mean of all Citations used for Person's Events
    """
    counter = 0
    t0 = time.time()

    result = Person.get_confidence(uniq_id)
    for record in result:
        p = Person()
        p.uniq_id = record["uniq_id"]
        
        if len(record["list"]) > 0:
            sumc = 0
            for ind in record["list"]:
                sumc += int(ind)
                
            confidence = sumc/len(record["list"])
            p.confidence = "%0.1f" % confidence # string with one decimal
        p.set_confidence(tx)
            
        counter += 1

    if isinstance(batch_logger, Batch):
        batch_logger.log_event({'title':"Confidences set", 
                                'count':counter, 'elapsed':time.time()-t0})
    return


def set_estimated_dates(batch_logger=None):
    """ Asettaa henkilölle arvioidut syntymä- ja kuolinajat
    """
    t0 = time.time()
        
    msg = Person_combo.set_estimated_dates()
                        
    if isinstance(batch_logger, Batch):
        batch_logger.log_event({'title':"Estimated birth and death dates set. " + msg, 
                                'elapsed':time.time()-t0})
    return msg


def set_person_refnames(self=None, uniq_id=None, batch_logger=None):
    """ Set Refnames to all or one Persons
        If self is defined
        - if there is transaction tx, use it, else create new 
        - if there is self.namecount, the number of names set is increased
    """
    pers_count = 0
    name_count = 0
    t0 = time.time()

    if self and self.tx:
        my_tx = self.tx
    else:
        my_tx = User.beginTransaction()
    names = Name.get_personnames(my_tx, uniq_id)

    # Process each name part (first names, surname, patronyme) of each Person
    for rec in names:
        # ╒═════╤════════════════════╤══════════╤══════════════╤═════╕
        # │"ID" │"fn"                │"sn"      │"pn"          │"sex"│
        # ╞═════╪════════════════════╪══════════╪══════════════╪═════╡
        # │30796│"Björn"             │""        │"Jönsson"     │"M"  │
        # ├─────┼────────────────────┼──────────┼──────────────┼─────┤
        # │30827│"Johan"             │"Sibbes"  │""            │"M"  │
        # ├─────┼────────────────────┼──────────┼──────────────┼─────┤
        # │30844│"Maria Elisabet"    │""        │"Johansdotter"│"F"  │
        # └─────┴────────────────────┴──────────┴──────────────┴─────┘
        # Build new refnames
        pid = rec["ID"]         # Person id
        firstname = rec["fn"]
        surname = rec["sn"]
        patronyme = rec["pn"]
        #gender = rec["sex"]

        # 1. firstnames
        if firstname and firstname != 'N':
            for name in firstname.split(' '):
                Refname.link_to_refname(my_tx, pid, name, 'firstname')
                name_count += 1

        # 2. surname and patronyme
        if surname and surname != 'N':
            Refname.link_to_refname(my_tx, pid, surname, 'surname')
            name_count += 1

        if patronyme:
            Refname.link_to_refname(my_tx, pid, patronyme, 'patronyme')
            name_count += 1
        pers_count += 1

        # ===   [NOT!] Report status for each name    ====
        if False:
            rnames = []
            recs = Person_combo.get_refnames(pid)
            for rec in recs:
                # ╒══════════════════════════╤═════════════════════╕
                # │"a"                       │"li"                 │
                # ╞══════════════════════════╪═════════════════════╡
                # │{"name":"Alfonsus","source│[{"use":"firstname"}]│
                # │":"Messu- ja kalenteri"}  │                     │
                # └──────────────────────────┴─────────────────────┘        
 
                name = rec['a']
                link = rec['li'][0]
                rnames.append("{} ({})".format(name['name'], link['use']))
            logging.debug("Set Refnames for {} - {}".format(pid, ', '.join(rnames)))
    
    if self == None or self.tx == None:
        # End my own created transformation
        User.endTransaction(my_tx)

    if self and self.namecount != None:
        self.namecount += name_count

    if isinstance(batch_logger, Batch):
        batch_logger.log_event({'title':"Refname references", 
                                'count':name_count, 'elapsed':time.time()-t0})
    return



def joinpersons(base_id, join_ids):
    """ Yhdistetään henkilöön oid=base_id toiset henkilöt, joiden oid:t on
        listassa join_ids.
        
        Yhdistämisen tulisi koskea attribuutteja ja tapahtumia, 
        jotka liittyvät ko. henkilöiin
    """
    logging.debug('Pitäisi yhdistää ' + str(base_id) + " + " + str(join_ids) )

    pass