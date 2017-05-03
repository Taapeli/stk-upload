# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 29.12.2015

import logging
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__, instance_relative_config=True)
#app.config.from_object('config')
app.config.from_pyfile('config.py') # instance-hakemistosta
app.secret_key = "kuu on juustoa"
import models.genealogy
import models.loadfile          # Datan lataus käyttäjältä
import models.datareader        # Tietojen haku kannasta (tai työtiedostosta) 
import models.cvs_refnames      # Referenssinimien luonti
import models.dataupdater       # Tietojen päivitysmetodit

global session
session = None


@app.route('/')
def index(): 
    """Aloitussivun piirtäminen"""
    return render_template("index.html")

#--------
#@app.route('/dbtest')
#def dbtest():
#    "Onkohan tietokantayhteyttä palvelimelle?"
#    #TODO Poista dbtest ja app.config -käyttö
#    try:
#        graph = Graph('http://{0}/db/data/'.format(app.config['DB_HOST_PORT']))
#        authenticate(app.config['DB_HOST_PORT'], 
#                     app.config['DB_USER'], app.config['DB_AUTH'])
#        query = "MATCH (p:Person) RETURN p.firstname, p.lastname LIMIT 5"
#        x = graph.cypher.execute(query).one
#        text = "Henkilö: {0}, {1}".format(x[0], x[1])
#        return redirect(url_for('db_test_tulos', text=text))
#
#    except Exception as e:
#        return redirect(url_for('db_test_tulos', text="Exception "+str(e)))
#    
#@app.route('/dbtest/tulos/<text>')
#def db_test_tulos(text=''):
#    return render_template("db_test.html", text=text)
#-------

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
        except Exception as e:
            return redirect(url_for('virhesivu', code=1, text=str(e)))
        

@app.route('/lataa', methods=['POST'])
def lataa(): 
    """ Versio 2: Lataa cvs-tiedoston talletettavaksi
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
    dburi = models.genealogy.connect_db()
    try:
        if subj == 'henkilot':  # Käräjille osallistuneiden tiedot
            status = models.datareader.datastorer(pathname)
        else:
            if subj == 'refnimet': # Referenssinimet
                # Tallettaa Refname-objekteja # TODO Määrärajoitus pois!
                status=models.cvs_refnames.referenssinimet(pathname, max=1100)
            else:
                if subj == 'karajat': # TODO: Tekemättä
                    status="Käräjätietojen lukua ei ole vielä tehty"
                else:
                    return redirect(url_for('virhesivu', code=1, text= \
                        "Aineistotyypin '" + aineisto + "' käsittely puuttuu vielä"))
    except KeyError as e:
        return render_template("virhe_lataus.html", code=1, \
               text="Oikeaa sarakeotsikkoa ei löydy: " + str(e))
    return render_template("talletettu.html", text=status, uri=dburi)

@app.route('/lista/henkilot')
def nayta_henkilot():   
    """ tietokannan henkiloiden näyttäminen ruudulla """
    dburi = models.genealogy.connect_db()
    persons = models.datareader.lue_henkilot()
    return render_template("table1.html", persons=persons, uri=dburi)

@app.route('/lista/refnimet', defaults={'reftype': None})
@app.route('/lista/refnimet/<string:reftype>')
def nayta_refnimet(reftype): 
    """ referenssinimien näyttäminen ruudulla """
    models.genealogy.connect_db()
    if reftype and reftype != "":
        names = models.datareader.lue_typed_refnames(reftype)
        return render_template("table_refnames_1.html", names=names, reftype=reftype)
    else:
        names = models.datareader.lue_refnames()
        return render_template("table_refnames.html", names=names)

@app.route('/tyhjenna/kaikki/kannasta')
def tyhjenna():   
    """ tietokannan tyhjentäminen mitään kyselemättä """
    connect_db()
    alusta_kanta()
    return render_template("talletettu.html", text="Koko kanta on tyhjennetty")


@app.route('/yhdista', methods=['POST'])
def nimien_yhdistely():   
    """ Nimien listaus tietokannasta ehtolauseella
        oid=arvo        näyttää nimetyn henkilön
        names=arvo      näyttää henkilöt, joiden nimi alkaa arvolla
    """
    names = request.form['names']
    logging.debug('Poimitaan ' + names )
    return redirect(url_for('nayta_ehdolla', ehto='names='+names))

@app.route('/samahenkilo', methods=['POST'])
def henkiloiden_yhdistely():   
    """ Yhdistetään base-henkilöön join-henkilöt tapahtumineen, 
        minkä jälkeen näytetään muuttunut henkilölista
    """
    names = request.form['names']
    print (dir(request.form))
    base_id = request.form['base']
    join_ids = request.form.getlist('join')
    #TODO lisättävä valitut ref.nimet, jahka niitä tulee
    models.dataupdater.joinpersons(base_id, join_ids)
    flash('Yhdistettiin (muka) ' + str(base_id) + " + " + str(join_ids) )
    return redirect(url_for('nayta_ehdolla', ehto='names='+names))


@app.route('/poimi/<string:ehto>')
def nayta_ehdolla(ehto):   
    """ Nimien listaus tietokannasta ehtolauseella
        oid=arvo        näyttää nimetyn henkilön
        names=arvo      näyttää henkilöt, joiden nimi alkaa arvolla
    """
    key, value = ehto.split('=')
    connect_db()
    try:
        if key == 'oid':
            persons = models.datareader.lue_henkilot(oid=value)            
            return render_template("person.html", persons=persons)
        elif key == 'names':
            value=value.title()
            persons = models.datareader.lue_henkilot(names=value)
            return render_template("join_persons.html", 
                                   persons=persons, pattern=value)
        else:
            raise(KeyError("Vain oid:llä voi hakea"))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

@app.route('/virhe_lataus/<int:code>/<text>')
def virhesivu(code, text=''):
    """ Virhesivu näytetään """
    logging.debug('Virhesivu ' + str(code) )
    return render_template("virhe_lataus.html", code=code, text=text)



if __name__ == '__main__':
    if False:
        # Ajo paikallisesti
        logging.basicConfig(level=logging.DEBUG)
        app.run(debug='DEBUG')
    else:
        # Julkinen sovellus
        logging.basicConfig(level=logging.INFO)
        app.run(host='0.0.0.0', port=8000)

