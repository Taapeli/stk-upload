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
import shareds
#from neo4j.exceptions import ClientError #, ConstraintError

#---- (change uuid_to_iid) Replace uuid keys by iid and set b.cd_schema ----
from pe.neo4j.util import IsotammiId

IID_1_batches_with_missing_iids = """
    MATCH (b:Root)
        WHERE b.db_schema IS NULL OR NOT b.db_schema = $schema_ver
    OPTIONAL MATCH (b) --> (a) WHERE a.iid IS NULL
    WITH b, id(a) AS uid, labels(a)[0] AS lbl
        ORDER BY b.id DESC, lbl
        LIMIT $limit
    RETURN b.id AS batch_id, b.db_schema AS schema, lbl, COLLECT(uid) AS uids
"""
IID_a_change_uuid_to_iid = """
    MATCH (b:Root{id:$bid}) --> (a)
        WHERE $lbl IN labels(a) AND a.iid IS NULL
    WITH a LIMIT 1
        SET a.iid=$iid, a.uuid = NULL
"""
IID_b_batch_remove_uuids = """
    MATCH (b:Root{id:$bid})
    OPTIONAL MATCH (b) --> (a)
        WHERE a.iid IS NULL AND a.uuid IS NOT NULL
    WITH b, a LIMIT $limit
        SET a.uuid = NULL
    RETURN COUNT(a)
"""
IID_c_update_batch_schema = """
    MATCH (b:Root {id:$bid}) 
        SET b.db_schema = $schema_ver
"""

def uuid_to_iid():
    """ 1. For all batches b
            a) for each chunk b of missing a.iid keys
                - Allocate set of iid keys
                - for each a: set a.iid, remove a.uuid
            - update b.db_schema
            b) for each chunk b with no a.iid key
                - remove uuid
            - update b.db_schema
    """
    from database.accessDB import DB_SCHEMA_VERSION


    def generate_iids(jobs_i):
        """ For given list of batches b, their node labels and list of node a uniq_ids,
            - for each node a set a.iid and remove a.uuid
            - finally set b.db_schema for the batch
            After that all objects has a.iid key
        """
        n_objects = 0
        n_batches = 0
        batch_prev = ""
        for batch_id, schema, label, uids in jobs_i:
            chunck_size = len(uids)
            n_objects += chunck_size
            iid_generator = IsotammiId(session, obj_name=label)
            iid_generator.reserve(chunck_size)
            for _n in range(chunck_size):
                iid = iid_generator.get_one()

                session.run(IID_a_change_uuid_to_iid,
                            bid=batch_id, lbl=label, iid=iid)

            print(f"# ... generate_iids: set {n_objects} new iid keys for {label!r} in {batch_id!r}")
            
            if schema != DB_SCHEMA_VERSION and batch_id != batch_prev:
                # All iid keys set in this batch. (There are no nodes with both uuid and n iid)
                n_batches += 1
                batch_prev = batch_id
                session.run(IID_c_update_batch_schema,
                            bid=batch_id, schema_ver=DB_SCHEMA_VERSION)
                print(f"# ... generate_iids: {batch_id!r} updated")
        # returns number of batches and objects processed
        return n_batches, n_objects


    def remove_uuids(jobs_u):
        """ For given list of batches b not having current b.db_schema value
            - for each node with a.uiid remove a.uuid
            - finally set b.db_schema for the batch
            After that no object has a.uuid key
        """
        n_objects = 0
        n_batches = 0

        for batch_id, schema in jobs_u:
            cnt = -1
            while cnt != 0: # Loop until no changes in database
                cnt = 0

                result = session.run(IID_b_batch_remove_uuids,
                                     bid=batch_id, limit=100)

                for record in result: # Actually 0-1 records
                    cnt = record[0]
                    if cnt > 0:
                        n_objects += cnt
                        #print(f"#remove_uuids: {cnt} uuid keys removed from {batch_id!r}")
                if cnt == 0 and schema != DB_SCHEMA_VERSION:
                    # All uuids removed from this batch
                    n_batches += 1

                    session.run(IID_c_update_batch_schema,
                                bid=batch_id, schema_ver=DB_SCHEMA_VERSION)

        print(f"# ...remove_uuids: {n_batches} batches, {n_objects} uuid removals")
        # returns number of batches and objects processed
        return n_batches, n_objects


    # =========== uuid_to_iid starts here ==============
    
    with shareds.driver.session() as session:
        total_batches = 0
        total_nodes = 0
        done = False
        while not done:
            # For a chunk of batches find objects having missing a.iid
            jobs_i = []
            jobs_u = []
            done = True

            result = session.run(IID_1_batches_with_missing_iids,
                                 limit=200, schema_ver=DB_SCHEMA_VERSION)

            for batch_id, schema, label, uids in result:

                if label is None:
                    # No iids: should remove a.uuid keys
                    jobs_u.append((batch_id, schema))
                else:
                    # Generate a.iid (and remove a.uuid)
                    # uids is a list of uniq_ids needing new a.iid keys
                    jobs_i.append((batch_id, schema, label, uids))
                done = False

            if jobs_i:
                a_batches, a_nodes = generate_iids(jobs_i)
                #print(f"#uuid_to_iid: {a_batches} batches, {a_nodes} iid creations")
                total_batches += a_batches
                total_nodes += a_nodes
            if jobs_u:
                b_batches, b_nodes = remove_uuids(jobs_u)
                #print(f"#uuid_to_iid: {b_batches} batches, {b_nodes} uuid deletions")
                total_batches += b_batches
                total_nodes += b_nodes
            pass

        print(f"#uuid_to_iid: TOTAL {total_batches} batch updates,"\
              f" {total_nodes} iid creations")
    return


def do_schema_fixes():
    """ Search current obsolete terms and structures in schema and fix them.

        Set a new DB_SCHEMA_VERSION value in database.accessDB to activate this method.
        #TODO: Muokataan tätä aina kun skeema muuttuu (tai muutos on ohi)

        @See: https://neo4j.com/docs/api/python-driver/current/api.html#neo4j.SummaryCounters
    """

    # --- For DB_SCHEMA_VERSION = '2022.1.2', 4.6.2022/HRo

    # For all batches b:
    #    - if found objects with missing a.iid: generate a.iid and remove a.uiid
    #    - else remove a.uuid
    #    - set b.db_schema version
    uuid_to_iid()

#---- (change uuid_to_iid) ----


    STATS_link_to_from = """
        MATCH (b:Root) -[:STATS]-> (x:Stats)
        DETACH DELETE x"""
    with shareds.driver.session() as session: 
        result = session.run(STATS_link_to_from)
        counters = shareds.db.consume_counters(result)
        stats_removed = counters.nodes_deleted
        if stats_removed:
            print(f" -- removed {stats_removed} old stats with forwards link (:Root) -[:STATS]-> (:Stats)")
            # New stats are created with backwards link (:Root) <-[:STATS]- (:Stats)")

    DOES_AUDIT_ts = """
        MATCH () -[r:DOES_AUDIT]-> () WHERE NOT r.timestamp IS null
            SET r.ts_from = r.timestamp
            SET r.timestamp = null        
        """
    with shareds.driver.session() as session: 
        result = session.run(DOES_AUDIT_ts)
        counters = shareds.db.consume_counters(result)
        rel_changed = int(counters.properties_set / 2)
        if rel_changed:
            print(f" -- updated properties in {rel_changed} DOES_AUDIT relations")

    clear_root_audited = """
        MATCH (r:Root) WHERE NOT r.audited IS null
            SET r.audited = null        
        """
    with shareds.driver.session() as session: 
        result = session.run(clear_root_audited)
        counters = shareds.db.consume_counters(result)
        removed = int(counters.properties_set)
        if removed:
            print(f" -- updated properties in {removed} Root objects")

    return

    # # --- For DB_SCHEMA_VERSION = '2022.1.1', 1.4.2022/JMä
    # STATS_link_to_from = """
    #     MATCH (b:Root) -[:STATS]-> (x:Stats)
    #     DETACH DELETE x"""
    # with shareds.driver.session() as session: 
    #     result = session.run(STATS_link_to_from)
    #     counters = shareds.db.consume_counters(result)
    #     stats_removed = counters.nodes_deleted
    #     if stats_removed:
    #         print(f" -- removed {stats_removed} old stats with forwards link (:Root) -[:STATS]-> (:Stats)")
    #         # New stats are created with backwards link (:Root) <-[:STATS]- (:Stats)")

    # DOES_AUDIT_ts = """
    #     MATCH () -[r:DOES_AUDIT]-> () WHERE NOT r.timestamp IS null
    #         SET r.ts_from = r.timestamp
    #         SET r.timestamp = null        
    #     """
    # with shareds.driver.session() as session: 
    #     result = session.run(DOES_AUDIT_ts)
    #     counters = shareds.db.consume_counters(result)
    #     rel_changed = int(counters.properties_set / 2)
    #     if rel_changed:
    #         print(f" -- updated properties in {rel_changed} DOES_AUDIT relations")

    # clear_root_audited = """
    #     MATCH (r:Root) WHERE NOT r.audited IS null
    #         SET r.audited = null        
    #     """
    # with shareds.driver.session() as session: 
    #     result = session.run(clear_root_audited)
    #     counters = shareds.db.consume_counters(result)
    #     removed = int(counters.properties_set)
    #     if removed:
    #         print(f" -- updated properties in {removed} Root objects")

    # return

    # --- For DB_SCHEMA_VERSION = '2021.2.0.4', deleted 22.1.2022/JMä
    # from bl.batch.root import State
    #
    # # Batch: Root.state depends on b.status; Root.material = b.material_type
    # change_Batch_to_Root = f"""
    #     MATCH (b:Batch) WITH b LIMIT 1
    #     SET b:Root
    #     SET b.material=
    #         CASE b.material_type
    #             WHEN "" THEN $default_material
    #             WHEN NULL THEN $default_material
    #             ELSE b.material
    #         END
    #     SET b.state=CASE
    #             WHEN b.status = 'started' THEN '{State.ROOT_STORING}'
    #             WHEN b.status = 'completed' THEN '{State.ROOT_CANDIDATE}'
    #             WHEN b.status = 'audit_requested' THEN '{State.ROOT_AUDIT_REQUESTED}'
    #             ELSE '{State.ROOT_REMOVED}'
    #         END
    #     REMOVE b:Batch, b.status, b.material_type"""
    # # Audit: Root.state = "Audit Requested"; Root.material = "Family Tree"
    # change_Audit_to_Root = f"""
    #     MATCH (b:Audit) WITH b LIMIT 1
    #     SET b:Root
    #     SET b.material=
    #         CASE b.material_type
    #             WHEN "" THEN $default_material
    #             WHEN NULL THEN $default_material
    #             ELSE b.material
    #         END
    #     SET b.state='{State.ROOT_AUDITING}'
    #     REMOVE b:Audit, b.status, b.material_type"""
    # {object_label: relation_type}
    # root_relations = {
    #     ":Person": ":OBJ_PERSON",
    #     ":Family": ":OBJ_FAMILY",
    #     ":Place": ":OBJ_PLACE",
    #     ":Source": ":OBJ_SOURCE",
    #     "" : ":OBJ_OTHER"
    #     }
    # # Root relation to objects (types OWNS or PASSED) are split to types
    # # OBJ_PERSON, OBJ_FAMILY, OBJ_PLACE, OBJ_SOURCE" and OBJ_OTHER
    # OWNS_to_OBJ_x = """
    #     MATCH (b:Root) -[r{old_type}]-> (x{label})
    #     WITH b,r,x
    #         CREATE (b) -[{new_type}]-> (x)
    #         DELETE r"""

    # # Comment and Topic:
    # #  - Identify old Comments by existing c.user
    # # a) Delete object comments except the 1st one
    # # b) Connect remaining comments to UserProfile,
    # #    change label to Topic and
    # #    remove c.user
    # Delete_comment_tails = """
    #     MATCH (x) -[:COMMENT]-> (c:Comment) WHERE c.user IS NOT null 
    #     WITH x, c ORDER BY id(x), c.timestamp
    #     WITH x, collect(c)[1..] as coms
    #     UNWIND coms AS com
    #         DETACH DELETE com
    # """
    # Rename_label_Comment_to_Topic = """
    #     MATCH (root:Root) --> (x) -[:COMMENT]-> (c:Comment) WHERE c.user IS NOT null
    #     MATCH (up:UserProfile) WHERE up.username = root.user
    #     WITH up, c                                             LIMIT 3
    #         MERGE (up) -[:COMMENTED]-> (c)
    #         SET c.user = null
    #         SET c:Topic
    #         REMOVE c:Comment
    # """

    # with shareds.driver.session() as session: 
    # --- For DB_SCHEMA_VERSION = '2021.2.0.4', deleted 22.1.2022/JMä
    #     try:
    #         for old_root, cypher_to_root, old_type in [
    #             ("Batch", change_Batch_to_Root, ":OWNS"), 
    #             ("Audit", change_Audit_to_Root, ":PASSED")]:
    #             # 1. Change Batch label to Root
    #             #
    #             # Change (:Batch {"material_type":"Family Tree", "status":"completed"})
    #             # to     (:Root  {material:'Family Tree', state:'Candidate'}) etc
    #             labels_added = -1 
    #             while labels_added != 0:
    #                 result = session.run(cypher_to_root, default_material="Family Tree")
    #                 counters = shareds.db.consume_counters(result)
    #                 labels_added = counters.labels_added 
    #                 #properties_set = counters.properties_set
    #                 print(f"do_schema_fixes: change {labels_added} {old_root} nodes to Root")
    #
    #                 # 2. Change OWNS OR PASSED links to distinct OBJ_* links
    #                 #
    #                 #    Change (:Root) -[r]-> (:Label) 
    #                 #    to     (:Root) -[:OBJ_LABEL]-> (:Label)
    #                 #    using root_relations dictionary
    #                 for label, rtype in root_relations.items():
    #                     cypher = OWNS_to_OBJ_x.format(label=label, old_type=old_type, new_type=rtype)
    #                     result = session.run(cypher)
    #                     counters = shareds.db.consume_counters(result)
    #                     relationships_created = counters.relationships_created
    #                     if relationships_created:
    #                         print(f" -- created {relationships_created} links (:Root) -[{rtype}]-> ({label})")
    #
    #     except Exception as e:
    #         logger.error(f"do_schema_fixes: {e} in database.schema_fixes.do_schema_fixes"
    #                      f" Failed {e.__class__.__name__} {e}")
    #         return

        # 3. Create index for Root.material, Root.state

        # --- For DB_SCHEMA_VERSION = '2021.2.0.4', deleted 22.1.2022/JMä
        # try:
        #     result = session.run(f'CREATE INDEX FOR (b:Root) ON (b.material, b.state)')
        #     counters = shareds.db.consume_counters(result)
        #     indexes_added = counters.indexes_added
        #     print(f"do_schema_fixes: created {indexes_added} indexes for (:Root)")
        # except ClientError as e:
        #     msgs = e.message.split(',')
        #     print(f'do_schema_fixes: New index for Root ok: {msgs[0]}')
        # except Exception as e: 
        #     logger.warning(f"do_schema_fixes: Indexes for Root not created." 
        #                    f" Failed {e.__class__.__name__} {e.message}") 

        # 4. Change 1st Comments to Topic and remove others

        # try:
        #     result = session.run(Delete_comment_tails)
        #     counters = shareds.db.consume_counters(result)
        #     comments_removed = counters.nodes_deleted
        #     print(f"do_schema_fixes: removed {comments_removed} old Comments")
        #
        #     result = session.run(Rename_label_Comment_to_Topic)
        #     counters = shareds.db.consume_counters(result)
        #     labels_changed = counters.labels_added
        #     print(f"do_schema_fixes: changed {labels_changed} Comments to Topics")
        # except Exception as e: 
        #     msg = f"do_schema_fixes: Comments to Topic failed. {e.__class__.__name__} {e.message}"
        #     print (msg)
        #     logger.warning(msg) 


# Removed 5.6.2021
# dropped=0
# created=0
# for label in ['Citation', 'Event', 'Family', 'Media', 'Name',
#               'Note', 'Person', 'Place', 'Place_name', 'Repository',
#               'Source']:
#     try:
#         result = session.run(f'CREATE INDEX ON :{label}(handle)')
#         counters = shareds.db.consume_counters(result)
#         created += counters.indexes_added
#     except ClientError as e:
#         msgs = e.message.split(',')
#         print(f'Unique constraint for {label}.handle ok: {msgs[0]}')
#         return
#     except Exception as e: 
#         logger.warning(f"do_schema_fixes Index for {label}.handle not created." 
#                        f" Failed {e.__class__.__name__} {e.message}") 
# return 
#
# print(f"database.schema_fixes.do_schema_fixes: index updates: {dropped} removed, {created} created")


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
