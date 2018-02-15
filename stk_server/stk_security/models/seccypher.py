#add submission time for all SUBMITTED with ON MATCH SET and ON CREATE SET
class Cypher():

    user_find = (
        '''
        MATCH (user:User) 
            WHERE user.username = $username_or_email
            OR user.email = $username_or_email 
        RETURN user 
        '''
        )

    username_find = (
        '''
        MATCH (user:User)
            WHERE user.username = $username
        RETURN user 
        '''
        )

    email_or_id_find = ( 
        '''
        MATCH (user:User) 
            WHERE user.email = $id_or_email 
               OR id(user) = $id_or_email   
        RETURN user 
        '''
        )

    id_find = (
        '''
        MATCH (user:User) 
            WHERE id(user) = $id 
        RETURN user 
        '''
        )

    get_users = (
        '''
        MATCH (user:User)-[:HAS_ROLE]->(role:Role)  
        RETURN DISTINCT user, COLLECT(role) 
            ORDER BY user.username
        '''
        )

    confirm_email = (
        '''
        MATCH (user:User)  
            WHERE user.email = $email 
            SET    confirmed_at = timestamp()
        RETURN user
        '''
        )

    password_reset = (
        '''
        MATCH (user:User)
            WHERE user.email = $email
        SET user.password = $password 
        RETURN user'
        '''
        )

    user_register = (
        '''
        MATCH  (role:Role) WHERE role.name IN $roles
        CREATE (user:User 
            {username : $username, 
            password : $password,  
            email : $email, 
            name : $name,
            language : $language, 
            is_active : $is_active, 
            roles : $roles}) 
            -[:HAS_ROLE]->(role) 
        RETURN user
        '''
        )

    user_update = (
        '''
        MATCH (user:User)
            WHERE id(user) = $id 
        SET user.username = $username,
            user.password = $password, 
            user.email = $email, 
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
        RETURN user
        '''
        )

    user_del = (
        '''
        MATCH (user:User)'
            WHERE user.username = $uname_or_mail 
            OR user.email = $uname_or_mail 
        DELETE user 
        '''
        )

    user_profile_add = (
        '''         
        MATCH (u:User) WHERE id(u) = $uid
        CREATE (up:UserProfile
            {userName: $username,
            numSessions : 0,
            lastSessionTime : timestamp() })
            <-[:SUPPLEMENTED]-(u) 
        '''
        )

    role_register = (
        '''
        CREATE (role:Role 
            {name : $name,
            description : $description,
            time : $timestamp }
        RETURN role
        '''
        )

    role_find = (
        '''
        MATCH (role:Role) 
            WHERE role.name = $name 
        RETURN role 
        '''
        )

    role_get = (
        '''
        MATCH (role:Role)
            WHERE id(role) = $id
        RETURN role 
        '''
        )

    user_roles_delete = (
        '''
        MATCH (u:User)-[h:HAS_ROLE]->() 
            WHERE id(u)=$id
        SET u.roles = []
        DELETE h
        '''
        )

    roles_get = (
        '''
        MATCH (role:Role)
        RETURN role 
        '''
        )

    roles_count = (
        '''
        MATCH (a:Role) RETURN COUNT(a)
        '''
        )   

    user_roles_find = (
        '''
        MATCH (user:User{email:$email})--(role:Role) 
        RETURN role 
        '''
        )

    user_role_add = (
        '''         
        MATCH  (r:Role {name: &name}), 
                (u:User) WHERE id(u) = &id 
        SET u.roles = u.roles + r.name 
        CREATE (u)-[:HAS_ROLE]->(r)
        '''
        )


    email_register = (
        '''
        CREATE (email:Allowed_email 
            {allowed_email : $email,
            default_role : $role,
            timestamp : timestamp() })
        '''
        )
    
    
    get_emails = (
        '''
        MATCH (email:Allowed_email)
        RETURN DISTINCT email 
            ORDER BY email.timestamp DESC
        '''
        )
    
    
    find_email = (
        '''
        MATCH (email:Allowed_email)
        RETURN DISTINCT email 
            WHERE email.allowed_email = $email
        ''' 
        )
    
       