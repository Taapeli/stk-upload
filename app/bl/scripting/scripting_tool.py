#!/usr/bin/env python3


"""
Lists all batches from the database.

    usage: batchlist.py
    
"""

import datetime
import functools
import html
import json
import traceback

from pprint import pprint 

from typing import List

# parser = argparse.ArgumentParser()
# parser.add_argument("--batch_id", required=True)
# parser.add_argument("--scope", choices=["Person","Family","Event","Place"], required=True)
# parser.add_argument("--init")
# parser.add_argument("--statements")
# parser.add_argument("--filter")
# parser.add_argument("--expressions")
# parser.add_argument("--limit", type=int, default=-1)
# args = parser.parse_args()
# 
# from unittest.mock import Mock
# 
import shareds
from bl.batch.root import Root

# from app import app
# from types import SimpleNamespace
# 
# 
# # the necessary statements taken from setups.py:
# from pe.neo4j.neo4jengine import Neo4jEngine
# 
# shareds.db = Neo4jEngine(shareds.app)
# shareds.driver  = shareds.db.driver

class NULLException(Exception): pass

class Lazyenv(dict):
    def __init__(self, obj, attrs, exception_from_null=False):
        self.obj = obj
        self.attrs = attrs
        self['self'] = obj
        self.exception_from_null = exception_from_null
    def __getitem__(self, attrname):
        if attrname in self.attrs + ["scope"]:
            value = getattr(self.obj, attrname, NULL)
            if value is NULL and self.exception_from_null:
                raise NULLException()
            return value
        return dict.__getitem__(self, attrname)

class Proxy:
    def __init__(self, executor, uid, values):
        self._executor = executor
        self.scope = executor._args.scope
        self.batch_id = executor.batch_id
        self.uid = uid
        self.__dict__.update(**values)

    @property
    def attrs(self):
        return [name for name in dir(self) if not name.startswith("_")]

    @property
    def _attrs(self):
        return [name for name in self.attrs if name != "attrs"]

    def __repr__(self):
        return self._getlink_or_id()
        #return f"{self.__class__.__name__.replace('Proxy','')}[{self.id}]"

    def _getlink_or_id(self):
        objtype = self.__class__.__name__.replace('Proxy','').lower()
        #objtype = self.scope.lower()
        sep = "?"
        haslink = True
        if objtype == "person": sep = "?"
        if objtype == "family": sep = "?"
        if objtype == "event": sep = "/"
        if objtype == "place": sep = "/"
        if objtype == "place": objtype = "location"
        if objtype == "citation": 
            haslink = False
        if objtype == "repository": 
            haslink = False
        if objtype == "note": 
            haslink = False
        if haslink:
            return  f"""<a href="/scene/{objtype}{sep}uuid={self.uuid}" target="_blank">{self.id}</a>""" 
        elif hasattr(self, 'id'):
            return self.id
        else:
            pprint(self.__dict__)
            return str(self.uid)

    @property
    @functools.lru_cache(1)
    def notes(self):
        cypher = """
        match 
            (r:Root{id:$batch_id})
                --> (x)
                -[:NOTE]-> (n:Note) 
        where
            id(x) = $uid
        return id(n) as id, n as obj
        """
        
        values = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid):
            obj = rec['obj']
            values.append(NoteProxy(self._executor, rec['id'],dict(obj)))
        return values

USE_MOCK = True
USE_MOCK = False
if USE_MOCK:
    from unittest.mock import MagicMock
    NULL = MagicMock()
    NULL.__bool__.return_value = False
else:
    @functools.total_ordering
    class NullProxy:
        def __repr__(self):
            return "NULL"
        def __str__(self):
            return ""
        def __getattr__(self, _attrname):
            return NULL
        def __getitem__(self, _index):
            return NULL
        def __add__(self, _other):
            return NULL
        def __sub__(self, _other):
            return NULL
        def __mul__(self, _other):
            return NULL
        def __div__(self, _other):
            return NULL
        def __floordiv__(self, _other):
            return NULL
        def __lt__(self, _other):
            return NULL
        def __gt__(self, _other):
            return NULL
        def __eq__(self, _other):
            return NULL
        def __call__(self, _other):
            return NULL
        def __bool__(self):
            return False
    
    NULL = NullProxy()


import bl.dates as dates

def getSortkey(tuplevalue):
    return "-".join([f"{a:04}" for a in tuplevalue])

@functools.total_ordering
class DateProxy():
    def __init__(self, dates: List[int]):  # dates = [yyyy,mm,dd]
        self.dates1 = dates[:]
        self.dates = dates[:]
        while len(self.dates) < 3: self.dates.append(0)
        #self.dt = datetime.date(*self.dates)

    @staticmethod
    def from_daterange(datetype, date1, date2):
        dr = dates.DateRange(datetype, date1, date2)
        dp = DateProxy(dr.date1.vector())
        return dp

    def __repr__(self):
        return "("+",".join(str(a) for a in self.dates)+")"
    
    def __str__(self):
        return "-".join([f"{a:02}" for a in self.dates])

    def normalize(self, yy, mm, dd):
        while dd <= 0:
            mm -= 1
            dd += 30
        while mm <= 0:
            yy -= 1
            mm += 12
        while dd > 30:
            mm += 1
            dd -= 30
        while mm > 12:
            yy += 1
            mm -= 12
        return (yy,mm,dd) 
    
    def normalize_interval(self, yy, mm, dd):
        while dd < 0:
            mm -= 1
            dd += 30
        while mm < 0:
            yy -= 1
            mm += 12
        while dd > 30:
            mm += 1
            dd -= 30
        while mm > 12:
            yy += 1
            mm -= 12
        return (yy,mm,dd) 

    def __sub__(self, other):
        if other is NULL:
            return NULL
        if isinstance(other, DateProxy):
            yy = self.dates[0] - other.dates[0]
            mm = self.dates[1] - other.dates[1]
            dd = self.dates[2] - other.dates[2]
            (yy,mm,dd) = self.normalize_interval(yy,mm,dd)
            return [yy,mm,dd]
        if isinstance(other, int):
            d1 = self.dates1
            while len(d1) < 3: d1.append(1)
            d1 = datetime.date(*d1)
            d2 = d1 - datetime.timedelta(other)
            return [d1.year,d2.month,d2.day]
        if isinstance(other, (tuple,list)):
            assert len(other) <= 3
            return self - DateProxy(other)

    def __add__(self, other):
        if other is NULL:
            return NULL
        if isinstance(other, int):
            d1 = self.dates1
            while len(d1) < 3: d1.append(1)
            d1 = datetime.date(*d1)
            d2 = d1 + datetime.timedelta(other)
            (yy,mm,dd) = self.normalize(d2.year,d2.month,d2.day)
            return DateProxy([yy,mm,dd])
        if isinstance(other, (tuple,list)):
            assert len(other) <= 3
            d1 = list(other[:])
            while len(d1) < 3: d1.append(0)
            yy = self.dates[0] + d1[0]
            mm = self.dates[1] + d1[1]
            dd = self.dates[2] + d1[2]
            (yy,mm,dd) = self.normalize(yy,mm,dd)
            return DateProxy([yy,mm,dd])

    def __lt__(self, other):
        if other is NULL:
            return NULL
        if isinstance(other, DateProxy):
            return self.dates < other.dates
        if isinstance(other, (tuple,list)):
            assert len(other) <= 3
            d1 = list(other[:])
            while len(d1) < 3: d1.append(0)
            return self.dates < d1
        if isinstance(other, int):
            return self < (other,0,0)
        raise RuntimeError(f"Invalid comparison: {self} < {other}")
    def __eq__(self, other):
        if other is NULL:
            return NULL
        if isinstance(other, DateProxy):
            return self.dates == other.dates
        if isinstance(other, (tuple,list)):
            assert len(other) <= 3
            d1 = list(other[:])
            while len(d1) < 3: d1.append(0)
            return self.dates == d1
        if isinstance(other, int):
            return self.dates == (other,0,0)
        raise RuntimeError(f"Invalid comparison: {self} == {other}")


class EventProxy(Proxy):

    @property
    @functools.lru_cache(1)
    def place(self):
        #print("---> place", self)
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_OTHER]-> (e:Event) 
                -[:PLACE]-> (place:Place) 
        where
            id(e) = $uid
        return id(place) as id, place
        """
        
        rec = self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid).single()
        if not rec: return NULL
        place = rec['place']
        if not place: return NULL
        return PlaceProxy(self._executor, rec['id'],dict(place))

    @property
    def date(self):
        if hasattr(self, 'datetype'):
            return DateProxy.from_daterange(self.datetype, self.date1, self.date2)
        else:
            return NULL
        
    @property
    @functools.lru_cache(1)
    def citations(self):
        #print("---> citations", self)
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_OTHER]-> (e:Event)
                -[:CITATION]-> (c:Citation) 
        where
            id(e) = $uid
        return id(c) as id, c
        """
        
        values = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid):
            obj = rec['c']
            values.append(CitationProxy(self._executor, rec['id'],dict(obj)))
        return values

"""
d1 - d2 -> int (days)
datediff(d1,d2) -> DateInterval  - years,months,days
d1 + int -> d2
d1 + DateInterval -> d2
d1 + ( years,months,days) -> d2
"""        

class PlaceProxy(Proxy):
    @property
    def name(self):
        return self.pname

    @property
    @functools.lru_cache(1)
    def enclosed_by(self):
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_PLACE]-> (p1:Place)
                -[:IS_INSIDE]-> (p2:Place)
        where
            id(p1) = $uid
        return id(p2) as id, p2 as obj
        """
        
        values = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid):
            obj = rec['obj']
            values.append(PlaceProxy(self._executor, rec['id'],dict(obj)))
        return values

    @property
    @functools.lru_cache(1)
    def encloses(self):
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_PLACE]-> (p2:Place)
                -[:IS_INSIDE]-> (p1:Place)
        where
            id(p1) = $uid
        return id(p2) as id, p2 as obj
        """
        
        values = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid):
            obj = rec['obj']
            values.append(PlaceProxy(self._executor, rec['id'],dict(obj)))
        return values

    @property
    @functools.lru_cache(1)
    def longname(self):
        def get_enclosing_names(place):
            upper_places = place.enclosed_by
            if len(upper_places) > 0:
                upper = upper_places[0]
                upper_names = get_enclosing_names(upper)
            else:
                upper_names = []
            return [place.pname] + upper_names

        names = get_enclosing_names(self)
        return ", ".join(names)

    @property
    @functools.lru_cache(1)
    def altnames(self):
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_PLACE]-> (p:Place)
                -[:NAME_LANG]-> (pn:Place_name)
        where
            id(p) = $uid
        return id(pn) as id, pn as obj
        """
        
        values = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid):
            obj = rec['obj']
            values.append(obj['name'])
        return values

class FamilyProxy(Proxy):

    @property
    @functools.lru_cache(1)
    def father(self):
        #print("---> father", self)
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_PERSON]-> (p:Person) 
                <-[:PARENT{role:'father'}]- (f:Family) 
        where
            id(f) = $uid
        return id(p) as id, p
        """
        
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid):
            p = rec['p']
            return PersonProxy(self._executor, rec['id'],dict(p))
        return NULL
        
    @property
    @functools.lru_cache(1)
    def mother(self):
        #print("---> mother", self)
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_PERSON]-> (p:Person) 
                <-[:PARENT{role:'mother'}]- (f:Family) 
        where
            id(f) = $uid
        return id(p) as id, p
        """
        
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid):
            p = rec['p']
            return PersonProxy(self._executor, rec['id'],dict(p))
        return NULL

    @property
    @functools.lru_cache(1)
    def children(self):
        #print("---> children", self)
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_FAMILY]-> (f:Family)
                -[:CHILD]-> (p:Person)
        where
            id(f) = $uid
        return id(p) as id, p as obj
        """
        
        values = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid):
            obj = rec['obj']
            values.append(PersonProxy(self._executor, rec['id'],dict(obj)))
        return values

class PersonProxy(Proxy):
    @property
    def name(self):
        return self.names[0] if self.names else NULL

    @property
    def firstname(self):
        self.names # load names
        return self.firstnames[0] if self.firstnames else NULL

    @property
    def patronymic(self):
        self.names
        return self.patronymics[0] if self.patronymics else NULL

    @property
    def surname(self):
        self.names
        return self.surnames[0] if self.surnames else NULL

    @property
    def gender(self):
        return "M" if self.sex == 1 else "F" if self.sex == 2 else "U"

    @property
    @functools.lru_cache(1)
    def names(self):
        #print("---> names", self, id(self))
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_PERSON]-> (p:Person) 
                -[:NAME]-> (n:Name) 
        where
            id(p) = $uid
        return n
        """
        
        values = []
        self.firstnames = []
        self.patronymics = []
        self.surnames = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid):
            n = rec['n']
            firstname = f"{n['firstname']}"
            patronymic = f"{n['suffix']}"
            surname = f"{n['surname']}"
            name = firstname
            if firstname:
                self.firstnames.append(firstname)
            if patronymic: 
                name += " " + patronymic
                self.patronymics.append(patronymic)
            if surname: 
                name += " " + surname
                self.surnames.append(surname)
            values.append(name)
        return values
    
    @property
    @functools.lru_cache(1)
    def families(self):
        #print("---> families", self)
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_PERSON]-> (p:Person) 
                <-[:PARENT]- (f:Family) 
        where
            id(p) = $pid
        return id(f) as id, f
        """
        
        values = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, pid=self.uid):
            family = rec['f']
            values.append(FamilyProxy(self._executor, rec['id'],dict(family)))
        return values

    @property
    @functools.lru_cache(1)
    def parent_families(self):
        #print("---> parent_families", self)
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_PERSON]-> (p:Person) 
                <-[:CHILD]- (f:Family) 
        where
            id(p) = $pid
        return id(f) as id, f
        """
        
        values = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, pid=self.uid):
            family = rec['f']
            values.append(FamilyProxy(self._executor, rec['id'],dict(family)))
        return values

    @property
    @functools.lru_cache(1)
    def children(self):
        #print("---> children", self)
        values = []
        for f in self.families:
            for c in f.children:
                values.append(c)
        return values

    @property
    @functools.lru_cache(1)
    def parents(self):
        #print("---> parents", self)
        values = []
        for f in self.parent_families:
            if f.father: values.append(f.father)
            if f.mother: values.append(f.mother)
        return values

    @property
    @functools.lru_cache(1)
    def father(self):
        #print("---> father", self)
        for f in self.parent_families:
            if f.father: return f.father
        return NULL

    @property
    @functools.lru_cache(1)
    def mother(self):
        #print("---> mother", self)
        for f in self.parent_families:
            if f.mother: return f.mother
        return NULL

    @property
    @functools.lru_cache(1)
    def events(self):
        #print("---> events", self)
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_PERSON]-> (p:Person) 
                -[:EVENT]-> (e:Event) 
        where
            id(p) = $pid
        return id(e) as id, e
        """
        
        values = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, pid=self.uid):
            event = rec['e']
            values.append(EventProxy(self._executor, rec['id'],dict(event)))
        return values

    @property
    def birth(self):
        for event in self.events:
            if event.type == 'Birth':
                return event
        return NULL

    @property
    def death(self):
        for event in self.events:
            if event.type == 'Death':
                return event
        return NULL

class CitationProxy(Proxy):

    @property
    @functools.lru_cache(1)
    def source(self):
        #print("---> citations", self)
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_OTHER]-> (c:Citation)
                -[:SOURCE]-> (obj:Source) 
        where
            id(c) = $uid
        return id(obj) as id, obj
        """

        rec = self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid).single()
        if not rec: return NULL
        obj = rec['obj']
        if not obj: return NULL
        return SourceProxy(self._executor, rec['id'],dict(obj))

    @property
    @functools.lru_cache(1)
    def events(self):
        #print("---> events", self)
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_OTHER]-> (e:Event) 
                -[:CITATION]-> (c:Citation)
        where
            id(c) = $uid
        return id(e) as id, e
        """
        
        values = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid):
            event = rec['e']
            values.append(EventProxy(self._executor, rec['id'],dict(event)))
        return values


class SourceProxy(Proxy):
    @property
    @functools.lru_cache(1)
    def citations(self):
        #print("---> citations", self)
        cypher = """
        match 
            (r:Root{id:$batch_id})
                -[:OBJ_SOURCE]-> (s:Source) 
                <-[:SOURCE]-> (c:Citation)
        where
            id(s) = $uid
        return id(c) as id, c as obj
        """
        
        values = []
        for rec in self._executor.session.run(cypher, batch_id=self.batch_id, uid=self.uid):
            obj = rec['obj']
            values.append(CitationProxy(self._executor, rec['id'],dict(obj)))
        return values

class RepositoryProxy(Proxy):
    pass

class MediaProxy(Proxy):
    pass

class NoteProxy(Proxy):
    pass


proxies = {
    "Person":   PersonProxy,
    "Family":   FamilyProxy,
    "Place":    PlaceProxy,
    "Event":    EventProxy,
    "Citation":     CitationProxy,
    "Source":       SourceProxy,
    "Repository":   RepositoryProxy,
    "Media":        MediaProxy,
    "Note":         NoteProxy,
}

import ast
MAXHDRLEN = 25
ELLIPSIS = "..."
def parse_hdrs(s):

    def strip_comma(s):
        s = s.strip()
        if s.endswith(","):
                s = s[:-1]
        s = s.strip()
        if len(s) > MAXHDRLEN:
            s = s[0:MAXHDRLEN-len(ELLIPSIS)] + ELLIPSIS
        return s

    def leftmost(e):
        pos = e.col_offset
        for subelem in ast.walk(e):
            #print(subelem)
            if hasattr(subelem,"col_offset"):
                if subelem.col_offset < pos:
                    pos = subelem.col_offset
        if isinstance(e,ast.Tuple):
            i = s.rfind("(",0,pos)
            if i >= 0: return i
        return pos
        
    expr = ast.parse(s, mode='eval')
    offsets = [leftmost(e) for e in expr.body.elts]
    hdrs = [strip_comma(s[i:j]) for (i,j) in zip(offsets,offsets[1:]+[len(s)-1])] # this removes the trailing bracket (])
    #return [ast.unparse(e) for e in expr.body.elts]  # Python 3.9+

    return hdrs
    
class Executor:
    def __init__(self, batch_id, format="html"):
        self.batch_id = batch_id
        self.format = format
        self.session = shareds.driver.session()

    def set_headers(self, hdrs):
        print("set_headers", hdrs)
        self.hdrs = hdrs
        self.result_string += "\n<tr><th>ID<th>" + "<th>".join(self.hdrs)

    def add_to_result(self, row, env):
        print("add_to_result", row)
        row = eval(str(row), env)
        #self.result_string += "<tr><td><td>" + "<td>".join(str(eval(repr(col),env)) for col in row)
        self.result_string += "<tr><td><td>" + "<td>".join(str(col) for col in row)
    
    def execute1(self, args):
        self._args = args
        proxyclass = proxies[args.scope]
        if args.where.strip():
            where = "where " + args.where
        else:
            where = ""
        cypher = """
        match (r:Root{id:$batch_id}) --> (obj:%(scope)s) 
        %(where)s
        return id(obj) as id, obj
        order by obj.id
        """ % {"scope": args.scope, "where": where}
        if args.limit.isdigit():
            limit = int(args.limit)
            if limit > 0: cypher += " limit $limit"
        else:
            limit = None
        json_result = []
        self.hdrs = None
        globals = {}
        #globals["os"] = None
        env = Lazyenv(None, get_attrs(args.scope))
        env["xx"] = 123
        env["set_headers"] = lambda x: self.set_headers(x)
        env["add_to_result"] = lambda x: self.add_to_result(x,env)
        env["NULL"] = NULL
        #globals.update(env)
        self.result_string = "<table>"

        exec( args.initial_statements, env)
        
        total = 0
        count = 0
        for rec in self.session.run(cypher, batch_id=self.batch_id, limit=limit):
            # {'birth_high': 1546,
            #  'birth_low': 1436,
            #  'change': 1624785939,
            #  'confidence': '',
            #  'death_high': 1656,
            #  'death_low': 1546,
            #  'id': 'I0000',
            #  'searchattr': ' Björn Jönsson ',
            #  'searchkey1': 'GBjörn XJönsson',
            #  'searchkey_2021_09_05_002': 'GBjörn XJönsson ',
            #  'sex': 1,
            #  'sortname': '#Björn#Jönsson',
            #  'uuid': '4e6c356760f4400eb6c04190ca769124'}
            total += 1
            p = proxyclass(self, rec['id'],dict(rec['obj']))
            if self.hdrs is None:
                if args.expressions == "*":
                    self.hdrs = get_attrs(args.scope)
                else:
                    expressions = "["+args.expressions.replace("\n", " ").strip() + "]"
                    self.hdrs = parse_hdrs(expressions)
                    #hdrs = [hdr.strip() for hdr in args.expressions.replace("\n", " ").split(",")]
                #env = Lazyenv(p, get_attrs(args.scope))
                self.result_string += "\n<tr><th>ID<th>" + "<th>".join(self.hdrs)
            env.obj = p
            env["self"] = p
            if args.statements:
                globals.update(env)
                exec( args.statements, env)
            if args.filter.strip():
                args.filter = args.filter.replace("\n", " ")
                globals.update(env)
                value = eval( args.filter, env)
                if not value: continue
            count += 1
            if args.expressions:
                expressions = args.expressions.replace("\n", " ").strip()
                if expressions == "*":
                    expressions = ",".join(self.hdrs)
                row = eval("["+expressions+"]", env)
                #row = [p.id] + list(row)
                self.result_string += "\n    <tr><td>"
                self.result_string += p._getlink_or_id()

                #self.result_string += "<td>" + "<td>".join(str(col) for col in row)
                rowhtml = ""
                for col in row:
                    if isinstance(col, list):
                        rowhtml += f"<td data-sortkey={getSortkey(col)}>{col}"
                    else:
                        rowhtml += f"<td>{col}"
                self.result_string += rowhtml

                json_row = [p._getlink_or_id()]
                json_row.extend([str(col) for col in row])
                json_result.append(json_row)
        self.result_string += "\n</table>"
        self.result_string += f"<small id=count hx-swap-oob=true>Count: {count}/{total}</small>"
        
        # table sorting javascript from https://stackoverflow.com/questions/14267781/sorting-html-table-with-javascript
        self.result_string += """
            <script>
            const getCellValue = (tr, idx) => tr.children[idx].getAttribute("data-sortkey") || tr.children[idx].innerText || tr.children[idx].textContent;
            
            const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
                v1 !== '' && v2 !== '' && !isNaN(v1) && !isNaN(v2) ? v1 - v2 : v1.toString().localeCompare(v2)
                )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));
            
            // do the work...
            document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {
                const table = th.closest('table');
                Array.from(table.querySelectorAll('tr:nth-child(n+2)'))
                    .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
                    .forEach(tr => table.appendChild(tr) );
            })));
            </script>
            """
        if self.format == "json":
            return json.dumps({"status":"OK","rows":json_result,"headers":hdrs})
        else:
            return self.result_string

    def execute(self, args):
        try:
            return self.execute1(args)
        except:
            if self.format == "json":
                return json.dumps({"status":"Error","errortext": traceback.format_exc()})
            else:
                return  "<pre>" + traceback.format_exc() + "</pre"
        
def get_attrs(scope):
    if scope == "Person":
        return [
            'batch_id',
            'birth',
            'birth_high',
            'birth_low',
            'change',
            'children',
            'confidence',
            'death',
            'death_high',
            'death_low',
            'events',
            'families',
            'father',
            'firstname',
            'gender',
            'id',
            'mother',
            'name',
            'names',
            'notes',
            'parent_families',
            'parents',
            'patronymic',
            'sex',
            'sortname',
            'spouses',
            'surname',
            'uid',
            'uuid']
    if scope == "Family":
        return [
             'batch_id',
             'change',
             'children',
             'father',
             'father_sortname',
             'handle',
             'id',
             'mother',
            'notes',
             'rel_type',
             'uid',
             'uuid']        
    if scope == 'Event':
        return [ 
            'batch_id',
            'change',
            'citations',
            'date',
            'date1',
            'date2',
            'datetype',
            'description',
            'id',
            'notes',
            'place',
            'scope',
            'type',
            'uid',
            'uuid']
    if scope == 'Place':
        return [
            'altnames',
            'batch_id',
            'change',
            'coord',
            'enclosed_by',
            'encloses',
            'id',
            'longname',
            'name',
            'notes',
            'pname',
            'scope',
            'type',
            'uid',
            'uuid']
    if scope == 'Citation':
        return [
            'batch_id',
            'change',
            'confidence',
            'events',
            'id',
            'notes',
            'page',
            'scope',
            'source',
            'uid',
            'uuid']         
 
    if scope == 'Source':
        return [
            'batch_id',
            'change',
            'citations',
            'id',
            'notes',
            'sauthor',
            'scope',
            'spubinfo',
            'stitle',
            'uid',
            'uuid']         
    if scope == 'Repository':
        return [
            'batch_id', 'change', 'id', 
            'notes',
            'rname', 'scope', 'type', 'uid', 'uuid'] 
    if scope == 'Media':
        return [
            'batch_id',
            'change',
            'description',
            'id',
            'mime',
            'name',
            'notes',
            'scope',
            'src',
            'uid',
            'uuid']
    if scope == "Note":
        return ['batch_id', 'id', 'scope', 'text', 'type', 'uid', 'url']            

    return ["Unknown"]

