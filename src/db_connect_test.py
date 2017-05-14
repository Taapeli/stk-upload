'''
Created on 11.5.2017

@author: jm
'''
# from neo4j.v1 import GraphDatabase, basic_auth
import models.dbutil
from flask import Flask, g
from neo4j.v1 import ServiceUnavailable
import time

global app, g
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py') # instance-hakemistosta

@app.route('/')
def hello_world():
    ''' Connects database, writes a TestPerson and prints all TestPersons '''
    models.dbutil.connect_db()
    
    t = time.strftime('%Y-%m-%d %H:%M:%S')
    session = g.driver.session()
    try:
        session.run("CREATE (a:TestPerson {name: {name}, title: {title}, date: {date}})",
                    {"name": "Arthur", "title": "King", "date": t})
        
        result = session.run("MATCH (a:TestPerson) WHERE a.name = {name} "
                             "RETURN a.name AS name, a.title AS title, a.date AS date",
                             {"name": "Arthur"})
    except ServiceUnavailable:
        return("<b>Tietokantayhteys ei onnistunut</b>")

    ret = []
    for record in result:
        ret.append("{} {} <small>({})</small>".format(record["title"], record["name"], record["date"]))
    
    session.close()
    return "\n<br>".join(ret)

@app.route('/seq')
@app.route('/seq/<string:count>')
def sequence_test(count="1"):
    ''' Test handle generation '''
    models.dbutil.connect_db()

    if count:
        cnt = int(count)
    else:
        cnt = 1
#    with  as hand:
    hand = models.dbutil.get_new_handles(cnt)
    return ("Saatu handlet: {}".format(hand))

  
if __name__ == '__main__':
    app.run(debug='DEBUG')
