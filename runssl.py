# coding=UTF-8

from app import app 
import logging
print('Käynnistys: ' + str(app))
"""
 ----------------------------- Käynnistys ------------------------------- 
 ----------------------------- URL https://127.0.0.1:5000/ --------------  
"""
logging.basicConfig(level=logging.DEBUG, format=('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger('stkserver')

if __name__ == '__main__':
    if True:
        # Ajo paikallisesti
        print ("stk-run.run ajetaan DEGUB-lokitasolla")
        app.run(debug='DEBUG', ssl_context='adhoc')
    else:
        # Julkinen sovellus
        app.run(host='0.0.0.0', port=8000, ssl_context='adhoc')
