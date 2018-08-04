import sys
import os
import tempfile
import logging
import io

import pytest

sys.path.append("stk_server")
from stk_server import app

#logging.basicConfig(level=logging.DEBUG, filename="test.log")
logging.basicConfig(level=logging.INFO)

test_username = app.config['TEST_USERNAME']
test_password = app.config['TEST_PASSWORD']
gedcom_dir = "gedcoms/" + test_username
test_gedcom = "aaa.ged"
test_gedcom_fname = os.path.join(gedcom_dir,test_gedcom)

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    client = app.test_client()

    rv = login(client)
    assert b'Oma sukupuuni' in rv.data

    yield client
    

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
    
def test_login_logout(client):
    """Make sure login and logout works."""

    rv = login(client)
    assert b'Oma sukupuuni' in rv.data

    rv = logout(client)
    assert b'Kirjaudu tunnuksillasi' in rv.data

    rv = login(client, "aaa", "bbb")
    assert b'Kirjaudu tunnuksillasi' in rv.data

    try:
        os.remove(test_gedcom_fname)
    except FileNotFoundError:
        pass
    
def test_gedcom_upload(client):
    rv = login(client)
    assert not os.path.exists(test_gedcom_fname)

    args = dict(file=(io.BytesIO(b"aaa"),"aaa.ged"),desc="Description")
    rv = client.post('/gedcom/upload',data=args,follow_redirects=True, content_type='multipart/form-data')
    assert b'Ladatut gedcomit' in rv.data
    assert b'aaa.ged' in rv.data
    assert b'Description' in rv.data
    assert os.path.exists(test_gedcom_fname)
        
def test_gedcom_list(client):
    rv = login(client)

    rv = client.get('/gedcom/list')
    assert b'Ladatut gedcomit' in rv.data
    
    for name in os.listdir(gedcom_dir):
        if not name.endswith(".ged"): continue
        assert name in rv.data.decode("utf-8")

def test_gedcom_info(client):
    rv = login(client)

    rv = client.get('/gedcom/info/'+test_gedcom)
    assert b'Muunnokset' in rv.data

def test_gedcom_versions(client):
    rv = login(client)

    rv = client.get('/gedcom/versions/'+test_gedcom)
    assert b'[]' in rv.data

def test_gedcom_transform_params(client):
    rv = login(client)

    rv = client.get('/gedcom/transform/'+test_gedcom+"/kasteet.py")
    assert b'kasteet muunnosparametrit' in rv.data
    
def test_gedcom_transform(client):
    rv = login(client)

    args = {
        "--dryrun":"on",
        "--display-changes":"on",   
    }
    rv = client.post('/gedcom/transform/'+test_gedcom+"/kasteet.py",data=args)
    assert b'Lokitiedot' in rv.data
    
        
