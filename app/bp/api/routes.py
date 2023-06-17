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

# Flask routes program for Stk application API blueprint
# @ SSS 2019
# KKu 19.12.2019

import logging 
#import urllib
#from flask_security import roles_accepted, current_user

logger = logging.getLogger('stkserver')

from flask import request, jsonify
# from flask_security import roles_accepted, login_required #, render_template, current_user ,roles_required
#from flask_babelex import _

from . import bp
from . import apikey
from . import api
from . import placeapi
from . import refnameapi
#from . import refnameapi_v1

@bp.route('/placeapi/search', methods=['POST'])
def placeapi_v0_search():
    key = request.form.get("apikey")
    if not apikey.is_validkey(key): 
        return jsonify(dict(
            status="Error",
            statusText="Wrong API Key",
        ))
#    print(f"Request.form = {request.form}")    
    lookfor = request.form.get("lookfor")
    if not lookfor: 
        return jsonify(dict(
            status="Error",
            statusText="Missing argument 'lookfor'",
        ))
    rsp = placeapi.search(lookfor) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@bp.route('/placeapi/record', methods=['POST'])
def placeapi_v0_record():
    key = request.form.get("apikey")
    if not apikey.is_validkey(key): 
        return jsonify(dict(
            status="Error",
            statusText="Wrong API Key",
        ))
    print(f"Request.form = {request.form}")
    rid = request.form.get("id")
    if not rid: 
        return jsonify(dict(
            status="Error",
            statusText="Missing argument 'id'",
        ))
    rsp = placeapi.record(int(rid)) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@bp.route('/placeapi/record_with_subs', methods=['POST'])
def placeapi_v0_record_with_subs():
    key = request.form.get("apikey")
    if not apikey.is_validkey(key): 
        return jsonify(dict(
            status="Error",
            statusText="Wrong API Key",
        ))
    print(f"Request.form = {request.form}")
    rid = request.form.get("id")
    if not rid: 
        return jsonify(dict(
            status="Error",
            statusText="Missing argument 'id'",
        ))
    d1 = request.form.get("d1") 
    d2 = request.form.get("d2")
    dt = request.form.get("dt") 
    if d1 and d2 and dt:          
        rsp = placeapi.record_with_subs(rid, d1=d1, d2=d2, dt=dt) 
    else:
        rsp = placeapi.record_with_subs(rid)    
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

# @bp.route('/placeapi/v0/record_with_selected_subs', methods=['POST'])
# def placeapi_v0_record_with_selected_subs():
#     key = request.form.get("apikey")
#     if not apikey.is_validkey(key): 
#         return jsonify(dict(
#             status="Error",
#             statusText="Wrong API Key",
#         ))
# 
#     rid = request.form.get("id")
#     if not rid: 
#         return jsonify(dict(
#             status="Error",
#             statusText="Missing argument 'id'",
#         ))
#         
#     selects = request.form.get("selects")
#     if not selects: 
#         return jsonify(dict(
#             status="Error",
#             statusText="Missing argument 'selects'",
#         )) 
#            
#     rsp = placeapi.record_with_seleted_subs(int(rid, selects)) 
#     response = jsonify(rsp)
#     response.headers['Access-Control-Allow-Origin'] = '*'
#     return response

@bp.route('/refnameapi/search', methods=['POST'])
def refnameapi_v0_basename():
    key = request.form.get("apikey")
    if not apikey.is_validkey(key): return jsonify(dict(
            status="Error",
            statusText="Wrong API Key",
        ))
    
    lookfor = request.form.get("lookfor")
#    print(lookfor)
    if not lookfor: 
        return jsonify(dict(
            status="Error",
            statusText="Missing argument 'lookfor'",
        ))
    rsp = refnameapi.search_refname(lookfor) 
    response = jsonify(rsp)
    print(response)    
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@bp.route('/refnameapi/fetch_namefamily', methods=['POST'])
def refnameapi_v0_namefamily():
    print(request.form)
    key = request.form.get("apikey")
    if not apikey.is_validkey(key): return jsonify(dict(
            status="Error",
            statusText="Wrong API Key",
        ))
    
    lookfor = request.form.get("lookfor")
    use = request.form.get("use")
#    print(lookfor)
    if not lookfor: return jsonify(dict(
            status="Error",
            statusText="Missing argument 'lookfor'",
        ))
    rsp = refnameapi.fetch_namefamily(lookfor, use) 
    response = jsonify(rsp)
    print(response)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@bp.route('/api/v1/search', methods=['GET'])
def api_v1_search():
    lookfor = request.args.get("lookfor")
    print(lookfor)
    if not lookfor: return jsonify(dict(
            status="Error",
            statusText="Missing argument 'lookfor'",
        ))
    rsp = api.search(lookfor) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@bp.route('/api/v1/record', methods=['GET'])
def api_v1_record():
    rid = request.args.get("id")
    if not rid: return jsonify(dict(
            status="Error",
            statusText="Missing argument 'id'",
        ))
    rsp = api.record(int(rid)) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@bp.route('/api/v1/record_with_subs', methods=['GET'])
def api_v1_record_with_subs():
    rid = request.args.get("id")
    if not rid: return jsonify(dict(
            status="Error",
            statusText="Missing argument 'id'",
        ))
    rsp = api.record_with_subs(int(rid)) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@bp.route('/api/v2/search', methods=['POST'])
def api_v2_search():
    apikey = request.form.get("apikey")
    if not api.is_validkey(apikey): return jsonify(dict(
            status="Error",
            statusText="Wrong API Key",
        ))
    
    lookfor = request.form.get("lookfor")
    print(lookfor)
    if not lookfor: return jsonify(dict(
            status="Error",
            statusText="Missing argument 'lookfor'",
        ))
    rsp = api.search(lookfor) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@bp.route('/api/v2/record', methods=['POST'])
def api_v2_record():
    apikey = request.form.get("apikey")
    if not api.is_validkey(apikey): return jsonify(dict(
            status="Error",
            statusText="Wrong API Key",
        ))

    rid = request.form.get("id")
    if not rid: return jsonify(dict(
            status="Error",
            statusText="Missing argument 'id'",
        ))
    rsp = api.record(int(rid)) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@bp.route('/api/v2/record_with_subs', methods=['POST'])
def api_v2_record_with_subs():
    apikey = request.form.get("apikey")
    if not api.is_validkey(apikey): return jsonify(dict(
            status="Error",
            statusText="Wrong API Key",
        ))

    rid = request.form.get("id")
    if not rid: return jsonify(dict(
            status="Error",
            statusText="Missing argument 'id'",
        ))
    rsp = api.record_with_subs(int(rid)) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 
