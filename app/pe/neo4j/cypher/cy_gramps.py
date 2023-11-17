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

from ..util import relation_type_by_label
'''
Database write clauses using Gramps handle.

    In the link_* methods, the referred targets must be created before linking them.

Created on 23.3.2020

@author: jm
'''

class CypherLink():

    @staticmethod
    def link_handle(src_label, dst_label, set_rel=False) -> str:
        """ Creates query for connecting src note to dst node item.
            Set relation parameters, if requested by set_rel.

            In Cypher, you can not give Labels as parameters, so this function
            creates different Cypher clauses for each combination of src, dst.

            Examples:
                tx.run(CypherLink.link_handle("Event", "Note"),
                       pid=place.iid, hlink=n_handle)
                tx.run(CypherLink.link_handle(src_label=resu.obj_name,
                                              dst_label="Citation",
                                              set_rel=True),
                       src=place.handle, dst=m_ref.handle, r_attr=r_attr)

            (src:<src_lbl>{handle: $src}) -[r:<link_type>]-> (dst:<dst_lbl>{handle:$dst})
        """
        link_type = relation_type_by_label(dst_label)
        query = f"""
MATCH (s:{src_label} {{handle: $src}})
MATCH (d:{dst_label} {{handle: $dst}})
CREATE (s) -[r:{link_type}]-> (d)"""
        if set_rel:
            query += "\n    SET r = $r_attr"
        #print("#! link_handle:"+query.replace("\n","  "))
        return query

