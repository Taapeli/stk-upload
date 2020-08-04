'''
    A class for creating Neo4j database connection for `database` module
    and executing Cypher commands

@author: TimNal - Timo Nallikari 2017

@change: 21.4.2020 JMä
    For use Neo4.1 with older 1.7 driver needs encrypted=False driver option
'''
from neo4j import GraphDatabase

DEBUG = False

#neo4j config
class Neo4jEngine():
    def __init__(self, app):
        #=======================================================================
        # # Neo4jDB Config
        # self.config = {}
        # self.config['NEO4J_DB'] = 'stk.secdb'
        # self.config['NEO4J_HOST'] = 'localhost'
        # self.config['NEO4J_PORT'] = 27017
        # self.uri = "bolt://localhost:7687"
        #=======================================================================
#        print(os.getenv('PATH'))
        print(app.config['NEO4J_USERNAME'] + ' connect')
#        print(os.getenv('NEO4J_PASSWORD'))                
        self.driver = GraphDatabase.driver(
            app.config['NEO4J_URI'], 
            auth = (app.config['NEO4J_USERNAME'], 
                    app.config['NEO4J_PASSWORD']),
            connection_timeout = 15,
            encrypted=False)
   
    def close(self):
        self.driver.close()

    def execute(self, cypher, **kwargs):
        with self.driver.session() as session:
            session.write_transaction(self._execute, cypher, kwargs)
        
    @staticmethod
    def _execute(tx, cypher, **kwargs):
        result = tx.run(cypher, kwargs)
        return result.single()[0]
    