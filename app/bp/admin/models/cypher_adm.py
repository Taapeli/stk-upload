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
MATCH (u:UserProfile) -[*]-> (a) WHERE u.username=$user
DETACH DELETE a"""

    allowed_email_register = """
CREATE (ae:Allowed_email {
    allowed_email: $email,
    default_role: $role,
    approved: $approved,
    creator: $creator,
    created_at: timestamp() } )"""
    
    allowed_email_confirm = """
MATCH (ae:Allowed_email)
  WHERE ae.allowed_email = $email 
SET ae.confirmed_at = timestamp()
RETURN ae """
             
    allowed_email_update = """
MATCH (ae:Allowed_email)
    WHERE ae.allowed_email = $email
SET ae.default_role = $role,
    ae.approved = $approved,
    ae.creator = $creator
RETURN ae"""

#     allowed_email_update = """
# MATCH (email:allowed_email {allowed_email: $email})    
# SET email.default_role = $role,
#     email.creator = $admin_name,
#     email.approved = $approved,
#     email.created_at = $created_at,     
#     email.confirmed_at = $confirmed_at
# RETURN email""" 
      
    allowed_emails_get = """
MATCH (ae:Allowed_email)
RETURN DISTINCT ae 
    ORDER BY ae.created_at DESC"""    
    
    allowed_email_find = """
MATCH (ae:Allowed_email)
    WHERE ae.allowed_email = $email
RETURN ae"""

    user_profile_register = """
CREATE (up:UserProfile {   
    name: $name,
    email: $email,
    username: $username,
    language: $language,
    research_years: $research_years,
    software: $software,
    researched_names: $researched_names,
    researched_places: $researched_places,
    text_message: $text_message,
    created_at: timestamp() } )"""

    user_profile_update = """
MATCH (up:UserProfile) WHERE up.email = $email 
    SET name = $name,
    SET email = $email,
    SET username = $username,
    SET language = $language,
    SET research_years = $research_years,
    SET software = $software,
    SET researched_names = $researched_names,
    SET researched_places = $researched_places,
    SET text_message = profile.text_message
RETURN up)"""


#     user_profile_add = '''         
# MATCH (u:User) 
#     WHERE u.email = $email
# CREATE (up:UserProfile {
#         username: $username,
#         numSessions: 0,
#         lastSessionTime: timestamp() }
#     ) <-[:SUPPLEMENTED]- (u)'''
    
    user_profile_add = '''         
MATCH (u:User) 
    WHERE u.email = $email
MERGE (p:UserProfile {email: u.email})    
  ON CREATE SET p.name = u.name, p.username = u.username, p.language = u.language, p.created_at = timestamp()
  ON MATCH SET p.language = u.language, p.username = u.username
CREATE (u) -[:SUPPLEMENTED]-> (p)'''
       
    user_profiles_get = '''
MATCH (p:UserProfile)
RETURN DISTINCT p 
    ORDER BY p.created_at DESC'''  

    user_update = '''
MATCH (user:User {email: $email})
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


class Cypher_stats():
    
    get_batches = '''
match (b:Batch) where b.user = $user
optional match (b) -[:OWNS]-> (x)
return b.user as user, b.id as batch,  b.timestamp as timestamp,
    labels(x)[0] as label, count(x) as cnt 
    order by user, batch'''

    get_user_batch_names = '''
match (b:Batch) where b.user = $user
optional match (b) -[r:OWNS]-> (:Person)
return b.id as batch, b.timestamp as timestamp, b.status as status,
    count(r) as persons 
    order by batch'''
