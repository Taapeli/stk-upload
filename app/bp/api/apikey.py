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


