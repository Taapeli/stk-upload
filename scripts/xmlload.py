#!/usr/bin/env python3

"""
Loads a Gramps XML file to the database.

    usage: xmlload.py [-h] [--username USERNAME] xmlfilename
    
    positional arguments:
      xmlfilename (e.g. data.gramps)
    
    optional arguments:
      -h, --help           show this help message and exit
      --username USERNAME
    
A default username can be stored in the instance/config.py as

    TEST_USERNAME = "username"

"""

import argparse
import os
import sys
from unittest.mock import Mock
import traceback
import shutil

sys.path.append("../app")
import shareds
from bl.base import Status, IsotammiException
from bl.gramps.gramps_loader import xml_to_stkbase
from bl.root.root_updater import RootUpdater
#from bl.root import BatchUpdater

import shareds

from app import app

username = shareds.app.config['TEST_USERNAME']

parser = argparse.ArgumentParser()
parser.add_argument("xmlfilename")
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


try:
    class Root:  # emulate real Root
        pass
    with BatchUpdater("update")  as batch_service:
        batch = batch_service.new_batch(args.username)
        upload_folder = "uploads/" + args.username
        batch_upload_folder = os.path.join(upload_folder, batch.id)
        os.makedirs(batch_upload_folder, exist_ok=True)
        destfile = shutil.copy(args.xmlfilename, batch_upload_folder)
        batch.file = destfile
        batch.user = args.username
        batch.xmlname = os.path.split(destfile)[1]
        batch.metaname = batch.file + ".meta"
        batch.logname = batch.file + ".log"

        batch.save(batch_service.dataservice) # todo: batch_service.save_batch(batch) ?

    xml_to_stkbase(batch)
    
except IsotammiException as e:
    print("xmlload: IsotammiException")
    traceback.print_exc()
    for arg,value in e.kwargs.items():
        print(f"{arg} = {value}")
except Exception as e:
    print("xmlload: Exception")
    traceback.print_exc()
    
