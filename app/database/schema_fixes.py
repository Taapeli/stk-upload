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
Fix obsolete terms and structures in schema.

Created on 6.6.2020 
moved from database.accessDB.do_schema_fixes

@author: jm
'''
import logging
logger = logging.getLogger('stkserver') 

from neo4j.exceptions import ClientError #, ConstraintError

import shareds
from bl.batch import State

def do_schema_fixes():
    """ Search current obsolete terms and structures in schema and fix them.
    
        @See: https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.SummaryCounters
    
        #TODO: Muokataan tätä aina kun skeema muuttuu (tai muutos on ohi)
    """


    with shareds.driver.session() as session: 
        try:
            # 1. Change Batch label to Root
            #
            # Change (:Batch {"material_type":"Family Tree", "status":"completed"})
            # to     (:Root  {material:'Family Tree', state:'Candidate'})
            change_Batch_to_Root = """
                MATCH (b:Batch) where b.id="2021-05-03.003"
                SET b:Root
                SET b.material=coalesce(b.material_type, "Family Tree")
                SET b.state="candidate"
                REMOVE b.Batch, b.status, b.material_type"""
            result = session.run(change_Batch_to_Root,
                                 default_state=State.ROOT_CANDIDATE,
                                 default_material="Family Tree")
            counters = shareds.db.consume_counters(result)
            labels_added = counters.labels_added
            print(f"do_schema_fixes: change {labels_added} Batch nodes to Root")

            # 2. Change (:Root) -[:OWNS]-> (:Label) 
            #    to     (:Root) -[:OBJ_LABEL]-> (:Label)
            #    using root_relations dictionary
            root_relations = {          # {object_label: relation_type}
                ":Person": ":OBJ_PERSON",
                ":Family": ":OBJ_FAMILY",
                ":Place": ":OBJ_PLACE",
                "" : ":OBJ_OTHER"
                }
            OWNS_to_OBJ_x = """
                MATCH (b:Root) -[r:OWNS]-> (x{label})
                WITH b,r,x CREATE (b) -[{rtype}]-> (x), DELETE r"""
            for label, rtype in root_relations.items():
                cypher = OWNS_to_OBJ_x.format(label=":Person", rtype=":OBJ_PERSON")
                result = session.run(cypher)
                counters = shareds.db.consume_counters(result)
                relationships_created = counters.relationships_created
                print(f"do_schema_fixes: created {relationships_created} links (:Root) -[{rtype}]-> ({label})")

            # for record in result:
            #     # If any found, get the counters of changes
            #     _cnt = record[0]
            #     counters = shareds.db.consume_counters(result)
            #     #print(counters)
            #     rel_created = counters.relationships_created
            #     rel_deleted = counters.relationships_deleted
            #     print(f"do_schema_fixes: Audit links {rel_deleted} removed, {rel_created} added")
            #     if rel_created + rel_deleted > 0:
            #         logger.info(f"database.schema_fixes.do_schema_fixes: "
            #                     f"Audit links {rel_deleted} removed, {rel_created} added")

            # # Name field missed
            # result = session.run(change_Stk_name)
            # counters = shareds.db.consume_counters(result)
            # if counters.properties_set > 0:
            #     logger.info("database.schema_fixes.do_schema_fixes: profile _Stk_ name set")

        except Exception as e:
            logger.error(f"{e} in database.schema_fixes.do_schema_fixes"
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
