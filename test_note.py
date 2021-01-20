#----------------------------------------------------------
#
# Test of the note data of the xml file
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


def test_xml_with_note(mock_func):
    mock_patch = "bp.gramps.xml_dom_handler.DOM_handler.save_and_link_handle"
    with mock.patch(mock_patch) as mck:
        mck.side_effect = mock_func
        
        handler = DOM_handler("testdata/xml_tests/note_test.xml", "test_user")
        handler.batch = Batch("test_user")
        handler.batch.id = "2021-01-12"
        
        handler.blog = BatchLog("test_user")
        handler.blog.log_event({"XML test"})
             
        result = handler.handle_notes()
        
        assert result['for_test'].type == "Citation"
        
        assert result['for_test'].text == "Tuli kotivävyksi Sibben (esiintyy myös muodossa Sibbes) taloon. Tila jaettiin kahteen osaan 1794, jolloin Juho Matinpojasta tuli sen toisen puoliskon isäntä."
        
        assert result['for_test'].url == "http://www.sibelius.fi/suomi/suku_perhe/suku_sibelius.htm"
        
		