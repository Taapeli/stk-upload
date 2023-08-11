#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2023  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu,
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
Created on 11.8.2023

@author: jm
"""
from bl.base import Status
from pe.dataservice import DataService

class NodeReader(DataService):
    """
    Data reading class for all kind of objects.

    - Returns a Result object.
    """
    def get_object_attrs(self, label:str, iid:str): #label:str, iid:str):
        """ Read Gramps attributes for given object.
        """
        user = self.user_context.batch_user()
        material = self.user_context.material
        lbl = label.title()
        res = self.dataservice.dr_get_object_attrs(user, material,
                                                   lbl, iid)
        if Status.has_failed(res):
            return res
        return res

        