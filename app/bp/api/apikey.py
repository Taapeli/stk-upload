import shareds
 
import uuid

cypher_check_apikey = """
    match   (user:User{is_active:true}) --> 
            (prof:UserProfile{apikey:$apikey})
    where 'research' in user.roles 
    return user
"""
    
cypher_get_apikey = """
    match (prof:UserProfile{username:$username})
    return prof.apikey as apikey
"""

cypher_save_apikey = """
    match (prof:UserProfile{username:$username})
    set prof.apikey = $apikey
"""

def is_validkey(apikey):
    result = shareds.driver.session().run(cypher_check_apikey,apikey=apikey).single()
    if result: 
        return True
    else:
        return False
    

def save_apikey(current_user, apikey):
    result = shareds.driver.session().run(cypher_save_apikey,username=current_user.username,apikey=apikey).single()


def get_apikey(current_user):
    if 'research' not in current_user.roles: return None
    result = shareds.driver.session().run(cypher_get_apikey,username=current_user.username).single()
    if result: 
        apikey = result['apikey']
    else:
        apikey = None
    if not apikey:
        apikey = uuid.uuid4().hex
        save_apikey(current_user,apikey)
    return apikey


