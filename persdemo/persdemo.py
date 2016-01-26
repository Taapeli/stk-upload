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

from models.genealogy import *  # Tietokannan luokat
import models.loadfile          # Datan lataus käyttäjältä
import models.datareader        # Tietojen haku kannasta (tai työtiedostosta) 

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
        read_data = "(Tiedosto ei ole UTF-8)"
    

    # Vaihtoehto a:
    if fmt == 'list':   # Tiedosto sellaisenaan
        return render_template("lista1.html", name=pathname, data=read_data)
    
    # Vaihtoehto b: Luetaan tiedot taulukoksi
    else:
        try:
            persons, events = models.datareader.henkilolista(pathname)
            return render_template("table1.html", name=pathname, \
                   persons=persons, events=events)
        except KeyError as e:
            return render_template("virhe_lataus.html", code=1, text=e)
        

@app.route('/lataa', methods=['POST'])
def lataa(): 
    """ Lataa tiedoston ja näyttää latauksen mahdolliset ilmoitukset
    """
    infile = request.files['filenm']
    return models.loadfile.upload_file(infile)

@app.route('/talleta/<string:filename>')
def talleta(filename):   # tietojen tallettaminen kantaan
    pathname = models.loadfile.fullname(filename)
    
    # Luetaan tmp-tiedosto ja talletetaan tiedot tietokantaan 
    try:
#       u = User('u1234', 'Pekka')
#       u.save()
#       logging.debug('Talletettiin uusi käyttäjä ' + str(u))

        status = models.datareader.datastorer(pathname)
    except KeyError as e:
        return render_template("virhe_lataus.html", code=1, text=e)
    return render_template("talletettu.html", text=status)

@app.route('/lista/henkilot')
def nayta_henkilot():   # tietokannan henkiloiden näyttäminen ruudulla
    try:
        persons, events = models.datareader.lue_henkilot()
        return render_template("table1.html", persons=persons, events=events)
    except KeyError as e:
        return render_template("virhe_lataus.html", code=1, text=e)

@app.route('/tyhjenna/kaikki/kannasta')
def tyhjenna():   # tietokannan tyhjentäminen mitään kyselemättä
    tyhjenna_kanta()
    return render_template("talletettu.html", text="Koko kanta on tyhjennetty")

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

