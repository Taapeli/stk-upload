#!/usr/bin/python
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
        return redirect(url_for('virhesivu', code=415, text=str(e)))

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
            status = models.cvs_refnames.referenssinimet(pathname, maxrows=100)
        elif subj == 'xml_file': # gramps backup xml file to Neo4j db
            status = models.datareader.xml_to_neo4j(pathname)
        elif subj == 'karajat': # TODO: Tekemättä
            status = "Käräjätietojen lukua ei ole vielä tehty"
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
    elif subj == "henkilot2":
        persons = models.datareader.lue_henkilot2()
        return render_template("table_persons2.html", persons=persons)
    elif subj == "k_persons":
        persons = models.datareader.lue_henkilot2()
        return render_template("k_persons.html", persons=persons)
    elif subj == "surnames":
        surnames = models.gen.person.Name.get_surnames()
        return render_template("table_surnames.html", surnames=surnames)
    elif subj == 'events_wo_cites':
        headings, titles, lists = models.datareader.read_events_wo_cites()
        return render_template("table_of_data.html", 
               headings=headings, titles=titles, lists=lists)
    elif subj == 'events_wo_place':
        headings, titles, lists = models.datareader.read_events_wo_place()
        return render_template("table_of_data.html", 
               headings=headings, titles=titles, lists=lists)
    elif subj == 'notes':
        titles, notes = models.datareader.get_notes()
        return render_template("table_notes.html", 
                               titles=titles, notes=notes)
    elif subj == 'objects':
        objects = models.datareader.read_objects()
        return render_template("table_objects.html", 
                               objects=objects)
    elif subj == 'repositories':
        repositories = models.datareader.read_repositories()
        return render_template("table_repositories.html", 
                               repositories=repositories)
    elif subj == 'sources':
        sources = models.datareader.read_sources()
        return render_template("table_sources.html", 
                               sources=sources)
    elif subj == 'sources_wo_cites':
        headings, titles, lists = models.datareader.read_sources_wo_cites()
        return render_template("table_of_data.html", 
               headings=headings, titles=titles, lists=lists)
    elif subj == 'places':
        headings, titles, lists = models.datareader.read_places()
        return render_template("table_of_data.html", 
               headings=headings, titles=titles, lists=lists)
    elif subj == "users":
        lista = models.gen.user.User.get_all()
        return render_template("table_users.html", users=lista)
    else:
        return redirect(url_for('virhesivu', code=1, text= \
            "Aineistotyypin '" + subj + "' käsittely puuttuu vielä"))


@app.route('/aseta/refnames')
def aseta_refnames(): 
    """ referenssinimien asettaminen henkilöille """
    models.dbutil.connect_db()
    dburi = models.dbutil.connect_db()
    
    message = models.datareader.set_refnames()
    return render_template("talletettu.html", text=message, uri=dburi)


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
    
    
@app.route('/lista/people_by_surname/', defaults={'surname': ""})
@app.route('/lista/people_by_surname/<string:surname>')
def list_people_by_surname(surname): 
    """ henkilöiden, joilla on sama sukunimi näyttäminen ruudulla """
    models.dbutil.connect_db()
    people = models.datareader.get_people_by_surname(surname)
    return render_template("table_people_by_surname.html", 
                           surname=surname, people=people)
    
    
@app.route('/lista/person_data/<string:uniq_id>')
def show_person_data(uniq_id): 
    """ henkilön tietojen näyttäminen ruudulla """
    models.dbutil.connect_db()
    person, events, photos = models.datareader.get_person_data_by_id(uniq_id)
    return render_template("table_person_by_id.html", 
                           person=person, events=events, photos=photos)
    
    
@app.route('/lista/family_data/<string:uniq_id>')
def show_family_data(uniq_id): 
    """ henkilön perheen tietojen näyttäminen ruudulla """
    models.dbutil.connect_db()
    person, families = models.datareader.get_families_data_by_id(uniq_id)
    return render_template("table_families_by_id.html", 
                           person=person, families=families)


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
        elif key == 'cite_sour_repo':
            events = models.datareader.read_cite_sour_repo(uniq_id=value)
            return render_template("cite_sour_repo.html", 
                                   events=events)
        elif key == 'repo_uniq_id':
            repositories = models.datareader.read_repositories(uniq_id=value)
            return render_template("repo_sources.html", 
                                   repositories=repositories)
        elif key == 'source_uniq_id':
            sources = models.datareader.read_sources(uniq_id=value)
            return render_template("source_citations.html", 
                                   sources=sources)
        elif key == 'uniq_id':
            persons = models.datareader.lue_henkilot2(uniq_id=value)            
            return render_template("person2.html", persons=persons)
        else:
            raise(KeyError("Vain oid:llä voi hakea"))
    except KeyError as e:
        return redirect(url_for('virhesivu', code=1, text=str(e)))


@app.route('/newuser', methods=['POST'])
def new_user(): 
    """ Lisää tai päivittää käyttäjätiedon
    """
    try:
        models.dbutil.connect_db()
        userid = request.form['userid']
        if userid:
            u = models.gen.user.User(userid)
            u.name = request.form['name']
            u.save()
        else:
            flash("Anna vähintään käyttäjätunnus", 'warning')
         
    except Exception as e:
        flash("Lisääminen ei onnistunut: {} - {}".\
              format(e.__class__.__name__,str(e)), 'error')
        #return redirect(url_for('virhesivu', code=1, text=str(e)))

    return redirect(url_for('nayta_henkilot', subj='users'))


@app.route('/virhe_lataus/<int:code>/<text>')
def virhesivu(code, text=''):
    """ Virhesivu näytetään """
    logging.debug('Virhesivu ' + str(code) )
    return render_template("virhe_lataus.html", code=code, text=text)


@app.route('/stk')
def stk_harjoitus():   
    return render_template("a_home.html")



if __name__ == '__main__':
    if True:
        # Ajo paikallisesti
        logging.basicConfig(level=logging.DEBUG)
        print ("stk-run.__main__ ajetaan DEGUB-moodissa")
        app.run(debug='DEBUG')
    else:
        # Julkinen sovellus
        logging.basicConfig(level=logging.INFO)
        app.run(host='0.0.0.0', port=8000)

