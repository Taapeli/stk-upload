'''
Created on 11.5.2017

@author: jm
'''
import logging
import shareds
#===============================================================================
# from neo4j.v1 import GraphDatabase, basic_auth
# from flask import g
# import instance.config as config
#===============================================================================


def connect_db():
    """ Opens a new database connection if there is none yet for the
        current application context.

        Ks. https://neo4j.com/docs/developer-manual/current/drivers/client-applications/
    """

    #===========================================================================
    # if not hasattr(g, 'driver'):
    #     # Create driver for application life time
    #     if hasattr(config,'DB_HOST_PORT'):
    #         print ("connect_db - server {}".format(config.DB_HOST_PORT))
    #         shareds.driver = GraphDatabase.driver(config.DB_HOST_PORT, \
    #                                         auth=basic_auth(config.DB_USER, config.DB_AUTH))
    #     else:
    #         print ("connect_db - default local")
    #         shareds.driver = GraphDatabase.driver("bolt://localhost", 
    #                                         auth=basic_auth("neo4j", "localTaapeli"))
    # else:
    #     print('connect_db - ok')
    # # Return True, if no driver can be accessed
    # #return shareds.driver.pool.closed
    #===========================================================================


def get_new_handles(inc=1):
    ''' Create a sequence of new handle keys '''
    ret = []

    with shareds.driver.session() as session:
#         newhand = session.write_transaction(lambda tx: _update_seq_node(tx, inc))
        with session.begin_transaction() as tx:
            for record in tx.run('''
MERGE (a:Seq) 
SET a.handle = coalesce(a.handle, 10000) + {inc} 
RETURN a.handle AS handle''', {"inc": inc} ):
                newhand=record["handle"]
            tx.commit()

    for i in range(inc, 0, -1):
        ret.append("Handle{}".format(newhand - i))
    return (ret)

def _update_seq_node(self, tx, inc):
    record_list = tx.run('''
MATCH (a:Seq) 
SET a.seq = coalesce(a.seq, 10000) + {inc} 
RETURN a.handle AS handle''', {"inc": inc})
    return int(record_list[0][0])


def alusta_kanta():
    """ Koko kanta tyhjennetään """
    result = shareds.driver.session().run("MATCH (a) DETACH DELETE a")
    counters = result.consume().counters
    msg = "Poistettu {} solmua, {} relaatiota".\
          format(counters.nodes_deleted, counters.relationships_deleted)
    logging.info('Tietokanta tyhjennetty! ' + msg)
    return (msg)

#TODO: Korjaa tämä: skeema sch määrittelemättä
#     # Poistetaan vanhat rajoitteet ja indeksit
#     for uv in sch.get_uniqueness_constraints('Refname'):
#         try:
#             sch.drop_uniqueness_constraint('Refname', uv)
#         except:
#             logging.warning("drop_uniqueness_constraint ei onnistunut:", 
#                 sys.exc_info()[0])
#     for iv in sch.get_indexes('Refname'):
#         try:
#             sch.drop_index('Refname', iv)
#         except:
#             logging.warning("drop_index ei onnistunut:", sys.exc_info()[0])
# 
#     # Luodaan Refname:n rajoitteet ja indeksit    
#     refname_uniq = ["oid", "name"]
#     refname_index = ["reftype"]
#     for u in refname_uniq:
#         sch.create_uniqueness_constraint("Refname", u)
#     for i in refname_index:
#         sch.create_index("Refname", i)


class Date():
    """ Päivämäärän muuntofunktioita
        Käytetty käräjäaineiston aikojen muunnoksiin 2014(?)
    """

    @staticmethod       
    def range_str(aikamaare):
        """ Karkea aikamäären siivous, palauttaa merkkijonon
        
            Aika esim. '1666.02.20-22' muunnetaan muotoon '1666-02-20 … 22':
            * Tekstin jakaminen sarakkeisiin käyttäen välimerkkiä ”-” 
              tai ”,” (kentät tekstimuotoiltuna)
            * Päivämäärän muotoilu ISO-muotoon vaihtamalla erottimet 
              ”.” viivaksi
         """
        t = aikamaare.replace('-','|').replace(',','|').replace('.', '-')
        if '|' in t:
            osat = t.split('|')
            # osat[0] olkoon tapahtuman 'virallinen' päivämäärä
            t = '%s … %s' % (osat[0], osat[-1])
            if len(osat) > 2:
                logging.warning('Aika korjattu: {} -> {}'.format(aikamaare, t))

        t = t.replace('.', '-')
        return t
