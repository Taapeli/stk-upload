
from neo4j.v1 import GraphDatabase

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
            connection_timeout = 15)
   
    def close(self):
        self._driver.close()

    def execute(self, cypher, **kwargs):
        pass
        with self._driver.session() as session:
            greeting = session.write_transaction(self._execute, cypher, kwargs)
        
    @staticmethod
    def _execute(tx, cypher, **kwargs):
        result = tx.run(cypher, kwargs)
        return result.single()[0]
    