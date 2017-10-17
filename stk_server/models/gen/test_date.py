'''
Created on 17.10.2017

@author: jm
'''
import unittest
from datetime import date
from models.gen import daterange


class TestDateRange(unittest.TestCase):
    """ Test DateRange class """

    def testSingleDateInit(self):
        d_date = date(1918, 12, 6)
        dr1 = daterange.DateRange(d_date)
        self.assertEqual(dr1.to_tuple(), (0, 700509), msg="date")
        
        d_str = "1918-12-06"
        dr2 = daterange.DateRange(d_str)
        self.assertEqual(dr2.to_tuple(), (0, 700509), msg="str")

        dr3 = daterange.DateRange(daterange.DATERANGE_TILL, 736618)
        self.assertEqual(dr3.to_tuple(), (1, 736618), msg="tuple")

    def testTwoDateInit(self):
        d1 = date(1918, 12, 6)
        d2 = date(2017, 10, 16)
        dr1 = daterange.DateRange(daterange.DATERANGE_BETWEEN, d1, d2)
        self.assertEqual(dr1.to_tuple(), (4, 700509, 736618), msg="between d1...d2")

        d_str = "1918-12-06"
        dr2 = daterange.DateRange(d_str)
        self.assertEqual(dr2.to_tuple(), (0, 700509), msg="str")

        dr3 = daterange.DateRange(1, 736618)
        self.assertEqual(dr3.to_tuple(), (1, 736618), msg="tuple")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testSingleDate']
    unittest.main()