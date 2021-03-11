#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

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


# def get_new_handles(inc=1):
#     ''' Create a sequence of new handle keys. NOT  IN USE 
#         Huom: Ei juuri käytössä models.gen.person.Person.save, 
#               omia avaimia ei ole tarkoitus generoida!
#     '''
#     ret = []
# 
#     with shareds.driver.session() as session:
#         with session.begin_transaction() as tx:
#             for record in tx.run('''
# MERGE (a:Seq) 
# SET a.handle = coalesce(a.handle, 10000) + {inc} 
# RETURN a.handle AS handle''', {"inc": inc} ):
#                 newhand=record["handle"]
#             tx.commit()
# 
#     for i in range(inc, 0, -1):
#         ret.append("Handle{}".format(newhand - i))
#     return (ret)


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

def aqcuire_lock(tx,lock_id):
    tx.run("merge (lock:Lock {id:$lock_id}) set lock.locked = true", lock_id=lock_id)

