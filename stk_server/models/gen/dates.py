'''
Created on 16.10.2017

@author: jm

TODO: estimate() .method
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

from datetime import date

#TODO: DR-arvot ja nimet tarkstettava ja suunniteltava
DR = {'DATE': 0,        # Exact date d1
    'TILL': 1,          # Date till d1
    'FROM': 2,          # Date from d1
    'PERIOD': 3,        # Date period d1-d2
    'BETWEEN': 4,       # A date between d1 and d2
    'ABOUT': 5,         # A date near d1
    'CALCULATED': 8,    # A calculated date near d1
    'ESTIMATED': 16     # An estimated date at d1
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

        if len(args) == 1:
            if isinstance(args[0], (list,tuple)) and len(args[0]) == 3:
                # The only argument is a tuple like (3, '1918-12', '2017-10-16')
                self.vec = list(args[0])
                if self.vec[2] == "":
                    self.vec[2] = None
                return
            elif isinstance(args[0], DateRange):
                self.vec = args[0].to_list()
                return
            elif isinstance(args[0], (str,date)):
                try:
                    # Maybe the only argument is some kind of date string
                    self.vec = [DR['DATE'], self._to_datestr(args[0]), None]
                    return
                except:
                    raise ValueError("Invalid DateRange({})".format(args[0]))
        
        if isinstance(args[0], int):
            """ Arguments are dtype and 1 or 2 datevalues:
                DateRange(DR['TILL'], date(2017, 10, 16))
                DateRange(DR['TILL'], "2017-10-16")
                DateRange(1, 736618)
                DateRange(DR['BETWEEN'], date(1917, 12, 6), date(2017, 10, 16))
                DateRange(DR['BETWEEN'], "1917-12-06", "2017-10-16")
                DateRange(4, 700144, 736618)
            """
            self.vec = [args[0], self._to_datestr(args[1]), None]
            dtype = self.vec[0]
            if dtype < 0 or dtype > DR['ESTIMATED']:
                raise ValueError('Invalid DateRange(type, ...)')
            if dtype in [DR['PERIOD'], DR['BETWEEN']]:
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
        dtype = self.vec[0]
        dstr1 = self._to_local(self.vec[1])
        dstr2 = self._to_local(self.vec[2])
        #print ("# dstr {} - {}".format(dstr1, dstr2))
        if dtype == DR['DATE']: # Exact date d1
            return dstr1
        elif dtype == DR['TILL']:  # Date till d1
            return "– {}".format(dstr1)
        elif dtype == DR['FROM']: # Date from d1
            return "{} –".format(dstr1)
        elif dtype == DR['PERIOD']: # Date period d1-d2
            return "{} – {}".format(dstr1, dstr2)
        elif dtype == DR['BETWEEN']: # A date between d1 and d2
            return "välillä {} … {}".format(dstr1, dstr2)
        elif dtype == DR['ABOUT']: # A date near d1
            return "noin {}".format(dstr1)
        elif dtype == DR['CALCULATED']: # A calculated date near d1
            return "laskettu {}".format(dstr1)
        elif dtype == DR['ESTIMATED']: # An estimated date at d1
            return "arviolta {}".format(dstr1)
        
        return "<Date type={}, {}...{}>".format(dtype, dstr1, dstr2)


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
#             selftype=dtype
#             othertype=other.vec[0]
#             A1 = self.vec[1]
#             #A2 = self.vec[2]
#             B1 = other.vec[1]
#             B2 = other.vec[2]
#         else:
#             # A is other, B is self
#             selftype=other.vec[0]
#             othertype=dtype
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


    def to_list(self):
        """ Returns a list [int, str, str] or [int, str] for saving to database
            Example: [DR['BETWEEN'], "1917", "2017-10-16"]
        """
        if self.vec[2]:
            return self.vec
        else:
            return self.vec[0:2]


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

def DateRange_gramps(DateRange):
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
    '''
    
    def __init__(xml_tag, xml_type, quality, date1, date2=None):
        """ 
        Importing a DateRange from Gramps xml structure elements
        """
        pass