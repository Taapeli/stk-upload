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
                    
    Properties:
        title       (not in use, yet)
        text        comment text
        timestamp   (created in database)
        (timestr)   converted from timestamp, available with obj.timestamp_str()
        user
    """

    def __init__(self):
        """ Create a new comment instance """
        NodeObject.__init__(self)
        self.text = ""
        self.user = ""
        self.title = ""

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
        #n.user = node["user"]
        n.timestamp = node["timestamp"]
        #n.timestr = n.timestamp_str()        # node["timestr"]
        return n


class CommentsUpdater(DataService):
    """
    Data update class for Comment and Topic objects with associated data.

    - Returns a Result object.
    """

    def add_comment(self, user:str, uniq_id:int, comment_text:str):
        """
        Create a new [Topic or] Comment from given comment.

        :param:    user            the commenting active username
        :param:    uniq_id         the object, where new comment shall be connected
        :param:    comment_text    Text

        The new node shall be connected to source object and user's profile.
        """
        attr = {
            "object_id": uniq_id, 
            "username": user, 
            "title": None, 
            "text": comment_text,
        }
        res = self.dataservice.ds_comment_save(attr)
        return res


class CommentReader(DataService):
    """
    Data reading class for Comment objects with associated data.

    - Returns a Result object.
    """

    def read_my_comment_list(self):
        """Read Comment object list using u_context."""
        topics = []
        fw = self.user_context.first  # next name
        limit = self.user_context.count
        ustr = "for user " + self.use_user if self.use_user else "approved"
        print(
            f"CommentReader.read_my_comment_list: Get max {limit} topics {ustr} starting {fw!r}"
        )

        res = self.dataservice.dr_get_topic_list(self.use_user, self.user_context.batch_id, fw, limit)
        if Status.has_failed(res):
            return res
        for record in res['recs']:
            # <Record 
            #    o=<Node id=189486 labels=frozenset({'Person'})
            #        properties={...}> 
            #    c=<Node id=189551 labels=frozenset({'Comment'})
            #        properties={'text': 'testi Gideon', 'timestamp': 1631965129453}>
            #    commenter='juha'
            #    count=0
            #    root=<Node id=189427 labels=frozenset({'Root'}) 
            #        properties={'xmlname': 'A-testi 2021 koko kanta.gpkg', 
            #            'material': 'Family Tree', 'state': 'Candidate', 
            #            'id': '2021-09-16.001', 'user': 'juha', ...}>
            # >

            node = record["c"]
            c = Comment.from_node(node)
            #c.label = list(node.labels).pop()
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
            c.obj_label = list(record['o'].labels).pop()
            c.count = record.get("count", 0)
            c.credit = record.get("commenter")

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

