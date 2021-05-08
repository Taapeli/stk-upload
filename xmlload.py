import sys
from unittest.mock import Mock

sys.path.append("app")
from bl.gramps.gramps_loader import xml_to_stkbase

xmlfilename = sys.argv[1]

import shareds
shareds.app = Mock()

configfile = "instance/config.py"
ns = {}
config_text = open(configfile).read()
exec(config_text, ns, ns )
#print(ns)

shareds.app.config = ns

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
    "simple":  Neo4jWriteService    # Without transaction
    }


xml_to_stkbase(xmlfilename,"kku")
