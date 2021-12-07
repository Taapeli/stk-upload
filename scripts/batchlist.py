#!/usr/bin/env python3


"""
Lists all batches from the database.

    usage: batchlist.py
    
"""

import argparse
import sys
from unittest.mock import Mock

import shareds
from bl.root.root import Root

from app import app

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
 