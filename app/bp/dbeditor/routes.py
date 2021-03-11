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

import json
import re
import traceback
from flask import request, jsonify # Flask

#from neo4j import GraphDatabase

# https://neo4j.com/docs/cypher-manual/3.5/schema/index/#schema-index-fulltext-search 
# http://lucene.apache.org/core/5_5_0/queryparser/org/apache/lucene/queryparser/classic/package-summary.html#package.description
#
# Requires Neo4j 3.5 or later

import shareds
from flask import render_template
from flask_security import roles_required
app = shareds.app
 
import setups   # Defines shareds.driver! Do not remove!!

#Removed 1.11.2020: got from setups
# neo4j_uri = app.config.get("NEO4J_URI")
# neo4j_username = app.config.get("NEO4J_USERNAME")
# neo4j_password = app.config.get("NEO4J_PASSWORD")
# neo4j_driver = GraphDatabase.driver(
#         neo4j_uri,
#         auth = (neo4j_username,neo4j_password),
#         connection_timeout = 15) 

def run(cypher,callback=None,**kwargs):
    try:
        res = shareds.driver.session().run(cypher, kwargs)
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
    res = shareds.driver.session().run(cypher, kwargs)
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
    #datatype = data['datatype']
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
    #id = int(data['id'])
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

