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

logging.basicConfig(level=logging.INFO)

test_user_session = None
test_current_user=None
test_request=None

@pytest.fixture(scope='module')
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    client = app.test_client()

    rv = login(client)
    #txt = "Oma sukupuuni"
    #txt = "Suomikannan käyttäjän alkusivu"
    txt = "Isotammen aloitussivusi"
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
        
def test_start_join1(client):
    rv = client.get(f'/join')
    data = rv.data.decode("utf-8")
    assert 'Liity Isotammeen' in data

def test_start_join2(client):
    rv = client.post(f'/join', data=dict(name="A",email="a@a.com"), follow_redirects=True)
    data = rv.data.decode("utf-8")
    assert 'Liittymisviesti lähetetty' in data

def test_start_message(client):
    rv = client.get(f'/message')
    data = rv.data.decode("utf-8")
    assert 'Viesti Toimistoon' in data

def test_start_send_email(client):
    rv = client.post(f'/send_email', data=dict(subject="A",message="B"))
    data = rv.data.decode("utf-8")
    assert data == "ok"

def test_start_settings(client):
    rv = client.get(f'/settings')
    data = rv.data.decode("utf-8")
    assert 'Muuta asetuksia' in data

def test_start_settings2(client):
    rv = client.post(f'/settings',data=dict(lang="sv"))
    data = rv.data.decode("utf-8")
    assert 'Ändra mina inställningar' in data

    rv = client.post(f'/settings',data=dict(lang="fi"))
    data = rv.data.decode("utf-8")
    assert 'Muuta asetuksia' in data
