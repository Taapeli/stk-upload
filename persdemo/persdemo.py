# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 29.12.2015

import csv
import logging
#from __future__ import print_function
from flask import Flask, render_template, request

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py') # instance-hakemistosta

from models.loadfile import upload_file, fullname

@app.route('/')
def index(): 
    """Aloitussivun piirtäminen"""
    return render_template("index.html")

@app.route('/lataa1a', methods=['POST'])
def lataa1a(): # Lataa tiedoston ja näyttää sen
    infile = request.files['filenm']
    logging.debug('Ladataan tiedosto ' + infile.filename)
    return upload_file(infile, fmt='list')

@app.route('/lataa1b', methods=['POST'])
def lataa1b(): # Lataa tiedoston ja näyttää sen taulukkona
    infile = request.files['filenm']
    return upload_file(infile, fmt='table')

@app.route('/lista1/<string:fmt>/<string:filename>')
def nayta1(filename, fmt):   # tiedoston näyttäminen ruudulla
    pathname = fullname(filename)
    try:
        with open(pathname, 'r') as f:
            read_data = f.read().decode('UTF-8')    
    except IOError as e:
        read_data = "(Tiedoston lukeminen ei onnistu" + e.strerror + ")"

    # Vaihtoehto a:
    if fmt == 'list':   # Tiedosto sellaisenaan
        return render_template("lista1.html", name=pathname, data=read_data)
    
    # Vaihtoehto b: Luetaan tiedot taulukoksi
    else:
        with open(pathname, 'rb') as f:
            reader = csv.DictReader(f)
            rivit = []

            for row in reader:
                # Onko henkilörivi?
                etu=row['Sukunimi_vakioitu']
                suku=row['Etunimi_vakioitu']
                if suku == '' and etu == '':
                    continue

                if etu == '': etu = 'N'
                if suku == '': suku = 'N'
                nimi='%s %s' % (etu, suku)

                """ Käräjät-tieto on yhdessä sarakkeessa tai 
                    Juhan muuntamana kolmessa: käräjä, alku, loppu
                """
                if 'Käräjäpaikka' in row:
                    karaja = '%s %s...%s' % \
                         (row['Käräjäpaikka'], row['Alkuaika'], row['Loppuaika'])
                    if karaja[-3:] == '...':
                        karaja = karaja[:-3]
                else:
                    karaja = row['Käräjät']

                rivi = dict( \
                    nimi=nimi.decode('UTF-8'), \
                    ammatti=row['Ammatti_vakioitu'].decode('UTF-8'), \
                    paikka=row['Paikka_vakioitu'].decode('UTF-8'), \
                    karajat=karaja.decode('UTF-8'))
                rivit.append(rivi)

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