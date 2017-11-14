'''
Created on 16.10.2017

@author: jm
'''
from datetime import date

class DateRange():
    '''
    DateRange handles date expressions needed for genealogical data.
    The dates are expressed with range type and one or two string values
    representing the date limits.

    This class is designed specially for efficient processing in the database
    and it's user interfaces.

    Saa also another way of expressing date range values, specially for data
    exchange:
    https://github.com/FamilySearch/gedcomx/blob/master/specifications/date-format-specification.md
    '''

    DR_DATE = 0          # Exact date d1
    DR_TILL = 1          # Date till d1
    DR_FROM = 2          # Date from d1
    DR_PERIOD = 3        # Date period d1-d2
    DR_BETWEEN = 4       # A date between d1 and d2
    DR_ABOUT = 5         # A date near d1
    DR_CALCULATED = 6    # A calculated date near d1
    DR_ESTIMATED = 7     # An estimated date at d1


    def __init__(self, *args):
        '''
        Constructor can be called following ways:
            DateRange(d1)
            DateRange(int, d1)
            DateRange(int, d1, d2)
            DataRange((int, str1, str2))

            The first int argument tells the range type. It is not obligatory, 
            when the type is DR_DATE (meaning a single exact date).

            Each d1, d2 for date '1917-12-06' can equally be expressed as:
            - a date object date(1917, 12, 6)
            - a complete date string '1917-12-06'
            - a partial date string '1917-12' for given year and month 
            - a year string '1917'
            - an ordinal int value 700144 ~ date(...).toordinal()
            The d2 can also be empty string "".
            
            The last form is used for loading a DataRange from database. The 
            argument is assumed to be a tuple like the output of DataRange.to_tuple() 
            method, and the components formats are not checked.
        '''

        if len(args) == 1:
            if type(args[0]).__name__ == 'tuple' and len(args[0]) == 3:
                # The only argument is a tuple like (3, '1918-12', '2017-10-16')
                self.dtype = args[0][0]
                self.date1 = args[0][1]
                self.date2 = args[0][2]
                return
            elif type(args[0]).__name__ == 'DateRange':
                self.dtype = args[0].dtype
                self.date1 = args[0].date1
                self.date2 = args[0].date2
                return

        try:
            # First argument is some kind of date
            self.date1 = self._to_datestr(args[0])
            self.dtype = self.DR_DATE
            self.date2 = ""
            return
        except:
            pass
        
        if type(args[0]).__name__ == 'int':
            """ Arguments are dtype and 1 or 2 datevalues:
                DateRange(DR_TILL, date(2017, 10, 16))
                DateRange(DR_TILL, "2017-10-16")
                DateRange(1, 736618)
                DateRange(DR_BETWEEN, date(1917, 12, 6), date(2017, 10, 16))
                DateRange(DR_BETWEEN, "1917-12-06", "2017-10-16")
                DateRange(4, 700144, 736618)
            """
            self.dtype = args[0]
            if self.dtype < 0 or self.dtype > self.DR_ESTIMATED:
                raise ValueError('Invalid DateRange(type, ...)')
            self.date1 = self._to_datestr(args[1])
            self.date2 = ""
            if self.dtype in [self.DR_PERIOD, self.DR_BETWEEN]:
                if len(args) == 3:
                    self.date2 = self._to_datestr(args[2])
                else:
                    raise ValueError('Two dates excepted for DateRange({}, date, date)'.
                                     format(self.dtype))
            else:
                if len(args) != 2:
                    raise ValueError('Too many arguments for DateRange({}, date)'.
                                     format(self.dtype))
            return

        raise ValueError("Invalid 1st argument for DateRange()")
    
    
    def __str__(self):
        """ Return DateRange in display format 
        """
        dstr1 = self._to_local(self.date1)
        dstr2 = self._to_local(self.date2)
        #print ("# dstr {} - {}".format(dstr1, dstr2))
        if self.dtype == self.DR_DATE: # Exact date d1
            return dstr1
        elif self.dtype == self.DR_TILL:  # Date till d1
            return "– {}".format(dstr1)
        elif self.dtype == self.DR_FROM: # Date from d1
            return "{} –".format(dstr1)
        elif self.dtype == self.DR_PERIOD: # Date period d1-d2
            return "{} – {}".format(dstr1, dstr2)
        elif self.dtype == self.DR_BETWEEN: # A date between d1 and d2
            return "välillä {} … {}".format(dstr1, dstr2)
        elif self.dtype == self.DR_ABOUT: # A date near d1
            return "noin {}".format(dstr1)
        elif self.dtype == self.DR_CALCULATED: # A calculated date near d1
            return "laskettu {}".format(dstr1)
        elif self.dtype == self.DR_ESTIMATED: # An estimated date at d1
            return "arviolta {}".format(dstr1)
        
        return "<Date type={}, {}...{}>".format(self.dtype, dstr1, dstr2)


    def __cmp__(self, other):
        """ The 'other' must be an objct of type DateRange.
        
            The return value of self.__cmp__(other) is 0 for equal to, 
            1 for greater than,  and -1 for less than the compared value.
        """
        assert isinstance(other, DateRange), 'Argument of wrong type!'

        if self.dtype < other.dtype:
            # A is self, B is other
            selftype=self.dtype
            othertype=other.dtype
            A1 = self.date1
            #A2 = self.date2
            B1 = other.date1
            B2 = other.date2
        else:
            # A is other, B is self
            selftype=other.dtype
            othertype=self.dtype
            A1 = other.date1
            #A2 = other.date2
            B1 = self.date1
            B2 = self.date2

        if selftype == DateRange.DR_DATE:
            if othertype == DateRange.DR_DATE:
                if A1 < B1:
                    return -1
                elif A1 > B1:
                    return 1
                return 0
            if othertype == DateRange.DR_TILL:
                if A1 > B1:
                    return 1
                return 0
            if othertype == DateRange.DR_FROM:
                if A1 < B1:
                    return -1
                return 0
            if othertype == DateRange.DR_PERIOD:
                if A1 < B1:
                    return -1
                elif A1 > B2:
                    return 1
                return 0
            else:   # DR_ABOUT, DR_CALC, DR_ESTIM
                # TODO dynaamisesti säätyvä delta tarkkuuden mukaan
                delta = "0000-00-30"
                if A1 < DateRange.minus(B1, delta):
                    return -1
                if A1 > DateRange.plus(B1, delta):
                    return 1
                return 0
        else:
            pass
        return 0


    @staticmethod
    def minus(d1, d2):
        ''' Returns date d1 - d2 
        '''
        #TODO calculate
        return d1
    
    @staticmethod
    def plus(d1, d2):
        ''' Returns date d1 + d2 
        '''
        #TODO calculate
        return d1


    def to_tuple(self):
        """ Returns a tuple (int, str, str) for save in database
            Example: (DR_BETWEEN, "1917", "2017-10-16")
        """
        return (self.dtype, self.date1, self.date2)


    def _to_datestr(self, val):
        """ Returns a date string '1972-12-06', '1972-12' or '1972', from
            - date object or
            - ordinal int value (later than year 1)
            - string value
        """
        if type(val).__name__ == 'date':
            return val.isoformat()
        elif isinstance(val, type("")):
            if len(val) == 10 and val[4] == '-' and val[7] == "-":
                # exact date '1999-12-31'
                return val
            elif len(val) == 7 and val[4] == '-':
                # year and month '1999-12'
                return val
            elif len(val) == 4:
                # year '1999'
                return val
        elif type(val).__name__ == 'int' and val > 365:
            return date.fromordinal(val).isoformat()
        
        raise ValueError("val={}".format(val))


    @staticmethod
    def _to_local(date_str):
        """ ISO-päivämäärä 2017-09-20 suodatetaan suomalaiseksi 20.9.2017 """
        try:
            a = date_str.split('-')
            if len(a) == 3:
                p = int(a[2])
                k = int(a[1])
                return "{}.{}.{}".format(p,k,a[0]) 
            elif len(a) == 2:
                k = int(a[1])
                return "{}.{}".format(k,a[0]) 
            else:
                return "{}".format(a[0])
        except:
            return date_str

