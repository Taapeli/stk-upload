'''
Created on 14.9.2023

@author: jm
'''
#---- Replace m.coord tuple by m.point                  ----
#---- Remove unused x.neo4jImportId and set b.cd_schema ----

# --- For DB_SCHEMA_VERSION = ''2022.1.10''...'2023.1.0' 14.9.2023JMä

import shareds

def coordinates_to_point_type():
    """ 1. For each batch b browse objects a:
            - add missing a.iid keys and remove a.uuid keys
            - remove a.uuid
            - finally update b.db_schema
    """
    from database.accessDB import DB_SCHEMA_VERSION, remove_prop_constraints

    def remove_neo4jImportId_constraint():
        """ Remove all neo4jImportId contraints. """
        remove_prop_constraints("neo4jImportId")

    def remove_unused_neo4jImportId():
        """ Loop nodes with neo4jImportId value,
            - for all nodes remove a.neo4jImportId
            - finally set b.db_schema for the batch
            After that no objects has a.neo4jImportId key
        """
        q_remove_neo4jImportId = """
            MATCH (a) WHERE NOT a.neo4jImportId IS NULL
                WITH a LIMIT 500
            SET a.neo4jImportId = NULL
            RETURN COUNT(a) AS cnt"""
        cnt = -1
        n_objects = 0
        while cnt != 0:
            cnt = 0
            with shareds.driver.session() as session:
                results = session.run(q_remove_neo4jImportId)
                for record in results:
                    cnt = record.get("cnt", 0)
                n_objects += cnt
                print(f"# ... remove_unused_neo4jImportId: removed {cnt} values")
        return n_objects

    # =========== coordinates to point type starts here ==============

    q_get_batches = """
        MATCH (b:Root) 
        WHERE b.db_schema IS NULL OR NOT b.db_schema = $schema_ver
        RETURN b.id ORDER BY b.id DESC"""
    q_temp = """
        MATCH (b:Root {id:$batch_id}) 
        MATCH (b) --> (p:Place) WHERE NOT p.coord IS NULL
        WITH b limit 2 // HUOM!
            SET p.point = POINT({longitude: p.coord[0], latitude: p.coord[1]})
            SET p.cood = NULL
        RETURN p.point"""
    # q_search_missing_iids = """
    #     MATCH (b:Root{id:$bid})
    #     OPTIONAL MATCH (b) --> (a) WHERE a.iid IS NULL
    #     WITH labels(a)[0] AS lbl, id(a) AS uid
    #         ORDER BY lbl LIMIT $limit
    #     RETURN lbl, COLLECT(uid) AS uids"""
    # q_remove_uuids = """
    #     MATCH (b:Root{id:$bid})
    #     OPTIONAL MATCH (b) --> (a) WHERE a.uuid IS NOT NULL
    #     WITH b, a LIMIT $limit
    #         SET a.uuid = NULL
    #     RETURN COUNT(a)"""
    q_update_batch_schema = """
        MATCH (b:Root {id:$bid}) 
            SET b.db_schema = $schema_ver"""


    with shareds.driver.session() as session:
        total_batches = 0
        total_nodes = 0
        limit = 1000
        batches = []

        # 1. List all batches

        result = session.run(q_get_batches, schema_ver=DB_SCHEMA_VERSION)

        for record in result:
            batch_id = record[0]
            batches.append(batch_id)

        # 2. For each batch

        n_removed = 0
        for batch_id in batches:

            # 2.1 Find objects without a.iid

            done = False
            n_iid_set = 0
            while not done:
                obj_ids = []
                done = True
                #print(f"#uuid_to_iid: next {limit} objects, schema={DB_SCHEMA_VERSION!r}")

                result = session.run(q_search_missing_iids, bid=batch_id, limit=limit)

                for label, uids in result:
                    if label:
                        obj_ids.append((label, uids))
                        done = False

                # 2.2 Set a.iid to those found

                if obj_ids:
                    a_nodes = set_iid_keys(batch_id, obj_ids)

                    #print(f"#uuid_to_iid: {batch_id}: {a_nodes} iid creations")
                    n_iid_set += a_nodes
                    total_nodes += a_nodes
                    total_batches += 1

            # 2.3 Remove a.uuid parameters, where still exists

            done = False
            n_removed = 0
            while not done:
                done = True

                result = session.run(q_remove_uuids, bid=batch_id, limit=1000)

                cnt = result.single()[0]
                if cnt > 0:
                    done = False
                    n_removed += cnt
                    print(f"# ... remove_uuid_keys: {batch_id!r}: {cnt} uuid keys removed")

            # 2.4 Batch done; Update Root.db_chema

            session.run(q_update_batch_schema,
                        bid=batch_id, schema_ver=DB_SCHEMA_VERSION)
            print(f"#uuid_to_iid: {batch_id!r} complete, {n_iid_set} keys generated")
            pass

        print(f"#uuid_to_iid: TOTAL {total_batches} batch updates,"\
              f" {total_nodes} iid creations, {n_removed} uuid removals.")
    return