'''
    A class for creating Neo4j database connection for `database` module
    and executing Cypher commands

@author: TimNal - Timo Nallikari 2017

@change: 21.4.2020 JMä
    For use Neo4.1 with older 1.7 driver needs encrypted=False driver option
'''
from neo4j import GraphDatabase
import logging 
logger = logging.getLogger('stkserver')

DEBUG = False

class Neo4jEngine():
    ''' The neo4j database engine connects to database and serves some operations.

        Database configuration is in instace config.py file:
            NEO4J_URI = "bolt://localhost:7687"
            NEO4J_USERNAME = 'neo4j'
            NEO4J_PASSWORD = 'passwd'
            NEO4J_VERSION = '4.0'         # Default: 3.5
    '''
    def __init__(self, app):
#        print(os.getenv('PATH'))
#        print(app.config['NEO4J_USERNAME'] + ' connect')
        self.driver = GraphDatabase.driver(
            app.config['NEO4J_URI'], 
            auth = (app.config['NEO4J_USERNAME'], 
                    app.config['NEO4J_PASSWORD']),
            connection_timeout = 15,
            encrypted=False)
        self.version = app.config.get('NEO4J_VERSION','3.5')
        print(f'Neo4jEngine: {app.config["NEO4J_USERNAME"]} connecting (v{self.version})')
   
    def close(self):
        self.driver.close()

    def execute(self, cypher, **kwargs):
        with self.driver.session() as session:
            session.write_transaction(self._execute, cypher, kwargs)
        
    @staticmethod
    def _execute(tx, cypher, **kwargs):
        result = tx.run(cypher, kwargs)
        return result.single()[0]

    def consume_counters(self, result):
        ''' Get counters from Neo4j.result object (both 3.5 & 4.1 versions).
        
            Use: shareds.db.consume_counters(result)
        '''
        try:
            if self.version >= '4.0':
                return result.consume().counters
            else:
                return result.summary().counters
        except AttributeError as e:
            logger.error('database.models.neo4jengine.Neo4jEngine.consume_counters:'
                         f'Invalid Neo4j database version, expected {self.version}')
            raise NotImplementedError('Wrong version, expecting Neo4j v'+self.version) from e
