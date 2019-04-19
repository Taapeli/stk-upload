import sys
from models.owner import OwnerFilter
import pytest
from flask.globals import request
# logging.basicConfig(level=logging.INFO)


def test_ownerfilter_nouser():
    # OwnerFilter(user_session)
    user_session = {}
    user_session['owner_filter'] = 1

    f = OwnerFilter(user_session)

    assert f.filter == 1
    assert f.owner_str() == 'Isotammi database'

    user_session['owner_filter'] = 2
    assert f.filter == 1
    assert f.owner_str() == 'Isotammi database', "No user gets wrong data"


def test_ownerfilter_user_selection():
    ''' Example: 
            - Show all my data / div=2
            - with common data / cmp=1

        <Request 'http://127.0.0.1:5000/scene/persons_all/?div=2&cmp=1' [GET]>
        <User Session {'_fresh': True, '_id': '...', 'csrf_token': '...', 
            'lang': 'en', 'next_person': ['', '>'], 'owner_filter': 2, 'user_id': 'juha'}>
    '''
    # OwnerFilter(user_session, current_user, request)
    # Allow user_session.get('username', None)
    user_session = {}
    user_session['owner_filter'] = 1
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

    f = OwnerFilter(user_session, current_user, request)

    assert f.filter == 1
    assert f.owner_str() == 'Isotammi database'
    x = f.use_owner_filter()
    assert x == False, "use_owner_filter() failed"
    x = f.use_common()
    assert x == True, "use_common() failed"


def test_ownerfilter_next_person():
    ''' Example: Show all my data  with common data
            default direction (fw)
            - from previous next_person: start '<'
            - from previous next_person 'Abrahamsson##Juho Kustaa'
            - from previous next_person: end '>'

        <Request 'http://127.0.0.1:5000/scene/persons_all/?div=2&cmp=1' [GET]>
        <User Session {'_fresh': True, '_id': '...', 'csrf_token': '...', 
            'lang': 'en', 'next_person': ['', '>'], 'owner_filter': 2, 'user_id': 'juha'}>
    '''
    # OwnerFilter(user_session, current_user, request)
    # Allow user_session.get('username', None)
    user_session = {}
    user_session['owner_filter'] = 1
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

    f = OwnerFilter(user_session, current_user, request)
    
    # 1. In the beginning
    user_session['next_person'] = ['', '<']
    f.store_next_person(request)
    
    x = f.person_name_fw()
    assert x == ' ', "next fw not in the beginning"
    
    # 2. At given point
    user_session['next_person'] = ['', 'Man']
    f.store_next_person(request)
    
    x = f.person_name_fw()
    assert x == 'Man', "next fw not at given point"
    
    # 3. At end
    user_session['next_person'] = ['', '>']
    f.store_next_person(request)
    
    x = f.person_name_fw()
    assert x == '> end', "next fw not at end"

