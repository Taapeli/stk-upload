import sys
import os
import tempfile
import logging
import io
import shutil
import json

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

    args = dict(file=(open(testdata_dir+"/allged.ged","rb"),temp_gedcom),desc="Description")
    rv = client.post('/gedcom/upload',data=args,follow_redirects=True, content_type='multipart/form-data')
    data = rv.data.decode("utf-8")
    assert os.path.exists(temp_gedcom_fname)
    assert 'Toiminnot' in data
    assert temp_gedcom in data
    meta_fname = temp_gedcom_fname + "-meta"
    assert os.path.exists(meta_fname)
    metadata = eval(open(meta_fname).read())
    assert type(metadata) == dict
    assert "encoding" in metadata

def test_gedcom_duplicate_upload(client):
    args = dict(file=(open(testdata_dir+"/allged.ged","rb"),temp_gedcom),desc="Description")
    rv = client.post('/gedcom/upload',data=args,follow_redirects=True, content_type='multipart/form-data')
    data = rv.data.decode("utf-8")
    assert 'Gedcom-tiedosto on jo olemassa' in data

def test_gedcom_invalid_upload(client):
    rv = client.post('/gedcom/upload',data={},follow_redirects=True, content_type='multipart/form-data')
    data = rv.data.decode("utf-8")
    assert 'Valitse ladattava gedcom-tiedosto' in data

def test_gedcom_analyze(client):
    rv = client.get('/gedcom/analyze/'+temp_gedcom)
    data = rv.data.decode("utf-8")
    assert "Sukupuolet" in data

def test_gedcom_analyze_invalid_gedcom(client):
    try:
        os.remove(temp_gedcom_fname)
    except FileNotFoundError:
        pass
    assert not os.path.exists(temp_gedcom_fname) 
    args = dict(file=(open(testdata_dir+"/invalid_gedcom.ged","rb"),temp_gedcom),desc="Invalid_gedcom")
    rv = client.post('/gedcom/upload',data=args,follow_redirects=True, content_type='multipart/form-data')
    rv = client.get('/gedcom/analyze/'+temp_gedcom)
    data = rv.data.decode("utf-8")
    assert data == 'error'
    
def test_gedcom_list(client):
    rv = client.get('/gedcom')
    data = rv.data.decode("utf-8")
    assert 'Gedcom-työkalut' in data
    
    for name in os.listdir(gedcom_dir):
        if not name.endswith(".ged"): continue
        assert name in data

def test_gedcom_info(client):
    rv = client.get('/gedcom/info/'+temp_gedcom)
    data = rv.data.decode("utf-8")
    assert 'Muunnokset' in data

def test_gedcom_info_nonexistent(client):
    rv = client.get('/gedcom/info/zzz.ged',follow_redirects=True)
    data = rv.data.decode("utf-8")
    assert 'Gedcom-työkalut' in data
    assert 'Tätä Gedcom-tiedostoa ei ole palvelimella' in data
#    assert 'Redirecting' in data


def test_gedcom_transform_params(client):
    rv = client.get('/gedcom/transform/'+temp_gedcom+"/kasteet.py")
    data = rv.data.decode("utf-8")
    assert 'Kasteet: muunnoksen vaihtoehdot' in data
    
def dotest_gedcom_transform(client,test_gedcom,transform,expected,**options):
    args = {
        "--dryrun":"on",
        "--display-changes":"on",   
    }
    orig_file = os.path.join(testdata_dir,test_gedcom)
    dest_file = os.path.join(gedcom_dir,temp_gedcom)
    shutil.copyfile(orig_file,dest_file)

    # this will generate the transformation options form
    rv = client.get('/gedcom/transform/'+temp_gedcom+"/"+transform)
    data1 = rv.data.decode("utf-8")
    assert "muunnoksen vaihtoehdot" in data1
    
    args.update({"--"+option:value for option,value in options.items()})
    rv = client.post('/gedcom/transform/'+temp_gedcom+"/"+transform,data=args)
    data1 = rv.data.decode("utf-8")
    #open("trace.txt","w").write(data1)
    data = json.loads(rv.data.decode("utf-8"))
    assert data["stderr"] == ""
    assert expected in data['stdout']

def test_gedcom_transform_kasteet(client):
    dotest_gedcom_transform(client,"kasteet-1.ged","kasteet.py","PLAC p1")
    
def test_gedcom_transform_marriages(client):
    dotest_gedcom_transform(client,"marriages-1.ged","marriages.py","PLAC p3, p1")

def test_gedcom_transform_places(client):
    dotest_gedcom_transform(client,"paikat-1.ged","places.py","2 PLAC-X Finland, Loviisa, a",
                            match="a",
                            mark_changes="on",
                            mark_all_matching="on",
                            display_nonchanges="on",
                            display_unique_changes="on",
                            auto_combine="on",
                            add_commas="on",
                            display_ignored="on",
                            auto_order="on",
                            reverse="on")

def test_gedcom_transform_places2(client):
    dotest_gedcom_transform(client,"paikat-1.ged","places.py","2 PLAC-X Finland, Loviisa, a",
                            add_commas="on",
                            mark_changes="on",
                            minlen="2",
                            ignore_digits="on",
                            ignore_lowercase="on",
                            reverse="on")

def test_gedcom_transform_sukujutut(client):
    dotest_gedcom_transform(client,"sukujutut-1.ged","sukujutut.py","2 CONT zzz",
        add_cont_if_no_level_number="on",
        insert_dummy_tags="on",
        remove_empty_dates="on",
        remove_empty_notes="on",
        remove_invalid_marriage_dates="on",
        remove_invalid_divorce_dates="on",
        remove_empty_nameparts="on",
        remove_duplicate_sources="on",
        remove_refn="on",
        remove_stat="on",
        fix_addr="on",
        fix_events="on",
        fix_events_kaksonen="on",
        remove_multiple_blanks="on",
        emig_to_resi="on",
        note_to_page="on",
        sour_under_note="on",
    )

def test_gedcom_transform_nimet(client):
    dotest_gedcom_transform(client,"sukujutut-1.ged","names.py","Ajo 'names'   alkoi",
        add_cont_if_no_level_number="on",
        insert_dummy_tags="on",
    )

def test_gedcom_transform_dates(client):
    dotest_gedcom_transform(client,"dates.ged","dates.py","Muunnos 'Päivämäärät' käynnistettiin",
        display_invalid_dates="on",
        add_cont_if_no_level_number="on",
        insert_dummy_tags="on",
        handle_dd_mm_yyyy="on",
        handle_yyyy_mm="on",
        handle_zeros="on",
        handle_zeros2="on",
        handle_intervals="on",
        handle_intervals2="on",
        handle_intervals3="on",
        handle_yyyy_mm_dd="on",
    )
    
def test_gedcom_transform_unmark(client):
    dotest_gedcom_transform(client,"unmark-1.ged","unmark.py","PLAC-X a,Loviisa, Finland")

def test_gedcom_save(client):
    rv = client.get('/gedcom/save/'+temp_gedcom)
    data = rv.data.decode("utf-8")
    rsp = json.loads(data)
    assert type(rsp) == dict
    assert "newname" in rsp

def test_gedcom_versions(client):
    rv = client.get('/gedcom/versions/'+temp_gedcom)
    data = rv.data.decode("utf-8")
    versions =  json.loads(data)
    assert type(versions) == list
    assert len(versions) == 2
        
def test_gedcom_download(client):
    rv = client.get('/gedcom/download/'+temp_gedcom)
    data = rv.data.decode("utf-8")
    assert data.startswith("0 HEAD")

def test_gedcom_check(client):
    rv = client.get(f'/gedcom/check/{temp_gedcom}')
    data = rv.data.decode("utf-8")
    assert data == "exists"

def test_gedcom_check_nonexistent(client):
    rv = client.get(f'/gedcom/check/zzz.ged')
    data = rv.data.decode("utf-8")
    assert data == "does not exist"

def test_gedcom_update_desc(client):
    rv = client.post('/gedcom/update_desc/'+temp_gedcom,data=dict(desc="Newdesc"))
    data = rv.data.decode("utf-8")
    assert data == "ok"

def test_gedcom_update_permission(client):
    rv = client.get(f'/gedcom/update_permission/{temp_gedcom}/true')
    data = rv.data.decode("utf-8")
    assert data == "ok"

def test_gedcom_history(client):
    rv = client.get('/gedcom/history/'+temp_gedcom)
    data = rv.data.decode("utf-8")
    assert "Uploaded" in data

def test_gedcom_get_excerpt(client):
    rv = client.get(f'/gedcom/get_excerpt/{temp_gedcom}/1')
    data = rv.data.decode("utf-8")
    assert data.startswith("<br><span class=linenum>1</span>: <span class=current_line>0 HEAD")

def test_gedcom_compare(client):
    rv = client.get(f'/gedcom/compare/{temp_gedcom}/{temp_gedcom}')
    data = rv.data.decode("utf-8")
    assert "No Differences Found" in data

def test_gedcom_revert(client):
    rv = client.get(f'/gedcom/revert/{temp_gedcom}/{temp_gedcom}.0')
    data = rv.data.decode("utf-8")
    rsp = json.loads(data)
    assert type(rsp) == dict
    assert "newname" in rsp

def test_gedcom_delete_old_versions(client):
    rv = client.get(f'/gedcom/delete_old_versions/{temp_gedcom}',follow_redirects=True)
    data = rv.data.decode("utf-8")
    assert 'Muunnokset' in data
    n = 0
    for name in os.listdir(gedcom_dir):
        if name == temp_gedcom or name.startswith(temp_gedcom+"."): n += 1 
    assert n == 1
    
def test_gedcom_revert2(client):
    rv = client.get(f'/gedcom/revert/{temp_gedcom}/{temp_gedcom}.0')
    data = rv.data.decode("utf-8")
    rsp = json.loads(data)
    assert type(rsp) == dict
    assert rsp["status"] == "Error" # was already deleted

def test_gedcom_delete(client):
    rv = client.get(f'/gedcom/delete/{temp_gedcom}',follow_redirects=True)
    data = rv.data.decode("utf-8")
    assert 'Gedcom-työkalut' in data
    n = 0
    for name in os.listdir(gedcom_dir):
        if name == temp_gedcom or name.startswith(temp_gedcom+"."): n += 1 
    assert n == 0