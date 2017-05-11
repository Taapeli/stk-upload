'''
Created on 11.5.2017

@author: jm
'''
# from neo4j.v1 import GraphDatabase, basic_auth
import models.genealogy
from flask import Flask, g
import time

global app, g
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py') # instance-hakemistosta

@app.route('/')
def hello_world():
#     return 'Hello, World!'

    models.genealogy.connect_db()
    
#     driver = GraphDatabase.driver("bolt://localhost:7687", auth=basic_auth("neo4j", "neo4j"))
#     g.session = g.driver.session()

    t = time.strftime('%Y-%m-%d %H:%M:%S')
    print ("Artturi " + t)
    g.session.run("CREATE (a:TestPerson {name: {name}, title: {title}, date: {date}})",
                {"name": "Arthur", "title": "King", "date": t})
    
    result = g.session.run("MATCH (a:TestPerson) WHERE a.name = {name} "
                         "RETURN a.name AS name, a.title AS title, a.date AS date",
                         {"name": "Arthur"})
    ret = []
    for record in result:
        ret.append("{} {} ({})".format(record["title"], record["name"], record["date"]))
    
#     g.session.close()
    return "\n<br>".join(ret)
  
if __name__ == '__main__':
    app.run(debug='DEBUG')
