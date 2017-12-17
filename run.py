# coding=UTF-8

from stk_server import app 
import logging
print('Käynnistys: ' + str(app))
""" ----------------------------- Käynnistys ------------------------------- """

logging.basicConfig(level=logging.DEBUG, format=('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger = logging.getLogger('stkserver')

if __name__ == '__main__':
    if True:
        # Ajo paikallisesti
<<<<<<< HEAD
        print ("stk-run.__main__ ajetaan DEGUB-moodissa")
=======
        logging.basicConfig(level=logging.DEBUG)
        print ("stk-run.run ajetaan DEGUB-lokitasolla")
>>>>>>> branch 'devel-tn-2' of https://github.com/Taapeli/stk-upload.git
        app.run(debug='DEBUG')
    else:
        # Julkinen sovellus
        app.run(host='0.0.0.0', port=8000)
