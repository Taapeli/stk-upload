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

'''
Database write clauses using Gramps handle.

    In the link_* methods, the referred targets must be created before linking them.

Created on 23.3.2020

@author: jm
'''

class CypherObjectWHandle():
    
    def link_item(self, src_label, dst_label, set_r_attr=False):
        """ Create connection between src note to dst node item.
            Optionally set relation parameters.
            
            In Cypher, you can not give Labels as parameters, so this function
            creates different Cypher clauses for each combination of src, dst.
            
            Examples:
                tx.run(CypherObjectWHandle.link_item("Event", "Note"),
                       pid=place.iid, hlink=n_handle)
                tx.run(CypherObjectWHandle.link_item(src_label=resu.obj_name,
                                                     dst_label="Citation",
                                                     set_r_attr=True),
                       src=place.handle, dst=media_handle, r_attr=r_attr)

            (src:<src_lbl>{handle: $src}) -[r:<link_type>]-> (dst:<dst_lbl>{handle:$dst})
        """
        type_by_label = {
            "Citation": "CITATION",
            "Event": "EVENT",
            "Media": "MEDIA",
            "Name": "NAME",
            "Note": "NOTE",
            # "Person": "CHILD",
            # "Person": "PARENT",
            # "Place": "IS_INSIDE",
            "Place": "PLACE",
            "Place_name": "NAME",
            # "Place_name": "NAME_LANG",
            "Repository": "REPOSITORY",
            "Source": "SOURCE",
            }
        link_type = type_by_label.get(dst_label)
        query = f"""MATCH (s:{src_label} {{handle: $src}})
                    MATCH (d:{dst_label}  {{handle: $dst}})
                        CREATE (s) -[r:{link_type}]-> (d)"""
        if set_r_attr:
            query += "\n    SET r = $r_attr"
        print("#! link_item: \n"+query)
        return query

#     link_media = """
# MATCH (e {iid: $src_iid}) WHERE $lbl in LABELS(e)
# MATCH (m:Media  {handle: $handle})
#   CREATE (e) -[r:MEDIA]-> (m)
#     SET r = $r_attr"""
#!RETURN ID(m) AS uniq_id"""

#     link_note_x = """MATCH (e: {iid: $src_iid}) WHERE $lbl in LABELS(e)
# MATCH (m:Note  {handle: $handle})
#   CREATE (e) -[r:NOTE]-> (m)"""

#     link_citation = """
# MATCH (e {iid: $src_iid}) WHERE $lbl in LABELS(e)
# MATCH (m:Citation  {handle: $handle})
#   CREATE (e) -[r:CITATION]-> (m)"""

