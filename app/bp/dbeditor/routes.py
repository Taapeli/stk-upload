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
from flask_security import roles_required
app = shareds.app
 
neo4j_uri = shareds.app.config.get("NEO4J_URI")
neo4j_username = shareds.app.config.get("NEO4J_USERNAME")
neo4j_password = shareds.app.config.get("NEO4J_PASSWORD")

neo4j_driver = GraphDatabase.driver(
        neo4j_uri,
        auth = (neo4j_username,neo4j_password),
        connection_timeout = 15) 

def run(cypher,callback=None,**kwargs):
    try:
        res = neo4j_driver.session().run(cypher, kwargs)
        n = 0
        for rec in res:
            if callback: callback(rec)
            n += 1
        return n
    except:
        traceback.print_exc()
        raise

def runcypher(cypher, **kwargs):
    print(cypher,kwargs)
    res = neo4j_driver.session().run(cypher, kwargs)
    return res

@app.route("/dbeditor/")
@roles_required('admin')
def index():
    fname = "dbeditor.html"
    return render_template(fname)

@app.route("/dbeditor/labels")
@roles_required('admin')
def labels():
    res = runcypher("call db.labels()")
    print(res)
    labels = sorted([rec[0] for rec in res])
    return jsonify(labels) #["Person","Event","Place"])

@app.route("/dbeditor/nodes/<label>/<skip>")
@roles_required('admin')
def nodes(label,skip):
    res = runcypher(f"match (n:{label}) return n,id(n) as id order by id skip {skip} limit 25")
    #print(res)
    nodes = [dict(id=rec['id'],attrs=dict(rec['n'])) for rec in res]
    #print(nodes)
    return jsonify(nodes)  

@app.route("/dbeditor/search",methods=["POST"])
@roles_required('admin')
def search():
    data = json.loads(request.data.decode("utf-8"))
    label = data['label']
    attr = data['attr']
    pattern = data.get('pattern')
    datatype = data['datatype']
    if pattern:
        pattern = re.escape(pattern)
        pattern = f"(?i).*{pattern}.*"
        res = runcypher(f"match (n:{label})  where n.{attr} =~ $pattern return n,id(n) as id order by id limit 25", pattern=pattern )
    else:
        res = runcypher(f"match (n:{label}) return n,id(n) as id order by id limit 25" )
    
    nodes = [dict(id=rec['id'],attrs=dict(rec['n'])) for rec in res]
    #print(nodes)
    return jsonify(nodes)  

@app.route("/dbeditor/update",methods=["POST"])
@roles_required('admin')
def update():
    print(request.data)
    data = json.loads(request.data.decode("utf-8"))
    print(data)
    id = int(data['id'])
    label = data['label']
    attr = data['attr']
    value = data.get('value','')
    datatype = data['datatype']
    if type(value) == str and datatype == 'number':
        if value == "":
            value = None
        elif value.isdigit():
            value = int(value)
        else:
            value = float(value)
    res = runcypher(f"match (n:{label}) where id(n) = $id set n.{attr} = $value",id=id,value=value)
    print(dir(res.summary()))
    #rsp = res.summary().counters["properties_set"]
    #print(rsp)
    rsp = "ok"
    return jsonify(rsp)

@app.route("/dbeditor/fetch/<int:nodeid>")
@roles_required('admin')
def fetch(nodeid):
    res = runcypher(f"match (n) where id(n) = $nodeid return n,labels(n) as labels", nodeid=nodeid).single()
    print("res1:",res)
    rsp = {"n":dict(res['n']),"label":res['labels'][0]}
    print(rsp)
    return jsonify(rsp)

@app.route("/dbeditor/fetch_links/<int:nodeid>")
@roles_required('admin')
def fetch_links(nodeid):
    res = runcypher(f"match (n)-[r]->(a) where id(n) = $nodeid return *,labels(a) as labels,id(a) as id", nodeid=nodeid)
    print(res)
    rsp1 = [dict(a=dict(rec['a']),r=dict(rec['r']),labels=rec['labels'],rtype=rec['r'].type,id=rec['id']) for rec in res]

    res = runcypher(f"match (n)<-[r]-(a) where id(n) = $nodeid return *,labels(a) as labels,id(a) as id", nodeid=nodeid)
    print(res)
    rsp2 = [dict(a=dict(rec['a']),r=dict(rec['r']),labels=rec['labels'],rtype=rec['r'].type,id=rec['id']) for rec in res]

    rsp = dict(links1=rsp1,links2=rsp2)
    print(rsp)
    return jsonify(rsp)

