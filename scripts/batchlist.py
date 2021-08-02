#!/usr/bin/env python3


"""
Lists all batches from the database.

    usage: batchlist.py
    
"""

import argparse
import sys
from unittest.mock import Mock

sys.path.append("../app")
import shareds
from bl.root import Root
#from bl.batch import Batch
 
def load_config(configfile):
    shareds.app = Mock()
    ns = {}
    config_text = open(configfile).read()
    exec(config_text, ns )
    shareds.app.config = ns
 
configfile = "../instance/config.py"
load_config(configfile)

parser = argparse.ArgumentParser()
args = parser.parse_args()

# the necessary statements taken from setups.py:
from pe.neo4j.neo4jengine import Neo4jEngine

shareds.db = Neo4jEngine(shareds.app)
shareds.driver  = shareds.db.driver

print(f"{'id':14s} {'user':10s}  {'material_type':15}  {'description':15} {'status':15s} {'file'}")
for b in Root.get_batches():
    id = b['id']
    state = b.get('state',"-")
    file = b.get('file',"-")
    user = b.get('user',"-")
    material_type = b.get('material_type','')
    description = b.get('description','').replace("\n"," ")
    print(f"{id:14s} {user:10s}  {material_type:15}  {description[0:15]:15} {state:15s} {file}")
 