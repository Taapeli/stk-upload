#!/usr/bin/env python3


"""
Removes a batch from the database.

    usage: batchdelete.py [-h] [--username USERNAME] batch_id
    
    positional arguments:
      batch_id (e.g. 2021-05-09.001)
    
    optional arguments:
      -h, --help           show this help message and exit
      --username USERNAME
    
A default username can be stored in the instance/config.py as

    TEST_USERNAME = "username"

"""

import argparse
import sys
from unittest.mock import Mock

sys.path.append("../app")
import shareds
from bl.batch import Batch

def load_config(configfile):
    shareds.app = Mock()
    ns = {}
    config_text = open(configfile).read()
    exec(config_text, ns )
    shareds.app.config = ns

configfile = "../instance/config.py"
load_config(configfile)

username = shareds.app.config['TEST_USERNAME']

parser = argparse.ArgumentParser()
parser.add_argument("batch_id")
parser.add_argument("--username", default=username)
args = parser.parse_args()

# the necessary statements taken from setups.py:
from pe.neo4j.neo4jengine import Neo4jEngine
from pe.neo4j.updateservice import Neo4jUpdateService
from pe.neo4j.writeservice import Neo4jWriteService
from pe.neo4j.readservice import Neo4jReadService
from pe.neo4j.readservice_tx import Neo4jReadServiceTx

shareds.db = Neo4jEngine(shareds.app)
shareds.driver  = shareds.db.driver
shareds.dataservices = {
    "read":    Neo4jReadService,
    "read_tx": Neo4jReadServiceTx,
    "update":  Neo4jUpdateService,
    "simple":  Neo4jWriteService
    }


ret = Batch.delete_batch(args.username, args.batch_id)
print(ret)
 
 