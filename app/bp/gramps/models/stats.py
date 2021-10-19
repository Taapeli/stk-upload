#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu, 
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Batch Statistics 
"""

from pprint import pprint

import shareds

# the necessary statements taken from setups.py:
from pe.neo4j.neo4jengine import Neo4jEngine

shareds.db = Neo4jEngine(shareds.app)
shareds.driver  = shareds.db.driver

labels = [
("Citation",0),
("Event",1),
("Family",1),
("Media",1),
("Name",1),
("Note",0),
("Person",1),
("Place",1),
("Repository",0),
("Source",0),
]

def getstats(batch_id, label, do_citations):
    cypher = """
        match (b:Root {id:$batch_id})
        match (b) --> (x:%(label)s)
        return count(x) as cnt
    """ % {"label":label}
    rec = shareds.driver.session().run(cypher, batch_id=batch_id).single()
    cnt = rec.get("cnt")
    if not do_citations:
        return (cnt,0)
    cypher2 = """
        match (b:Root {id:$batch_id})
        match (b) --> (x:%(label)s) --> (c:Citation)
        return count(distinct x) as cnt
    """ % {"label":label}
    rec = shareds.driver.session().run(cypher2,batch_id=batch_id).single()
    cnt2 = rec.get("cnt")
    return (cnt,cnt2)

def getstats_name(batch_id, label, do_citations):
    cypher = """
        match (b:Root {id:$batch_id})
        match (b) --> (p:Person) --> (x:%(label)s)
        return count(x) as cnt
    """ % {"label":label}
    rec = shareds.driver.session().run(cypher, batch_id=batch_id).single()
    cnt = rec.get("cnt")
    if not do_citations:
        return (cnt,0)
    cypher2 = """
        match (b:Root {id:$batch_id})
        match (b) --> (p:Person) --> (x:%(label)s) --> (c:Citation)
        return count(distinct x) as cnt
    """ % {"label":label}
    rec = shareds.driver.session().run(cypher2,batch_id=batch_id).single()
    cnt2 = rec.get("cnt")
    return (cnt,cnt2)

def get_stats(batch_id):
    rsp = []
    for label,do_citations in labels:
        if label == 'Name':
            ret = getstats_name(batch_id, label, do_citations)
        else:
            ret = getstats(batch_id, label, do_citations)
        rsp.append((label,do_citations,ret))
    pprint(rsp)
    return rsp
    
