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
Created on 19.5.2021

@author: jormah
"""
# blacked 2021-05-01 JMä
import shareds
from bl.base import NodeObject, Status
from bl.root import Root
from bl.person import PersonBl
from bl.family import FamilyBl
from bl.place import PlaceBl
#from bl.event import EventBl
from bl.source import SourceBl

from pe.dataservice import DataService
#from pe.neo4j.cypher.cy_comment import CypherComment


class Comment(NodeObject):
    """A comment object with description, file link and mime information.

    Tallenne

    Properties:
            text
            timestr
            user
            timestamp
    """

    def __init__(self, uniq_id=None):
        """ Create a new comment instance """
        NodeObject.__init__(self)
        self.text = ""
        self.user = ""


    def __str__(self):

        return f"{self.text}: {self.timestr} {self.user}" # {self.timestamp}"

    @classmethod
    def from_node(cls, node):
        """
        Transforms a db node to an object of type Comment.

        <Node id=164 labels={'Comment'}
            properties={'text': 'Amanda syntyi Porvoossa'}>
        """
        n = super(Comment, cls).from_node(node)
        n.title = node.get("title","")
        n.text = node["text"]
        n.timestr = node["timestr"]
        n.user = node["user"]
        n.timestamp = node["timestamp"]
        return n


class CommentReader(DataService):
    """
    Data reading class for Comment objects with associated data.

    - Returns a Result object.
    """

    def read_my_comment_list(self):
        """Read Comment object list using u_context."""
        topics = []
        fw = self.user_context.first  # next name
        user = self.user_context.batch_user()
        limit = self.user_context.count
        ustr = "for user " + user if user else "approved "
        print(
            f"CommentReader.read_my_comment_list: Get max {limit} topics {ustr} starting {fw!r}"
        )

        res = self.dataservice.dr_get_topic_list(self.use_user, self.user_context.batch_id, fw, limit)
        if Status.has_failed(res):
            return res
        for record in res['recs']:
            # <Record 
            #    o=<Node id=84627 labels=frozenset({'Person'}) 
            #        properties={'sortname': 'Lundman#Maja Stina#', 'death_high': 1846, 'change': 1585409699, 
            #            'sex': 2, 'confidence': '2.0', 'birth_low': 1770, 'birth_high': 1770, 'id': 'I1971', 
            #            'uuid': 'cecd3b128c5f42ca8873bd7d3d4d5a57', 'death_low': 1846}>
            #    c=<Node id=156264 labels=frozenset({'Topic'})
            #        properties={'timestr': '28.07.2021 19:53', 'text': 'Kutsutaanko myös Kirstiksi?',
            #            'timestamp': 1627491233.9907079}> credit='jpek'
            #    count=0
            #    root=<Node id=86708 labels=frozenset({'Root'})
            #        properties={'material': 'Family Tree', 'auditor': 'juha', 'state': 'Auditing', 
            #            'id': '2021-05-09.002', 'user': 'jpek', 'timestamp': 1620578577293}>>
                # <Record o=<Node id=393949 labels={'Comment'}
                #        properties={'text': 'Amanda syntyi Porvoossa',
                #            'batch_id': '2020-01-02.001'}>
                #    credit='juha'
                #    batch_id='2020-01-02.001'
                #    count=1>

            node = record["c"]
            c = Comment.from_node(node)
            c.label = list(node.labels).pop()
            if not c.title:
                # Show shortened text without line breaks as title
                text = c.text.replace("\n", " ")
                if len(text) > 50:
                    n = text[:50].rfind(" ")
                    if n < 2:
                        n = 50
                    c.title = text[:n]
                else:
                    c.title = c.text
            c.obj_label = record.get("label")
            c.count = record.get("count", 0)
            c.credit = record.get("credit")

            node = record['root']
            c.root = Root.from_node(node)
            #c.batch = record.get("batch_id")

            node = record["o"]
            c.obj_label = list(node.labels).pop()
            if c.obj_label == "Family":
                c.object = FamilyBl.from_node(node)
            elif c.obj_label == "Person":
                c.object = PersonBl.from_node(node)
            elif c.obj_label == "Place":
                c.object = PlaceBl.from_node(node)
            elif c.obj_label == "Source":
                c.object = SourceBl.from_node(node)
            else:
                print(f"CommentReader.read_my_comment_list: Discarded referring object '{c.obj_label}'")
                next
            topics.append(c)

        # Update the page scope according to items really found
        if topics:
            self.user_context.update_session_scope(
                "comment_scope",
                topics[0].timestamp,
                topics[-1].timestamp,
                limit,
                len(topics),
            )
            return {"status": Status.OK, "items": topics}
        return {"status": Status.NOT_FOUND}

