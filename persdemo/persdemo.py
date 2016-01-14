# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 29.12.2015

import logging
#from __future__ import print_function
from flask import Flask, render_template, request

app = Flask(__name__, instance_relative_config=True)

# config-tiedostot ei toimi ainakaan komentoriviltä, missähän vika?
#app.config.from_object('config')
#app.config.from_pyfile('config.py') # instance-hakemistosta

import models.loadfile
import models.datareader

@app.route('/')
def index(): 
    """Aloitussivun piirtäminen"""
    return render_template("index.html")

@app.route('/lataa1a', methods=['POST'])
def lataa1a(): # Lataa tiedoston ja näyttää sen
    infile = request.files['filenm']
    logging.debug('Ladataan tiedosto ' + infile.filename)
    return models.loadfile.upload_file(infile, fmt='list')

@app.route('/lataa1b', methods=['POST'])
def lataa1b(): # Lataa tiedoston ja näyttää sen taulukkona
    infile = request.files['filenm']
    return models.loadfile.upload_file(infile, fmt='table')

@app.route('/lista1/<string:fmt>/<string:filename>')
def nayta1(filename, fmt):   # tiedoston näyttäminen ruudulla
    pathname = models.loadfile.fullname(filename)
    try:
        with open(pathname, 'r', encoding='UTF-8') as f:
            read_data = f.read()    
    except IOError as e:
        read_data = "(Tiedoston lukeminen ei onnistu" + e.strerror + ")"
    except UnicodeDecodeError as e:
        read_data = "(Tiedosto ei ole UTF-8 " + e.strerror + ")"
    

    # Vaihtoehto a:
    if fmt == 'list':   # Tiedosto sellaisenaan
        return render_template("lista1.html", name=pathname, data=read_data)
    
    # Vaihtoehto b: Luetaan tiedot taulukoksi
    else:
        rivit = models.datareader.henkilolista(pathname)
        return render_template("table1.html", name=pathname, rivit=rivit)


@app.route('/lataa2', methods=['POST'])
def lataa2(): 
    """ Lataa tiedoston ja näyttää latauksen mahdolliset ilmoitukset, 
        yhteenvetotilasto
    """
    return render_template("ladattu2.html")

@app.route('/lista2/<string:ehto>')
def nayta2(ehto):   
    """ Nimien listaus tietokannasta
        mahdollisella määrittelemättömällä ehtolauseella
    """
    return render_template("lista2.html", my_arg=ehto)

@app.route('/virhe_lataus/<int:code>/<text>')
def virhesivu(code, text=''):
    """ Virhesivu näytetään """
    return render_template("virhe_lataus.html", code=code, text=text)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=80)
