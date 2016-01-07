# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 29.12.2015

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
    
    if fmt == 'list':   # Tiedosto sellaisenaan
        return render_template("lista1.html", name=pathname, data=read_data)
    else:               # Tiedot taulukkona
        return render_template("table1.html", name=pathname, data=read_data)


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
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=80)