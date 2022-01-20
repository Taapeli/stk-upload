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

LABEL_SET = [   # values (label, has_citations)
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
    timestamp: int

class StatsBuilder:
    def __init__(self, session):
        self.session = session
        
    def get_object_stats(self, batch_id, label, has_citations):
        """ Calculate number of different objects in this batch. """
        cypher = """
            match (b:Root {id:$batch_id})
            match (b) --> (x)
                where $lb in labels(x)
            return count(x) as cnt
        """
        rec = self.session.run(cypher, batch_id=batch_id, lb=label).single()
        cnt = rec.get("cnt")
        if not has_citations:
            return (cnt,0)
        cypher2 = """
            match (b:Root {id:$batch_id})
            match (b) --> (x) --> (c:Citation)
                where $lb in labels(x)
            return count(distinct x) as cnt
        """
        rec = self.session.run(cypher2,batch_id=batch_id, lb=label).single()
        cnt2 = rec.get("cnt")
        return (cnt,cnt2)
    
    def get_object_stats_name(self, batch_id, label, has_citations):
        """ Calculate number of label type objects and citations referred from Persons. """
        cypher = """
            match (b:Root {id:$batch_id})
            match (b) --> (p:Person) --> (x)
                where $lb in labels(x)
            return count(x) as cnt
        """
        rec = self.session.run(cypher, batch_id=batch_id, lb=label).single()
        cnt = rec.get("cnt")
        if not has_citations:
            return (cnt,0)
        cypher2 = """
            match (b:Root {id:$batch_id})
            match (b) --> (p:Person) --> (x) --> (c:Citation)
                where $lb in labels(x)
            return count(distinct x) as cnt
        """
        rec = self.session.run(cypher2, batch_id=batch_id, lb=label).single()
        cnt2 = rec.get("cnt")
        return (cnt,cnt2)
    
    
    def get_event_stats(self, batch_id, event_types=[]):
        """ Calculate number of different Events and their Citation links. 

            #Todo: Limit results by event_types 
        """
        cypher = """
            match (b:Root {id:$batch_id}) -[r]-> (e:Event)
            optional match (e) -[cr:CITATION]-> (c)
            with e, head(collect(c)) as citations
            return e.type as type, 
                count(distinct e) as cnt_events,
                count(citations) as cnt_citations
        """ 
        event_stats = []
        result = self.session.run(cypher, batch_id=batch_id)
        for record in result:
            typename = record["type"]
            cnt_events = record['cnt_events']
            cnt_citations = record['cnt_citations']
            pct = round(100*cnt_citations / cnt_events)
            print(f"{typename:20.20} {cnt_events:5} {cnt_citations:5} {pct}%")
            data = (typename, (cnt_events, cnt_citations, pct))
            event_stats.append(data)
            
        return event_stats
    
    
    def create_stats_node(self, batch_id:str):
        """ Read or create Stats node. """
        cypher = """
            match (b:Root {id:$batch_id})
            merge (b) -[:STATS]-> (stats:Stats)
                on create set
                    stats.event_stats = [],
                    stats.object_stats = []
            return stats
        """ 
        rec = self.session.run(cypher, batch_id=batch_id).single()
        print("build_stats_node",rec)
        return rec['stats']

    def get_stats_node(self, batch_id):
        """ Read Stats node for batch_id. """
        cypher = """
            match (b:Root {id:$batch_id})
                --> (stats:Stats)
            return stats
        """ 
        rec = self.session.run(cypher, batch_id=batch_id).single()
        logger.debug(f"bl.stats.StatsBuilder.get_stats_node {rec}")
        if rec is None: return None
        return rec.get('stats')

    def build_stats_object(self, batch_id, timestamp):
        """ Calculate number of objects by object type.  """
        object_stats = []
        for label, has_citations in LABEL_SET:
            if label == 'Name':
                ret = self.get_object_stats_name(batch_id, label, has_citations)
            else:
                ret = self.get_object_stats(batch_id, label, has_citations)
            object_stats.append((label,has_citations,ret))
        event_stats = self.get_event_stats(batch_id)
        return Stats(object_stats, event_stats, timestamp)


    def save_stats(self, batch_id, stats):
        cypher = """
            match (b:Root {id:$batch_id}) --> (stats:Stats)
            set stats.object_stats=$object_stats, 
                stats.event_stats=$event_stats,
                stats.timestamp=$ts
        """ 
        object_stats = json.dumps(stats.object_stats)
        event_stats = json.dumps(stats.event_stats)
        self.session.run(cypher,
                         batch_id=batch_id, 
                         object_stats=object_stats, 
                         event_stats=event_stats,
                         ts=stats.timestamp
                    ).single()
    
    
    def get_stats_from_node(self, node):
        object_stats = node['object_stats']
        event_stats = node['event_stats']
        timestamp = node.get('timestamp', 0)
        object_stats = json.loads(object_stats)
        event_stats = json.loads(event_stats)
        return Stats(object_stats, event_stats, timestamp)
    
    
    def get_stats(self, batch_id, timestamp):
        node = self.get_stats_node(batch_id)
        if node is None or node.get("timestamp",0) < timestamp:
            node = self.create_stats_node(batch_id)
            stats = self.build_stats_object(batch_id, timestamp)
            self.save_stats(batch_id, stats)
        else:
            stats = self.get_stats_from_node(node)
        return stats
    
def get_stats(batch_id, timestamp:int):
    """ Get Stats object by given Root.id and Root.timestamp.

        If the Root has no Stats node or Stats is older than Root,
        calculate new statistics info.
    """ 
    with shareds.driver.session() as session:
        handler = StatsBuilder(session)
        stats = handler.get_stats(batch_id, timestamp)
        return stats
        
        
        
        
        
        
        
        
        
        
