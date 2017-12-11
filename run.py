# coding=UTF-8

from stk_server import app 
import logging
print('Käynnistys: ' + str(app))
""" ----------------------------- Käynnistys ------------------------------- """

if __name__ == '__main__':
    if True:
        # Ajo paikallisesti
        logging.basicConfig(level=logging.DEBUG)
        print ("stk-run.run ajetaan DEGUB-lokitasolla")
        app.run(debug='DEBUG')
    else:
        # Julkinen sovellus
        logging.basicConfig(level=logging.INFO)
        app.run(host='0.0.0.0', port=8000)
