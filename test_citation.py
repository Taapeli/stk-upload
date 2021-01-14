#----------------------------------------------------------
#
# Test of the citation data of the xml file
#
# Note! the line: "from . import routes" should be commentted in gramps/__init__.py file
#
#----------------------------------------------------------


import pytest

from unittest import mock

import sys

sys.path.append("app")

from bp.gramps.xml_dom_handler import DOM_handler
from bp.gramps.batchlogger import BatchLog, LogItem

class Batch():
    '''
    User Batch node and statistics about them. 
    '''

    def __init__(self, userid=None):
        '''
        Creates a Batch object
        '''
        self.uniq_id = None
        self.user = userid
        self.file = None
        self.id = None              # batch_id
        self.status = 'started'
        self.mediapath = None       # Directory for media files
        self.timestamp = 0
        

@pytest.fixture(name="mock_func", scope="session")
def fixture_mock_func():
    def _mock_func(param1, **kwarks):
        # type = param1.type
        
        return param1
        
    return _mock_func


def test_xml_with_citation(mock_func):
    mock_patch = "bp.gramps.xml_dom_handler.DOM_handler.save_and_link_handle"
    with mock.patch(mock_patch) as mck:
        mck.side_effect = mock_func
        
        handler = DOM_handler("testdata/xml_tests/citation_test.xml", "test_user")
        handler.batch = Batch("test_user")
        handler.batch.id = "2021-01-12"
        
        handler.blog = BatchLog("test_user")
        handler.blog.log_event({"XML test"})
             
        result = handler.handle_citations()
        
        # assert result['for_test'].dates == "2017-07-24"
        
        assert result['for_test'].page == "Alexander Florin 5812"
        
        assert result['for_test'].confidence == "2"
        
        assert result['for_test'].note_handles[0] == "_da691070edc6e755358a085a3"
        
        assert result['for_test'].source_handle == "_da3b305ab6232bd2cbf352a13a"
        
        
        
        
		