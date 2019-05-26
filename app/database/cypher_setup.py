'''
Moved on 14.5.2019 from database.adminDB

@author: jm
'''

class SetupCypher():
    """ Cypher classes for setup """
#erase database 
    delete_database = """
    MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r
    """
    check_role_count = """
    MATCH (a:Role) RETURN COUNT(a)
    """

    set_role_constraint = """
    CREATE CONSTRAINT ON (role:Role) ASSERT role.name IS UNIQUE
    """

    role_create = """
    CREATE (role:Role 
    {level: $level, name: $name, 
    description: $description, timestamp: timestamp()})
    """

    master_check_existence = """
    MATCH  (user:User) WHERE user.username = 'master' RETURN COUNT(user)
    """
        
    email_val = """
    MATCH (a:Allowed_email) WHERE a.allowed_email = $email RETURN COUNT(a)
    """

    set_user_constraint1 = """
    CREATE CONSTRAINT ON (user:User) 
        ASSERT (user.email) IS UNIQUE;
    """
 
    set_user_constraint2 = """
    CREATE CONSTRAINT ON (user:User) 
        ASSERT (user.username) IS UNIQUE;
    """  
     
    set_allowed_email_constraint = """ 
    CREATE CONSTRAINT ON (email:Allowed_email) 
    ASSERT email.allowed_email IS UNIQUE
    """  
    
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