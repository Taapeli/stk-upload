import pytest


from bl.family import FamilyBl
from bl.place import PlaceBl

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
    rsp = svc.dr_get_families(
        {"batch_id":values.batch_id,"name":"","use_user":values.user})
    assert set(rsp.keys()) == {'recs', 'status'}
    assert rsp['status'] == 'OK'
    recs = rsp['recs']
    assert len(recs) == 50
    rec = recs[0]
    #print(rec)
    #assert type(rec) == neo4j.data.Record
    assert set(rec.keys()) == {'f', 'marriage_place',"parent","child","no_of_children"}
    
    
def test_get_family_by_uuid0(svc):    
    # valid user, invalid uuid
    rsp = svc.dr_get_family_by_uuid(values.user, uuid=INVALID_UUID)
    print(rsp)
    assert rsp is not None
    assert rsp['status'] == 'Not found'
    

def test_get_family_by_uuid1(svc):    
    # valid user, valid uuid
    rsp = svc.dr_get_family_by_uuid(values.user, uuid=values.family_uuid)
    print(rsp)    
    assert rsp is not None
    assert rsp['status'] == 'OK'
    f = rsp['item'] 
    assert isinstance(f, FamilyBl)
    print(dir(f))
    attrs = ['change', 'change_str', 'children', 'dates', 'events', 
             'father', 'father_sortname', 'handle', 'id', 
             'isotammi_id', 'marriage_dates', 'mother', 'mother_sortname', 
             'note_ref', 'notes', 'priv', 
             'rel_type', 'remove_privacy_limits', 'save', 'sources', 
             'state', 'timestamp_str', 'uniq_id', 'uuid', 'uuid_short']
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

def test_get_family_children0(svc):    
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
    rsp = svc.dr_get_place_list_fw(values.user, fw_from="", limit=10, batch_id=values.batch_id)
    print(rsp)    
    assert isinstance(rsp, list)
    assert len(rsp) == 10
    print(rsp[0].__dict__)
    assert isinstance(rsp[0], PlaceBl)

def test_get_place_w_names_notes_medias0a(svc):    
    # invalid user, invalid uuid
    rsp = svc.dr_get_place_w_names_notes_medias(INVALID_USER, uuid="x", lang="fi")
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'place', 'uniq_ids'}
    place = rsp['place'] 
    uniq_ids = rsp['uniq_ids'] 
    assert rsp['place'] is None
    assert rsp['uniq_ids'] == []

def test_get_place_w_names_notes_medias0b(svc):    
    # valid user, invalid uuid
    rsp = svc.dr_get_place_w_names_notes_medias(values.user, uuid=INVALID_UUID, lang="fi")
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'place', 'uniq_ids'}
    place = rsp['place'] 
    uniq_ids = rsp['uniq_ids'] 
    assert rsp['place'] is None
    assert rsp['uniq_ids'] == []

def test_get_place_w_names_notes_medias0c(svc):    
    # invalid user, valid uuid
    rsp = svc.dr_get_place_w_names_notes_medias(user=INVALID_USER, uuid=values.place_uuid, lang="fi")
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'place', 'uniq_ids'}
    place = rsp['place'] 
    uniq_ids = rsp['uniq_ids'] 
    assert rsp['place'] is None
    assert rsp['uniq_ids'] == []

def test_get_place_w_names_notes_medias1(svc):    
    # valid user, valid uuid
    rsp = svc.dr_get_place_w_names_notes_medias(values.user, uuid=values.place_uuid, lang="fi")
    print(rsp)    
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'place', 'uniq_ids'}
    place = rsp['place'] 
    uniq_ids = rsp['uniq_ids'] 
    assert isinstance(place, PlaceBl)
    assert isinstance(uniq_ids, list)
    assert len(uniq_ids) == 1

"""
    def dr_get_material_batches(self, user: str, uuid: str):

    def dr_get_event_by_uuid(self, user: str, uuid: str):
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

    def dr_get_place_list_fw(self, user, fw_from, limit, lang="fi", batch_id=None):
    def dr_get_place_w_names_notes_medias(self, user, uuid, lang="fi"):
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
