import pytest

from bl.family import FamilyBl
from bl.place import PlaceBl

from pe.neo4j.readservice_tx import Neo4jReadServiceTx  
import app
import shareds
from utils import get_test_values
from bl.material import Material
values = get_test_values(shareds.driver)

# user = "kku"
# batch_id = "2021-12-20.014"
# family_uuid = "b4a142f60d87478ebacf7bc435414bcc"
# family_uniq_id = 103383
# 
# 
# place_uuid = '465734f43901480aaf55f5bba456321d'
# place_uniq_id = 93021
    
@pytest.fixture
def svc():
    with shareds.driver.session(default_access_mode="READ") as session:
        svc = Neo4jReadServiceTx(shareds.driver)
        svc.tx = session
        yield svc
        
# ----------------------------------------------------------------------        
#     def tx_get_person_list(self, args):
#         """ Read Person data from given fw_from.
#         
#             args = dict {use_user, fw, limit, rule, key, years}
#         """
#         material_type = args.get('material_type')
#         state = args.get('state')
#         username = args.get('use_user')
#         rule = args.get('rule')
#         key = args.get('key')
#         fw_from = args.get('fw','')
#         years= args.get('years',[-9999,9999])
#         limit = args.get('limit', 100)
#         batch_id = args.get('batch_id')
#         restart = (rule == 'start')
    
def test_tx_get_person_list0(svc):
    # invalid args
    args = {}
    rsp = svc.tx_get_person_list(args)
    print(rsp)
    # rsp = {'items': [], 'status': 'Error', 'statustext': 'tx_get_person_list: Invalid rule'}
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'persons', 'status', 'statustext'}
    assert rsp['persons'] == []
    assert rsp['status'] == 'Error'
    assert rsp['statustext'] == 'tx_get_person_list: Invalid rule'

def test_tx_get_person_list1(svc):
    # all persons
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    args = {"pg":"all", 
            "use_user": values.user, 
            "material": material}
    rsp = svc.tx_get_person_list(args)
    print(rsp)
    # rsp = {'items': [], 'status': 'Error', 'statustext': 'tx_get_person_list: Invalid rule'}
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'persons', 'status'}
    assert rsp['status'] == 'OK'
    items = rsp['persons'] 
    assert isinstance(items, list)
    assert len(items) == 100
    
def test_tx_get_person_list2(svc):
    # limit = 10
    material = Material(session=None, request=None)
    material.batch_id = values.batch_id 
    args = {"pg":"all", 
            "use_user": values.user, 
            "material": material,
            "limit":10}
    rsp = svc.tx_get_person_list(args)
    print(rsp)
    # rsp = {'items': [], 'status': 'Error', 'statustext': 'tx_get_person_list: Invalid rule'}
    assert isinstance(rsp, dict)
    assert set(rsp.keys()) == {'persons', 'status'}
    assert rsp['status'] == 'OK'
    items = rsp['persons'] 
    assert isinstance(items, list)
    assert len(items) == 10
    
    
    
