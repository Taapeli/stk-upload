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
import time

# import logging
# logger = logging.getLogger('stkserver')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.FileHandler("stkserver.log"))
#logger.basicConfig(filename='myapp.log', level=logging.DEBUG)


sys.path.append("../app")
import shareds
from app import app

from database.accessDB import DB_SCHEMA_VERSION

from bl.base import Status, IsotammiException
from bl.batch.root import Root, State
from bl.gramps.gramps_loader import xml_to_stkbase
from bl.batch.root_updater import RootUpdater

from bp.admin import uploads

username = shareds.app.config['TEST_USERNAME']

parser = argparse.ArgumentParser()
parser.add_argument("xmlfilename")
parser.add_argument("--username", default=username)
parser.add_argument("--batch_id")
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


# Modified from RootUpdater.create_batch_
def create_batch(dataservice, username, filename, batch_id):
    """ Create a new Root node for given user and infile. 
    """
    def new_batch_tx(tx, dataservice):
        """ A session.write_transaction function.
            :param:    dataservice    Neo4jUpdateService
            :param:    username   str
        """
        # Lock db to avoid concurrent Batch loads
        if not dataservice.ds_aqcuire_lock(tx, "batch_id"):
            return None

        # New Root object with next free batch id
        root = Root()
        if batch_id:
            root.id = batch_id
        else:
            root.id = dataservice.ds_new_batch_id(tx)
        root.user = username
        root.db_schema = DB_SCHEMA_VERSION
        res = root.save(tx)
        if Status.has_failed(res):
            raise IsotammiException("Could not create Root node")

        # Prepare uploads folder
        upload_folder = uploads.get_upload_folder(username)
        batch_upload_folder = os.path.join(upload_folder, root.id)
        os.makedirs(batch_upload_folder, exist_ok=True)

        destfile = shutil.copy(filename, batch_upload_folder)

        root.xmlname = os.path.basename(filename)
        root.file = os.path.join( batch_upload_folder, root.xmlname)
        root.metaname = root.file + ".meta"
        root.logname = root.file + ".log"
        root.save(tx)

        # Create metafile
        uploads.set_meta(
            username,
            root.id,
            root.xmlname,
            status=State.FILE_UPLOADED,
            upload_time=time.time(),
            # material_type=material_type, description=description,
        )
        return root

    with shareds.driver.session() as session:

        # Create Root node with next free batch id
        root = session.write_transaction(new_batch_tx,
                                         dataservice)
        return root



try:
    with RootUpdater("update")  as batch_service:
        batch = create_batch(batch_service.dataservice, args.username, args.xmlfilename, args.batch_id)
    
        xml_to_stkbase(batch)
    
except IsotammiException as e:
    print("xmlload: IsotammiException")
    traceback.print_exc()
    for arg,value in e.kwargs.items():
        print(f"{arg} = {value}")
except Exception as e:
    print("xmlload: Exception")
    traceback.print_exc()
    
