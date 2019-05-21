# coding=UTF-8
import logging
logging.basicConfig(level=logging.INFO, format=('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger('stkserver')

# Do not log neo4j.bolt INFO messages
neo4j_log = logging.getLogger("neo4j.bolt")
neo4j_log.setLevel(logging.WARNING)

"""
 ----------------------------- Käynnistys -------------------------------
 ----------------------------- URL http://127.0.0.1:5000/ --------------
"""

if __name__ == '__main__':
    from app import app
    print('Käynnistys: ' + str(app))

    if True:
        loglevel = 'DEBUG'
        # Ajo paikallisesti
        print(f"Using log levels: Flask {loglevel}, Neo4j {neo4j_log.getEffectiveLevel()},"
              f" stkserver {logger.getEffectiveLevel()}")
        app.run(debug=loglevel)
    else:
        # Julkinen sovellus
        app.run(host='0.0.0.0', port=8000)
