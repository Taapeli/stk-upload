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
from models.gen.family_combo import Family_combo


def set_confidence_values(tx, uniq_id=None, batch_logger=None):
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


def set_estimated_person_dates(uids=None):
    """ Sets an estimated lifietime in Person.lifetime
        (the properties in Person node are datetype, date1, and date2)

        With transaction, see gramps_loader.DOM_handler.set_estimated_dates_tr

        Asettaa kaikille tai valituille henkilölle arvioidut syntymä- ja kuolinajat

        Called from bp.admin.routes.estimate_dates
    """
    my_tx = User.beginTransaction()

    cnt = Person_combo.estimate_lifetimes(my_tx, uids)

    msg = _("Estimated {} person lifetimes").format(cnt)
    User.endTransaction(my_tx)
    
    return msg


def set_family_name_properties(tx=None, uniq_id=None):
    """ Set Family.father_sortname and Family.mother_sortname using the data in Person
        Set Family.date1 using the data in marriage Event
        Set Family.datetype and Family.date2 using the data in divorce or death Events
        If handler is defined
        - if there is transaction tx, use it, else create a new 
    """
    dates_count = 0
    sortname_count = 0
    
    if tx:
        my_tx = tx
    else:
        my_tx = User.beginTransaction()

    # Process each family 
    result = Family_combo.get_dates_parents(my_tx, uniq_id)
    for record in result:
        father_sortname = record['father_sortname']
        father_death_date = record['father_death_date']
        mother_sortname = record['mother_sortname']
        mother_death_date = record['mother_death_date']
        marriage_date = record['marriage_date']
        divorce_date = record['divorce_date']
        
        datetype = ''
        end_date = ''
        if divorce_date:
            end_date = divorce_date
        elif father_death_date and mother_death_date:
            if father_death_date < mother_death_date:
                end_date = father_death_date
            else:
                end_date = mother_death_date
        elif father_death_date:
            end_date = father_death_date
        elif mother_death_date:
            end_date = mother_death_date

        if end_date:
            datetype = "3"
        elif marriage_date:
            datetype = "0"
            end_date = marriage_date
        
        # Copy the dates from Event node and sortnames from Person nodes
        Family_combo.set_dates_sortnames(my_tx, uniq_id, datetype, marriage_date, end_date,
                                         father_sortname, mother_sortname)
        dates_count += 1
        sortname_count += 1
    
    if not tx:
        # Close my own created transaction
        User.endTransaction(my_tx)

    return (dates_count, sortname_count)


def set_person_name_properties(tx=None, uniq_id=None, ops=['refname', 'sortname']):
    """ Set Refnames to all Persons or one Person with given uniq_id; 
        also sets Person.sortname using the default name

        If handler is defined
        - if there is transaction tx, use it, else create a new 
    """
    sortname_count = 0
    refname_count = 0
    do_refnames = 'refname' in ops
    do_sortname = 'sortname' in ops

    if tx:
        my_tx = tx
    else:
        my_tx = User.beginTransaction()

    # Process each name 
    result = Name.get_personnames(my_tx, uniq_id)
    for record in result:
        # <Record name=<Node id=185239 labels={'Name'} 
        #    properties={'firstname': 'Jan Erik', 'suffix': 'Jansson', 
        #        'type': 'Birth Name', 'surname': 'Mannerquist', 'order': 0}
        # > >
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
    
    if not tx:
        # Close my own created transaction
        User.endTransaction(my_tx)

    return (refname_count, sortname_count)


# Moved to bp.tools.models.dataupdater.joinpersons
# def joinpersons(base_id, join_ids):
#     """ Yhdistetään henkilöön oid=base_id toiset henkilöt, joiden oid:t on
#         listassa join_ids.
#         
#         Yhdistämisen tulisi koskea attribuutteja ja tapahtumia, 
#         jotka liittyvät ko. henkilöiin
#     """
#     logging.debug('Pitäisi yhdistää ' + str(base_id) + " + " + str(join_ids) )
#     pass
