# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 11.4.2016

import logging
from models.genealogy import *  # Tietokannan luokat

def joinpersons(base_id, join_ids):
    """ Yhdistetään henkilöön id=base_id toiset henkilöt, joiden id:t on
        listassa join_ids.
        
        Yhdistämisen tulisi koskea attribuutteja ja tapahtumia, 
        jotka liittyvät ko. henkilöiin
    """
    logging.debug('Pitäisi yhdistää ' + str(base_id) + " + " + str(join_ids) )

    pass