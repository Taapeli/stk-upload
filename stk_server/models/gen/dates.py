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

class DateRange():
    '''
    DateRange handles date expressions needed for genealogical data.
    The dates are expressed with range type and one or two string values
    representing the date limits.

    This class is designed specially for efficient processing in the database
    and it's user interfaces.
    
    The data is stored in vector self.vec, which has following contents:
    - vec[0]    date type, an integer from DR
    - vec[1]    1st date, in string format
    - vec[2]    2nd date, a string or None

    Saa also another way of expressing date range values, specially for data
    exchange:
    https://github.com/FamilySearch/gedcomx/blob/master/specifications/date-format-specification.md
    '''

    def __init__(self, *args):
        '''
        Constructor can be called following ways:
            DateRange(d1)
            DateRange(int, d1)
            DateRange(int, d1, d2)
            DataRange((int, str1, str2))

            The first int argument tells the range type. It is not obligatory, 
            when the type is DR['DATE'] (meaning a single exact date).

            Each d1, d2 for date '1917-12-06' can equally be expressed as:
            - a date object date(1917, 12, 6)
            - a complete date string '1917-12-06'
            - a partial date string '1917-12' for given year and month 
            - a year string '1917'
            - an ordinal int value 700144 ~ date(...).toordinal()
            The d2 can also be empty string "".
            
            The last form is used for loading a DataRange from database. The 
            argument is assumed to be a tuple like the output of DataRange.to_list() 
            method, and the components formats are not checked.
        '''

#         if not args[0]:
#             # Creating an empty date
#             self.vec = [0, "", None]
#             return

        if len(args) == 1:
            if isinstance(args[0], (list,tuple)) and len(args[0]) in [2, 3]:
                # The only argument is a tuple like (3, '1918-12', '2017-10-16')
                vec0 = int(args[0][0])
                vec1 = args[0][1]
                if len(args[0]) == 3:
                    vec2 = args[0][2] if not args[0][2] == "" else None
                else:
                    vec2 = None
                self.vec = [vec0, vec1, vec2]
                return
            elif isinstance(args[0], (DateRange, Gramps_DateRange)):
                # The only argument is DataRange
                self.vec = args[0].to_list()
                return
            elif isinstance(args[0], (str,date)):
                # Maybe the only argument is some kind of date string
                try:
                    self.vec = [DR['DATE'], self._to_datestr(args[0]), None]
                    return
                except:
                    raise ValueError("Invalid DateRange({})".format(args[0]))
        
        if isinstance(args[0], int) or \
          (isinstance(args[0], str) and args[0].isdigit()):
            """ Arguments are dtype (int or numeric str) 
                and there is 1 or 2 date values:
                    DateRange(DR['BEFORE'], date(2017, 10, 16))
                    DateRange(DR['BEFORE'], "2017-10-16")
                    DateRange("1", "2017-10-16")
                    DateRange(1, 736618)
                    DateRange(DR['BETWEEN'], date(1917, 12, 6), date(2017, 10, 16))
                    DateRange(DR['BETWEEN'], "1917-12-06", "2017-10-16")
                    DateRange(4, 700144, 736618)
            """
            self.vec = [int(args[0]), self._to_datestr(args[1]), None]
            dtype = self.vec[0]
            if dtype < 0 or dtype > DR['EST_ABOUT']:
                raise ValueError('Invalid DateRange(type, ...)')
            if dtype in [DR['PERIOD'], DR['BETWEEN'],
                         DR['CALC_PERIOD'], DR['CALC_BETWEEN'],
                         DR['EST_PERIOD'], DR['EST_BETWEEN']]:
                if len(args) == 3:
                    self.vec[2] = self._to_datestr(args[2])
                else:
                    raise ValueError('Two dates excepted for DateRange({}, date, date)'.
                                     format(dtype))
            else:
                if len(args) != 2:
                    raise ValueError('Too many arguments for DateRange({}, date)'.
                                     format(dtype))
            return

        raise ValueError("Invalid 1st argument for DateRange()")
    
    
    def __str__(self):
        """ Return DateRange in display format 
        """
        type_e = self.vec[0] & 7        # Lower bits has effective type code
        type_opt = self.vec[0]-type_e   # Upper bits has options
        dopt = ''
        
        if type_opt == 8:           
            # Code name starts with 'CALC_'
            dopt = 'laskettuna '
        elif type_opt == 16:
            # Code name starts with 'EST_'
            dopt = 'arviolta '

        dstr1 = self._to_local(self.vec[1])
        dstr2 = self._to_local(self.vec[2])
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
        
        return "<Date type={}, {}...{}>".format(self.vec[0], dstr1, dstr2)


#     def __cmp__(self, other):
#         """ The 'other' must be an objct of type DateRange.
#         
#             The return value of self.__cmp__(other) is 0 for equal to, 
#             1 for greater than,  and -1 for less than the compared value.
#         """
#         assert isinstance(other, DateRange), 'Argument of wrong type!'
# 
#         if self.vec[0] < other.vec[0]:
#             # A is self, B is other
#             selftype=type_e
#             othertype=other.vec[0]
#             A1 = self.vec[1]
#             #A2 = self.vec[2]
#             B1 = other.vec[1]
#             B2 = other.vec[2]
#         else:
#             # A is other, B is self
#             selftype=other.vec[0]
#             othertype=type_e
#             A1 = other.vec[1]
#             #A2 = other.vec[2]
#             B1 = self.vec[1]
#             B2 = self.vec[2]
# 
#         if selftype == DR['DATE']:
#             if othertype == DR['DATE']:
#                 if A1 < B1:
#                     return -1
#                 elif A1 > B1:
#                     return 1
#                 return 0
#             if othertype == DR['TILL']:
#                 if A1 > B1:
#                     return 1
#                 return 0
#             if othertype == DR['FROM']:
#                 if A1 < B1:
#                     return -1
#                 return 0
#             if othertype == DR['PERIOD']:
#                 if A1 < B1:
#                     return -1
#                 elif A1 > B2:
#                     return 1
#                 return 0
#             else:   # DR['ABOUT'], DR['CALC'], DR['ESTIM']
#                 # TODO dynaamisesti säätyvä delta tarkkuuden mukaan
#                 delta = "0000-00-30"
#                 if A1 < DateRange.minus(B1, delta):
#                     return -1
#                 if A1 > DateRange.plus(B1, delta):
#                     return 1
#                 return 0
#         else:
#             pass
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
        return self.vec[1]
    
    def plain_type(self):
        """ Gives numeric type code without 'CALC_' or 'EST_' """
        return self.vec[0] & 7
    
    def is_calculated(self):
        """ Is this date calculated?
            The type code has bit corresponding 8 set
        """
        return (self.vec[0] & 8) != 0

    def is_estimated(self):
        """ Is this date calculated?
            The type code has bit corresponding 16 set
        """
        return (self.vec[0] & 16) != 0

    def to_list(self):
        """ Returns a list [int, str, str] or [int, str] 
            Example: [DR['BETWEEN'], "1917", "2017-10-16"]
        """
        if self.vec[2]:
            return self.vec
        else:
            return self.vec[0:2]

    def for_db(self):
        """ Returns a list like to_list, but type code is converted to string 
            for saving to database.
            Example: ["4", "1917", "2017-10-16"]
        """
        ret = [str(self.vec[0]), self.vec[1]]
        if self.vec[2]:
            ret.append(self.vec[2])

        return ret

    def _to_datestr(self, val):
        """ Returns a date-like string '1972-12-06', '1972-12' or '1972', from
            - date object or
            - ordinal int value (later than year 1)
            - string value
        """
        if isinstance(val, date):
            return val.isoformat()
        elif isinstance(val, str):
            if len(val) == 10 and val[4] == '-' and val[7] == "-":
                # exact date '1999-12-31'
                return val
            elif len(val) == 7 and val[4] == '-':
                # year and month '1999-12'
                return val
            elif len(val) == 4:
                # year '1999'
                return val
        elif isinstance(val, int) and val > 365:
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

    @staticmethod
    def date_to_int(date_str):
        """ Converts a date like '2017-09-20' or '2017-09' or '2017'
            to int value, which can be easily compared.

            The missing day or month value is set in the middle of
            year or month respectively, as if '6½th month' and '15½th day'.

            'yyyy-mm-dd'            
            a[0]  a[1]  a[2]   | y       m       d
            -------------------+-----------------------
            9999               | a[0]    7       0
            9999  1..6         | a[0]    a[1]-1  16
            9999  7..12        | a[0]    a[1]    16
            9999  99    1..15  | a[0]    *       a[2]-1
            9999  99    16..31 | a[0]    *       a[2]

            return      (d*32 + m)*32 + y

            date '2047-02-02' gives binary
                0000 0000 0001 1111 ¤ 1111 1100 0010 0001
                             y yyyy ¤ yyyy yymm mmmd dddd
                0....:....1....:....2. ...:. ...3.
                0000000000011111111111 00001 00001
                           yyyyyyyyyyy mmmmm ddddd
                           [0:21]    [22:26] [27:31]
        """
        a = date_str.split('-', 2)
        dy = int(a[0])
        if len(a) == 1 or a[1] == '00':
            dm = 7
            dd = 16
        else:
            dm = int(a[1])
            if dm < 7:
                dm -= 1

            if len(a) == 2 or a[2] == '00':
                dd = 16
            else:
                dd = int(a[2])
                if dd < 16:
                    dd -= 1

        ret = (dy<<10) | (dm<<5) | dd
        print("{:4d} {:02d} {:02d} = {:07d} / {:032b} internal".\
              format(dy,dm,dd, ret, ret))

        return ret

    @staticmethod
    def int_to_date(date_int):
        """ Converts an int date to ISO date string.
                0....:....1....:....2. ...:. ...3.
                0000000000011111111111 00001 00001
                           yyyyyyyyyyy mmmmm ddddd
                           [0:21]    [22:26] [27:31]
        """
        dy = date_int >> 10
        dm = (date_int >> 5) & 0x0f
        dd = date_int & 0x1f

        if dm < 7:
            dm += 1
        elif dm == 7:
            dm = 0
        
        if dd < 16:
            dd += 1
        elif dd == 16:
            dd = 0

        s = "{:04d}-{:02d}-{:02d}".format(dy, dm, dd)
        print (s + " returned")
        return s

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
        dateval   type=$vec[0] quality=$quality val=$vec[1]

    Between $date1 and $date2:
        daterange type=None    quality=$quality start=$vec[1] stop=$vec[2]

    From $date1 to $date2:
        datespan  type=None    quality=$quality start=$vec[1] stop=$vec[2]

    Unformal string expression $str (passed?)
        datestr   type=None    quality=None     val=str

    - where $quality = {calculated|estimated|None}

    TODO: All the combinations:
    
    tag       type   quality    attr       DR value      vec[0] text(fi)          estimate
    ---       ----   -------    ----       --------     ------- ----              --------
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
        
