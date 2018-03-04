# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 11.4.2016

import logging
import time
from models.gen.user import User
from models.gen.person import Person, Name
from models.gen.refname import Refname


def set_confidence_value(tx):
    """ Sets a quality rate for a Person
        Asettaa henkilölle laatuarvion
        
        Person.confidence is mean of all Citations used for Person's Events
    """
    counter = 0

    result = Person.get_confidence()
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
            
    text = "Number of confidences set: " + str(counter)
    return (text)


def set_estimated_dates():
    """ Asettaa henkilölle arvioidut syntymä- ja kuolinajat
    """
    message = []
        
    msg = Person.set_estimated_dates()
                        
    text = "Estimated birth and death dates set. " + msg
    message.append(text)
    return (message)


def set_person_refnames(got_tx=None, uniq_id=None):
    """ Set Refnames to all or selected Persons
    """
    pers_count = 0
    name_count = 0
    t0 = time.time()

    if got_tx:
        tx = got_tx
    else:
        tx = User.beginTransaction()
    names = Name.get_personnames(tx, uniq_id)

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
        pid = rec["ID"]
        firstname = rec["fn"]
        surname = rec["sn"]
        patronyme = rec["pn"]
        #gender = rec["sex"]

        # 1. firstnames
        if firstname and firstname != 'N':
            for name in firstname.split(' '):
                Refname.link_to_refname(tx, pid, name, 'firstname')
                name_count += 1

        # 2. surname and patronyme
        if surname and surname != 'N':
            Refname.link_to_refname(tx, pid, surname, 'surname')
            name_count += 1

        if patronyme:
            Refname.link_to_refname(tx, pid, patronyme, 'patronyme')
            name_count += 1
        pers_count += 1

#         # ===   [NOT!] Report status for each name    ====
#         rnames = []
#         recs = Person.get_refnames(pid)
#         for rec in recs:
#             # ╒══════════════════════════╤═════════════════════╕
#             # │"a"                       │"li"                 │
#             # ╞══════════════════════════╪═════════════════════╡
#             # │{"name":"Alfonsus","source│[{"use":"firstname"}]│
#             # │":"Messu- ja kalenteri"}  │                     │
#             # └──────────────────────────┴─────────────────────┘        
# 
#             name = rec['a']
#             link = rec['li'][0]
#             rnames.append("{} ({})".format(name['name'], link['use']))
#         logging.debug("Set Refnames for {} - {}".format(pid, ', '.join(rnames)))
    
    if not got_tx:
        User.endTransaction(tx)
    msg="Processed {} names of {} persons in {} sek".\
        format(name_count, pers_count, time.time()-t0)
    logging.info(msg)
    return msg



def joinpersons(base_id, join_ids):
    """ Yhdistetään henkilöön oid=base_id toiset henkilöt, joiden oid:t on
        listassa join_ids.
        
        Yhdistämisen tulisi koskea attribuutteja ja tapahtumia, 
        jotka liittyvät ko. henkilöiin
    """
    logging.debug('Pitäisi yhdistää ' + str(base_id) + " + " + str(join_ids) )

    pass