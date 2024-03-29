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

# coding: utf-8  

#from datetime import datetime
import logging
import traceback
from bl.base import IsotammiException

logger = logging.getLogger('stkserver')

#from neobolt.exceptions import ConstraintError # Obsolete
from neo4j.exceptions import ClientError, ConstraintError #,CypherSyntaxError
from flask_security import utils as sec_utils

import shareds
#!if shareds.app.config.get("NEO4J_VERSION", "0") >= "5.0":
from .cypher_setup import SetupCypher
from bl.admin.models.cypher_adm import Cypher_adm
# else:
#     # Cypher clauses using syntax before Neo4j version 5.0
#     from .cypher_setup_v3_4 import SetupCypher
#     from bl.admin.models.cypher_adm_v3_4 import Cypher_adm

from .schema_fixes import do_schema_fixes

# All User roles here:
ROLES = ({'level':'0',  'name':'guest',    'description':'Rekisteröitymätön käyttäjä, näkee esittelysukupuun'},
         {'level':'1',  'name':'gedcom',   'description':'Kirjautunut käyttäjä, pääsee vain gedcom-muunnoksiin'},
         {'level':'2',  'name':'member',   'description':'Seuran jäsen täysin lukuoikeuksin'},
         {'level':'4',  'name':'research', 'description':'Tutkija, joka voi käsitellä omaa tarjokasaineistoaan'},
         {'level':'8',  'name':'audit',    'description':'Valvoja, joka auditoi ja hyväksyy gramps- ja tarjokasaineistoja'},
         {'level':'16', 'name':'admin',    'description':'Ylläpitäjä kaikin oikeuksin'},
         {'level':'32', 'name':'master',   'description':'Tietokannan pääkäyttäjä, ei sovellusoikeuksia'},
         {'level':'-1', 'name':'to_be_approved','description':'Käyttäjä joka odottaa hyväksymistä'}
)

# ====== Stk database schema ======
#TODO Always change (increment) this, if schema must be updated
# The value is also stored in each Root node
# Syntax: <year>.<running number>.<fix number>
DB_SCHEMA_VERSION = "2023.1.0"
# =============================


def initialize_db():
    '''
    Check and initiate important nodes and constraints and schema fixes,
    if (:Lock{id:'initiated'}) schema is not == database.accessDB.DB_SCHEMA_VERSION.
    
    The database connection has been established in
    pe.neo4j.neo4jengine.Neo4jEngine called from app.setups.py

    ''' 
    if schema_updated():
        logger.info('database.accessDB.initialize_db: checking roles, constraints '
                    f'and schema fixes (version {DB_SCHEMA_VERSION})' )

        if not roles_exist():
            create_role_constraints()
            create_roles()
            
        if not user_exists('master'):
            create_user_constraints()
            create_master_user()
            
        if not user_exists('guest'):
            create_guest_user()

        if not profile_exists('_Stk_'):
            create_single_profile('_Stk_')

        # Fix possible Root.id uniqueness
        fix_empty_roots()

        create_lock_w_constraint()

        create_year_indexes()

        constr_list = {
            "Root":{"id"},
            "Citation":{"iid", "handle"},
            "Event":{"iid", "handle"},
            "Family":{"iid", "handle"},
            "Media":{"iid", "handle"},
            "Note":{"iid", "handle"},
            "Person":{"iid", "handle"},
            "Name":{"iid"},
            "Place":{"iid", "handle"},
            "Place_name":{"iid"},
            "Repository":{"iid", "handle"},
            "Source":{"iid", "handle"},
            "Role":{"name"},
            "User":{"email", "username"},
            "Refname":{"name"},
        }
        check_constraints(constr_list)

        create_freetext_index()
        create_freetext_index_for_notes()
        create_freetext_index_for_sources()
                
        # Fix changed schema
        do_schema_fixes()


# --------------  Database Administration -------------

def delete_database(tx):
    #erase total database 
    tx.run(SetupCypher.delete_database)

def schema_updated():
    # Check, that Lock 'initiated' exists and schema is updated.
    result = shareds.driver.session().run(SetupCypher.check_lock_initiated)
    active_version = 0
    for record in result:
        active_version = record[0]
    return active_version != DB_SCHEMA_VERSION

def roles_exist():
    #  Tarkista roolien olemassaolo
    print(f'Check there exist all {len(ROLES)} user roles')
    roles_found = []
    results = shareds.driver.session().run(SetupCypher.check_role_count)
    for result in results:
        roles_found.append(result[0])
    for i in ROLES:
        if not i['name'] in roles_found:
            print (f'role {i.get("name")} not found')
            return False
    return True

def role_exists(name):
    # print(f'Check the existense of the {name} role')
    num_of_roles = 0  
    for result in shareds.driver.session().run(SetupCypher.role_check_existence, rolename=name):
        num_of_roles = result[0] 
    return(num_of_roles > 0) 
       
def create_role(tx, role):
    try:
        tx.run(SetupCypher.role_create,
            level=role['level'],    
            name=role['name'], 
            description=role['description'])
        print(f'Role {role["name"]} created')
    except ClientError as e:
        #print(f'Role {role["name"]} exists')
        return
    except Exception as e:
        logging.error(f'database.accessDB.create_role: {e.__class__.__name__}, {e}')            
        raise      

def create_roles():
    with shareds.driver.session() as session:
        for role in ROLES:
            create_role(session, role)

        print('Roles initialized')


def user_exists(name):
    print(f'Check the existense of the {name} user')
    num_of_users = 0  
    for result in shareds.driver.session().run(SetupCypher.user_check_existence, username=name):
        num_of_users = result[0]
    return(num_of_users > 0)    

def profile_exists(name):
    print(f'Check the existense of {name} profile')
    num_of_users = 0  
    for result in shareds.driver.session().run(SetupCypher.profile_check_existence, username=name):
        num_of_users = result[0]
    return(num_of_users > 0)    

def remove_unlinked_nodes():
    """    Find and remove nodes with no link (:Batch) --> (x).
    """
    is_loading = "MATCH (b:Root{state:'Storing'}) RETURN count(b)"
    # 
    delete_unlinked_nodes = """
        MATCH (n) WHERE n.handle IS NOT NULL 
        OPTIONAL MATCH (root) --> (n) 
        WITH n, root WHERE root IS NULL
             DETACH DELETE n
             RETURN count(n), LABELS(n)[0] AS label ORDER BY label"""
    deleted = 0

    running = shareds.driver.session().run(is_loading).single()
    if running:
        print(f"database.accessDB.remove_unlinked_nodes: Not run because of 'Storing' batch!")
    else:
        del_d = 0
        while del_d:
            del_d = 0
            result = shareds.driver.session().run(delete_unlinked_nodes)
            for count, label in result:
                print(
                    f"database.accessDB.remove_unlinked_nodes: Deleted {count} {label} not linked to Root"
                )
                del_d += count
                deleted += count

    return deleted

def build_master_user():
    with shareds.app.app_context():
        return( 
            {'username': 'master', 
             'password': sec_utils.hash_password(shareds.app.config['MASTER_USER_PASSWORD']),  
             'email': shareds.app.config['MASTER_USER_EMAIL'], 
             'name': 'Stk-kannan pääkäyttäjä',
             'language': 'fi',  
             'is_active': True,
             #'confirmed_at': datetime.now().timestamp()/1000, 
             'roles': ['master'],
             #'last_login_at': datetime.now().timestamp()/1000,
             #'current_login_at': datetime.now().timestamp()/1000,
             'last_login_ip': '127.0.0.1',  
             'current_login_ip': '127.0.0.1',
             'login_count': 0            
             } )
            
def create_master_user():
    master_user = build_master_user()
    with shareds.driver.session() as session: 
        try:
            session.run(SetupCypher.master_create, master_user) 
        except Exception as e:
            logging.error(f'database.accessDB.create_master_user: {e.__class__.__name__}, {e}')            
            return
    logger.info('Master user account created')    

def build_guest_user():
    with shareds.app.app_context():
        return(shareds.user_model( 
            username = 'guest', 
            password = sec_utils.hash_password(shareds.app.config['GUEST_USER_PASSWORD']),  
            email = shareds.app.config['GUEST_USER_EMAIL'], 
            name = 'Vieraileva käyttäjä',
            language = 'fi',  
            is_active = True,
            #confirmed_at = datetime.now().timestamp()*1000, 
            roles= ['guest'],
            #last_login_at = datetime.now().timestamp()*1000,
            #current_login_at = datetime.now().timestamp()*1000,
            last_login_ip = '127.0.0.1',  
            current_login_ip = '127.0.0.1',
            login_count = 0 )           
               )

def create_guest_user():
    guest = build_guest_user()
    user = shareds.user_datastore.put(guest)                
    if user:
        logger.info('Guest user account created') 
    else:       
        logger.error('Guest user account not created')

def create_single_profile(name):
    """ Create the profile, where approved Audit nodes shall be connected.

        There is no User node for this UserProfile.
    """
    attr = {"numSessions":0,
            "lastSessionTime":0,
            "username":name}
    with shareds.driver.session() as session: 
        try:
            session.run(SetupCypher.single_profile_create, attr=attr)
        except Exception as e:
            logger.error("database.accessDB.create_single_profile"
                         f" Failed {e.__class__.__name__} {e.message}")
            return
    logger.info(f'Profile {name} created')    


def create_role_constraints():
    with shareds.driver.session() as session: 
        try:
            session.run(SetupCypher.set_role_constraint)
        except ClientError as e:
            msgs = e.message.split(',')
            print(f'Role constraint ok: {msgs[0]}')
            return
        except Exception as e:
            logging.error(f'database.accessDB.create_role_constraints: {e.__class__.__name__}, {e}')            
            return
    logger.info('Role constraints created')


def create_user_constraints():
    ''' Unique constraint for User email and user properties
    '''
    cnt = 0
    with shareds.driver.session() as session:
        for query in [SetupCypher.set_user_constraint1, 
                      SetupCypher.set_user_constraint2]:
            try:  
                session.run(query)
                cnt += 1
            except ConstraintError: #print(f'User constraint ok')
                pass
            except ClientError:     #print(f'User constraint seems to be ok')
                pass
            except Exception as e:
                logging.error(f'database.accessDB.create_user_constraints: {e.__class__.__name__}, {e}')            
                return
    if cnt:
        logger.info(f'{cnt} User constraints created')
    else:
        print(f'User constraint ok')

def create_year_indexes():
    ''' Person node is indexed by two year properties.
    '''
    cnt = 0
    with shareds.driver.session() as session:
        for query in [SetupCypher.index_year_birth_low, 
                      SetupCypher.index_year_death_high]:
            try:  
                session.run(query)
                cnt += 1
            except ConstraintError: #print(f'Person years index ok')
                pass
            except ClientError:     #print(f'Person years seems to be ok')
                pass
            except Exception as e:
                msgs = e.message.split(',')
                print(f'database.accessDB.create_year_indexes: {e.__class__.__name__}, {msgs[0]}')            
                return
    if cnt:
        logger.info(f'{cnt} Person years indexes created')
    else:
        print(f'Person years indexes ok')


def check_constraints(needed:dict):
    ''' Create missing UNIQUE constraints for given nodes and parameters.
    '''
    for label, props in needed.items():
        for prop in props:
            create_unique_constraint(label, prop, f"{label}_{prop}")
    return

def create_lock_w_constraint():
    # Initial lock with schema version.
    with shareds.driver.session() as session:
        # Create first Lock node and constraint
        session.run(SetupCypher.update_lock, 
                    id="initiated", 
                    db_schema=DB_SCHEMA_VERSION, 
                    locked=False)
        print(f'Initial Lock (version {DB_SCHEMA_VERSION}) created')
        create_unique_constraint('Lock', 'id', 'lock_id')
        return

def find_roots_to_update() -> int:
    """ Find batches not following current db_schema """
    batches = []
    with shareds.driver.session() as session:
        result = session.run(SetupCypher.find_roots_db_schema, 
                             db_schema=DB_SCHEMA_VERSION)
        for record in result:
            batches.append(record[0])
    return batches

def update_root_schema(batch_id:str):
    """ Mark this batch is following current db_schema """
    if (not batch_id) or (not DB_SCHEMA_VERSION):
        IsotammiException("database.accessDB.update_root_schema FAILED")
    with shareds.driver.session() as session:
        # Also remove neo4jImportId, if exists
        result = session.run(SetupCypher.set_root_db_schema, 
                             id=batch_id, db_schema=DB_SCHEMA_VERSION)
        summary = result.consume()
        if summary.counters.properties_set == 1:
            print(f"update_root_schema: Batch {batch_id} updated to version {DB_SCHEMA_VERSION})")
    return

def re_initiate_nodes_constraints_fixes():
    # Remove initial lock for re-creating nodes, constraints and schema fixes
    with shareds.driver.session() as session:
        session.run(SetupCypher.remove_lock_initiated)
        logger.info(f'database.accessDB.re_initiate_nodes_constraints_fixes: requested')
        print('Initial Lock removed')
        return

def fix_empty_roots():
    """ Remove possible empty (duplicate?) root nodes, to fix Root.id uniqueness.
    
        Reason was missing unique constraint. Also removes unused Root nodes.
    """
    elem_ids = []
    node_sum = 0
    with shareds.driver.session() as session:
        result = session.run(SetupCypher.find_empty_roots)
        # b.id, elementId(b) AS uid, COLLECT(DISTINCT lbl) as lbls
        for _root_id, elem_id, lbls in result:
            elem_ids.append(elem_id)
            logger.info("database.accessDB.fix_empty_roots:"
                        f"empty Root: {elem_id} with links {lbls}")
        elem_cnt = len(elem_ids)
        if elem_cnt:
            result = session.run(SetupCypher.remove_empty_roots, elem_ids=elem_ids)
            summary = result.consume()
            node_cnt = summary.counters.nodes_deleted
            node_sum += node_cnt
            rela_cnt = summary.counters.relationships_deleted
            logger.info(f"database.accessDB.fix_empty_roots: deleted "
                        f"{elem_cnt} empty Root nodes with {rela_cnt} near node types "
                        f"and {node_cnt} nodes")
        print(f"Deleted {elem_cnt} empty Root nodes and {node_sum-elem_cnt} other nodes")
        return

def create_unique_constraint(label, property_name, constraint_name=""):
    """ Create an unique constraint for given label and property.
    """
    with shareds.driver.session() as session:
        query=f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS" + \
            f"   FOR (n:{label}) REQUIRE n.{property_name} IS UNIQUE"
        # query = f"create constraint on (n:{label})"
        try:
            result = session.run(query)
            summary = result.consume()
            #cnt = summary.counters.relationships_created
            if summary and summary.counters.relationships_created:
                print(f"Constraint {constraint_name} for {label}.{property_name} created")
            else:
                print(f"A constraint for {label}.{property_name} exist")

        except Exception as e:
            logger.error("database.accessDB.create_unique_constraint for "
                f"{constraint_name}: {e.__class__.__name__} {e}" )
            raise
    return

def drop_prop_constraints(prop: str):
    """ Drop all indexes for given property.

        Database copy from older version to new database created temporary
        neo4jImportId fields and their indexes. Here we drop their unique indexes,
    """
    cy_list_constraints = """
        SHOW ALL CONSTRAINTS 
        YIELD name, labelsOrTypes, properties WHERE $prop in properties"""
    # ╒═════════════════════╤═════════════════╤═════════════════╕
    # │name                 │labelsOrTypes    │properties       │
    # ╞═════════════════════╪═════════════════╪═════════════════╡
    # │"constraint_2026f827"│["Note"]         │["neo4jImportId"]│
    # ├─────────────────────┼─────────────────┼─────────────────┤

    drops_done = 0
    drops_todo = []
    with shareds.driver.session() as session: 
        result = session.run(cy_list_constraints, prop=prop)
        for record in result:
            constraint_name = record[0]
            label = record[1][0]
            drops_todo.append((constraint_name,label))
        for name, label in drops_todo:
            result = session.run(f"DROP CONSTRAINT {name} IF EXISTS")
            summary = result.consume()
            count = summary.counters.constraints_removed
            drops_done += count
            print(f"drop_prop_constraints: {name} for {label}.{prop} "
                  f"{['not existed','removed'][count]}")
                
        if drops_done:
            print(f"drop_prop_constraints: {drops_done} indexes removed")
    return drops_done


def create_freetext_index():
    #Note: Should not need ClientError with Neo4j 5.1 IF NOT EXISTS
    #TODO: Use create_person_search_index, create_note_text_index and create_source_text_index
    #      cypher clauses for text-2.0 indexes
    try:
        _result = shareds.driver.session().run(Cypher_adm.create_freetext_index)
    except ClientError as e:
        msgs = e.message.split(',')
        print(f'Create_freetext_index ok: {msgs[0]}')
        return
    except Exception as e:
        traceback.print_exc()
        logger.error(f'database.accessDB.create_freetext_index: {e.__class__.__name__} {e}' )
        raise

def create_freetext_index_for_notes():
    try:
        _result = shareds.driver.session().run(Cypher_adm.create_freetext_index_for_notes)
    except ClientError as e:
        msgs = e.message.split(',')
        print(f'Create_freetext_index for notes, ok: {msgs[0]}')
        return
    except Exception as e:
        traceback.print_exc()
        logger.error(f'database.accessDB.create_freetext_index_for_notes: {e.__class__.__name__} {e}' )
        raise

def create_freetext_index_for_sources():
    try:
        _result = shareds.driver.session().run(Cypher_adm.create_freetext_index_for_sources)
    except ClientError as e:
        msgs = e.message.split(',')
        print(f'Create_freetext_index for sources, ok: {msgs[0]}')
        return
    except Exception as e:
        traceback.print_exc()
        logger.error(f'database.accessDB.create_freetext_index_for_sources: {e.__class__.__name__} {e}' )
        raise
