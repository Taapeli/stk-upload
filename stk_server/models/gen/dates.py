'''
Created on 16.10.2017

@author: jm
'''
from datetime import date, datetime

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
            #DataRange(Daterange) - not needed?
            DateRange(d1)
            DateRange(int, d1)
            DateRange(int, d1, d2)

            The first int argument tells the range type. 
            It is not obligatory, when the type is DR_DATE 
            (meaning a single exact date).

            Each d1, d2 for date '1917-12-06' can equally be expressed as:
            - a date object date(1917, 12, 6)
            - a complete date string '1917-12-06'
            - a partial date string '1917-12' for given year and month 
            - a year string '1917'
            - an ordinal int value 700144 ~ date(...).toordinal()
        '''
        try:
            # First argument is some kind of date
            self.date1 = self._to_datestr(args[0])
            self.dtype = self.DR_DATE
            self.date2 = None
            return
        except:
            pass
        
        if isinstance(args[0],type(1)):
            """ Arguments are dtype and 1 or 2 datevalues:
                DateRange(DATERANGE_TILL, date(2017, 10, 16))
                DateRange(DATERANGE_TILL, "2017-10-16")
                DateRange(1, 736618)
                DateRange(DATERANGE_BETWEEN, date(1917, 12, 6), date(2017, 10, 16))
                DateRange(DATERANGE_BETWEEN, "1917-12-06", "2017-10-16")
                DateRange(4, 700144, 736618)
            """
            self.dtype = args[0]
            if self.dtype < 0 or self.dtype > self.DR_ESTIMATED:
                raise ValueError('Invalid DateRange(type, ...)')
            self.date1 = self._to_datestr(args[1])
            self.date2 = None
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
        if self.dtype == self.DR_DATE: # Exact date d1
            return self.date1
        elif self.dtype == self.DR_TILL:  # Date till d1
            return "{} asti".format(self.date1)
        elif self.dtype == self.DR_FROM: # Date from d1
            return "{} alkaen".format(self.date1)
        elif self.dtype == self.DR_PERIOD: # Date period d1-d2
            return "{} – {}".format(self.date1, self.date2)
        elif self.dtype == self.DR_BETWEEN: # A date between d1 and d2
            return "välillä {} … {}".format(self.date1, self.date2)
        elif self.dtype == self.DR_ABOUT: # A date near d1
            return "noin {}".format(self.date1)
        elif self.dtype == self.DR_CALCULATED: # A calculated date near d1
            return "laskettu {}".format(self.date1)
        elif self.dtype == self.DR_ESTIMATED: # An estimated date at d1
            return "arviolta {}".format(self.date1)
        
        return "<Date type={}, {}...{}>".format(self.dtype, self.date1, self.date2)
    

    def to_tuple(self):
        """ Returns a tuple (int, str, str) for save in database
            Example: (DR_BETWEEN, "1917", "2017-10-16")
        """
        if self.date2:
            return (self.dtype, self.date1, self.date2)
        else:
            return (self.dtype, self.date1)


    def _to_datestr(self, val):
        """ Returns a date string '1972-12-06', '1972-12' or '1972', from
            - date object or
            - ordinal int value (later than year 1)
            - string value
        """
        if isinstance(val, type(date(1,1,1))):
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
        elif isinstance(val, type(1)) and val > 365:
            return date.fromordinal(val).isoformat()
        
        raise ValueError("val={}".format(val))
        
