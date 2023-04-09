import pytest


from bl.family import FamilyBl
from bl.place import PlaceBl
from bl.material import Material
from bl.event import EventBl
from bl.person import PersonBl
from bl.media import Media
from bl.note import Note

INVALID_BATCH_ID = "xxx"
INVALID_USER = "xxx"
INVALID_UUID = "xxx"
INVALID_UNIQ_ID = 0

from pe.neo4j.readservice import Neo4jReadService  
import app
import shareds
from utils import get_test_values
values = get_test_values(shareds.driver)

@pytest.fixture
def svc():
    svc = Neo4jReadService(shareds.driver)
    return svc
    
# ==================== Families ==========================
def test_get_families(svc):    
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.dr_get_families(
        {"material":material,"name":"","use_user":values.user})
    assert set(rsp.keys()) == {'families', 'status'}
    assert rsp['status'] == 'OK'
    families = rsp['families']
    assert len(families) == 50
    f = families[0]
    assert type(f) == FamilyBl
    print(f)
    print(dir(f))
    attrs = [
        'change', 'change_str', 'children', 'dates', 'events', 'father', 'father_sortname', 
        'handle', 'id', 'iid', 'marriage_dates', 'marriage_place', 'mother', 'mother_sortname', 
        'no_of_children', 'note_ref', 'notes', 'num_hidden_children', 'priv', 
        'rel_type', 'remove_privacy_limits', 'sources', 'split_with_hyphen', 'state', 'timestamp_str', 'uniq_id',
        #'uuid', 'uuid_short'
        ]
    for attr in attrs:
        assert attr in dir(f)
    
    
def test_get_family_by_uuid0(svc):    
    # valid user, invalid uuid
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.dr_get_family_by_uuid(values.user, uuid=INVALID_UUID, material=material)
    print(rsp)
    assert rsp is not None
    assert rsp['status'] == 'Not found'
    

def test_get_family_by_uuid1(svc):    
    # valid user, valid uuid
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.dr_get_family_by_uuid(values.user, uuid=values.family_uuid, material=material)
    print(rsp)    
    assert rsp is not None
    assert rsp['status'] == 'OK'
    f = rsp['item'] 
    assert isinstance(f, FamilyBl)
    print(dir(f))
    attrs = ['change', 'change_str', 'children', 'dates', 'events', 
             'father', 'father_sortname', 'handle', 'id', 
             'iid', 'marriage_dates', 'mother', 'mother_sortname', 
             'note_ref', 'notes', 'priv', 
             'rel_type', 'remove_privacy_limits', 'sources', 
             'state', 'timestamp_str', 'uniq_id',
             # 'uuid', 'uuid_short'
             ]
    for attr in attrs:
        assert attr in dir(f)


def test_get_family_parents0(svc):    
    # invalid unid_iq
    rsp = svc.dr_get_family_parents(uniq_id=INVALID_UNIQ_ID, with_name=True)
    print(rsp)    
    assert rsp is not None
    assert rsp['status'] == 'OK'
    parents = rsp['items'] 
    assert isinstance(parents, list)
    assert len(parents) == 0

def test_get_family_parents1(svc):    
    # valid unid_iq, with names
    rsp = svc.dr_get_family_parents(uniq_id=values.family_uniq_id, with_name=True)
    print(rsp)    
    assert rsp is not None
    assert rsp['status'] == 'OK'
    parents = rsp['items'] 
    assert isinstance(parents, list)
    assert len(parents) == 2
    print(parents[0].__dict__)
    assert isinstance(parents[0].names, list)
    print(parents[0].names)
    print(parents[1].names)

def test_get_family_parents2(svc):    
    # valid unid_iq, without names (the result is the same as with names)
    rsp = svc.dr_get_family_parents(uniq_id=values.family_uniq_id, with_name=False)
    print(rsp)    
    assert rsp is not None
    assert rsp['status'] == 'OK'
    parents = rsp['items'] 
    assert isinstance(parents, list)
    assert len(parents) == 2
    assert isinstance(parents[0].names, list)
    print(parents[0].names)
    print(parents[1].names)

def test_get_family_children0(svc):    
    # invalid uniq id
    rsp = svc.dr_get_family_children(uniq_id=INVALID_UNIQ_ID, with_events=True, with_names=True)
    print(rsp)    
    assert rsp is not None
    assert rsp['status'] == 'OK'
    children = rsp['items'] 
    assert isinstance(children, list)
    assert len(children) == 0

def test_get_family_children1(svc):    
    # valid uniq id
    rsp = svc.dr_get_family_children(uniq_id=values.family_uniq_id, with_events=True, with_names=True)
    print(rsp)    
    assert rsp is not None
    assert rsp['status'] == 'OK'
    children = rsp['items'] 
    assert isinstance(children, list)
    assert len(children) == 8
    assert isinstance(children[0].names, list)


# ==================== Places ==========================
def test_get_place_list_fw(svc):    
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.tx_get_place_list_fw(values.user, fw_from="", limit=10, lang="fi", material=material)
    print(rsp)    
    assert isinstance(rsp, list)
    assert len(rsp) == 10
    print(rsp[0].__dict__)
    assert isinstance(rsp[0], PlaceBl)

def test_get_place_w_names_notes_medias0a(svc):    
    # invalid user, invalid uuid
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.tx_get_place_w_names_citations_notes_medias(INVALID_USER, uuid="x", lang="fi", material=material)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'place', 'uniq_ids'}
    place = rsp['place'] 
    uniq_ids = rsp['uniq_ids'] 
    assert rsp['place'] is None
    assert rsp['uniq_ids'] == []

def test_get_place_w_names_notes_medias0b(svc):    
    # valid user, invalid uuid
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.tx_get_place_w_names_citations_notes_medias(values.user, uuid=INVALID_UUID, lang="fi", material=material)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'place', 'uniq_ids'}
    place = rsp['place'] 
    uniq_ids = rsp['uniq_ids'] 
    assert rsp['place'] is None
    assert rsp['uniq_ids'] == []

def test_get_place_w_names_notes_medias0c(svc):    
    # invalid user, valid uuid
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.tx_get_place_w_names_citations_notes_medias(user=INVALID_USER, uuid=values.place_uuid, lang="fi", material=material)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'place', 'uniq_ids'}
    place = rsp['place'] 
    uniq_ids = rsp['uniq_ids'] 
    assert rsp['place'] is None
    assert rsp['uniq_ids'] == []

def test_get_place_w_names_notes_medias1(svc):    
    # valid user, valid uuid
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.tx_get_place_w_names_citations_notes_medias(values.user, uuid=values.place_uuid, lang="fi", material=material)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'place', 'uniq_ids'}
    place = rsp['place'] 
    uniq_ids = rsp['uniq_ids'] 
    assert isinstance(place, PlaceBl)
    assert isinstance(uniq_ids, list)
    assert len(uniq_ids) == 1

def test_get_event_by_uuid0(svc):    
    # valid user, invalid uuid
    # def dr_get_event_by_iid(self, user:str, uuid:str, material:Material):
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.dr_get_event_by_iid(values.user, uuid=INVALID_UUID, material=material)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'item', 'status', 'statustext'}
    assert rsp['item'] is None 
    assert rsp['status'] == 'Not found'
    assert rsp['statustext'] == 'No Event found'

def test_get_event_by_uuid1(svc):    
    # valid user, valid uuid
    # def dr_get_event_by_iid(self, user:str, uuid:str, material:Material):
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.dr_get_event_by_iid(values.user, uuid=values.event_uuid, material=material)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'item', 'status'}
    event = rsp['item'] 
    assert isinstance(event, EventBl)
    assert event.uuid == values.event_uuid

def test_get_event_participants0(svc):    
    # invalid uid
    # def dr_get_event_participants(self, uid):
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.dr_get_event_participants(INVALID_UNIQ_ID)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'items', 'status'}
    items = rsp['items']
    assert type(items) == list
    assert len(items) == 0 

def test_get_event_participants1(svc):    
    # valid uid
    # def dr_get_event_participants(self, uid):
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.dr_get_event_participants(values.event_uniq_id)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'items', 'status'}
    items = rsp['items']
    assert type(items) == list
    assert len(items) == 1 
    item = items[0]
    assert isinstance(item, PersonBl)
    assert item.id == 'I0044'

def test_get_event_place0(svc):    
    # invalid uid
    # def dr_get_event_place(self, uid):
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.dr_get_event_place(INVALID_UNIQ_ID)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'items', 'status'}
    items = rsp['items']
    assert type(items) == list
    assert len(items) == 0

def test_get_event_place1(svc):    
    # valid uid
    # def dr_get_event_place(self, uid):
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.dr_get_event_place(values.event_uniq_id)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'items', 'status'}
    items = rsp['items']
    assert type(items) == list
    assert len(items) == 1 
    item = items[0]
    assert isinstance(item, PlaceBl)
    assert item.id == 'P1435'

def test_dr_get_event_notes_medias0(svc):    
    # invalid uid
    # def dr_get_event_notes_medias(self, uid):
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.dr_get_event_notes_medias(INVALID_UNIQ_ID)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'medias', 'notes', 'status'}
    assert rsp['status'] == 'OK'   # !!!
    assert rsp['medias'] == []
    assert rsp['notes'] == []

def test_dr_get_event_notes_medias1(svc):    
    # valid uid
    # def dr_get_event_notes_medias(self, uid):
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    rsp = svc.dr_get_event_notes_medias(values.event_uniq_id)
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'medias', 'notes', 'status'}
    medias = rsp['medias']
    assert type(medias) == list
    assert len(medias) == 1 
    media = medias[0]
    assert isinstance(media, Media)
    assert media.id == 'O0000'
    assert rsp['notes'] == []   # no notes

"""
    def dr_get_material_batches(self, user: str, uuid: str):

    def dr_get_event_by_iid(self, user: str, uuid: str):
    def dr_get_event_participants(self, uid):
    def dr_get_event_place(self, uid):
    def dr_get_event_notes_medias(self, uid):

    def dr_get_family_parents(self, uniq_id: int, with_name=True):
    def dr_get_family_children(self, uniq_id, with_events=True, with_names=True):
    def dr_get_family_events(self, uniq_id, with_places=True):
    def dr_get_family_sources(self, id_list, with_notes=True):
    def dr_get_family_notes(self, id_list: list):
    def dr_get_family_members_by_id(self, oid, which):

    def dr_get_person_families_uuid(self, uuid):

    def tx_get_place_list_fw(self, user, fw_from, limit, lang="fi", batch_id=None):
    def tx_get_place_w_names_citations_notes_medias(self, user, uuid, lang="fi"):
    def dr_get_place_tree(self, locid, lang="fi"):
    def dr_get_place_events(self, uniq_id, privacy):

    def dr_get_source_list_fw(self, args):
    def dr_get_source_w_repository(self, user, uuid):

    def dr_get_media_list(self, user, batch_id, fw_from, limit):
    def dr_get_media_single(self, user, batch_id, uuid):

    def dr_get_topic_list(self, user, batch_id, fw_from, limit):

    def dr_get_source_citations(self, sourceid: int):
    def dr_inlay_person_lifedata(self, person):
    def dr_get_surname_list(self, username, batch_id, count):
    def dr_get_placename_list(self, username, batch_id, count=50): 
"""
