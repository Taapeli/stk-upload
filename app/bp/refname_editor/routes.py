#!/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import traceback
from flask import Flask, request, jsonify

from neo4j import GraphDatabase

# https://neo4j.com/docs/cypher-manual/3.5/schema/index/#schema-index-fulltext-search 
# http://lucene.apache.org/core/5_5_0/queryparser/org/apache/lucene/queryparser/classic/package-summary.html#package.description
#
# Requires Neo4j 3.5 or later

import config
import shareds
from flask import render_template
from flask_security import roles_accepted, current_user
import urllib
from bp.refname_editor.models import refnameapi_v1
app = shareds.app
 

@app.route("/refname_editor/")
@roles_accepted('audit')
def index1():
    fname = "refname_editor.html"
    return render_template(fname)

@app.route('/refnameapi/v1/search', methods=['POST'])
@roles_accepted('audit')
def refnameapi_search_v1():
    lookfor = request.form.get("lookfor")
    lookfor = urllib.parse.unquote(lookfor)
#    print(lookfor)
    if not lookfor: 
        return jsonify(dict(
            status="Error",
            statusText="Missing argument 'lookfor'",
        ))
    #usage = 'firstname'
    usage = request.form.get("usage")
    match = request.form.get("match")
    rsp = refnameapi_v1.search(lookfor, usage, match) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@app.route('/refnameapi/v1/prefixes', methods=['POST'])
@roles_accepted('audit')
def refnameapi_prefixes_v1():
    lookfor = request.form.get("lookfor")
    lookfor = urllib.parse.unquote(lookfor)
    if lookfor is None: 
        return jsonify(dict(
            status="Error",
            statusText="Missing argument 'lookfor'",
        ))
    usage = request.form.get("usage")
    rsp = refnameapi_v1.prefixes(lookfor, usage) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@app.route('/refnameapi/v1/fetch_namefamily', methods=['POST'])
@roles_accepted('audit')
def refnameapi_fetch_v1():
    "Fetch a name family"
    lookfor = request.form.get("lookfor")
    lookfor = urllib.parse.unquote(lookfor)
    if lookfor is None: 
        return jsonify(dict(
            status="Error",
            statusText="Missing argument 'lookfor'",
        ))
    usage = request.form.get("usage")
    rsp = refnameapi_v1.fetch_namefamily(lookfor, usage) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 
        
@app.route('/refnameapi/v1/add_to_family', methods=['POST'])
@roles_accepted('audit')
def refnameapi_add_to_family_v1():
    "add_to_family"
    basename = request.form.get("basename")
    basename = urllib.parse.unquote(basename)
    names = request.form.get("names")
    names = urllib.parse.unquote(names).split(",")
    usage = request.form.get("usage")
    rsp = refnameapi_v1.add_to_family(basename, names, usage) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@app.route('/refnameapi/v1/remove_from_family', methods=['POST'])
@roles_accepted('audit')
def refnameapi_remove_from_family():
    "add_to_family"
    basename = request.form.get("basename")
    basename = urllib.parse.unquote(basename)
    names = request.form.get("names")
    names = urllib.parse.unquote(names).split(",")
    usage = request.form.get("usage")
    rsp = refnameapi_v1.remove_from_family(basename, names, usage) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@app.route('/refnameapi/v1/addname', methods=['POST'])
@roles_accepted('audit')
def refnameapi_addname():
    "add_a new name"
    name = request.form.get("name")
    name = urllib.parse.unquote(name)
    source = f"Käyttäjän {current_user.name} lisäämä"
    rsp = refnameapi_v1.addname(name, source) 
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@app.route('/refnameapi/v1/delnames', methods=['POST'])
@roles_accepted('audit')
def refnameapi_delnames():
    "delete a name"
    names = request.form.get("names")
    names = urllib.parse.unquote(names).split(",")
    rsp = refnameapi_v1.delnames(names)
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

@app.route('/refnameapi/v1/save_name', methods=['POST'])
@roles_accepted('audit')
def refnameapi_save_name():
    "save new values for name and source"
    original_name = urllib.parse.unquote(request.form.get("original_name"))
    name = urllib.parse.unquote(request.form.get("name"))
    source = urllib.parse.unquote(request.form.get("source"))
    rsp = refnameapi_v1.save_name(original_name, name, source)
    response = jsonify(rsp)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response 

