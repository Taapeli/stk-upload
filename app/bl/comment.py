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
import os

import shareds
from .base import NodeObject, Status
from bl.person import PersonBl
from bl.family import FamilyBl
from bl.place import PlaceBl
from bl.event import EventBl

from pe.dataservice import DataService
from pe.neo4j.cypher.cy_comment import CypherComment


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
        """ Create a new comment individ """
        NodeObject.__init__(self)
        self.text = ""
        self.user = ""


    def __str__(self):

        return f"{self.text}: {self.timestr} {self.user} {self.timestamp}"

    @classmethod
    def from_node(cls, node):
        """
        Transforms a db node to an object of type Comment.

        <Node id=164 labels={'Comment'}
            properties={'text': 'Amanda syntyi Porvoossa'}>
        """
        n = super(Comment, cls).from_node(node)
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
        comments = []
        fw = self.user_context.first  # next name
        user = self.user_context.batch_user()
        limit = self.user_context.count
        ustr = "for user " + user if user else "approved "
        print(
            f"CommentReader.read_my_comment_list: Get max {limit} comments {ustr} starting {fw!r}"
        )

        res = shareds.dservice.dr_get_comment_list(self.use_user, fw, limit)
        if Status.has_failed(res):
            return res
        for record in res.get("recs", None):
            # <Record o=<Node id=393949 labels={'Comment'}
            #        properties={'text': 'Amanda syntyi Porvoossa',
            #            'batch_id': '2020-01-02.001'}>
            #    credit='juha'
            #    batch_id='2020-01-02.001'
            #    count=1>
            node = record["o"]
            m = Comment.from_node(node)
            m.count = record.get("count", 0)
            m.credit = record.get("credit")
            m.batch = record.get("batch_id")
            comments.append(m)

        # Update the page scope according to items really found
        if comments:
            self.user_context.update_session_scope(
                "comment_scope",
                comments[0].text,
                comments[-1].text,
                limit,
                len(comments),
            )
            return {"status": Status.OK, "items": comments}
        return {"status": Status.NOT_FOUND}

