import sys
from ui.user_context import UserContext
import pytest
from flask.globals import request
# logging.basicConfig(level=logging.INFO)

@pytest.fixture
def user_env():
    ''' Set a typical set of user session, current user and http request
    '''
    user_session = {}
    user_session['user_context'] = 1
    user_session['lang'] = 'en'
    # # Set current user
    class CurrentUser():pass
    current_user = CurrentUser()
    current_user.is_active = True
    current_user.is_authenticated = True
    current_user.username = 'jussi'
    # Allow request.args.get('div', 0)
    class Request(): pass
    request = Request()
    request.args = {}
    request.args['div'] = '1'
    request.args['cmp'] = 0
    return [user_session, current_user, request]


def test_ownerfilter_nouser():
    # UserContext()
    user_session = {}
    user_session['user_context'] = "common"

    f = UserContext()

    assert f.breed == "common"
    assert f.display_current_material() == 'Isotammi database'

    user_session['user_context'] = "batch"
    assert f.breed == "common"
    assert f.display_current_material() == 'Isotammi database', "No user gets wrong data"


def test_ownerfilter_user_selection(user_env):
    ''' Example: 
            - Show all my data / div=2
            - with common data / cmp=1

        <Request 'http://127.0.0.1:5000/scene/persons/all?div=2&cmp=1' [GET]>
        <User Session {'_fresh': True, '_id': '...', 'csrf_token': '...', 
            'lang': 'en', 'next_person': ['', '>'], 'user_context': 2, 'user_id': 'juha'}>
    '''
    user_session, current_user, request = user_env

    f = UserContext()

    assert f.breed == "common"
    assert f.display_current_material() == 'Isotammi database'
    # x = f.use_owner_filter()
    # assert x == False, "use_owner_filter() failed"
    x = f.use_common()
    assert x == True, "use_common() failed"


def test_ownerfilter_next_item(user_env):
    ''' Example: Show all my data  with common data
            default direction (fw)
            - from previous next_person: start '<'
            - from previous next_person 'Abrahamsson##Juho Kustaa'
            - from previous next_person: end '>'

        <Request 'http://127.0.0.1:5000/scene/persons/all?div=2&cmp=1' [GET]>
        <User Session {'_fresh': True, '_id': '...', 'csrf_token': '...', 
            'lang': 'en', 'next_person': ['', '>'], 'user_context': 2, 'user_id': 'juha'}>
    '''
    user_session, current_user, request = user_env

    # 0. Initialize UserContext with current session, user and request info
    f = UserContext()
    
    # 1. In the beginning
    user_session['person_scope'] = ['', '<']
    f.set_scope_from_request('person_scope')
    #    Read data here --> got required amount
    f.update_session_scope('person_name', '##Elisabet', '#Hansson#Lars', 100, 100)
    
    x = f.next_name('fw')
    assert x == '', "next fw not in the beginning"
    
    # 2. At given point
    user_session['person_scope'] = ['Za', None]
    f.set_scope_from_request('person_scope')
    #    Read data here --> reached end
    f.update_session_scope('person_name', 'Zakrevski##Arseni', 'Östling##Carl', 50, 28)
    
    x = f.next_name('fw')
    assert x == 'Zakrevski##Arseni', "next fw not at given point"
    
    # 3. At end
    user_session['person_scope'] = ['>', None]
    #    Read data here --> reached end
    f.set_scope_from_request('person_scope')
    
    x = f.next_name('fw')
    assert x == '> end', "next fw not at end"

