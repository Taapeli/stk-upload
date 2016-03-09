# Luodaan tietokantayhteys palvelimelle

from py2neo import Graph, authenticate

try:
    graph = Graph('http://{0}/db/data/'.format(app.config['DB_HOST_PORT']))
    authenticate(app.config['DB_HOST_PORT'], 
                 app.config['DB_USER'], app.config['DB_AUTH'])
    print("Suoritettu __init__ autentikointi")
    
except Exception as e:
    print("Epäonnistunut __init__ autentikointi")
    return redirect(url_for('db_test_tulos', text="Exception "+str(e)))
