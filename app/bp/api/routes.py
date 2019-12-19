# Flask routes program for Stk application API blueprint
# @ SSS 2019
# KKu 19.12.2019

import logging 
logger = logging.getLogger('stkserver')

from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_security import roles_accepted, login_required #, current_user ,roles_required
from flask_babelex import _

from . import bp
from . import api

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
