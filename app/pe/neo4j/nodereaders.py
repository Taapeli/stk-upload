#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2022  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu,
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
import os

from bl.media import Media
from bl.comment import Comment

def init(cls, node):
    n = cls()
    n.uniq_id = node.id
    n.id = node["id"]
    n.uuid = node["uuid"]
    if node["handle"]:
        n.handle = node["handle"]
    n.change = node.get("change")
    return n


def Comment_from_node(node):
    """
    Transforms a db node to an object of type Comment.

    <Node id=164 labels={'Comment'}
        properties={'text': 'Amanda syntyi Porvoossa'}>
    """
    n = init(Comment, node)
    n.title = node.get("title","")
    n.text = node["text"]
    #n.user = node["user"]
    n.timestamp = node["timestamp"]
    #n.timestr = n.timestamp_str()        # node["timestr"]
    return n

def MediaBl_from_node(node):
    """
    Transforms a db node to an object of type Media.

    <Node id=100441 labels={'Media'}
        properties={'description': 'Katarina Borg (1812-1892)', 'handle': '_d78f9fb8e4f180c1212',
        'id': 'O0005', 'src': 'Sukututkimusdata/Sibelius/katarina_borg.gif',
        'mime': 'image/gif', 'change': 1524411014}>
    """
    n = init(Media, node)
    n.description = node["description"]
    n.src = node["src"]
    n.mime = node["mime"]
    if n.src:
        n.name = os.path.split(n.src)[1]
    else:
        n.name = ""
    return n
