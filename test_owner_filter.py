import sys
# import os
# import tempfile
# import logging
# import io
# import shutil
# import json
from models.owner import OwnerFilter
import pytest
# logging.basicConfig(level=logging.INFO)


@pytest.fixture(scope="module")
def create_env():
    class MockUserSession():
        ''' Usage example: user_session.get('username', None)
        '''
        def __init(self, **args):
            ''' When creating this mock the arguments must be a dict like 
                {'user_id':None, 'owner_filter':None, 'next_person':['',''], 'lang':'fi'}
            '''
            self.args = args
            
        def get(self, var_name, default_value=None):
            if var_name in self.args.keys():
                return self.args[var_name]
            else:
                return default_value
    
    class MockRequest():
        ''' Usage example: request.args.get('div', 0)
        '''
        def __init__(self, **args):
            ''' When creating this mock the arguments must be a dict like 
                {'div':'2', 'cmp':'1'}
            '''
            # request.args ~ ImmutableMultiDict([('div', '2'), ('cmp', '1')])
            if args:
                self.args = args
            else:
                self.args = {}
    
    mock_request = MockRequest
    mock_user_session = MockUserSession

#------------------------------------------------------------------------------

@pytest.mark.usefixtures("create_env") 
def test_ownerfilter_getuser():
    user_session = create_env.MockUserSession(owner_filter=1, username='jussi')
    user = user_session.get('username', None)
    assert user == 'jussi'

    f = OwnerFilter(user_session)

    assert f.filter == 1
    assert f.owner_str() == 'Isotammi database'


def test_ownerfilter_1():
    user_session = {}
    user_session['owner_filter'] = 1

    f = OwnerFilter(user_session)

    assert f.filter == 1
    assert f.owner_str() == 'Isotammi database'
