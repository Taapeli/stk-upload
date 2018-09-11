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



def get_server_location():
    # Returns server address as a str
    dbloc = shareds.driver.address
    return ':'.join((dbloc[0],str(dbloc[1])))


def get_new_handles(inc=1):
    ''' Create a sequence of new handle keys 
        Huom: Ei juuri käytössä models.gen.person.Person.save, 
              omia avaimia ei ole tarkoitus generoida!
    '''
    ret = []

    with shareds.driver.session() as session:
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
