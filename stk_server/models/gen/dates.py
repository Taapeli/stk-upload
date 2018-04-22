'''
Created on 16.10.2017

@author: jm

'''

from datetime import date

DR = {
    'DATE':0,           # exact date d1
    'BEFORE':1,         # date till d1
    'AFTER':2,          # date from d1
    'PERIOD':3,         # during the period of d1, d2
    'BETWEEN':4,        # date between d1, d2
    'ABOUT':5,          # about d1
    'CALC_DATE':8,
    'CALC_BEFORE':9,
    'CALC_AFTER':10,
    'CALC_PERIOD':11,
    'CALC_BETWEEN':12,
    'CALC_ABOUT':13,
    'EST_DATE':16,
    'EST_BEFORE':17,
    'EST_AFTER':18,
    'EST_PERIOD':19,
    'EST_BETWEEN':20,
    'EST_ABOUT':21
}

# class DateTolerance():
#     '''
#     pelkkä vuosiluku – toleranssi 10 vuotta
#     kuukausi ja vuosi – toleranssi 1.–31. päivä
#     noin pvm – toleranssi 5 vuotta
#     alkaen / jälkeen – avoimen pään toleranssi 100 vuotta(?)
# '''
#     @staticmethod
#     def upperYear(dateint):
#         return DateRange.DateInt(10)
#     @staticmethod
#     def lowerYear():
#         return DateRange.DateInt(10)
# 
#     @staticmethod
#     def forMonth(year, month, day=None):
#         return DateRange.DateInt(year, month)
# 
#     @staticmethod
#     def forDay(year, month, day):
#         return DateRange.DateInt(year, month, day)


class DateRange():
    '''
    DateRange handles date expressions needed for genealogical data.
    The dates are expressed with date range type and one or two string values
    representing the date limits (from, to).

    This class is designed specially for efficient processing in the database
    and it's user interfaces.

    The data is stored in the following variables:
    - datetype    int    date type from DR array
    - datestr1    string 'from' date
    - datestr2    string 'to' date, a string or None
    '''

    def __init__(self, *args):
        '''
        DateRange constructor can be called following ways:
            DateRange(d1)
            DateRange(int, d1)
            DateRange(int, d1, d2)
            DataRange((int, str1, str2))

            The first int argument tells the range type. It is not obligatory, 
            when the type is DR['DATE'] (meaning a single exact date).

            Each d1, d2 for date '1917-12-06' can equally be expressed as:
            - an DateInt value 700144
            - a date object date(1917, 12, 6)
            - a complete date string '1917-12-06'
            - a partial date string '1917-12' for given year and month 
            - a year string '1917'
            The d2 can also be empty string "".

            The last form is used for loading a DataRange from database. The 
            argument is assumed to be a tuple like the output of DataRange.to_list() 
            method, and the components formats are not checked.
        '''

        if len(args) == 1:
            if isinstance(args[0], (list, tuple)) and len(args[0]) in [2, 3]:
                # The only argument is a tuple like (3, '1918-12', '2017-10-16')
                self.datetype = int(args[0][0])
                self.date1 = DateRange.DateInt(args[0][1])
                if len(args[0]) == 3 and args[0][2] != None and args[0][2] != '':
                    self.date2 = self.DateInt(args[0][2])
                else:
                    self.date2 = None
                return
            elif isinstance(args[0], (DateRange, Gramps_DateRange)):
                # The only argument is a DataRange
                self.datetype = args[0].datetype
                self.date1 = self.DateInt(args[0].date1)
                self.date2 = self.DateInt(args[0].date2)
                return
            elif isinstance(args[0], (str, date)):
                # Maybe the only argument is some kind of date string
                try:
                    self.datetype = DR['DATE']
                    self.date1 = self.DateInt(args[0])
                    self.date2 = None
                    return
                except:
                    raise ValueError("Invalid DateRange({})".format(args[0]))

        if isinstance(args[0], int) or \
          (isinstance(args[0], str) and args[0].isdigit()):
            """ Arguments are datetype (int or numeric str) 
                and there is 1 or 2 date values:
                    DateRange(DR['BEFORE'], date(2017, 10, 16))
                    DateRange(DR['BEFORE'], "2017-10-16")
                    DateRange("1", "2017-10-16")
                    DateRange(1, 736618)
                    DateRange(DR['BETWEEN'], date(1917, 12, 6), date(2017, 10, 16))
                    DateRange(DR['BETWEEN'], "1917-12-06", "2017-10-16")
                    DateRange(4, 700144, 736618)
            """
            self.datetype = int(args[0])
            self.date1 = self.DateInt(args[1])
            self.date2 = None
            if self.datetype < 0 or self.datetype > DR['EST_ABOUT']:
                raise ValueError('Invalid DateRange(type, ...)')
#             if self.datetype in [DR['PERIOD'], DR['BETWEEN'],
#                                  DR['CALC_PERIOD'], DR['CALC_BETWEEN'],
#                                  DR['EST_PERIOD'], DR['EST_BETWEEN']]:
            if len(args) == 3 and args[1] != args[2]:
                self.date2 = self.DateInt(args[2])
#             else:
#                 raise ValueError('Two dates excepted for DateRange({}, date, date)'.
#                                  format(self.datetype))
#             else:
#                 if len(args) != 2:
#                     raise ValueError('Too many arguments for DateRange({}, date)'.
#                                      format(self.datetype))
            return

        raise ValueError("Invalid 1st argument for DateRange()")


    def __str__(self):
        """ Return DateRange in display format like 'välillä 1700 … 9.1800'
        """
        type_e = self.datetype & 7        # Lower bits has effective type code
        type_opt = self.datetype-type_e   # Upper bits has options

        if type_opt == 8:   
            # Code name starts with 'CALC_'
            dopt = 'laskettuna '
        elif type_opt == 16:
            # Code name starts with 'EST_'
            dopt = 'arviolta '
        else:
            dopt = ''

        dstr1 = self.date1.to_local()
        dstr2 = "" if self.date2 == None else self.date2.to_local()
        #print ("# dstr {} - {}".format(dstr1, dstr2))
        if type_e == DR['DATE']: # Exact date d1
            return dopt + dstr1
        elif type_e == DR['BEFORE']:  # Date till d1
            return "{}{} mennessä".format(dopt, dstr1)
        elif type_e == DR['AFTER']: # Date from d1
            return "{}{} alkaen".format(dopt, dstr1)
        elif type_e == DR['PERIOD']: # Date period d1-d2
            return "{}{} – {}".format(dopt, dstr1, dstr2)
        elif type_e == DR['BETWEEN']: # A date between d1 and d2
            return "{}välillä {} … {}".format(dopt, dstr1, dstr2)
        elif type_e == DR['ABOUT']: # A date near d1
            return "{}noin {}".format(dopt, dstr1)

        return "<Date type={}, {}...{}>".format(self.datetype, dstr1, dstr2)


#     def __cmp__(self, other):
#         """ The 'other' must be an objct of type DateRange.
# 
#             The return value of self.__cmp__(other) is 0 for equal to, 
#             1 for greater than,  and -1 for less than the compared value.
#         """
#         assert isinstance(other, DateRange), 'Argument of wrong type!'
# 
#          # ... etc ...
#         return 0


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

    def estimate(self):
        """ Gives a date estimate """
        return self.date1.long_date()

    def plain_type(self):
        """ Gives numeric type code without 'CALC_' or 'EST_' """
        return self.datetype & 7

    def is_calculated(self):
        """ Is this date calculated?
            The type code has bit corresponding 8 set
        """
        return (self.datetype & 8) != 0

    def is_estimated(self):
        """ Is this date calculated?
            The type code has bit corresponding 16 set
        """
        return (self.datetype & 16) != 0

    def to_list(self):
        """ Returns a list [int, str, str] or [int, str] 
            Example: [DR['BETWEEN'], "1917", "2017-10-16"]
        """
        if self.date2 != None:
            return [self.datetype, self.date1.short_date(), self.date2.short_date()]
        else:
            return [self.datetype, self.date1.short_date()]

    def to_local(self):
        """ Returns a list [int, str, str] or [int, str] for display
            Example: [DR['BETWEEN'], "1917", "16.10.2017"]
        """
        if self.date2 != None:
            return [self.datetype, self.date1.to_local(), self.date2.to_local()]
        else:
            return [self.datetype, self.date1.to_local()]

    def for_db(self):
        """ Returns a dictionary consisting of int datetype and 
            always two dates as intvalues
        """
        v1 = self.date1.value()
        v2 = self.date2.value() if self.date2 != None else v1
        ret = {'datetype': self.datetype, 'date1': v1, 'date2': v2}
        return ret


    # ----------------------- DateRange.DateInt class --------------------------

    class DateInt():
        ''' DateRange.DateInt class carries single date components as an integer, 
            which is can be oredered even if there are missing date parts.

            The missing day or month value is set in the middle of
            year or month respectively, as if '6½th month' and '15½th day'.

            >>> DateInt("1917-12-15")
            # 1917 12 14 = 1963406 / 00000000000111011111010110001110 internal
            >>> DateInt(1917, 12)
            # 1917 12 15 = 1963407 / 00000000000111011111010110001111 internal
            >>> DateInt(1917, 12, 16)
            # 1917 12 16 = 1963408 / 00000000000111011111010110010000 internal
        '''
        def __init__(self, arg0=None, month=None, day=None):
            """ DateRange.DateInt.__init__() builds an DateInt value from
                - date expressions like '2017-09-20' or '2017-09' or '2017'
                - int values year, month, day

                The missing day or month values are simulated as
                '6½th month' and '15½th day' to allow some kind of sorting.

                The int value special cases:
                - if the day part is 15 --> only year-month are given
                - if the month part is 6 --> only year is given

                'yyyy- mm - dd'
                a[0]  a[1]  a[2]   | y       m       d
                -------------------+-----------------------
                9999  1..6  -      | a[0]    a[1]-1  15
                9999  -     -      | a[0]    6       0
                9999  7..12 -      | a[0]    a[1]    15
                9999  99    1..15  | a[0]    *       a[2]-1
                9999  99    -      | a[0]    *       15
                9999  99    16..31 | a[0]    *       a[2]

                The stored value is (d*32 + m)*32 + y
            """
            if arg0 == None:
                # No value
                self.intvalue = 0
            elif isinstance(arg0, int):
                if arg0 > 9999:
                    # Not a year but a ready DateInt value
                    self.intvalue = arg0
                else:
                    # Integer year, month, day values
                    self._set(arg0, month, day)
            elif isinstance(arg0, date):
                # A datetime.date
                self._set(arg0.year, arg0.month, arg0.day)
            elif isinstance(arg0, str):
                # A date string
                a = arg0.split('-', 2)
                year = int(a[0])
                month = int(a[1]) if len(a) > 1 else None
                day  =  int(a[2]) if len(a) > 2 else None
                self._set(year, month, day)
            else:
                raise TypeError('DateInt({})'.format(arg0))
            return

        def _set(self, year, month, day):
            ''' Set dateint value by components '''
            if month == None or month == 0:
                month = 6
                day = 0
            else:
                if month < 7:
                    month -= 1
    
                if day == None or day == 0:
                    day = 15
                else:
                    if day < 16:
                        day -= 1
    
            self.intvalue = (year<<10) | (month<<5) | day
#             print("# {:4d} {:02d} {:02d} = {:07d} / {:032b} internal".\
#                   format(year,month,day, self.intvalue, self.intvalue))

        def __str__(self):
            return self.long_date()

        def value(self):
            ''' Returns the comparable date integer value of DateRange.DateInt '''
            return self.intvalue

        def vector(self):
            """ Splits the DateRange.DateInt value to integer components.

                A date '2047-02-02' gives binary list (2047, 2, 2)
                    0....:....1....:....2. ...:. ...3.
                    0000000000011111111111 00001 00001
                               yyyyyyyyyyy mmmmm ddddd
                               [0:21]    [22:26] [27:31]
                Special processing:
                - if the day part is 15 --> only year-month are returned
                - if the month part is 6 --> only year is returned
            """
            dy = self.intvalue >> 10
            dm = (self.intvalue >> 5) & 0x0f
            dd = self.intvalue & 0x1f

            if dm == 6:     # = Year only
                return [dy]
            else:
                if dm < 6:
                    dm += 1
                if dd == 15:    # Year and month
                    return [dy, dm]
                else:           # Year, month, day
                    if dd < 15:
                        dd += 1
                    return [dy, dm, dd]

        def long_date(self):
            """ Converts the DateRange.DateInt value to ISO date string.
                    0....:....1....:....2. ...:. ...3.
                    0000000000011111111111 00001 00001
                               yyyyyyyyyyy mmmmm ddddd
                               [0:21]    [22:26] [27:31]
                Special processing:
                - if the day part is 15 --> only year-month are given
                - if the month part is 6 --> only year is given
            """
            vec = self.vector()
            if len(vec) > 2:
                return "{:04d}-{:02d}-{:02d}".format(vec[0], vec[1], vec[2])
            elif len(vec) == 2:
                return "{:04d}-{:02d}-00".format(vec[0], vec[1])
            else:
                return "{:04d}-00-00".format(vec[0])

        def short_date(self):
            """ Converts DateRange.DateInt value to possible shortened 
                ISO date string where zero month or day parts are removed.
            """
            s = self.long_date()
            while s[-3:] == "-00":
                s = s[:-3]
            return s

        def to_local(self):
            """ DateRange.DateInt.to_local() converts the DateInt value to
                Finnish style 20.9.2017 date, even when the month or day are zeroes
            """
            try:
                a = self.vector()
                if len(a) == 3:
                    p = int(a[2])
                    k = int(a[1])
                    return "{}.{}.{}".format(a[2],a[1],a[0]) 
                elif len(a) == 2:
                    k = int(a[1])
                    return "{}.{}".format(a[1],a[0]) 
                else:
                    return "{}".format(a[0])
            except:
                # Could not split
                return "({})".format(self.long_date())


# -------------------------- Gramps_DateRange class ---------------------------

class Gramps_DateRange(DateRange):
    '''
    Imports Gramps xml fields into a DateRange object.

    Some Gramps xml examples:
    <daterange start=$date1 stop=$date2 />
    <daterange start=$date1 stop=$date2 quality="estimated"/>
    <datespan start=$date1 stop=$date2 />
    <datespan start=$date1 stop=$date2 quality="calculated"/>
    <datespan start=$date1 stop=$date2 quality="estimated"/>
    <dateval val=$date1 quality="calculated"/>
    <dateval val=$date1 quality="estimated"/>
    <dateval val=$date1 type="about"/>
    <dateval val=$date1 type="after"/>
    <dateval val=$date1 type="after" quality="estimated"/>
    <dateval val=$date1 type="before"/>
    <datestr val=$str />

    A date $date1:
        dateval   type=$datetype quality=$quality val=$datestr1

    Between $date1 and $date2:
        daterange type=None    quality=$quality start=$datestr1 stop=$datestr2

    From $date1 to $date2:
        datespan  type=None    quality=$quality start=$datestr1 stop=$datestr2

    Unformal string expression $str (passed?)
        datestr   type=None    quality=None     val=str

    - where $quality = {calculated|estimated|None}

    TODO: All the combinations:

    tag       type   quality    attr       DR value    datetype text(fi)          estimate
    ---       ----   -------    ----       --------    -------- ----              --------
    dateval   None   None       val        DATE         0     0 {val}             val
    dateval   before None       val        BEFORE       1     1 {val} asti        val
    dateval   after  None       val        AFTER        2     2 {val} alkaen      val
    datespan  None   None       start,stop PERIOD       3     3 {start} – {stop}  (stop-start)/2
    daterange None   None       start,stop BETWEEN      4     4 {start} ja {stop} 
                                                                valillä           (stop-start)/2
    dateval   about  None       val        ABOUT        5     5 noin {val}        val

    dateval   None   None       val        CALC_DATE    0+8   8 laskettuna {val}
    dateval   before calculated val        CALC_BEFORE  1+8   9 laskettuna {val} asti
    dateval   after  calculated val        CALC_AFTER   2+8  10 laskettuna {val} alkaen
    datespan  None   calculated start,stop CALC_PERIOD  3+8  11 laskettuna {start} – {stop}
    daterange None   calculated start,stop CALC_BETWEEN 4+8  12 laskettuna {start} ja {stop} valillä
    dateval   about  calculated val        CALC_ABOUT   5+8  13 laskettuna noin {val}

    dateval   None   None       val        EST_DATE     0+16 16 arviolta {val}
    dateval   before estimated  val        EST_BEFORE   1+16 17 arviolta {val} asti
    dateval   after  estimated  val        EST_AFTER    2+16 18 arviolta {val} alkaen
    datespan  None   estimated  start,stop EST_PERIOD   3+16 19 arviolta {start} – {stop}
    daterange None   estimated  start,stop EST_BETWEEN  4+16 20 arviolta {start} ja {stop} valillä 
    dateval   about  estimated  val        EST_ABOUT    5+16 21 arviolta noin {val}
    '''

    def __init__(self, xml_tag, xml_type, quality, date1, date2=None):
        """ 
        Importing a DateRange from Gramps xml structure elements
        """
        if xml_tag == 'dateval':
            if xml_type:
                dr = xml_type.upper()
            else:
                dr = 'DATE'
        elif xml_tag == 'daterange':
            dr = 'BETWEEN'
        elif xml_tag == 'datespan':
            dr = 'PERIOD'
        else:
            dr = None

        if quality == 'calculated':
            dr = 'CALC_' + dr
        elif quality == 'estimated':
            dr = 'EST_' + dr

        super(Gramps_DateRange, self).__init__((DR[dr], date1, date2))

