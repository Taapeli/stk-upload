# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 11.4.2016

import logging
import time
from flask_babelex import _

from bp.gramps.batchlogger import Batch
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


def set_estimated_dates(uid=None, batch_logger=None):
    """ Sets an estimated lifietime in Person.lifetime
        (in Person node properties datetype, date1, and date2)
        Asettaa kaikille tai valituille henkilölle arvioidut syntymä- ja kuolinajat
    """
    t0 = time.time()
        
    cnt = Person_combo.set_estimated_lives(uid)
    msg = _("Estimated {} person lifetimes").format(cnt)
                        
    if isinstance(batch_logger, Batch):
        batch_logger.log_event({'title':_("Estimated person lifetimes"), "count":cnt, 
                                'elapsed':time.time()-t0})
    else:
        print(msg)

    return msg


def calculate_person_properties(handler=None, uniq_id=None, ops=['refname'], batch_logger=None):
    """ Set Refnames to all or one Persons; 
        also set Person.sortname using default name

        If handler is defined
        - if there is transaction tx, use it, else create new 
        - if there is handler.namecount, the number of names set is increased
    """
    sortname_count = 0
    refname_count = 0
#     confidence_count = 0
#     do_confidence = 'confidence' in ops
#     do_lifetime = 'lifetime' in ops
    do_refnames = 'refname' in ops
    do_sortname = 'sortname' in ops
    t0 = time.time()

    if handler and handler.tx:
        my_tx = handler.tx
    else:
        my_tx = User.beginTransaction()

    # Process each name 
    result = Name.get_personnames(my_tx, uniq_id)
    for record in result:
        # <Record name=<Node id=185239 labels={'Name'} 
        #    properties={'firstname': 'Jan Erik', 'suffix': 'Jansson', 
        #        'type': 'Birth Name', 'surname': 'Mannerheim', 'order': 0}
        # >  >

        pid = record['pid']
        node = record['name']
        name = Name.from_node(node)
        
        if do_refnames:
            # Build new refnames
    
            # 1. firstnames
            if name.firstname and name.firstname != 'N':
                for nm in name.firstname.split(' '):
                    Refname.link_to_refname(my_tx, pid, nm, 'firstname')
                    refname_count += 1
    
            # 2. surname and patronyme
            if name.surname and name.surname != 'N':
                Refname.link_to_refname(my_tx, pid, name.surname, 'surname')
                refname_count += 1
    
            if name.suffix:
                Refname.link_to_refname(my_tx, pid, name.suffix, 'patronyme')
                refname_count += 1
        
        if do_sortname and name.order == 0:
            # If default name, store sortname key to Person node
            Person.set_sortname(my_tx, uniq_id, name)
            sortname_count += 1

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
    
    if handler == None or handler.tx == None:
        # End my own created transformation
        User.endTransaction(my_tx)

    if handler and handler.namecount != None:
        handler.namecount += refname_count

    if isinstance(batch_logger, Batch):
        t = time.time()-t0
        if do_refnames: 
            batch_logger.log_event({'title':"Refname references", 
                                    'count':refname_count, 'elapsed':t})
            t=''
        if do_sortname: 
            batch_logger.log_event({'title':"Sort names", 
                                    'count':sortname_count, 'elapsed':t})
            t=''
#         if do_confidence:
#             batch_logger.log_event({'title':"Confidence values", 
#                                     'count':confidence_count, 'elapsed':t})
    return



def joinpersons(base_id, join_ids):
    """ Yhdistetään henkilöön oid=base_id toiset henkilöt, joiden oid:t on
        listassa join_ids.
        
        Yhdistämisen tulisi koskea attribuutteja ja tapahtumia, 
        jotka liittyvät ko. henkilöiin
    """
    logging.debug('Pitäisi yhdistää ' + str(base_id) + " + " + str(join_ids) )

    pass