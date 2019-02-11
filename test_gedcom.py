import sys
import os
import tempfile
import logging
import io
import shutil

import pytest

sys.path.append("app")
from app import app

#logging.basicConfig(level=logging.DEBUG, filename="test.log")
logging.basicConfig(level=logging.INFO)

test_username = app.config['TEST_USERNAME']
test_password = app.config['TEST_PASSWORD']
gedcom_dir = "gedcoms/" + test_username
testdata_dir = "gedcoms/testdata"
temp_gedcom = "temporary_test.ged"
temp_gedcom_fname = os.path.join(gedcom_dir,temp_gedcom)

@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    client = app.test_client()

    rv = login(client)
    #txt = "Oma sukupuuni"
    txt = "Suomikannan käyttäjän alkusivu"
    assert txt in rv.data.decode("utf-8")
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
    
def xtest_login_logout(client):
    """Make sure login and logout works."""

    #rv = logout(client)
    #data = rv.data.decode("utf-8")
    #assert 'Kirjaudu tunnuksillasi' in data

    rv = login(client, "aaa", "bbb")
    data = rv.data.decode("utf-8")
    assert 'Kirjaudu tunnuksillasi' in data

    rv = login(client)
    
def test_gedcom_upload(client):
    try:
        os.remove(temp_gedcom_fname)
    except FileNotFoundError:
        pass
    assert not os.path.exists(temp_gedcom_fname) 

    args = dict(file=(io.BytesIO(b"0 @I123@ INDI"),temp_gedcom),desc="Description")
    rv = client.post('/gedcom/upload',data=args,follow_redirects=True, content_type='multipart/form-data')
    data = rv.data.decode("utf-8")
    assert os.path.exists(temp_gedcom_fname)
    assert 'Lisävalinnat' in data
    assert temp_gedcom in data
    #os.remove(temp_gedcom_fname)
        
def test_gedcom_list(client):
    rv = client.get('/gedcom/list')
    data = rv.data.decode("utf-8")
    assert 'Ladatut gedcomit' in data
    
    for name in os.listdir(gedcom_dir):
        if not name.endswith(".ged"): continue
        assert name in data

def test_gedcom_info(client):
    rv = client.get('/gedcom/info/'+temp_gedcom)
    data = rv.data.decode("utf-8")
    assert 'Muunnokset' in data

def test_gedcom_versions(client):
    rv = client.get('/gedcom/versions/'+temp_gedcom)
    data = rv.data.decode("utf-8")
    assert type(eval(data)) == list

def test_gedcom_transform_params(client):
    rv = client.get('/gedcom/transform/'+temp_gedcom+"/kasteet.py")
    data = rv.data.decode("utf-8")
    assert 'kasteet muunnoksen vaihtoehdot' in data
    
def dotest_gedcom_transform(client,test_gedcom,transform,expected,**options):
    args = {
        "--dryrun":"on",
        "--display-changes":"on",   
    }
    orig_file = os.path.join(testdata_dir,test_gedcom)
    dest_file = os.path.join(gedcom_dir,temp_gedcom)
    shutil.copyfile(orig_file,dest_file)
    args.update({"--"+option:value for option,value in options.items()})
    rv = client.post('/gedcom/transform/'+temp_gedcom+"/"+transform,data=args)
    data1 = rv.data.decode("utf-8")
    open("trace.txt","w").write(data1)
    data = eval(rv.data.decode("utf-8"))
    assert data["stderr"] == ""
    assert expected in data['stdout']

def test_gedcom_transform_kasteet(client):
    dotest_gedcom_transform(client,"kasteet-1.ged","kasteet.py","PLAC p1")
    
def test_gedcom_transform_marriages(client):
    dotest_gedcom_transform(client,"marriages-1.ged","marriages.py","PLAC p3, p1")

def test_gedcom_transform_places(client):
    dotest_gedcom_transform(client,"paikat-1.ged","places.py","2 PLAC Finland, Loviisa, a",
                            reverse="on")

def test_gedcom_transform_sukujutut(client):
    dotest_gedcom_transform(client,"sukujutut-1.ged","sukujutut.py","2 CONT zzz",
        add_cont_if_no_level_number="on",
        insert_dummy_tags="on",
    )

def test_gedcom_transform_unmark(client):
    dotest_gedcom_transform(client,"unmark-1.ged","unmark.py","PLAC-X a,Loviisa, Finland")
        
