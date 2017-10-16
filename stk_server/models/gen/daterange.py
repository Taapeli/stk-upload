'''
Created on 16.10.2017

@author: jm
'''
from datetime import date, datetime

DATERANGE_DATE = 0          # Exact date d1
DATERANGE_TILL = 1          # Date till d1
DATERANGE_FROM = 2          # Date from d1
DATERANGE_PERIOD = 3        # Date period d1-d2
DATERANGE_BETWEEN = 4       # A date between d1 and d2
DATERANGE_ABOUT = 5         # A date near d1
DATERANGE_CALCULATED = 6    # A calculated date near d1
DATERANGE_ESTIMATED = 7     # An estimated date at d1

class DateRange():
    '''
    DateRange handles date expressions needed for genealogical data.
    The dates are expressed with range type and one or two type date values.

    This class is designed specially for efficient processing in the database
    and it's user interfaces.

    Saa also another way of expressing date range values, specially for data
    exchange:
    https://github.com/FamilySearch/gedcomx/blob/master/specifications/date-format-specification.md
    '''

    def __init__(self, *args):
        '''
        Constructor can be called following ways:
          # DataRange(Daterange) - not needed?
            DateRange(d1)
            DateRange(int, d1)
            DateRange(int, d1, d2)

            The first int argument tells the integer range type. 
            It is not obligatory, when the type is DATERANGE_DATE 
            (meaning a single exact date).

            Each d1, d2 for date '1917-12-06' can equally be expressed as:
            - a date object: date(1917, 12, 6)
            - a string value: '1917-12-06'
            - an ordinal int value (later than year 1!): 700144
        '''
        try:
            # First argument is some kind of date
            self.date1 = self._to_date(args[0])
            self.dtype = DATERANGE_DATE
            self.date2 = None
            return
        except:
            pass
        
        if type(args[0]) == "int":
            """ Arguments are dtype and 1 or 2 datevalues:
                DateRange(DATERANGE_TILL, date(2017, 10, 16))
                DateRange(DATERANGE_TILL, "2017-10-16")
                DateRange(1, 736618)
                DateRange(DATERANGE_BETWEEN, date(1917, 12, 6), date(2017, 10, 16))
                DateRange(DATERANGE_BETWEEN, "1917-12-06", "2017-10-16")
                DateRange(4, 700144, 736618)
            """
            self.dtype = args[0]
            if self.dtype < 0 or self.dtype > DATERANGE_ESTIMATED:
                raise ValueError('Invalid DateRange(type, ...)')
            self.date1 = self._to_date(args[1])
            self.date2 = None
            if self.dtype in [DATERANGE_PERIOD, DATERANGE_BETWEEN]:
                if len(args) > 2:
                    self.date2 = self._to_date(args[2])
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
        return "<Date type={}, {}...{}>".format(self.dtype, self.date1, self.date2)
    

    def to_tuple(self):
        """ Returns a tuple like (4, 700144, 736618) representing values
            (DATERANGE_BETWEEN, date(1917, 12, 6), date(2017, 10, 16))
        """
        if self.date2:
            return (self.dtype, self.date1.toordinal(), self.date2.toordinal())
        else:
            return (self.dtype, self.date1.toordinal())


    def _to_date(self, val):
        """ Returns a date object from
            - date object or
            - ordinal int value (later than year 1)
            - string value 
        """
        if type(val) == 'date':
            return val
        elif type(val) == "str":
            return datetime.strptime(val, '%Y-%m-%d').date()
        elif type(val) == "int" and val > 365:
            return date.fromordinal(val)
        else:
            return None
        
