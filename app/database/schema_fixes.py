'''
Fix obsolete terms and structures in schema.

Created on 6.6.2020 
moved from database.adminDB.do_schema_fixes

@author: jm
'''
import logging
logger = logging.getLogger('stkserver') 
import shareds


def do_schema_fixes():
    """ Search current obsolete terms and structures in schema and fix them.
    
        #TODO: Muokataan tätä aina kun skeema muuttuu (tai muutos on ohi)
    """

    if True:
        change_persons_BASENAME_to_REFNAME = """
MATCH (a:Person) <-[r0:BASENAME]- (b:Refname)
WITH a, r0, b
    CREATE (a) <-[r:REFNAME {use:r0.use}]- (b)
    DELETE r0
RETURN count(r)
"""
        # call with (use0="matronyme", use1="mother") or (use0="patronyme", use1="father")
        change_matronyme_BASENAME_to_PARENTNAME = """
MATCH (b:Refname) -[r0:BASENAME {use:$use0}]-> (c:Refname)
WITH b, r0, c, r0.use as old
    CREATE (b) <-[r:PARENTNAME {use:$use1}]- (c)
    DELETE r0
RETURN count(r)
"""

        with shareds.driver.session() as session: 
            try:
                result = session.run(change_persons_BASENAME_to_REFNAME)
                cnt1 = result.single()[0]
                result = session.run(change_matronyme_BASENAME_to_PARENTNAME,
                                     use0="matronyme", use1="mother")
                cnt2 = result.single()[0]
                result = session.run(change_matronyme_BASENAME_to_PARENTNAME,
                                     use0="patronyme", use1="father")
                cnt3 = result.single()[0]
                print(f"adminDB.do_schema_fixes: fixed Refname links {cnt1} REFNAME, {cnt2} matronyme, {cnt3} patronyme")
            except Exception as e:
                logger.error(f"{e} in database.adminDB.do_schema_fixes")
                return

            dropped=0
            created=0

# Removed 21.4.2020 
#             try:
#                 for label in ['Person', 'Event', 'Place', 'Family']:
#                     result = session.run(f'DROP INDEX ON :{label}(gramps_handle)')
#                     counters = result.summary().counters
#                     dropped += counters.indexes_removed
#             except Exception as e:
#                 pass

            for label in ['Citation', 'Event', 'Family', 'Media', 'Name',
                          'Note', 'Person', 'Place', 'Place_name', 'Repository',
                          'Source']:
                try:
                    result = session.run(f'CREATE INDEX ON :{label}(handle)')
                    counters = result.summary().counters
                    created += counters.indexes_added
                except Exception as e:
                    logger.info(f"Index for {label}.handle not created: {e}")

            print(f"adminDB.do_schema_fixes: index updates: {dropped} removed, {created} created")

    else:
        print("database.adminDB.do_schema_fixes: No schema changes tried")


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
