'''
Created on 10.11.2017

@author: jm
'''
import unittest
from datetime import date
from models.gen.dates import DateRange


class Test(unittest.TestCase):

    def test_create(self):
        d = DateRange(DateRange.DR_DATE, "2017-11-09")
        self.assertEqual(d.to_tuple(), (0, "2017-11-09", ""))
        d = DateRange(DateRange.DR_TILL, "2017-10-16")
        self.assertEqual(d.to_tuple(), (1, "2017-10-16", ""))
        d = DateRange(1, 736618)
        self.assertEqual(d.to_tuple(), (1, "2017-10-16", ""))
        d = DateRange(DateRange.DR_BETWEEN, date(1917, 12, 6), date(2017, 10, 16))
        self.assertEqual(d.to_tuple(), (4, "1917-12-06", "2017-10-16"))
        d = DateRange(DateRange.DR_PERIOD, "1917-12-06", "2017-10-16")
        self.assertEqual(d.to_tuple(), (3, "1917-12-06", "2017-10-16"))
        d = DateRange(4, 700144, 736618)
        self.assertEqual(d.to_tuple(), (4, "1917-12-06", "2017-10-16"))


    def testDateRange_date(self):
        """
        DR_DATE = 0          # Exact date d1
        DR_TILL = 1          # Date till d1
        DR_FROM = 2          # Date from d1
        DR_PERIOD = 3        # Date period d1-d2
        DR_BETWEEN = 4       # A date between d1 and d2
        DR_ABOUT = 5         # A date near d1
        DR_CALCULATED = 6    # A calculated date near d1
        DR_ESTIMATED = 7     # An estimated date at d1
        DateRange(d1)
        DateRange(int, d1)
        DateRange(int, d1, d2)
        DataRange((int, str1, str2))
        """
        d = DateRange(date(2017, 4, 8))
        self.assertEqual(d.to_tuple(), (0, "2017-04-08", ""))
        self.assertEqual(str(d), "8.4.2017")

        d = DateRange("2017-10-16")
        self.assertEqual(d.to_tuple(), (0, "2017-10-16", ""))
        self.assertEqual(str(d), "16.10.2017")

        d = DateRange((0, "1640-09-31", ""))
        self.assertEqual(d.to_tuple(), (0, "1640-09-31", ""))
        self.assertEqual(str(d), "31.9.1640")

        d = DateRange(0, "1820-01-01")
        self.assertEqual(d.to_tuple(), (0, "1820-01-01", ""))
        self.assertEqual(str(d), "1.1.1820")

#         #Fails
#         d = DateRange(0, "1820-01-01", "")


    def testDateRange_till_from(self):
        """
        DR_TILL = 1          # Date till d1
        DR_FROM = 2          # Date from d1
        DateRange(int, d1)
        DataRange((int, str1, str2))
        """
        d = DateRange(DateRange.DR_TILL, date(2017, 10, 16))
        self.assertEqual(d.to_tuple(), (1, "2017-10-16", ""))
        self.assertEqual(str(d), "– 16.10.2017")

        d = DateRange(DateRange.DR_FROM, date(2017, 4, 8))
        self.assertEqual(d.to_tuple(), (2, "2017-04-08", ""))
        self.assertEqual(str(d), "8.4.2017 –")

        d = DateRange((1, "2017-04-08", ""))
        self.assertEqual(d.to_tuple(), (1, "2017-04-08", ""))
        d = DateRange((2, "2017-04-08", ""))
        self.assertEqual(d.to_tuple(), (2, "2017-04-08", ""))


    def testDateRange_period_between(self):
        """
        DR_PERIOD = 3        # Date period d1-d2
        DR_BETWEEN = 4       # A date between d1 and d2
        DateRange(int, d1, d2)
        DataRange((int, str1, str2))
        """
        d = DateRange(DateRange.DR_PERIOD, date(2017, 4, 8), date(2017, 10, 16))
        self.assertEqual(d.to_tuple(), (3, "2017-04-08", "2017-10-16"))
        self.assertEqual(str(d), "8.4.2017 – 16.10.2017")
        
        d = DateRange(DateRange.DR_BETWEEN, date(2017, 4, 8), date(2017, 10, 16))
        self.assertEqual(d.to_tuple(), (4, "2017-04-08", "2017-10-16"))
        self.assertEqual(str(d), "välillä 8.4.2017 … 16.10.2017")
#         d = DateRange(DR_TILL, "2017-10-16")
#         d = DateRange(1, 736618)
#         d = DateRange(DR_BETWEEN, date(1917, 12, 6), date(2017, 10, 16))
#         d = DateRange(DR_BETWEEN, "1917-12-06", "2017-10-16")
#         d = DateRange(4, 700144, 736618)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testDateRange']
    unittest.main()