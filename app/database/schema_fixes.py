#   Isotammi Geneological Service for combining multiple researchers' results.
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
Fix obsolete terms and structures in schema.

Created on 6.6.2020 
moved from database.adminDB.do_schema_fixes

@author: jm
'''
import logging
logger = logging.getLogger('stkserver') 

from neo4j.exceptions import ClientError #, ConstraintError

import shareds


def do_schema_fixes():
    """ Search current obsolete terms and structures in schema and fix them.
    
        #TODO: Muokataan tätä aina kun skeema muuttuu (tai muutos on ohi)
    """
    if True:
        # // Fix master HAS_LOADED => Stk HAS_ACCESS
        # // and Add (:Batch) -[:AFTER_AUDIT]-> (:Audit) 
        change_master_HAS_LOADED_to_Stk_HAS_AUDITED = """
MATCH (stk:UserProfile{username:"_Stk_"})
WITH stk
    MATCH (master:UserProfile{username:"master"})-[r:HAS_LOADED]->(audit:Audit)
WITH master,stk,r,audit limit 50
    DELETE r
    MERGE (stk)-[:HAS_ACCESS]->(audit)
    WITH audit
        MATCH (b:Batch) WHERE b.id = audit.id
        MERGE (b)-[:AFTER_AUDIT]->(audit)
    RETURN count(audit)"""
        change_Stk_name = """
MATCH (u:UserProfile {username:'_Stk_'})
SET u.name = 'Suomi tk', u.change = timestamp()"""
        guest_role_removal = """
MATCH (a:Role{name:"guest"}) <-[r:HAS_ROLE]- (u:User {username:"guest"})
SET u.roles=""
SET u.email = 'nobody'
DELETE r"""
        guest_role_adding = """
MATCH (a:Role{name:"guest"}), (u:User {username:"guest"})
MERGE (a) <-[r:HAS_ROLE]- (u)
SET u.roles = 'guest'
SET u.email = 'nobody'"""

        with shareds.driver.session() as session: 
            try:
                # Name field missed
                if shareds.app.config.get('DEMO', False):
                    # Add guest role in demo service
                    result = session.run(guest_role_adding)
                    counters = shareds.db.consume_counters(result)
                    if counters.properties_set > 0:
                        msg = "database.schema_fixes.do_schema_fixes: guest role added to DEMO guest!"
                        print(msg)
                        logger.info(msg)
                else:
                    # Remove guest role from real services
                    result = session.run(guest_role_removal)
                    counters = shareds.db.consume_counters(result)
                    if counters.properties_set > 0:
                        msg = "database.schema_fixes.do_schema_fixes: guest role removed from guest!"
                        print(msg)
                        logger.info(msg)

                # From (:UserProfile{'master'} -[:HAS_LOADED]-> (a:Audit)
                #   to (:UserProfile{'_Stk_'} -[:HAS_ACCESS]-> (a:Audit) 
                #  and OPTIONAL (b:Batch) -[AUDITED]-> (a)
                result = session.run(change_master_HAS_LOADED_to_Stk_HAS_AUDITED)
                for record in result:
                    # If any found, get the counters of changes
                    _cnt = record[0]
                    counters = shareds.db.consume_counters(result)
                    #print(counters)
                    rel_created = counters.relationships_created
                    rel_deleted = counters.relationships_deleted
                    print(f"do_schema_fixes: Audit links {rel_deleted} removed, {rel_created} added")
                    if rel_created + rel_deleted > 0:
                        logger.info(f"database.schema_fixes.do_schema_fixes: "
                                    f"Audit links {rel_deleted} removed, {rel_created} added")

                # Name field missed
                result = session.run(change_Stk_name)
                counters = shareds.db.consume_counters(result)
                if counters.properties_set > 0:
                    logger.info("database.schema_fixes.do_schema_fixes: profile _Stk_ name set")

#                 cnt1 = result.single()[0]
#                 result = session.run(change_matronyme_BASENAME_to_PARENTNAME,
#                                      use0="matronyme", use1="mother")
#                 cnt2 = result.single()[0]
#                 result = session.run(change_matronyme_BASENAME_to_PARENTNAME,
#                                      use0="patronyme", use1="father")
#                 cnt3 = result.single()[0]
#                 print(f"database.schema_fixes.do_schema_fixes: fixed Refname links {cnt1} REFNAME, {cnt2} matronyme, {cnt3} patronyme")
            except Exception as e:
                logger.error(f"{e} in database.adminDB.do_schema_fixes/Audit"
                             f" Failed {e.__class__.__name__} {e}") 
                return


            dropped=0
            created=0
            for label in ['Citation', 'Event', 'Family', 'Media', 'Name',
                          'Note', 'Person', 'Place', 'Place_name', 'Repository',
                          'Source']:
                try:
                    result = session.run(f'CREATE INDEX ON :{label}(handle)')
                    counters = shareds.db.consume_counters(result)
                    created += counters.indexes_added
                except ClientError as e:
                    msgs = e.message.split(',')
                    print(f'Unique constraint for {label}.handle ok: {msgs[0]}')
                    return
                except Exception as e: 
                    logger.warning(f"do_schema_fixes Index for {label}.handle not created." 
                                   f" Failed {e.__class__.__name__} {e.message}") 
            return 

            print(f"database.schema_fixes.do_schema_fixes: index updates: {dropped} removed, {created} created")

    else:
        print("database.schema_fixes.do_schema_fixes: No schema changes tried")


#Removed 6.5.2020
#         change_persons_BASENAME_to_REFNAME = """
# MATCH (a:Person) <-[r0:BASENAME]- (b:Refname)
# WITH a, r0, b
#     CREATE (a) <-[r:REFNAME {use:r0.use}]- (b)
#     DELETE r0
# RETURN count(r)
# """
#         # call with (use0="matronyme", use1="mother") or (use0="patronyme", use1="father")
#         change_matronyme_BASENAME_to_PARENTNAME = """
# MATCH (b:Refname) -[r0:BASENAME {use:$use0}]-> (c:Refname)
# WITH b, r0, c, r0.use as old
#     CREATE (b) <-[r:PARENTNAME {use:$use1}]- (c)
#     DELETE r0
# RETURN count(r)
# """

# Removed 21.4.2020 
#             try:
#                 for label in ['Person', 'Event', 'Place', 'Family']:
#                     result = session.run(f'DROP INDEX ON :{label}(gramps_handle)')
#                     counters = shareds.db.consume_counters(result)
#                     dropped += counters.indexes_removed
#             except Exception as e:
#                 pass

# Removed 28.1.2020 in a69d57bcc9e4c2e0ba2e98f3370d8efab7b1990e
#     if False:
#         change_HIERARCY_to_IS_INSIDE = """
# MATCH (a) -[r:HIERARCY]-> (b)
#     MERGE (a) -[rr:IS_INSIDE]-> (b)
#         set rr = {datetype:r.datetype, date1:r.date1, date2:r.date2}
#     DELETE r
# RETURN count(rr)"""
#         change_userName_to_username = """
# match (u:UserProfile) where exists(u.userName)
#     set u.username = u.userName
#     set u.userName = null
# return count(u)"""
#         change_Repocitory_to_Repository = """
# match (a:Repocitory)
#     set a:Repository
#     remove a:Repocitory
# return count(a)"""
#         change_Family_dates = """
# match (f:Family) where f.datetype=3 and not exists(f.date1)
#     set f.datatype = 1
#     set f.data1 = f.data2
# return count(f)"""
#         change_wrong_supplemented_direction = """
# MATCH (u:User)<-[r:SUPPLEMENTED]-(p:UserProfile) 
#     DELETE r 
#     CREATE (u) -[:SUPPLEMENTED]-> (p)
# return count(u)"""

# Removed 21.4.2020
#         change_Root_to_Audit = '''
# MATCH (n:Root)
#     SET n:Audit
#     SET n.auditor = n.operator
#     REMOVE n:Root
#     SET n.operator = Null
# RETURN count(n)'''
#         
#         change_Audition_to_Audit = '''
# MATCH (n:Audition)
#     SET n:Audit
#     REMOVE n:Audition
# RETURN count(n)'''
