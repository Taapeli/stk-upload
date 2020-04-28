# coding=UTF-8
import logging

class ContextFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.

    Rather than use actual contextual information, we just use random
    data in this demo.
    """

    USERS = ['mari', 'li', 'katri']

    def __init__(self):
        from random import choice
        self.user = choice(ContextFilter.USERS)

    def filter(self, record):
        record.user = self.user #choice(ContextFilter.USERS)
        return True

print("Start loggers here")
logging.basicConfig(level=logging.INFO, format=('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger('stkserver')
fh = logging.FileHandler('/tmp/stkserver.log')
fh.setLevel(logging.DEBUG)
logger.addFilter(ContextFilter())
formatter = logging.Formatter('%(asctime)s %(name)s %(user)-7s %(levelname)-5s %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# logger.basicConfig(level=logging.DEBUG,
#                     format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
#                     datefmt='%m-%d %H:%M',
#                     filename='stkserver.log',
#                     filemode='w')
#logger.setLevel(logging.DEBUG)

# Do not log neo4j.bolt INFO messages
neo4j_log = logging.getLogger("neo4j.bolt")
neo4j_log.setLevel(logging.WARNING)

"""
 ----------------------------- Käynnistys -------------------------------
 ----------------------------- URL http://127.0.0.1:5000/ --------------
"""

if __name__ == '__main__':
    from app import app
    print(f'Käynnistys: {app}, logging {logger}')
    app.run()

#     if True:
#         loglevel = 'DEBUG'
#         # Ajo paikallisesti
#         print ("Stk server ajetaan {}-lokitasolla".format(loglevel))
#         app.run(debug=loglevel)
#     else:
#         # Julkinen sovellus
#         app.run(host='0.0.0.0', port=8000)
