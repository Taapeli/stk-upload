'''
Ohjelma sisältää kaksi toimintoa, jotka kirjoittavat ja lukevat Neo4j-kantaa.
- "/" kutsuu hello_word()-funktiota ja lisää yhden trestihenkilön joka kutsulla
- "/seq[/lkm] on transaktioesimerkki, joka hakee simuloituja Gramps-handleja
  metodilla models.dbutil.get_new_handles(). 
    
Usage:
    Käynnistä serveri "python db_connect_test.py"
    Mene selaimella osoitteeseen http://127.0.0.1:5000/
'''
# from neo4j.v1 import GraphDatabase, basic_auth
import models.dbutil
from flask import Flask, g
from neo4j.v1 import ServiceUnavailable
import time
help='''<ul>
<li><a href="/">Luo testihenkilö ja listaa luodut testihenkilöt</a></li>
<li><a href="/seq">Pyydä uusi simuloitu Gramps-handle</a></li>
<li><a href="/seq/3">Pyydä kolme simuloitua Gramps-handlea</a></li>
</ul><br/>'''

global app, g
app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py') # instance-hakemistosta

@app.route('/')
def hello_world():
    ''' Connects database, writes a TestPerson and prints all TestPersons '''
    models.dbutil.connect_db()
    
    t = time.strftime('%Y-%m-%d %H:%M:%S')
    session = shareds.driver.session()
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
    return help + "\n<br>".join(ret)

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
    return (help + "Saatu handlet: {}".format(hand))

  
if __name__ == '__main__':
    app.run(debug='DEBUG')
