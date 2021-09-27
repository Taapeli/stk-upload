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

class Cypher():
    """ Class for user and role register and access.
    
        (The class setups.SetupCypher checked and fixed exsistence of 
        master user and essential roles.)
        
        #TODO add submission time for all SUBMITTED with ON MATCH SET and ON CREATE SET
    """

# Not in use
#     user_find = '''
# MATCH (user:User) 
#     WHERE user.username = $username_or_email
#        OR user.email = $username_or_email 
# RETURN user'''

    username_find = '''
MATCH (user:User)
    WHERE user.username = $username
RETURN user'''

    email_or_id_find = '''
MATCH (user:User) 
    WHERE user.email = $id_or_email 
       OR user.username = $id_or_email   
RETURN user'''

    id_find = '''
MATCH (user:User) 
    WHERE user.username = $id 
RETURN user'''

    get_users = '''
MATCH (user:User)
OPTIONAL MATCH (user) -[:HAS_ROLE]-> (role:Role)  
RETURN DISTINCT user, COLLECT(role) 
    ORDER BY user.username'''

    confirm_email = '''
MATCH (user:User)  
    WHERE user.email = $email 
SET confirmed_at = timestamp()
RETURN user'''

    password_reset = '''
MATCH (user:User)
    WHERE user.email = $email
SET user.password = $password 
RETURN user'''

    user_register = '''
MATCH  (role:Role)
    WHERE role.name IN $roles
CREATE (user:User {
        username: $username, 
        password: $password,  
        email: $email, 
        name: $name,
        language: $language, 
        is_active: $is_active, 
        confirmed_at: $confirmed_at,
        roles: $roles}
    ) -[:HAS_ROLE]-> (role) 
RETURN user'''

    user_update = '''
MATCH (user:User)
    WHERE user.email = $email
SET user.username = $username,
    user.password = $password, 
    user.name = $name,
    user.language = $language,
    user.is_active = $is_active,
    user.confirmed_at = $confirmed_at,
    user.roles = $roles,
    user.last_login_at = $last_login_at,
    user.current_login_at = $current_login_at,
    user.last_login_ip = $last_login_ip,
    user.current_login_ip = $current_login_ip,
    user.login_count = $login_count 
RETURN user'''

# # Ei käytössä, rikki
#     user_to_profile_link = '''
# MATCH (user:User) 
#     WHERE user.email = $email   
# MATCH (profile:UserProfile)
#     WHERE profile.email = $email
# CREATE  (user) -[:HAS_ROLE]-> (profile) 
# RETURN user'''    
        

    user_del = '''
MATCH (user:User)'
    WHERE user.username = $uname_or_mail 
       OR user.email = $uname_or_mail 
DELETE user'''

    role_register = '''
CREATE (role:Role {
        name: $name,
        description: $description,
        time: $timestamp }
RETURN role'''

# --> role_get
#     role_find = ''' 
# MATCH (role:Role) 
#     WHERE role.name = $name 
# RETURN role'''

    role_get = '''
MATCH (role:Role)
    WHERE role.name = $id
RETURN role'''

    user_roles_delete = '''
MATCH (u:User) -[h:HAS_ROLE]-> () 
    WHERE role.name =$id
SET u.roles = []
DELETE h'''

    roles_get = '''
MATCH (role:Role)
RETURN role'''

    roles_count = '''
MATCH (a:Role)
RETURN COUNT(a)''' 

    user_roles_find = '''
MATCH (user:User{email:$email}) -[:HAS_ROLE]-> (role:Role) 
RETURN role'''

    user_role_add = '''         
MATCH  (r:Role) WHERE r.name = $name
MATCH  (u:User) WHERE u.email = $email
CREATE (u) -[:HAS_ROLE]-> (r)'''

    user_role_delete = '''
MATCH (u:User {email: $email}) -[c:HAS_ROLE]-> (r:Role {name: $name})
DELETE c'''

    get_userprofile = '''
MATCH (p:UserProfile {username: $username})
RETURN p'''

    get_userprofile_w_roles = """
MATCH (user:User) -[:SUPPLEMENTED]-> (p:UserProfile)
    WHERE user.username = $username
MATCH (user) -[r:HAS_ROLE]-> (role)
WITH p, role ORDER BY role.level LIMIT 200
RETURN p, role"""

