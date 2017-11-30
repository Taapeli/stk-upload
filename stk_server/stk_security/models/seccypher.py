#add submission time for all SUBMITTED with ON MATCH SET and ON CREATE SET
class Cypher():
	
	user_find = (
		'''
		MATCH (user:User) 
			WHERE user.username = $username 
				OR user.email = $email 
		RETURN user 
		'''
		)
	
	username_find = (
		'MATCH (user:User) '
			' WHERE user.username = $username '
		' RETURN user ')
	
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
		MATCH (user:User)--(role:Role)  
		RETURN DISTINCT user, role
			ORDER BY user.name
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
		'MATCH (user:User) '
			' WHERE user.email = $email '
			' SET user.password = $password ' 
			'RETURN user')
	
	user_register = (
		'''
		MATCH  (role:Role) WHERE role.name = $roles[0]  
		CREATE (user:User 
			{username : $username, 
			password : $password,  
			email : $email, 
			name : $name, 
			is_active : $is_active, 
			roles : $roles}) 
			-[:HAS_ROLE]->(role) 
		RETURN user
		'''
		)

	user_update = (
		'MATCH (user:User) '
			'WHERE id(user) = $id '
#			'SET user = $properties') '
			'SET user.username = $username, '
			'    user.password = $password, ' 
			'    user.email = $email, '
			'    user.name = $name, '
			'    user.is_active = $is_active, '
 			'    user.confirmed_at = $confirmed_at, '
			'    user.roles = $roles ' 
		'RETURN user')
	
	user_del = (
		'MATCH (user:User) '
			' WHERE user.username = $uname_or_mail '
			' OR user.email = $uname_or_mail  '
			' DELETE user ')

	role_register = (
		'CREATE (role:Role ' 
			'{name : $name, '
			' description : $description, '
			' time : $timestamp, ' )
	
	role_find = (
		'MATCH (role:Role) '
			'WHERE role.name = $name '
			'RETURN role ')
	
	role_get = (
		'MATCH (role:Role) '
			'WHERE id(role) = $id '
			'RETURN role ')
	
	user_roles_delete = (
		'''
		MATCH (u:User)-[h:HAS_ROLE]->() 
			WHERE id(u)=$id
		SET u.roles = []
		DELETE h
		'''
		)
	
	roles_get = (
		'MATCH (role:Role) '
			'RETURN role ')
		
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
            SET u.roles = u.roles + [r.name] 
            CREATE (u)-[:HAS_ROLE]->(r)
        '''
        )
