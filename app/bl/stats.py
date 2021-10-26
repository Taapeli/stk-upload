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

import json
from dataclasses import dataclass
#from pprint import pprint
from typing import List

import shareds
import logging

logger = logging.getLogger("stkserver")

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

@dataclass
class Stats:
    object_stats: List
    event_stats: List

class StatsBuilder:
    def __init__(self, session):
        self.session = session
        
    def get_object_stats(self, batch_id, label, has_citations):
        cypher = """
            match (b:Root {id:$batch_id})
            match (b) --> (x:%(label)s)
            return count(x) as cnt
        """ % {"label":label}
        rec = self.session.run(cypher, batch_id=batch_id).single()
        cnt = rec.get("cnt")
        if not has_citations:
            return (cnt,0)
        cypher2 = """
            match (b:Root {id:$batch_id})
            match (b) --> (x:%(label)s) --> (c:Citation)
            return count(distinct x) as cnt
        """ % {"label":label}
        rec = self.session.run(cypher2,batch_id=batch_id).single()
        cnt2 = rec.get("cnt")
        return (cnt,cnt2)
    
    def get_object_stats_name(self, batch_id, label, has_citations):
        cypher = """
            match (b:Root {id:$batch_id})
            match (b) --> (p:Person) --> (x:%(label)s)
            return count(x) as cnt
        """ % {"label":label}
        rec = self.session.run(cypher, batch_id=batch_id).single()
        cnt = rec.get("cnt")
        if not has_citations:
            return (cnt,0)
        cypher2 = """
            match (b:Root {id:$batch_id})
            match (b) --> (p:Person) --> (x:%(label)s) --> (c:Citation)
            return count(distinct x) as cnt
        """ % {"label":label}
        rec = self.session.run(cypher2,batch_id=batch_id).single()
        cnt2 = rec.get("cnt")
        return (cnt,cnt2)
    
    
    def get_event_stats(self, batch_id):
        cypher = """
            match (b:Root {id:$batch_id})
                --> (e:Event)
            return collect(distinct e.type) as types
        """ 
        rec = self.session.run(cypher, batch_id=batch_id).single()
        types = rec['types']
        event_stats = []
        for typename in types:
            cypher2 = """
                match (b:Root {id:$batch_id})
                    --> (e:Event{type:$type})
                return count(distinct e) as cnt
            """ 
            rec2 = self.session.run(cypher2, batch_id=batch_id, type=typename).single()
            cnt2 = rec2['cnt']
            
            cypher3 = """
                match (b:Root {id:$batch_id})
                    --> (e:Event{type:$type})
                match (e) -[:CITATION]-> (c)
                return count(distinct e) as cnt
            """ 
            rec3 = self.session.run(cypher3, batch_id=batch_id, type=typename).single()
            cnt3 = rec3['cnt']
            pct = round(100*cnt3/cnt2)
            print(f"{typename:20.20} {cnt2:5} {cnt3:5} {pct}%")
            data = (typename,(cnt2,cnt3,pct))
            event_stats.append(data)
            
        return event_stats
    
    
    def create_stats_node(self, batch_id):
        cypher = """
            match (b:Root {id:$batch_id})
            create (b) -[:STATS]-> (stats:Stats)
            return stats
        """ 
        rec = self.session.run(cypher, batch_id=batch_id).single()
        print("build_stats_node",rec)
        return rec['stats']
    
    
    def get_stats_node(self, batch_id):
        cypher = """
            match (b:Root {id:$batch_id})
                --> (stats:Stats)
            return stats
        """ 
        rec = self.session.run(cypher, batch_id=batch_id).single()
        logger.debug(f"bl.stats.StatsBuilder.get_stats_node {rec}")
        if rec is None: return None
        return rec.get('stats')
    
    def build_stats_object(self, batch_id):
        object_stats = []
        for label,has_citations in labels:
            if label == 'Name':
                ret = self.get_object_stats_name(batch_id, label, has_citations)
            else:
                ret = self.get_object_stats(batch_id, label, has_citations)
            object_stats.append((label,has_citations,ret))
        event_stats = self.get_event_stats(batch_id)   
        return Stats(object_stats, event_stats)
        

    def save_stats(self, batch_id, de, stats):
        cypher = """
            match (b:Root {id:$batch_id})
                --> (stats:Stats)
            set stats.object_stats=$object_stats, 
                stats.event_stats=$event_stats 
        """ 
        object_stats = json.dumps(stats.object_stats)
        event_stats = json.dumps(stats.event_stats)
        _rec = self.session.run(cypher, batch_id=batch_id, object_stats=object_stats, event_stats=event_stats).single()
    
    
    def get_stats_from_node(self, node):
        object_stats = node['object_stats']
        event_stats = node['event_stats']
        object_stats = json.loads(object_stats)
        event_stats = json.loads(event_stats)
        return Stats(object_stats,event_stats)
    
    
    def get_stats(self, batch_id):
        node = self.get_stats_node(batch_id)
        if node is None:
            node = self.create_stats_node(batch_id)
            stats = self.build_stats_object(batch_id)
            self.save_stats(batch_id, node, stats)
        else:
            stats = self.get_stats_from_node(node)
        return stats
    
def get_stats(batch_id):
    with shareds.driver.session() as session:
        handler = StatsBuilder(session)
        return handler.get_stats(batch_id)
        
        
        
        
        
        
        
        
        
        
        
