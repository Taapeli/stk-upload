# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 29.12.2015

import logging
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, instance_relative_config=True)

# config-tiedostot ei toimi ainakaan komentoriviltä, missähän vika?
#app.config.from_object('config')
#app.config.from_pyfile('config.py') # instance-hakemistosta

from models.genealogy import *  # Tietokannan kaikki luokat ja apuluokkia
import models.loadfile          # Datan lataus käyttäjältä
import models.datareader        # Tietojen haku kannasta (tai työtiedostosta) 
import models.cvs_refnames      # Referenssinimien luonti

@app.route('/')
def index(): 
    """Aloitussivun piirtäminen"""
    return render_template("index.html")


@app.route('/lataa1a', methods=['POST'])
def lataa1a(): 
    """ Lataa tiedoston ja näyttää sen """
    try:
        infile = request.files['filenm']
        logging.debug('Ladataan tiedosto ' + infile.filename)
        models.loadfile.upload_file(infile)
    except Exception as e:
        return render_template("virhe_lataus.html", code=code, text=str(e))

    return redirect(url_for('nayta1', filename=infile.filename, fmt='list'))
        
@app.route('/lataa1b', methods=['POST'])
def lataa1b(): 
    """ Lataa tiedoston ja näyttää sen taulukkona """
    infile = request.files['filenm']
    try:
        models.loadfile.upload_file(infile)
    except Exception as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    return redirect(url_for('nayta1', filename=infile.filename, fmt='table'))


@app.route('/lista1/<string:fmt>/<string:filename>')
def nayta1(filename, fmt):   
    """ tiedoston näyttäminen ruudulla """
    try:
        pathname = models.loadfile.fullname(filename)
        with open(pathname, 'r', encoding='UTF-8') as f:
            read_data = f.read()    
    except IOError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))
    except UnicodeDecodeError as e:
        return redirect(url_for('virhesivu', code=1, \
               text="Tiedosto ei ole UTF-8. " + str(e)))  

    # Vaihtoehto a:
    if fmt == 'list':   # Tiedosto sellaisenaan
        return render_template("lista1.html", name=pathname, data=read_data)
    
    # Vaihtoehto b: Luetaan tiedot taulukoksi
    else:
        try:
            persons = models.datareader.henkilolista(pathname)
            return render_template("table1.html", name=pathname, \
                   persons=persons)
        except KeyError as e:
            return redirect(url_for('virhesivu', code=1, text=str(e)))
        

@app.route('/lataa', methods=['POST'])
def lataa(): 
    """ Versio 2: Lataa tiedoston ja näyttää latauksen mahdolliset ilmoitukset
    """
    try:
        infile = request.files['filenm']
        aineisto = request.form['aineisto']
        logging.debug('Saatiin ' + aineisto + ", tiedosto: " + infile.filename )
        
        models.loadfile.upload_file(infile)
         
    except Exception as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    return redirect(url_for('talleta', filename=infile.filename, subj=aineisto))


@app.route('/talleta/<string:subj>/<string:filename>')
def talleta(filename, subj):   
    """ tietojen tallettaminen kantaan """
    pathname = models.loadfile.fullname(filename)
    
    try:
        if subj == 'henkilot':  # Käräjille osallistuneiden tiedot
            status = models.datareader.datastorer(pathname)
        else:
            if subj == 'refnimet': # Referenssinimet
                # Palauttaa toistaiseksi taulukon Refname-objekteja
                refnames=models.cvs_refnames.referenssinimet(pathname)
                logging.debug('Tuli ' + str(len(refnames)) + ' nimeä ')
                return render_template("table_refnames.html", name=pathname, \
                    refnames=refnames)
                pass
            else:
                if subj == 'karajat': # TODO: Tekemättä
                    status="Käräjätietojen lukua ei ole vielä tehty"
                else:
                    return redirect(url_for('virhesivu', code=1, text= \
                        "Aineistotyypin '" + aineisto + "' käsittely puuttuu vielä"))
    except KeyError as e:
        return render_template("virhe_lataus.html", code=1, \
               text="Oikeaa sarakeotsikkoa ei löydy: " + str(e))
    return render_template("talletettu.html", text=status)

@app.route('/lista/henkilot')
def nayta_henkilot():   
    """ tietokannan henkiloiden näyttäminen ruudulla """
    try:
        persons = models.datareader.lue_henkilot()
        return render_template("table1.html", persons=persons)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

@app.route('/tyhjenna/kaikki/kannasta')
def tyhjenna():   
    """ tietokannan tyhjentäminen mitään kyselemättä """
    tyhjenna_kanta()
    return render_template("talletettu.html", text="Koko kanta on tyhjennetty")

@app.route('/poimi/<string:ehto>')
def nayta_ehdolla(ehto):   
    """ Nimien listaus tietokannasta ehtolauseella
        id=arvo         näyttää nimetyn henkilön
    """
    key, value = ehto.split('=')
    try:
        if key != 'id':
            raise(KeyError("Vain id:llä voi hakea"))
        persons = models.datareader.lue_henkilot(id=value)
        
        # Testi5
        vkey  = persons[0].make_key()
        logging.info(vkey)
        
        return render_template("person.html", persons=persons)
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

@app.route('/virhe_lataus/<int:code>/<text>')
def virhesivu(code, text=''):
    """ Virhesivu näytetään """
    logging.debug('Virhesivu ' + str(code) )
    return render_template("virhe_lataus.html", code=code, text=text)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app.run(debug=True)
    # tai vaikka app.run(host='0.0.0.0', port=80)

