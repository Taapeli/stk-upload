# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 29.12.2015

import logging
from flask import Flask, render_template, request, redirect, url_for, flash, g

global app
app = Flask(__name__, instance_relative_config=True)
#app.config.from_object('config')
app.config.from_pyfile('config.py') # instance-hakemistosta
app.secret_key = "kuu on juustoa"

#import instance.config as config
import models.dbutil
import models.loadfile          # Datan lataus käyttäjältä
import models.datareader        # Tietojen haku kannasta (tai työtiedostosta) 
import models.dataupdater       # Tietojen päivitysmetodit
import models.cvs_refnames      # Referenssinimien luonti
import models.gen.user          # Käyttäjien tiedot


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
        return render_template("virhe_lataus.html", text=str(e))

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
            return render_template("table_persons.html", name=pathname, \
                   persons=persons)
        except Exception as e:
            return redirect(url_for('virhesivu', code=1, text=str(e)))
        

@app.route('/lataa', methods=['POST'])
def lataa(): 
    """ Versio 2: Lataa cvs-tiedoston työhakemistoon kantaan talletettavaksi
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
    dburi = models.dbutil.connect_db()
    try:
        if subj == 'henkilot':  # Käräjille osallistuneiden tiedot
            status = models.datareader.datastorer(pathname)
        elif subj == 'refnimet': # Referenssinimet
            # Tallettaa Refname-objekteja # TODO Määrärajoitus pois!
            status=models.cvs_refnames.referenssinimet(pathname, max=1100)
        elif subj == 'karajat': # TODO: Tekemättä
            status="Käräjätietojen lukua ei ole vielä tehty"
        else:
            return redirect(url_for('virhesivu', code=1, text= \
                "Aineistotyypin '" + subj + "' käsittely puuttuu vielä"))
    except KeyError as e:
        return render_template("virhe_lataus.html", code=1, \
               text="Oikeaa sarakeotsikkoa ei löydy: " + str(e))
    return render_template("talletettu.html", text=status, uri=dburi)


@app.route('/lista/<string:subj>')
def nayta_henkilot(subj):   
    """ tietokannan henkiloiden tai käyttäjien näyttäminen ruudulla """
    models.dbutil.connect_db()
    if subj == "henkilot":
        # dburi vain tiedoksi!
        dbloc = g.driver.address
        dburi = ':'.join((dbloc[0],str(dbloc[1])))

        persons = models.datareader.lue_henkilot()
        return render_template("table_persons.html", persons=persons, uri=dburi)
    elif subj == "users":
        lista = models.gen.user.User.get_all_userids()
        return render_template("table_users.html", users=lista)
    else:
        return redirect(url_for('virhesivu', code=1, text= \
            "Aineistotyypin '" + subj + "' käsittely puuttuu vielä"))


@app.route('/lista/refnimet', defaults={'reftype': None})
@app.route('/lista/refnimet/<string:reftype>')
def nayta_refnimet(reftype): 
    """ referenssinimien näyttäminen ruudulla """
    models.dbutil.connect_db()
    if reftype and reftype != "":
        names = models.datareader.lue_typed_refnames(reftype)
        return render_template("table_refnames_1.html", names=names, reftype=reftype)
    else:
        names = models.datareader.lue_refnames()
        return render_template("table_refnames.html", names=names)


@app.route('/tyhjenna/kaikki/kannasta')
def tyhjenna():   
    """ tietokannan tyhjentäminen mitään kyselemättä """
    models.dbutil.connect_db()
    models.dbutil.alusta_kanta()
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
    models.dbutil.connect_db()
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

@app.route('/newuser', methods=['POST'])
def new_user(): 
    """ Versio 2: Lataa cvs-tiedoston työhakemistoon kantaan talletettavaksi
    """
    try:
        models.dbutil.connect_db()
        userid = request.form['userid']
        name = request.form['name']
        
        models.gen.user.User.create_user(userid, name)
         
    except Exception as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))

    return redirect(url_for('nayta_henkilot', subj='users'))


@app.route('/virhe_lataus/<int:code>/<text>')
def virhesivu(code, text=''):
    """ Virhesivu näytetään """
    logging.debug('Virhesivu ' + str(code) )
    return render_template("virhe_lataus.html", code=code, text=text)



if __name__ == '__main__':
    if True:
        # Ajo paikallisesti
        logging.basicConfig(level=logging.DEBUG)
        app.run(debug='DEBUG')
    else:
        # Julkinen sovellus
        logging.basicConfig(level=logging.INFO)
        app.run(host='0.0.0.0', port=8000)

