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

#!/bin/env python
# -*- coding: utf-8 -*-

#import shareds
from flask_security import roles_accepted #, current_user
from bp.refplace_editor.models import refplaceeapi_v1 as api
from . import bp
from flask import render_template, request

from bl.base import Status, StkEncoder
from bl.place import PlaceUpdater


@bp.route("/refplace_editor/")
@roles_accepted('audit')
def refplace_editor():
    fname = "refplace_editor.html"
    return render_template(fname)

@bp.route('/refplaces/api/list_top_level_places', methods=['GET'])
@roles_accepted('audit')
def list_top_level_places():
    rsp = api.list_top_level_places() 
    response = StkEncoder.jsonify(rsp)
    return response 

@bp.route('/refplaces/api/list_subordinate_places', methods=['GET'])
@roles_accepted('audit')
def list_subordinate_places():
    parent_id = request.args.get("parent_id")
    print(parent_id)
    rsp = api.list_subordinate_places(int(parent_id)) 
    response = StkEncoder.jsonify(rsp)
    return response 

@bp.route('/refplaces/api/getplace', methods=['GET'])
@roles_accepted('audit')
def getplace():
    pid = request.args.get("id")
    rsp = api.getplace(int(pid)) 
    print(rsp)
    response = StkEncoder.jsonify(rsp)
    return response 

@bp.route('/refplaces/api/mergeplaces', methods=['GET'])
@roles_accepted('audit')
def mergeplaces():
    id1 = request.args.get("id1")
    id2 = request.args.get("id2")
    # #dataservice = Neo4jDataService(dbdriver)
    # dataservice = get_dataservice("update")
    # datastore = PlaceUpdater(dataservice)
    #print(f'#> bp.refplace_editor.routes.mergeplaces: datastore = {datastore}')

    try:
        with PlaceUpdater("update") as service:
            ret = service.merge2places(int(id1),int(id2))
    except Exception as e:
        ret = {
            "status": "Error",
            "statustext": str(e)
        }
    print(f"mergeplaces: {ret.get('statustext')}")
    return StkEncoder.jsonify(ret)

@bp.route('/refplaces/api/test_create', methods=['GET'])
@roles_accepted('audit')
def test_create():
    _rsp = api.test_create() 
    return "ok" 

@bp.route('/refplaces/api/test_delete', methods=['GET'])
@roles_accepted('audit')
def test_delete():
    _rsp = api.test_delete() 
    return "ok" 
