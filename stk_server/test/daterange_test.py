'''
Created on 10.11.2017

@author: jm
'''
import unittest
from datetime import date
from models.gen.dates import DateRange, DR


class Test(unittest.TestCase):

    def test_create(self):
        ''' DateRange creation formats '''
        d = DateRange(DR['DATE'], "2017-11-09")
        self.assertEqual(d.to_tuple(), (0, "2017-11-09", ""))
        d = DateRange(DR['TILL'], "2017-10-16")
        self.assertEqual(d.to_tuple(), (1, "2017-10-16", ""))
        d = DateRange(1, 736618)
        self.assertEqual(d.to_tuple(), (1, "2017-10-16", ""))
        d = DateRange(DR['BETWEEN'], date(1917, 12, 6), date(2017, 10, 16))
        self.assertEqual(d.to_tuple(), (4, "1917-12-06", "2017-10-16"))
        d = DateRange(DR['PERIOD'], "1917-12-06", "2017-10-16")
        self.assertEqual(d.to_tuple(), (3, "1917-12-06", "2017-10-16"))
        d = DateRange(4, 700144, 736618)
        self.assertEqual(d.to_tuple(), (4, "1917-12-06", "2017-10-16"))


    def testDateRange_date(self):
        ''' Single DateRange DR['DATE']

            DateRange(d1)
            DateRange(int, d1)
            DateRange(int, d1, d2)
        '''
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
        d = DateRange(DR['TILL'], date(2017, 10, 16))
        self.assertEqual(d.to_tuple(), (1, "2017-10-16", ""))
        self.assertEqual(str(d), "– 16.10.2017")

        d = DateRange(DR['FROM'], date(2017, 4, 8))
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
        d = DateRange(DR['PERIOD'], date(2017, 4, 8), date(2017, 10, 16))
        self.assertEqual(d.to_tuple(), (3, "2017-04-08", "2017-10-16"))
        self.assertEqual(str(d), "8.4.2017 – 16.10.2017")
        
        d = DateRange(DR['BETWEEN'], date(2017, 4, 8), date(2017, 10, 16))
        self.assertEqual(d.to_tuple(), (4, "2017-04-08", "2017-10-16"))
        self.assertEqual(str(d), "välillä 8.4.2017 … 16.10.2017")
#         d = DateRange(DR_TILL, "2017-10-16")
#         d = DateRange(1, 736618)
#         d = DateRange(DR_BETWEEN, date(1917, 12, 6), date(2017, 10, 16))
#         d = DateRange(DR_BETWEEN, "1917-12-06", "2017-10-16")
#         d = DateRange(4, 700144, 736618)


    def testDate_compare_DR_DATE(self):
        ''' Compare DR_DATE to other date types '''
        mydate=DateRange(DR['DATE'], "1645")
        
        self.assertEqual(-1, mydate.__cmp__(DateRange(DR['DATE'], "1640")))
        self.assertEqual(0, mydate.__cmp__(DateRange(DR['DATE'], "1645")))
        self.assertEqual(1, mydate.__cmp__(DateRange(DR['DATE'], "1650")))

        self.assertEqual(1, mydate.__cmp__(DateRange(DR['TILL'], "1640")))
        self.assertEqual(0, mydate.__cmp__(DateRange(DR['TILL'], "1645")))
        self.assertEqual(0, mydate.__cmp__(DateRange(DR['TILL'], "1650")))

        self.assertEqual(0, mydate.__cmp__(DateRange(DR['FROM'], "1640")))
        self.assertEqual(0, mydate.__cmp__(DateRange(DR['FROM'], "1645")))
        self.assertEqual(-1, mydate.__cmp__(DateRange(DR['FROM'], "1650")))

        self.assertEqual(1, mydate.__cmp__(DateRange(DR['PERIOD'], "1640", "1944")))
        self.assertEqual(0, mydate.__cmp__(DateRange(DR['PERIOD'], "1644", "1645")))
        self.assertEqual(0, mydate.__cmp__(DateRange(DR['PERIOD'], "1645", "1646")))
        self.assertEqual(0, mydate.__cmp__(DateRange(DR['PERIOD'], "1644", "1646")))
        self.assertEqual(-1, mydate.__cmp__(DateRange(DR['PERIOD'], "1650", "1656")))

        self.assertEqual(-1, mydate.__cmp__(DateRange(DR['ABOUT'], "1640")))
        self.assertEqual(0, mydate.__cmp__(DateRange(DR['ABOUT'], "1645")))
        self.assertEqual(1, mydate.__cmp__(DateRange(DR['ABOUT'], "1650")))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testDateRange']
    unittest.main()