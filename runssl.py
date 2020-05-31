# coding=UTF-8

from app import app 
import logging
from os import path

class ContextFilter(logging.Filter):
    """
    This is a filter which injects contextual information into the log.
    """

    def __init__(self):
        self.user = "<Nobody>" # choice(ContextFilter.USERS)

    def filter(self, record):
        if hasattr(self,'user'):
            record.user = self.user
        else:
            record.user = '-'
            print("# setups.ContextFilter.filter: 'user' not defined")
        return True

print('Käynnistys: ' + str(app))
"""
 ----------------------------- Käynnistys ------------------------------- 
 ----------------------------- URL https://127.0.0.1:5000/ --------------  
"""

"""
    Logger configuration
"""
print("Config Stk logger here")
logging.basicConfig(level=logging.INFO, format=('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger('')
logger.addFilter(ContextFilter())
logger = logging.getLogger('stkserver')

formatter = logging.Formatter('%(asctime)s %(name)s %(user)-7s %(levelname)-5s %(message)s')
if path.isdir('/var/log/httpd'):
    fh = logging.FileHandler('/var/log/httpd/stkserver.log')
else:
    fh = logging.FileHandler('/tmp/stkserver.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addFilter(ContextFilter())
logger.addHandler(fh)


if __name__ == '__main__':
    if True:
        # Ajo paikallisesti
        print ("stk-run.run ajetaan DEGUB-lokitasolla")
        app.run(debug='DEBUG', ssl_context='adhoc')
    else:
        # Julkinen sovellus
        app.run(host='0.0.0.0', port=8000, ssl_context='adhoc')
