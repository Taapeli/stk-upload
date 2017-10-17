'''
Created on 17.10.2017

@author: jm
'''
import unittest
from datetime import date
from models.gen.dates import DateRange


class TestDateRange(unittest.TestCase):
    """ Test DateRange class """

    def testSingleDateInit(self):
        d_date = date(1918, 12, 6)
        dr1 = DateRange(d_date)
        got = dr1.to_tuple()
        self.assertEqual(got, (0, '1918-12-06'), msg="date")
        
        d_str = "1918-12-06"
        dr2 = DateRange(d_str)
        got = dr2.to_tuple()
        self.assertEqual(got, (0, '1918-12-06'), msg="str")

        dr3 = DateRange(DateRange.DR_TILL, 736618)
        got = dr3.to_tuple()
        self.assertEqual(got, (1, '2017-10-16'), msg="tuple")

    def testTwoDateInit(self):
        d1 = date(1918, 12, 6)
        d2 = date(2017, 10, 16)
        dr1 = DateRange(DateRange.DR_BETWEEN, d1, d2)
        got = dr1.to_tuple()
        self.assertEqual(got, (4, '1918-12-06', '2017-10-16'), 
                         msg="between d1...d2")

        dr2 = DateRange("1918-12-06")
        self.assertEqual(dr2.to_tuple(), (0, '1918-12-06'), msg="str")

        dr3 = DateRange(DateRange.DR_TILL, 737034)
        self.assertEqual(dr3.to_tuple(), (1, '2018-12-06'), msg="tuple")

    def testStrOutput(self):
        d1 = "1918-02-06"
        d2 = "2017-10-16"
        dr1 = DateRange(DateRange.DR_DATE, d1)
        got = dr1.__str__()
        self.assertEqual(got, "1918-02-06", msg="exact")

        dr1 = DateRange(DateRange.DR_TILL, d1)
        got = dr1.__str__()
        self.assertEqual(got, "1918-02-06 asti", msg="till")
        
        dr1 = DateRange(DateRange.DR_FROM, d1)
        got = dr1.__str__()
        self.assertEqual(got, "1918-02-06 alkaen", msg="from")
        
        dr1 = DateRange(DateRange.DR_PERIOD, d1, d2)
        got = dr1.__str__()
        self.assertEqual(got, "1918-02-06 – 2017-10-16", msg="period")
        
        dr1 = DateRange(DateRange.DR_BETWEEN, d1, d2)
        got = dr1.__str__()
        self.assertEqual(got, "välillä 1918-02-06 … 2017-10-16", 
                         msg="between d1...d2")
        
        dr1 = DateRange(DateRange.DR_ABOUT, d1)
        got = dr1.__str__()
        self.assertEqual(got, "noin 1918-02-06", msg="about")
        
        dr1 = DateRange(DateRange.DR_CALCULATED, d1)
        got = dr1.__str__()
        self.assertEqual(got, "laskettu 1918-02-06", msg="calculated")
        
        dr1 = DateRange(DateRange.DR_ESTIMATED, d1)
        got = dr1.__str__()
        self.assertEqual(got, "arviolta 1918-02-06", msg="estimated")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSingleDate']
    unittest.main()
