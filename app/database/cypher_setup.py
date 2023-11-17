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
Moved on 14.5.2019 from database.accessDB

@author: jm
'''

class SetupCypher():
    """ Cypher clauses for setup """

    # erase database 
    delete_database = """
    MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r
    """

    # Missing lock means there is need for initialisation 
    check_lock_initiated = """
    MATCH (lock:Lock {id:'initiated'}) RETURN lock.db_schema
    """
    update_lock = """
    MERGE (lock:Lock {id:$id}) 
        SET lock.locked = $locked
        SET lock.db_schema = $db_schema
    """
    remove_lock_initiated = """
    MATCH (lock:Lock {id:'initiated'}) DELETE lock
    """
    find_empty_roots = """
    MATCH (b:Root) WHERE b.file IS NULL
    OPTIONAL MATCH (b) --> (x)
        WITH b, LABELS(x)[0] AS lbl ORDER BY b.id, lbl
    RETURN b.id, elementId(b) AS uid, COLLECT(DISTINCT lbl) as lbls
    """
    remove_empty_roots = """
    MATCH (b:Root) WHERE elementId(b) in $elem_ids
    OPTIONAL MATCH (b) --> (x)
        DETACH DELETE b, x
    """

    check_role_count = """
    MATCH (a:Role) RETURN a.name
    """
    set_role_constraint = """
    CREATE CONSTRAINT FOR (role:Role) 
        REQUIRE role.name IS UNIQUE
    """
    role_check_existence = """
    MATCH  (role:Role) WHERE role.name = $rolename RETURN COUNT(role)
    """
    role_create = """
    CREATE (role:Role {level: $level, name: $name, 
                       description: $description, timestamp: timestamp()})
    """

    user_check_existence = """
    MATCH  (user:User) WHERE user.username = $username 
    RETURN COUNT(user)
    """
    profile_check_existence = """
    MATCH  (u:UserProfile {username:$username})
    RETURN COUNT(u)
    """

    set_user_constraint1 = """
    CREATE CONSTRAINT FOR (user:User) 
        REQUIRE user.email IS UNIQUE
    """
    set_user_constraint2 = """
    CREATE CONSTRAINT FOR (user:User) 
        REQUIRE user.username IS UNIQUE
    """

    index_year_birth_low = "CREATE INDEX ON :Person(birth_low)"
    index_year_death_high = "CREATE INDEX ON :Person(death_high)"

    master_create = """
    MATCH  (role:Role) WHERE role.name = 'master'
    CREATE (user:User 
        {username : $username, 
        password : $password,  
        email : $email, 
        name : $name,
        language : $language, 
        is_active : $is_active,
        confirmed_at : timestamp(), 
        roles : $roles,
        last_login_at : timestamp(),
        current_login_at : timestamp(),
        last_login_ip : $last_login_ip,
        current_login_ip : $current_login_ip,
        login_count : $login_count} )           
        -[:HAS_ROLE]->(role)
    """ 
    single_profile_create = """
    CREATE (u:UserProfile)
        SET u = $attr
    """ 

