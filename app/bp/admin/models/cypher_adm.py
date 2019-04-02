'''
Created on 8.3.2019

@author: jm
'''
    
class Cypher_adm():
    ' Cypher clauses for admin purposes'
    
    remove_all_nodes = "MATCH (a) DETACH DELETE a"

    remove_data_nodes = """
MATCH (a) 
where not ( 'UserProfile' IN labels(a)
    OR 'Allowed_email' IN labels(a)
    OR 'User' IN labels(a)
    OR 'Role' IN labels(a) )
DETACH DELETE a"""

    remove_my_nodes = """
MATCH (a)<-[r:REVISION|HAS_LOADED]-(u:UserProfile {userName:$user})
DETACH DELETE a"""

    allowed_email_register = """
CREATE (email:Allowed_email {
    allowed_email: $email,
    default_role: $role,
    approved: False
    creator: $admin_name,
    created_at: timestamp() } )"""
    
    allowed_email_confirm = """
MATCH (email:Allowed_email)
  WHERE email.allowed_email = $email 
SET email.confirmed_at = timestamp()
RETURN email """
             
    allowed_email_update = """
MATCH (email:Allowed_email)
    WHERE email.allowed_email = $email    
SET email.default_role = $default_role,
    email.approved = $approved
RETURN email"""
        
    allowed_emails_get = """
MATCH (email:Allowed_email)
RETURN DISTINCT email 
    ORDER BY email.created_at DESC"""    
    
    allowed_email_find = """
MATCH (email:Allowed_email)
    WHERE email.allowed_email = $email
RETURN email"""

    user_profile_register = """
CREATE (up:UserProfile {   
    name: $name,
    email: $email,
    userName: $userName,
    language: $language,
    research_years: $research_years,
    software: $software,
    researched_names: $researched_names,
    researched_places: $researched_places,
    text_message: profile.text_message
    created_at: timestamp() } )"""

    user_profile_update = """
MATCH (up:UserProfile) WHERE up.email = $email 
    SET name = $name,
    SET email = $email,
    SET userName = $userName,
    SET language = $language,
    SET research_years = $research_years,
    SET software = $software,
    SET researched_names = $researched_names,
    SET researched_places = $researched_places,
    SET text_message = profile.text_message
RETURN up)"""
    
    user_profile_add = '''         
MATCH (u:User) 
    WHERE u.email = $email
CREATE (up:UserProfile {
        userName: $username,
        numSessions: 0,
        lastSessionTime: timestamp() }
    ) <-[:SUPPLEMENTED]- (u)'''

    user_update = '''
MATCH (user:User)
    WHERE user.email = $email
SET user.name = $name,
    user.language = $language,
    user.is_active = $is_active,
    user.roles = $roles
RETURN user'''

    user_update_language = '''
MATCH (user:User)
    WHERE user.username = $username
SET 
    user.language = $language
RETURN user'''

    user_role_add = '''         
MATCH  (r:Role) WHERE r.name = $name
MATCH  (u:User) WHERE u.email = $email
CREATE (u) -[:HAS_ROLE]-> (r)'''

    user_role_delete = '''
MATCH (u:User {email: $email}) -[c:HAS_ROLE]-> (r:Role {name: $name})
DELETE c'''
