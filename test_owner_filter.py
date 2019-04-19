import sys
import os
import tempfile
import logging
import io
import shutil
import json
#See: https://github.com/getsentry/responses
import responses
import requests
import pytest

sys.path.append("app")
from app import app

#logging.basicConfig(level=logging.DEBUG, filename="test.log")
logging.basicConfig(level=logging.INFO)

test_username = app.config['TEST_USERNAME']
test_password = app.config['TEST_PASSWORD']
gedcom_dir = "gedcoms/" + test_username
testdata_dir = "testdata"
temp_gedcom = "temporary_test.ged"
temp_gedcom_fname = os.path.join(gedcom_dir,temp_gedcom)

@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    client = app.test_client()

    rv = login(client)
    #txt = "Oma sukupuuni"
    #txt = "Suomikannan käyttäjän alkusivu"
    txt = "Käyttäjän Isotammi-aloitussivu"
    assert txt in rv.data.decode("utf-8")
    yield client

@pytest.fixture
def mocked_responses():
    with responses.RequestsMock() as rsps:
        yield rsps

def test_api(mocked_responses):
    mocked_responses.add(
        responses.GET, 'http://isotest.isotammi.net/scene/persons_all/?div=1',
        json={'div': 1},status=200,
        content_type='application/json')
    resp = requests.get('http://isotest.isotammi.net/scene/persons_all/?div=1')
    assert resp.status_code == 200

#--------

@responses.activate
def test_simple_response():
    
    responses.add(responses.GET, 'http://isotest.isotammi.net/scene/persons_all/?div=1',
                  json={'error': 'not found'}, status=404)

    resp = requests.get('http://isotest.isotammi.net/scene/persons_all/?div=1')
    print(f"---responses {responses}", file=sys.stderr)
    print(f"---resp {resp}", file=sys.stderr)
    #print(f"--- {request}", file=sys.stderr)
    #print(f"--- {user_session}", file=sys.stderr)

    assert resp.json() == {"error": "not found"}

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == 'http://isotest.isotammi.net/scene/persons_all/?div=1'
    assert responses.calls[0].response.text == '{"error": "not found"}'

#----------

# @pytest.mark.parametrize("userid, firstname",[(1,"George"),(2,"Janet")])
# def test_list_valid_user(supply_url,userid,firstname):
#     url = supply_url + "/users/" + str(userid)
#     resp = requests.get(url)
#     j = json.loads(resp.text)
#     assert resp.status_code == 200, resp.text
#     assert j['data']['id'] == userid, resp.text
#     assert j['data']['first_name'] == firstname, resp.text
# 
# def test_list_invaliduser(supply_url):
#     url = supply_url + "/users/50"
#     resp = requests.get(url)
#     assert resp.status_code == 404, resp.text

#---------

def login(client, username=None, password=None):
    if username is None: username = test_username
    if password is None: password = test_password
    return client.post('/login', data=dict(
        email=username,
        password=password,
    ), follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)


def xtest_nologon(client):
    rv = client.get('/',follow_redirects=True)
    assert b'Hanki toimivat tunnukset' in rv.data
    
def xtest_login_logout(client):
    """Make sure login and logout works."""

    #rv = logout(client)
    #data = rv.data.decode("utf-8")
    #assert 'Kirjaudu tunnuksillasi' in data

    rv = login(client, "aaa", "bbb")
    data = rv.data.decode("utf-8")
    assert 'Kirjaudu tunnuksillasi' in data

    rv = login(client)
