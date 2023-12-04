'''
Created on 10.11.2017

@author: jm
'''
import unittest
from datetime import date
from bl.dates import DateRange, DR
from bl.base import NodeObject


class Test(unittest.TestCase):

    def testDateInt_day(self):
        ''' Check mid-month date order 
            Test the adjacent days in range 1917-12-14...16 including missing day
        '''
        comp = 1963405
        for s in ["1917-12-14", "1917-12-15", "1917-12", "1917-12-16"]:
#             print(" unit_test day {}".format(s))
            val = DateRange.DateInt(s).value()
            self.assertEqual(val, comp, s)
            comp += 1

    def testDateInt_month(self):
        ''' Check mid-year date order 
            Test the months in range 5..7 including missing month
        '''
        comp = 1963198
        for s in ["1917-06-30", "1917-06-31", "1917"]:
#             print(" tst month {}".format(s))
            val = DateRange.DateInt(s).value()
            self.assertEqual(val, comp, s)
            comp += 1
        # There is a gap bewtween "1917" and "1917-07-01" ~ no problem?
        s = "1917-07-01"
        comp += 31  
#         print(" unit_test month {}".format(s))
        val = DateRange.DateInt(s).value()
        self.assertEqual(val, comp, s)

    def test_create(self):
        ''' DateRange creation formats '''
        d = DateRange(DR['DATE'], "2017-11-09")
        self.assertEqual(d.to_list(), [0, "2017-11-09"])
        d = DateRange(DR['BEFORE'], "2017-10-16")
        self.assertEqual(d.to_list(), [1, "2017-10-16"])
        d = DateRange(1, 2065744)
        self.assertEqual(d.to_list(), [1, "2017-10-16"])
        d = DateRange(DR['BETWEEN'], date(1917, 12, 6), date(2017, 10, 16))
        self.assertEqual(d.to_list(), [4, "1917-12-06", "2017-10-16"])
        d = DateRange(4, 1963397, 2065744)
        self.assertEqual(d.to_list(), [4, "1917-12-06", "2017-10-16"])
        d = DateRange("1", "2017-10-16")
        self.assertEqual(d.to_list(), [1, "2017-10-16"])
        d = DateRange(DR['PERIOD'], "1917-12-06", "2017-10-16")
        dic = {'datetype': 3, 
               'date1': DateRange.DateInt("1917-12-06").value(), 
               'date2': DateRange.DateInt("2017-10-16").value() }
        self.assertEqual(d.for_db(), dic)
        d = DateRange(DR['PERIOD'], "1784", "1796-05")
        dic = {'datetype': 3, 
               'date1': DateRange.DateInt("1784").value(), 
               'date2': DateRange.DateInt("1796-05").value() }
        self.assertEqual(d.for_db(), dic)

    def testDateRange_date(self):
        ''' Single DateRange DR['DATE']
            DateRange(d1)
            DateRange(int, d1)
            DateRange(int, d1, d2)
        '''
        d = DateRange(date(2017, 4, 8))
        self.assertEqual(d.to_list(), [0, "2017-04-08"])
        self.assertEqual(str(d), "8.4.2017")

        d = DateRange("2017-10-16")
        self.assertEqual(d.to_list(), [0, "2017-10-16"])
        self.assertEqual(str(d), "16.10.2017")

        d = DateRange((0, "1640-09-31", ""))
        self.assertEqual(d.to_list(), [0, "1640-09-31"])
        self.assertEqual(str(d), "31.9.1640")

        d = DateRange(0, "1820-01-01")
        self.assertEqual(d.to_list(), [0, "1820-01-01"])
        self.assertEqual(str(d), "1.1.1820")


    def testDateRange_before_after(self):
        """
        DR_TILL = 1          # Date till d1
        DR_FROM = 2          # Date from d1
        DateRange(int, d1)
        DataRange((int, str1, str2))
        """
        d = DateRange(DR['BEFORE'], date(2017, 10, 16))
        self.assertEqual(d.to_list(), [1, "2017-10-16"])
        self.assertEqual(str(d), "till 16.10.2017")

        d = DateRange(DR['AFTER'], date(2017, 4, 8))
        self.assertEqual(d.to_list(), [2, "2017-04-08"])
        self.assertEqual(str(d), "from 8.4.2017")

        d = DateRange((1, "2017-04-08", ""))
        self.assertEqual(d.to_list(), [1, "2017-04-08"])
        d = DateRange((2, "2017-04-08", ""))
        self.assertEqual(d.to_list(), [2, "2017-04-08"])


    def testDateRange_period_between(self):
        """
        DR_PERIOD = 3        # Date period d1-d2
        DR_BETWEEN = 4       # A date between d1 and d2
        DateRange(int, d1, d2)
        DataRange((int, str1, str2))
        """
        d = DateRange(DR['PERIOD'], date(2017, 4, 8), date(2017, 10, 16))
        self.assertEqual(d.to_list(), [3, "2017-04-08", "2017-10-16"])
        self.assertEqual(str(d), "8.4.2017 – 16.10.2017")
        
        d = DateRange(DR['BETWEEN'], date(2017, 4, 8), date(2017, 10, 16))
        self.assertEqual(d.to_list(), [4, "2017-04-08", "2017-10-16"])
        self.assertEqual(str(d), "between 8.4.2017 … 16.10.2017")

        d = DateRange(DR['PERIOD'], "1784", "1796")
        self.assertEqual(d.to_list(), [3, "1784", "1796"])
        self.assertEqual(str(d), "1784 – 1796")

        d = DateRange(4, 1740992, 1843503)
        self.assertEqual(d.to_list(), [4, '1700', '1800-09'])
        self.assertEqual(str(d), 'between 1700 … 9.1800')

    def testDateRange_calc_est(self):
        """
            'CALC_BEFORE':9,
            'CALC_BETWEEN':12,
            'CALC_ABOUT':13,
            'EST_BEFORE':17,
            'EST_AFTER':18,
            'EST_PERIOD':19,
            'EST_BETWEEN':20,
            'EST_ABOUT':21
        """
        d = DateRange(DR['CALC_BEFORE'], date(2017, 10, 16))
        self.assertEqual(d.to_list(), [9, "2017-10-16"])
        self.assertEqual(str(d), "calculated till 16.10.2017")
        
        d = DateRange(DR['EST_PERIOD'], date(2017, 4, 8), date(2017, 10, 16))
        self.assertEqual(d.to_list(), [19, "2017-04-08", "2017-10-16"])
        self.assertEqual(str(d), "estimated 8.4.2017 – 16.10.2017")
        
        d = DateRange(DR['CALC_BETWEEN'], date(2017, 4, 8), date(2017, 10, 16))
        self.assertEqual(d.to_list(), [12, "2017-04-08", "2017-10-16"])
        self.assertEqual(str(d), "calculated between 8.4.2017 … 16.10.2017")

        d = DateRange(DR['EST_ABOUT'], date(2017, 10, 16))
        self.assertEqual(d.to_list(), [21, "2017-10-16"])
        self.assertEqual(str(d), "estimated about 16.10.2017")

    def testDateRange_DateInt(self):
        """
        Converts string format to int and vice versa
        """
        s = "2047-01-09"
        d = DateRange.DateInt(s)
        ds = d.short_date()
        self.assertEqual(s, ds)
        
        s = "1900-12-31"
        d = DateRange.DateInt(s)
        ds = d.short_date()
        self.assertEqual(s, ds)
        
        s = "1800-09"
        d = DateRange.DateInt(s)
        ds = d.long_date()
        self.assertEqual(s + '-00', ds)
        
        s = "1700"
        d = DateRange.DateInt(s)
        ds = d.long_date()
        self.assertEqual(s + '-00-00', ds)


    def testDateRange_add_years(self):
        """
        Add years to date
        """
        d = DateRange(DR['DATE'], "2047-01-09").add_years(3)
        ds = str(d)
        self.assertEqual(ds, "9.1.2050")

        d = DateRange(DR['BETWEEN'], date(2017, 4, 8), date(2017, 10, 16))
        da = d.add_years(-100)
        dl = da.to_list()
        self.assertEqual(dl, [4, "1917-04-08", "1917-10-16"])
        self.assertEqual(str(da), "between 8.4.1917 … 16.10.1917")
        
    def testNodeObject_sort(self):
        cmp = NodeObject(1)
        cmp.dates = DateRange("1917-12-15")
        datevector = [
            DateRange("1917-12-15"), 
            DateRange("1917-12"),
            None,
            DateRange("1917-12-14"), 
            DateRange("1917-12-16")]
        nodevector = []
        for i in range(len(datevector)):
            nodevector.append(NodeObject(i+1))
            nodevector[i].dates = datevector[i]
#             print(f"{nodevector[i]}")

#         print (f"Compare dates:")
#         for i in range(len(datevector)):
#             node = nodevector[i]
#             print(f'A {cmp} < {node} = {cmp.__lt__(node)}')
#             print(f'B {node} < {cmp} = {node.__lt__(cmp)}')

        nodesorted = sorted(nodevector)
        expected_uids = [3, 4, 1, 2, 5]
        for i in range(len(nodesorted)):
            self.assertEqual(nodesorted[i].iid, expected_uids[i], f"Invalid sort order, pos {i}")

#         print (f"Sorted nodes:")
#         for node in nodesorted:
#             print(f'{node}')

    def testDate_compare(self):
        ''' Compare DR_DATE to other date types '''

        mydate=DateRange(DR['DATE'], "1645")
        # If self < other?
        self.assertEqual(mydate.__lt__(DateRange(DR['DATE'], "1650")), True, "Not 1645 < 1650")
        self.assertEqual(mydate.__eq__(DateRange(DR['DATE'], "1645")), True, "Not 1645 == 1645")
        self.assertEqual(mydate.__gt__(DateRange(DR['DATE'], "1640")), True, "Not 1645 > 1640")
        self.assertEqual(mydate.__gt__(None), True, "Not 1645 > None")

#TODO: other DR-types not implemented 
# Note: The __cmp__() is obsolete in python3 
#         self.assertEqual(1, mydate.__cmp__(DateRange(DR['TILL'], "1640")))
#         self.assertEqual(0, mydate.__cmp__(DateRange(DR['TILL'], "1645")))
#         self.assertEqual(0, mydate.__cmp__(DateRange(DR['TILL'], "1650")))
#  
#         self.assertEqual(0, mydate.__cmp__(DateRange(DR['FROM'], "1640")))
#         self.assertEqual(0, mydate.__cmp__(DateRange(DR['FROM'], "1645")))
#         self.assertEqual(-1, mydate.__cmp__(DateRange(DR['FROM'], "1650")))
#  
#         self.assertEqual(1, mydate.__cmp__(DateRange(DR['PERIOD'], "1640", "1944")))
#         self.assertEqual(0, mydate.__cmp__(DateRange(DR['PERIOD'], "1644", "1645")))
#         self.assertEqual(0, mydate.__cmp__(DateRange(DR['PERIOD'], "1645", "1646")))
#         self.assertEqual(0, mydate.__cmp__(DateRange(DR['PERIOD'], "1644", "1646")))
#         self.assertEqual(-1, mydate.__cmp__(DateRange(DR['PERIOD'], "1650", "1656")))
#  
#         self.assertEqual(-1, mydate.__cmp__(DateRange(DR['ABOUT'], "1640")))
#         self.assertEqual(0, mydate.__cmp__(DateRange(DR['ABOUT'], "1645")))
#         self.assertEqual(1, mydate.__cmp__(DateRange(DR['ABOUT'], "1650")))


class ExpectedFailureTest(unittest.TestCase):
    @unittest.expectedFailure
    def testDateRange_tooMenyArguments(self):
        print(DateRange(0, "1820-01-01", ""))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testDateRange']
    unittest.main()