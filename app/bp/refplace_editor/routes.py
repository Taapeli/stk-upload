#!/bin/env python
# -*- coding: utf-8 -*-

import shareds
from flask_security import roles_accepted #, current_user
from bp.refplace_editor.models import refplaceeapi_v1 as api
from . import bp
from flask import render_template, request

from pe.db_writer import DbWriter
from pe.neo4j.dataservice import Neo4jDataService
from models.jsonify import stk_jsonify

@bp.route("/refplace_editor/")
@roles_accepted('audit')
def refplace_editor():
    fname = "refplace_editor.html"
    return render_template(fname)

@bp.route('/refplaces/api/list_top_level_places', methods=['GET'])
@roles_accepted('audit')
def list_top_level_places():
    rsp = api.list_top_level_places() 
    response = stk_jsonify(rsp)
    return response 

@bp.route('/refplaces/api/list_subordinate_places', methods=['GET'])
@roles_accepted('audit')
def list_subordinate_places():
    parent_id = request.args.get("parent_id")
    print(parent_id)
    rsp = api.list_subordinate_places(int(parent_id)) 
    response = stk_jsonify(rsp)
    return response 

@bp.route('/refplaces/api/getplace', methods=['GET'])
@roles_accepted('audit')
def getplace():
    pid = request.args.get("id")
    rsp = api.getplace(int(pid)) 
    print(rsp)
    response = stk_jsonify(rsp)
    return response 

@bp.route('/refplaces/api/mergeplaces', methods=['GET'])
@roles_accepted('audit')
def mergeplaces():
    id1 = request.args.get("id1")
    id2 = request.args.get("id2")
    dbdriver = Neo4jDataService(shareds.driver, tx=None)
    writer = DbWriter(dbdriver) 
    place = writer.mergeplaces(int(id1),int(id2)) 
    return stk_jsonify(place)

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
