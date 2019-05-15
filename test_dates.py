import argparse
import sys
import pytest

sys.path.append("app")

from bp.gedcom.transforms import dates

@pytest.fixture(scope='module')
def transformer():
    t = dates.initialize(options={})
    yield t
    
def dotest(transformer,option,value,expected):    
    class Item: pass
    item = Item()
    item.tag = "DATE"
    item.value = value
    item.path = "INDI.BIRT.DATE"
    parser = argparse.ArgumentParser()
    dates.add_args(parser)
    options = parser.parse_args([option])
    item2 = transformer.transform(item,options,1)
    assert item2.value == expected

def test_dd_mm_yyyy(transformer):
    dotest(transformer,"--handle_dd_mm_yyyy","12.3.1899","12 MAR 1899")

def test_yyyy_mm_dd(transformer):
    dotest(transformer,"--handle_yyyy_mm_dd","1899-03-12","12 MAR 1899")

def test_yyyy_mm(transformer):
    dotest(transformer,"--handle_yyyy_mm","1899-03","MAR 1899")

def test_zeros(transformer):
    dotest(transformer,"--handle_zeros","0.3.1899","MAR 1899")

def test_zeros2(transformer):
    dotest(transformer,"--handle_zeros2","0 MAR 1899","MAR 1899")

def test_intervals(transformer):
    dotest(transformer,"--handle_intervals","1890-1899","FROM 1890 TO 1899")

def test_intervals2(transformer):
    dotest(transformer,"--handle_intervals2",">1899","AFT 1899")

def test_intervals3(transformer):
    dotest(transformer,"--handle_intervals3","<1899","BEF 1899")


