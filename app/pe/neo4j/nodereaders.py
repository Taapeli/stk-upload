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
from datetime import datetime

from bl.base import PRIVACY_LIMIT

from bl.citation import Citation
from bl.comment import Comment
from bl.dates import DateRange
from bl.event import EventBl
from bl.family import FamilyBl
from bl.media import Media
from bl.note import Note
from bl.person import PersonBl
from bl.place import PlaceBl, PlaceName
from bl.repository import Repository
from bl.source import SourceBl
from bl.person_name import Name


def init(cls, node):
    n = cls()
    n.uniq_id = node.id
    n.id = node["id"]
    n.uuid = node.get("uuid","")
    n.iid = node.get("iid","")
    if node["handle"]:
        n.handle = node["handle"]
    n.change = node.get("change")
    return n

def Citation_from_node(node):
    """
    Transforms a db node to an object of type Citation.
    """
    n = init(Citation, node)
    n.confidence = node["confidence"]
    n.page = node["page"]
    n.dates = DateRange_from_node(node)

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


def DateRange_from_node(node):
    """
    Extracts a DateRange value from any db node, if present.
    """
    if node["datetype"] != None:
        return DateRange(node["datetype"], node["date1"], node["date2"])

    return DateRange()

def EventBl_from_node(node):
    """
    Transforms a db node to an object of type Event or EventBl.

    <Node id=88532 labels={'Event'}
        properties={'type': 'Birth', 'change': 1500907890, attr_value': '',
            'id': 'E0161', 'attr_type': '', 'description': ''
            'datetype': 0, 'date1': 1754183, 'date2': 1754183}>
    """
    #if node is None: return None
    n = init(EventBl, node)
    n.type = node["type"]
    if "datetype" in node:
        n.dates = DateRange(node["datetype"], node["date1"], node["date2"])
    else:
        n.dates = DateRange()
    n.dates.calendar = node["calendar"]
    n.description = node["description"] or ""
    n.attr = node.get("attr", dict())
    return n

def FamilyBl_from_node(node):
    """
    Transforms a db node to an object of type Family.

    You can create a Family or FamilyBl instance. (cls is the class
    where we are, either Family or FamilyBl)

    <Node id=99991 labels={'Family'}
        properties={'rel_type': 'Married', 'handle': '_da692e4ca604cf37ac7973d7778',
        'id': 'F0031', 'change': 1507492602}>
    """
    n = init(FamilyBl, node)
    n.rel_type = node.get("rel_type", "")
    n.father_sortname = node.get("father_sortname", "")
    n.mother_sortname = node.get("mother_sortname", "")
    if "datetype" in node:
        n.dates = DateRange(node["datetype"], node["date1"], node["date2"])
    else:
        n.dates = DateRange()
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

def Name_from_node(node):
    """
    Transforms a db node to an object of type Name

    <Node id=80308 labels={'Name'}
        properties={'title': 'Sir', 'firstname': 'Brita Helena', 'suffix': '', 'order': 0,
            'surname': 'Klick', '': 'Birth Name'}>
    """
    n = Name()
    n.uniq_id = node.id
    # n.id = node.id    # Name has no id "N0000"
    n.type = node["type"]
    n.firstname = node.get("firstname", "")
    n.prefix = node.get("prefix", "")
    n.suffix = node.get("suffix", "")
    n.title = node.get("title", "")
    n.surname = node.get("surname", "")
    n.order = node["order"]
    
    if "datetype" in node:
        n.dates = DateRange(node["datetype"], node["date1"], node["date2"])
        n.dates.calendar = node["calendar"]
    return n


def Note_from_node(node):
    """
    Transforms a db node to an object of type Note.
    """
    n = init(Note, node)
    if "priv" in node:
        n.priv = node["priv"]
    n.type = node.get("type", "")
    n.text = node.get("text", "")
    n.url = node.get("url", "")
    return n

def PersonBl_from_node(node, obj=None):
    """
    Transforms a db node to an object of type Person.

    Youc can create a Person or Person_node instance. (cls is the class
    where we are, either Person or PersonBl)

    <Node id=80307 labels={'Person'}
        properties={'id': 'I0119', 'confidence': '2.5', 'sex': '2', 'change': 1507492602,
        'handle': '_da692a09bac110d27fa326f0a7', 'priv': 1}>
    """
    obj = init(PersonBl, node)
    obj.sex = node.get("sex", "UNKNOWN")
    obj.confidence = node.get("confidence", "")
    obj.sortname = node["sortname"]
    obj.priv = node["priv"]
    obj.birth_low = node.get("birth_low", 0)
    obj.birth_high = node.get("birth_high", 9999)
    obj.death_low = node.get("death_low", 9999)
    obj.death_high = node.get("death_high", 0)
    last_year_allowed = datetime.now().year - PRIVACY_LIMIT
    #         if obj.death_high < 9999:
    #             print('ok? uniq_id=',obj.uniq_id,obj.death_high)
    obj.too_new = obj.death_high > last_year_allowed
    return obj


def PlaceBl_from_node( node):
    """Creates a node object of type Place from a Neo4j node.

    Example node:
    <Node id=78279 labels={'Place'}
        properties={'handle': '_da68e12a415d936f1f6722d57a', 'id': 'P0002',
            'change': 1500899931, 'pname': 'Kangasalan srk', 'type': 'Parish'}>
    """
    p = init(PlaceBl, node)
    p.type = node.get("type", "")
    p.pname = node.get("pname", "")
    p.coord = node.get("coord", None)
    return p

def PlaceName_from_node(node):
    """Transforms a db node to an object of type Place_name.

    <Node id=78278 labels={'Place_name'}
        properties={'lang': '', 'name': 'Kangasalan srk'}>
    """
    pn = PlaceName() 
    pn.uniq_id = node.id
    pn.name = node.get("name", "?")
    pn.lang = node.get("lang", "")
    pn.dates = node.get("dates")
    return pn

def Repository_from_node(node):
    """
    Transforms a db node to Repository object

    <Node id=100269 labels={'Repository'}
        properties={'handle': '_d7910c4dfa419204848', 'id': 'R0000',
            'rname': 'Hämeenlinnan kaupunkiseurakunnan arkisto',
            'type': 'Archive', 'change': '1522861211'}>
    """
    n = init(Repository, node)
    n.uniq_id = node.id
    n.id = node["id"] or ""
    n.handle = node["handle"] or None
    n.change = node["change"] or 0
    n.rname = node["rname"] or ""
    n.type = node["type"] or ""
    return n

def SourceBl_from_node(node):
    """
    Transforms a db node to an object of type Source.
    """
    # <Node id=355993 labels={'Source'}
    #     properties={'id': 'S0296', 'stitle': 'Hämeenlinnan lyseo 1873-1972',
    #         'uuid': 'c1367bbdc6e54297b0ef12d0dff6884f', 'spubinfo': 'Karisto 1973',
    #         'sauthor': 'toim. Mikko Uola', 'change': 1585409705}>

    s = init(SourceBl, node)
    s.stitle = node["stitle"]
    s.sauthor = node["sauthor"]
    s.spubinfo = node["spubinfo"]
    s.sabbrev = node.get("sabbrev", "")
    return s

