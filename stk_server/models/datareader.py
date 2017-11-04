# coding=UTF-8
# Taapeli harjoitustyö @ Sss 2016
# JMä 12.1.2016

import csv
import logging
import time
import xml.dom.minidom
from operator import itemgetter
from models.dbutil import Date
from models.gen.event import Event, Event_for_template
from models.gen.family import Family, Family_for_template
from models.gen.note import Note
from models.gen.object import Object
from models.gen.person import Person, Name, Person_as_member
from models.gen.place import Place
from models.gen.refname import Refname
from models.gen.source_citation import Citation, Repository, Source
from models.gen.user import User


def _poimi_(person_id, event_id, row, url):
    """ Poimitaan henkilötiedot riviltä ja palautetaan Person-objektina
    """

    suku=row['Sukunimi_vakioitu']
    etu=row['Etunimi_vakioitu']

    """ Käräjät-tieto on yhdessä sarakkeessa muodossa 'Tiurala 1666.02.20-22'
        Paikka erotetaan ja aika muunnetaan muotoon '1666-02-20 … 22'
        Päivämäärän korjaus tehdään jos kentässä on väli+numero.
        - TODO Pelkää vuosiluku käräjäpaikkana pitäisi siirtää alkuajaksi
     """
    if ' 1' in row['Käräjät']:
        kpaikka, aika = row['Käräjät'].split(' 1')
        aika = Date.range_str('1' + aika)
    else:
        kpaikka, aika = (row['Käräjät'], '')

    # Luodaan henkilö ja käräjätapahtuma

    p = Person(person_id)
    n = Name(etu, suku)
    p.names.append(n)
    p.name_orig = "{0} /{1}/".format(etu, suku)
    p.occupation = row['Ammatti_vakioitu']
    p.place=row['Paikka_vakioitu']

    e = Event(event_id, 'Käräjät')
    e.names = kpaikka
    e.date = aika
    e.name_orig = row['Käräjät']

    c = Citation()
    c.tyyppi = 'Signum'
    c.oid = row['Signum']
    c.url = url
    c.name_orig = row['Signum']
    c.source = Source()
    c.source.nimi = kpaikka + ' ' + aika
    e.citation = c

    p.events.append(e)
    return p


def henkilolista(pathname):
    """ Lukee csv-tiedostosta aineiston, ja luo kustakin 
        syöttörivistä Person-objektit
    """
    persons = []
    row_nro = 0
    url = ''

    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, dialect='excel')

        for row in reader:
            if row_nro == 0:
                logging.debug("Tiedosto " + pathname + ", sarakkeet: " + str(reader.fieldnames))
                if not "Käräjät" in reader.fieldnames:
                    raise KeyError('Sarake "Käräjät" puuttuu: ' + str(reader.fieldnames))
            row_nro += 2
            person_id = row_nro
    
            # Onko otsikkorivi? Tästä url kaikille seuraaville riveille
            if row['Käräjät'][:4] == 'http':
                url = row['Käräjät']
                #logging.debug('%s: url=%s' % (person_id, url))
                continue

            # Onko henkilörivi?
            if row['Sukunimi_vakioitu'] == '' and row['Etunimi_vakioitu'] == '':
                logging.warning('%s: nimikentät tyhjiä!' % person_id)
                continue
                            
            p = _poimi_(row_nro, row_nro+1, row, url)
            persons.append(p)

    logging.info(u'%s: %d riviä' % (pathname, row_nro))
    return (persons)


def datastorer(pathname):
    """ Lukee csv-tiedostosta aineiston, ja tallettaa kustakin syöttörivistä
         Person-objektit sisältäen käräjä-Eventit, Citation-viittaukset ja
         Place-paikat
    """
    row_nro = 0
    url = ''

    with open(pathname, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f, dialect='excel')

        for row in reader:
            if row_nro == 0:
                logging.debug("Tiedosto " + pathname + ", sarakkeet: " + str(reader.fieldnames))
                if not "Käräjät" in reader.fieldnames:
                    raise KeyError('Sarake "Käräjät" puuttuu: ' + str(reader.fieldnames))
            row_nro += 2
            person_id = row_nro
    
            # Onko otsikkorivi? Tästä url kaikille seuraaville riveille
            if row['Käräjät'][:4] == 'http':
                url = row['Käräjät']
                #logging.debug('%s: url=%s' % (person_id, url))
                continue

            # Onko henkilörivi?
            if row['Sukunimi_vakioitu'] == '' and row['Etunimi_vakioitu'] == '':
                logging.warning('%s: nimikentät tyhjiä!' % person_id)
                continue
                
            p = _poimi_(row_nro, row_nro+1, row, url)
    
            # Tallettaa Person-olion ja siihen sisältyvät Eventit
            # (Person)-[OSALLISTUU]->(Event)
            p.save("User100")

    message ='Talletettu %d riviä tiedostosta %s' % (row_nro, pathname)
    return message


def lue_henkilot(oid=None, names=None, nmax=1000):
    """ Lukee tietokannasta Person- ja Event- objektit näytettäväksi
        
        Palauttaa riveillä listan muuttujia: henkilön tiedot ja lista
        käräjätapahtuman muuttujalistoja
    """
    
    persons = []
    t0 = time.time()
    recs = Person.get_person_events(nmax=nmax, pid=oid, names=names)
    nro = 0
    for rec in recs:
        nro = nro + 1
        # Saatu Person ja collection(Event)
        #Palauttaa riveillä listan muuttujia:
        #n.oid, n.firstname, n.lastname, n.occu, n.place, type(r), events
        #  0      1            2           3       4      5        6
        # 146    Bengt       Bengtsson   soldat   null    OSALLISTUI [[...]]    

        pid = rec['n.id']
        p = Person(pid)
        etu = ""
        suku = ""
        if rec['k.firstname']:
            etu = rec['k.firstname']
        if rec['k.surname']:
            suku = rec['k.surname']
        p.names.append(Name(etu,suku))
#        if rec['n.name_orig']:
#            p.name_orig = rec['n.name_orig']
#         if rec['n.occu']:
#             p.occupation = rec['n.occu']
#         if rec['n.place']:
#             p.place= rec['n.place']

        for ev in rec['events']:
            # 'events' on lista käräjiä, jonka jäseninä on lista muuttujia:
            #[[e.oid, e.kind,  e.name,  e.date,          e.name_orig]...]
            #    0      1        2        3                4
            #[[ 147,  Käräjät, Sakkola, 1669-03-22 … 23, Sakkola 1669.03.22-23]]

            event_id = ev[0]
            if event_id:
                e = Event(event_id, ev[1])
    #             e.name = ev[2]
    #             e.date = ev[3]
    #             e.name_orig = ev[4]
                p.events.append(e)    
    #            logging.info("lue_henkilot: Tapahtuma {}".format(e))

#            c = Citation()
#            c.tyyppi = 'Signum'
#            c.oid = 'Testi3'
#            c.url = url
#            c.source = Source()
#            c.source.nimi = 'Testi3'
#            e.citation = c

        persons.append(p)

    if nro == 0:
        logging.warning("lue_henkilot: ei ketään oid={}, names={}".format(oid, names))
    else:
        logging.info("lue_henkilot: {} henkiloä".format(nro))
        #print ("Lue_henkilot:\n", retList[0])
    logging.debug("TIME lue_henkilot {} sek".format(time.time()-t0))

    return (persons)


def lue_henkilot_k(keys=None):
    """ Lukee tietokannasta Person- ja Event- objektit näytettäväksi
        
        Palauttaa riveillä listan muuttujia: henkilön tiedot ja lista
        tapahtuman muuttujalistoja
    """
    
    persons = []
    result = Person.get_events_k(keys)
    for record in result:
        # Got ["id", "confidence", "firstname", "refname", "surname", "suffix", "events"]
        uniq_id = record['id']
        p = Person()
        p.uniq_id = uniq_id
        p.confidence = record['confidence']
        pname = Name()
        if record['firstname']:
            pname.firstname = record['firstname']
        if record['refname']:
            pname.refname = record['refname']
        if record['surname']:
            pname.surname = record['surname']
        if record['suffix']:
            pname.patronyme = record['suffix']
        p.names.append(pname)
    
        # Events

        for event in record['events']:
            # Got event with place name: [id, type, date,
            #   datetype, daterange_start, daterange_stop, place.pname]
            e = Event_for_template()
            e.uniq_id = event[0]
            event_type = event[1]
            if event_type:
                e.type = event_type
                e.date = event[2]
                e.datetype = event[3]
                e.daterange_start = event[4]
                e.daterange_stop = event[5]
                e.place = event[6]
        
                if e.daterange_start != '' and e.daterange_stop != '':
                    e.daterange = e.daterange_start + " - " + e.daterange_stop
                elif e.daterange_start != '':
                    e.daterange = str(e.daterange_start) + "-"
                elif e.daterange_stop != '':
                    e.daterange = "-" + str(e.daterange_stop)
                
                p.events.append(e)
 
        persons.append(p)

    return (persons)


def set_confidence_value():
    """ Asettaa henkilölle laatu arvion
    """
    
    message = []
    counter = 0
    
    tx = User.beginTransaction()
    
    result = Person.get_confidence()
    for record in result:
        p = Person()
        p.uniq_id = record["uniq_id"]
        
        if len(record["list"]) > 0:
            sumc = 0
            for ind in record["list"]:
                sumc += int(ind)
                
            confidence = sumc/len(record["list"])
            p.confidence = "%0.1f" % confidence # confidence with one decimal
        p.set_confidence()
            
        counter += 1
            
    User.endTransaction(tx)
    text = "Number of confidences set: " + str(counter)
    message.append(text)
    return (message)
    
    
def set_refnames():
    """ Asettaa henkilöille refnamet
    """
    set_count = 0
    get_count = 0
    tx = User.beginTransaction()

    names = Name.get_all_firstnames()
    # Process each different first name
    for rec in names:
        # ╒═══════╤══════════════════════╤════════════╤════════════════╤═════╕
        # │"ID"   │"fn"                  │"sn"        │"pn"            │"sex"│
        # ╞═══════╪══════════════════════╪════════════╪════════════════╪═════╡
        # │"30281"│"Agata Eufrosine"     │"Tolpo"     │"Gabrielsdotter"│"F"  │
        # └───────┴──────────────────────┴────────────┴────────────────┴─────┘

        # Build a new refname
        # 1. first names
        firstname = rec["fn"]
        if firstname == 'N':
            firstnames = ''
        else:
            fn_list = []
            prev=('?', '?')
            for name in firstname.split(' '):
                if name == prev[0]:
                    # Same as previous
                    fn_list.append(prev[1])
                else:
                    nm = None
                    # For each of first names find refname
                    results = Refname.get_refname(name)
                    result = results.single()
                    if result:
                        nm = result['rname']
                        get_count += 1
                    else:
                        nm = name
                    fn_list.append(nm)
                    prev = (name, nm)
            firstnames = " ".join(fn_list)

        # 2. surname and patronyme
        surname = rec["sn"]     #.strip()
        if (surname == 'N'):
            surname = ''
        suffix = rec["pn"]
        # 3. join "firstnames/surname/suffix"
        if surname:
            refname = "".join((firstnames,'/',surname,'/'))
        else:
            refname = "".join((firstnames,'//',suffix))
        # 4. Store it
        if refname != rec["rn"]:
            Name.set_refname(tx, rec["ID"], refname)
            set_count += 1

    User.endTransaction(tx)
    msg="Sovellettu {} referenssinimeä {} nimeen".format(get_count, set_count)
    logging.info(msg)
    return msg


def lue_refnames():
    """ Lukee tietokannasta Refname- objektit näytettäväksi
        (n:Refname)-[r]->(m)
    """
    namelist = []
    t0 = time.time()
    recs = Refname.getrefnames()
    for rec in recs:
        namelist.append(rec)

    logging.info("TIME get_refnames {} sek".format(time.time()-t0))

    return (namelist)


def lue_typed_refnames(reftype):
    """ Lukee tietokannasta Refname- objektit näytettäväksi
    """
    namelist = []
    t0 = time.time()
    if not (reftype and reftype != ""):
        raise AttributeError("Mitä referenssityyppiä halutaan?")
    
    recs = Refname.get_typed_refnames(reftype)
# Esimerkki:
# >>> for x in v_names: print(x)
# <Record a.oid=3 a.name='Aabi' a.gender=None a.source='harvinainen' 
#         base=[[2, 'Aapeli', None]] other=[[None, None, None]]>
# <Record a.oid=5 a.name='Aabraham' a.gender='M' a.source='Pojat 1990-luvulla' 
#         base=[[None, None, None]] other=[[None, None, None]]>
# <Record a.oid=6 a.name='Aabrahami' a.gender=None a.source='harvinainen' 
#         base=[[7, 'Aappo', None]] other=[[None, None, None]]>
# >>> for x in v_names: print(x[1])
# Aabrahami
# Aabrami
# Aaca

#a.oid  a.name  a.gender  a.source   base                 other
#                                     [oid, name, gender]  [oid, name, gender]
#-----  ------  --------  --------   ----                 -----
#3493   Aake	F	  Messu- ja  [[null, null, null], [[3495, Aakke, null],
#                         kalenteri   [null, null, null],  [3660, Acatius, null],
#                                     [null, null, null],  [3662, Achat, null],
#                                     [null, null, null],  [3664, Achatius, M],
#                                     [null, null, null],  [3973, Akatius, null],
#                                     [null, null, null],  [3975, Ake, null],
#                                     [null, null, null]]  [3990, Akke, null]]
#3495   Aakke   null     harvinainen [[3493, Aake, F]]    [[null, null, null]]

    for rec in recs:
#        logging.debug("oid={}, name={}, gender={}, source={}, base={}, other={}".\
#               format( rec[0], rec[1],  rec[2],    rec[3],    rec[4],  rec[5]))
        # Luodaan nimi
        r = Refname(rec['a.name'])
        r.oid = rec['a.id']
        if rec['a.gender']:
            r.gender = rec['a.gender']
        if rec['a.source']:
            r.source= rec['a.source']

        # Luodaan mahdollinen kantanimi, johon tämä viittaa (yksi?)
        baselist = []
        for fld in rec['base']:
            if fld[0]:
                b = Refname(fld[1])
                b.oid = fld[0]
                if fld[2]:
                    b.gender = fld[2]
                baselist.append(b)

        # Luodaan lista muista nimistä, joihin tämä viittaa
        otherlist = []
        for fld in rec['other']:
            if fld[0]:
                o = Refname(fld[1])
                o.oid = fld[0]
                if fld[2]:
                    o.gender = fld[2]
                otherlist.append(o)

        namelist.append((r,baselist,otherlist))
    
    logging.info("TIME get_named_refnames {} sek".format(time.time()-t0))

    return (namelist)


def read_cite_sour_repo(uniq_id=None):
    """ Lukee tietokannasta Repository-, Source- ja Citation- objektit näytettäväksi

    """
    
    sources = []
    result_cite = Event.get_event_cite(uniq_id)
    for record_cite in result_cite:
        pid = record_cite['id']
        e = Event()
        e.uniq_id = pid
        if record_cite['type']:
            e.type = record_cite['type']
        if record_cite['date']:
            e.date = record_cite['date']
        if record_cite['datetype']:
            e.datetype = record_cite['datetype']
        if record_cite['daterange_start']:
            e.daterange_start = record_cite['daterange_start']
        if record_cite['daterange_stop']:
            e.daterange_stop = record_cite['daterange_stop']
        if e.daterange_start != '' and e.daterange_stop != '':
            e.daterange = e.daterange_start + " - " + e.daterange_stop
        elif e.daterange_start != '':
            e.daterange = e.daterange_start + " - "
        elif e.daterange_stop != '':
            e.daterange = " - " + e.daterange_stop

        for source_cite in record_cite['sources']:
            c = Citation()
            c.uniq_id = source_cite[0]
            c.dateval = source_cite[1]
            c.page = source_cite[2]
            c.confidence = source_cite[3]
            
            c.get_sourceref_hlink()
            if c.sourceref_hlink != '':
                s = Source()
                s.uniq_id = c.sourceref_hlink
                result_source = s.get_source_data()
                for record_source in result_source:
                    if record_source['stitle']:
                        s.stitle = record_source['stitle']
                        
                    s.get_reporef_hlink()
                    if s.reporef_hlink != '':

                        r = Repository()
                        r.uniq_id = s.reporef_hlink
                        result_repo = r.get_repo_data()
                        for record_repo in result_repo:
                            if record_repo['rname']:
                                r.rname = record_repo['rname']
                            if record_repo['type']:
                                r.type = record_repo['type']
                        
                        s.repos.append(r)
                c.sources.append(s)
            e.citations.append(c)
            
        sources.append(e)

    return (sources)


def read_objects(uniq_id=None):
    """ Lukee tietokannasta Object- objektit näytettäväksi

    """
    
    objects = []
    result = Object.get_objects(uniq_id)
    for record in result:
        pid = record['uniq_id']
        o = Object()
        o.uniq_id = pid
        if record['o']['src']:
            o.src = record['o']['src']
        if record['o']['mime']:
            o.mime = record['o']['mime']
        if record['o']['description']:
            o.description = record['o']['description']
 
        objects.append(o)

    return (objects)


def read_repositories(uniq_id=None):
    """ Lukee tietokannasta Repository- ja Source- objektit näytettäväksi

    """
    
    repositories = []
    result = Repository.get_repository_source(uniq_id)
    for record in result:
        pid = record['id']
        r = Repository()
        r.uniq_id = pid
        if record['rname']:
            r.rname = record['rname']
        if record['type']:
            r.type = record['type']
        if record['url_href']:
            r.url_href.append(record['url_href'])
        if record['url_type']:
            r.url_type.append(record['url_type'])
        if record['url_description']:
            r.url_description.append(record['url_description'])

        for source in record['sources']:
 
            s = Source()
            s.uniq_id = source[0]
            s.stitle = source[1]
            s.reporef_medium = source[2]
            r.sources.append(s)
 
        repositories.append(r)

    return (repositories)


def read_sources(uniq_id=None):
    """ Lukee tietokannasta Source- ja Citation- objektit näytettäväksi

    """
    
    sources = []
    result = Source.get_source_citation(uniq_id)
    for record in result:
        pid = record['id']
        s = Source()
        s.uniq_id = pid
        if record['stitle']:
            s.stitle = record['stitle']

        for citation in record['citations']:
 
            c = Citation()
            c.uniq_id = citation[0]
            c.dateval = citation[1]
            c.page = citation[2]
            c.confidence = citation[3]
            s.citations.append(c)
 
        sources.append(s)

    return (sources)


def read_events_wo_cites():
    """ Lukee tietokannasta Event- objektit, joilta puuttuu viittaus näytettäväksi

    """
    
    headings = []
    titles, events = Event.get_events_wo_citation()
    
    headings.append("Tapahtumaluettelo")
    headings.append("Näytetään tapahtumat, joilla ei ole lähdeviittausta")

    return (headings, titles, events)


def read_events_wo_place():
    """ Lukee tietokannasta Event- objektit, joilta puuttuu paikka näytettäväksi

    """
    
    headings = []
    titles, events = Event.get_events_wo_place()
    
    headings.append("Tapahtumaluettelo")
    headings.append("Näytetään paikattomat tapahtumat")

    return (headings, titles, events)


def read_people_wo_birth():
    """ Lukee tietokannasta Person- objektit, joilta puuttuu syntymätapahtuma
        näytettäväksi

    """
    
    headings = []
    titles, people = Person.get_people_wo_birth()
    
    headings.append("Tapahtumaluettelo")
    headings.append("Näytetään henkilöt ilman syntymätapahtumaa")

    return (headings, titles, people)


def read_old_people_top():
    """ Lukee tietokannasta Person- objektit, joilla syntymä- ja kuolintapahtuma
        näytettäväksi

    """
    
    headings = []
    titles, people = Person.get_old_people_top()
    
    sorted_people = sorted(people, key=itemgetter(7), reverse=True)
    top_of_sorted_people = []
    for i in range(20):
        top_of_sorted_people.append(sorted_people[i])
    
    headings.append("Tapahtumaluettelo")
    headings.append("Näytetään vanhat henkilöt ja heidän ikä")

    return (headings, titles, top_of_sorted_people)


def read_places():
    """ Lukee tietokannasta Place- objektit näytettäväksi

    """
    
    headings = []
    titles, events = Place.get_places()
    
    headings.append("Paikkaluettelo")
    headings.append("Näytetään paikat")

    return (headings, titles, events)


def get_source_with_events(sourceid):
    """ Lukee tietokannasta Source- objektin tapahtumat näytettäväksi

    """
    
    s = Source()
    s.uniq_id = sourceid
    result = s.get_source_data()
    for record in result:
        s.stitle = record["stitle"]
    result = Source.get_events(sourceid)

    event_list = []
    for record in result:               # Events record
                
        for citation in record["citations"]:
            c = Citation()
            c.page = citation[0]
            c.confidence = citation[1]
            
            for event in citation[2]:
                e = Event()
                e.uniq_id = event[0]
                e.type = event[1]
                e.edate = event[2]
                
                for name in event[3]:
                    n = Name()
                    n.uniq_id = name[0]        
                    n.surname = name[1]        
                    n.firstname = name[2]  
                        
                    e.names.append(n)
                          
                c.events.append(e)
                
            event_list.append(c)

    return (s.stitle, event_list)


def read_sources_wo_cites():
    """ Lukee tietokannasta Source- objektit, joilta puuttuu viittaus näytettäväksi

    """
    
    headings = []
    titles, lists = Source.get_sources_wo_citation()
    
    headings.append("Lähdeluettelo")
    headings.append("Näytetään lähteet, joilla ei ole yhtään lähdeviittausta")

    return (headings, titles, lists)


def read_sources_wo_repository():
    """ Lukee tietokannasta Source- objektit, joilta puuttuu arkisto näytettäväksi

    """
    
    headings = []
    titles, lists = Source.get_sources_wo_repository()
    
    headings.append("Lähdeluettelo")
    headings.append("Näytetään lähteet, joilla ei ole arkistoa")

    return (headings, titles, lists)


def get_people_by_surname(surname):
    people = []
    result = Name.get_people_with_surname(surname)
    for record in result:
        p = Person()
        p.uniq_id = record['uniq_id']
        p.get_person_and_name_data_by_id()
        people.append(p)
        
    return (people)


def get_person_data_by_id(uniq_id):
    """ Get 5 data sets:
        person: uniq_id and name data
        events list: uniq_id, date, location name and id (?)
        photos
        sources
        families
    """
    p = Person()
    p.uniq_id = int(uniq_id)
    #.get_person_and_name_data_by_id()
    p.get_person_w_names()
    p.get_hlinks_by_id()
    
    events = []
    sources = []
    source_cnt = 0
    mybirth = ''

    # Events

    for i in range(len(p.eventref_hlink)):
        e = Event_for_template()
        e.uniq_id = p.eventref_hlink[i]
        e.role = p.eventref_role[i]
        e.get_event_data_by_id()
        
        if e.daterange_start != '' and e.daterange_stop != '':
            e.daterange = e.daterange_start + " - " + e.daterange_stop
        elif e.daterange_start != '':
            e.daterange = str(e.daterange_start) + "-"
        elif e.daterange_stop != '':
            e.daterange = "-" + str(e.daterange_stop)
            
        if e.place_hlink != '':
            place = Place()
            place.uniq_id = e.place_hlink
            place.get_place_data_by_id()
            # Location / place data
            e.location = place.pname
            e.locid = place.uniq_id
            e.ltype = place.type
                    
        if e.noteref_hlink != '':
            note = Note()
            note.uniq_id = e.noteref_hlink
            result = note.get_note()
            for record in result:
                e.notepriv = record["note"]["priv"]
                e.notetype = record["note"]["type"]
                e.notetext = record["note"]["text"]
                
        events.append(e)

        # Citations

        if e.citationref_hlink != '':
            citation = Citation()
            citation.uniq_id = e.citationref_hlink
            # If there is already the same citation on the list,
            # use that index
            citation_ind = -1
            for i in range(len(sources)):
                if sources[i].uniq_id == citation.uniq_id:
                    citation_ind = i + 1
                    break
            if citation_ind > 0:
                # Citation found
                e.source = citation_ind
            else: # Store the new source to the list
                source_cnt += 1
                e.source = source_cnt

                result = citation.get_source_repo(citation.uniq_id)
                for record in result:
                    citation.dateval = record['date']
                    citation.page = record['page']
                    citation.confidence = record['confidence']
                    if not record['notetext']:
                        if citation.page[:4] == "http":
                            citation.notetext = citation.page
                            citation.page = ''
                    else: 
                        citation.notetext = record['notetext']
                    
                    for source in record['sources']:
                        s = Source()
                        s.uniq_id = source[0]
                        s.stitle = source[1]
                        s.reporef_medium = source[2]
            
                        r = Repository()
                        r.uniq_id = source[3]
                        r.rname = source[4]
                        r.type = source[5]
                        
                        s.repos.append(r)
                        citation.sources.append(s)
                        
                    sources.append(citation)
            
    photos = []
    for link in p.objref_hlink:
        o = Object()
        o.uniq_id = link
        o.get_object_data_by_id()
        photos.append(o)

    # Families

    # Returning a list of Family objects
    # - which include a list of members (Person with 'role' attribute)
    #   - Person includes a list of Name objects
    families = {}
    fid = ''
    result = Person.get_family_members(p.uniq_id)
    for record in result:
        # Got ["family_id", "f_uniq_id", "role", "m_id", "uniq_id", 
        #      "gender", "birth_date", "names"]
        if fid != record["f_uniq_id"]:
            fid = record["f_uniq_id"]
            if not fid in families:
                families[fid] = Family_for_template(fid)
                families[fid].id = record['family_id']

        member = Person_as_member()    # A kind of Person
        member.role = record["role"]
        if record["m_id"]:
            member.id = record["m_id"]
        member.uniq_id = record["uniq_id"]
        if member.uniq_id == p.uniq_id:
            # What kind of family this is? I am a Child or Parent in family
            if member.role == "CHILD":
                families[fid].role = "CHILD"
            else:
                families[fid].role = "PARENT"

        if record["gender"]:
            member.gender = record["gender"]
        if record["birth_date"]:
            member.birth_date = record["birth_date"]
        if record["names"]:
            for name in record["names"]:
                # Got [[alt, ntype, firstname, surname, suffix]
                n = Name()
                n.alt = name[0]
                n.type = name[1]
                n.firstname = name[2]
                n.surname = name[3]
                n.suffix = name[4]
                member.names.append(n)

        if member.role == "CHILD":
            families[fid].children.append(member)
        elif member.role == "FATHER":
            families[fid].father = member
        elif member.role == "MOTHER":
            families[fid].mother = member

    family_list = list(families.values())
    return (p, events, photos, sources, family_list)


def get_families_data_by_id(uniq_id):
    # Sivua "table_families_by_id.html" varten
    families = []
    
    p = Person()
    p.uniq_id = uniq_id
    p.get_person_and_name_data_by_id()
        
    if p.gender == 'M':
        result = p.get_his_families_by_id()
    else:
        result = p.get_her_families_by_id()
        
    for record in result:
        f = Family_for_template()
        f.uniq_id = record['uniq_id']
        f.get_family_data_by_id()
    
        result = p.get_parentin_id()
        for record in result:
            parents_hlink = record["parentin_hlink"]
            pf = Family()
            pf.uniq_id = parents_hlink
            pf.get_family_data_by_id()
            
            father = Person()
            father.uniq_id = pf.father
            father.get_person_and_name_data_by_id()
            f.father = father
            
            mother = Person()
            mother.uniq_id = pf.mother
            mother.get_person_and_name_data_by_id()
            f.mother = mother
        
        spouse = Person()
        if p.gender == 'M':
            spouse.uniq_id = f.mother
        else:
            spouse.uniq_id = f.father
        spouse.get_person_and_name_data_by_id()
        f.spouse = spouse
            
        for child_id in f.childref_hlink:
            child = Person()
            child.uniq_id = child_id
            child.get_person_and_name_data_by_id()
            f.children.append(child)
            
        families.append(f)
        
    return (p, families)


def get_place_with_events (loc_id):
    """ Luetaan aneettuun paikkaan liittyvä hierarkia ja tapahtumat
        Palauttaa paikkahierarkian ja (henkilö)tapahtumat muodossa
        [Place_list, Event_table].

    place_list: Lista Place-objekteja, joissa kentät
        id      locid eli uniq_id
        type    paikan tyyppi (Farm, Village, ...)
        pname   paikannimi
        parent  isäsolmun id

    event_table:
        uid           person's uniq_id
        names         list of tuples [name_type, given_name, surname]
        etype         event type
        edate         event date
        edatetype     event date type
        edaterange    event daterange
    """
    place = Place()
    place.uniq_id = int(loc_id)
    place.get_place_data_by_id()
    place_list = Place.get_place_tree(loc_id)
    event_table = Place.get_place_events(loc_id)
    return (place, place_list, event_table)


def get_notes(uniq_id=None):
    """ Lukee tietokannasta Note- objektit näytettäväksi
    """
    
    titles, notes = Note.get_notes(uniq_id)
    return (titles, notes)


def handle_citations(collection, tx):
    # Get all the citations in the collection
    citations = collection.getElementsByTagName("citation")
    
    print ("*****Citations*****")
    counter = 0
    
    # Print detail of each citation
    for citation in citations:
        
        c = Citation()
        
        if citation.hasAttribute("handle"):
            c.handle = citation.getAttribute("handle")
        if citation.hasAttribute("change"):
            c.change = citation.getAttribute("change")
        if citation.hasAttribute("id"):
            c.id = citation.getAttribute("id")
    
        if len(citation.getElementsByTagName('dateval') ) == 1:
            citation_dateval = citation.getElementsByTagName('dateval')[0]
            if citation_dateval.hasAttribute("val"):
                c.dateval = citation_dateval.getAttribute("val")
        elif len(citation.getElementsByTagName('dateval') ) > 1:
            print("Error: More than one dateval tag in a citation")
    
        if len(citation.getElementsByTagName('page') ) == 1:
            citation_page = citation.getElementsByTagName('page')[0]
            c.page = citation_page.childNodes[0].data
        elif len(citation.getElementsByTagName('page') ) > 1:
            print("Error: More than one page tag in a citation")
    
        if len(citation.getElementsByTagName('confidence') ) == 1:
            citation_confidence = citation.getElementsByTagName('confidence')[0]
            c.confidence = citation_confidence.childNodes[0].data
        elif len(citation.getElementsByTagName('confidence') ) > 1:
            print("Error: More than one confidence tag in a citation")
    
        if len(citation.getElementsByTagName('noteref') ) == 1:
            citation_noteref = citation.getElementsByTagName('noteref')[0]
            if citation_noteref.hasAttribute("hlink"):
                c.noteref_hlink = citation_noteref.getAttribute("hlink")
        elif len(citation.getElementsByTagName('noteref') ) > 1:
            print("Error: More than one noteref tag in a citation")
    
        if len(citation.getElementsByTagName('sourceref') ) == 1:
            citation_sourceref = citation.getElementsByTagName('sourceref')[0]
            if citation_sourceref.hasAttribute("hlink"):
                c.sourceref_hlink = citation_sourceref.getAttribute("hlink")
        elif len(citation.getElementsByTagName('sourceref') ) > 1:
            print("Error: More than one sourceref tag in a citation")
                
        c.save(tx)
        counter += 1
        
    msg = "Citations stored: " + str(counter)
        
    return(msg)



def handle_events(collection, userid, tx):
    # Get all the events in the collection
    events = collection.getElementsByTagName("event")
    
    print ("*****Events*****")
    counter = 0
      
    # Print detail of each event
    for event in events:

        e = Event()
        
        if event.hasAttribute("handle"):
            e.handle = event.getAttribute("handle")
        if event.hasAttribute("change"):
            e.change = event.getAttribute("change")
        if event.hasAttribute("id"):
            e.id = event.getAttribute("id")
            
        if len(event.getElementsByTagName('type') ) == 1:
            event_type = event.getElementsByTagName('type')[0]
            # If there are type tags, but no type data
            if (len(event_type.childNodes) > 0):
                e.type = event_type.childNodes[0].data
            else:
                e.type = ''
        elif len(event.getElementsByTagName('type') ) > 1:
            print("Error: More than one type tag in an event")
            
        if len(event.getElementsByTagName('description') ) == 1:
            event_description = event.getElementsByTagName('description')[0]
            # If there are description tags, but no description data
            if (len(event_description.childNodes) > 0):
                e.description = event_description.childNodes[0].data
            else:
                e.description = ''
        elif len(event.getElementsByTagName('description') ) > 1:
            print("Error: More than one description tag in an event")
    
        if len(event.getElementsByTagName('dateval') ) == 1:
            event_dateval = event.getElementsByTagName('dateval')[0]
            if event_dateval.hasAttribute("val"):
                e.date = event_dateval.getAttribute("val")
            if event_dateval.hasAttribute("type"):
                e.datetype = event_dateval.getAttribute("type")
        elif len(event.getElementsByTagName('dateval') ) > 1:
            print("Error: More than one dateval tag in an event")
    
        if len(event.getElementsByTagName('daterange') ) == 1:
            event_daterange = event.getElementsByTagName('daterange')[0]
            if event_daterange.hasAttribute("start"):
                e.daterange_start = event_daterange.getAttribute("start")
            if event_daterange.hasAttribute("stop"):
                e.daterange_stop = event_daterange.getAttribute("stop")
        elif len(event.getElementsByTagName('daterange') ) > 1:
            print("Error: More than one daterange tag in an event")
    
        if len(event.getElementsByTagName('place') ) == 1:
            event_place = event.getElementsByTagName('place')[0]
            if event_place.hasAttribute("hlink"):
                e.place_hlink = event_place.getAttribute("hlink")
        elif len(event.getElementsByTagName('place') ) > 1:
            print("Error: More than one place tag in an event")
    
        if len(event.getElementsByTagName('attribute') ) == 1:
            event_attr = event.getElementsByTagName('attribute')[0]
            if event_attr.hasAttribute("type"):
                e.attr_type = event_attr.getAttribute("type")
            if event_attr.hasAttribute("value"):
                e.attr_value = event_attr.getAttribute("value")
        elif len(event.getElementsByTagName('attribute') ) > 1:
            print("Error: More than one attribute tag in an event")
    
        if len(event.getElementsByTagName('noteref') ) == 1:
            event_noteref = event.getElementsByTagName('noteref')[0]
            if event_noteref.hasAttribute("hlink"):
                e.noteref_hlink = event_noteref.getAttribute("hlink")
        elif len(event.getElementsByTagName('noteref') ) > 1:
            print("Error: More than one noteref tag in an event")
    
        if len(event.getElementsByTagName('citationref') ) == 1:
            event_citationref = event.getElementsByTagName('citationref')[0]
            if event_citationref.hasAttribute("hlink"):
                e.citationref_hlink = event_citationref.getAttribute("hlink")
        elif len(event.getElementsByTagName('citationref') ) > 1:
            print("Error: More than one citationref tag in an event")
    
        if len(event.getElementsByTagName('objref') ) == 1:
            event_objref = event.getElementsByTagName('objref')[0]
            if event_objref.hasAttribute("hlink"):
                e.objref_hlink = event_objref.getAttribute("hlink")
        elif len(event.getElementsByTagName('objref') ) > 1:
            print("Error: More than one objref tag in an event")
                
        e.save(userid, tx)
        counter += 1
        
        # There can be so many individs to store that Cypher needs a pause
        # time.sleep(0.1)
        
    msg = "Events stored: " + str(counter)
        
    return(msg)


def handle_families(collection, tx):
    # Get all the families in the collection
    families = collection.getElementsByTagName("family")
    
    print ("*****Families*****")
    counter = 0
    
    # Print detail of each family
    for family in families:
        
        f = Family()
        
        if family.hasAttribute("handle"):
            f.handle = family.getAttribute("handle")
        if family.hasAttribute("change"):
            f.change = family.getAttribute("change")
        if family.hasAttribute("id"):
            f.id = family.getAttribute("id")
    
        if len(family.getElementsByTagName('rel') ) == 1:
            family_rel = family.getElementsByTagName('rel')[0]
            if family_rel.hasAttribute("type"):
                f.rel_type = family_rel.getAttribute("type")
        elif len(family.getElementsByTagName('rel') ) > 1:
            print("Error: More than one rel tag in a family")
    
        if len(family.getElementsByTagName('father') ) == 1:
            family_father = family.getElementsByTagName('father')[0]
            if family_father.hasAttribute("hlink"):
                f.father = family_father.getAttribute("hlink")
        elif len(family.getElementsByTagName('father') ) > 1:
            print("Error: More than one father tag in a family")
    
        if len(family.getElementsByTagName('mother') ) == 1:
            family_mother = family.getElementsByTagName('mother')[0]
            if family_mother.hasAttribute("hlink"):
                f.mother = family_mother.getAttribute("hlink")
        elif len(family.getElementsByTagName('mother') ) > 1:
            print("Error: More than one mother tag in a family")
    
        if len(family.getElementsByTagName('eventref') ) >= 1:
            for i in range(len(family.getElementsByTagName('eventref') )):
                family_eventref = family.getElementsByTagName('eventref')[i]
                if family_eventref.hasAttribute("hlink"):
                    f.eventref_hlink.append(family_eventref.getAttribute("hlink"))
                if family_eventref.hasAttribute("role"):
                    f.eventref_role.append(family_eventref.getAttribute("role"))
    
        if len(family.getElementsByTagName('childref') ) >= 1:
            for i in range(len(family.getElementsByTagName('childref') )):
                family_childref = family.getElementsByTagName('childref')[i]
                if family_childref.hasAttribute("hlink"):
                    f.childref_hlink.append(family_childref.getAttribute("hlink"))
                    
        f.save(tx)
        counter += 1
        
    msg = "Families stored: " + str(counter)
        
    return(msg)


def handle_notes(collection, tx):
    # Get all the notes in the collection
    notes = collection.getElementsByTagName("note")

    print ("*****Notes*****")
    counter = 0

    # Print detail of each note
    for note in notes:
        
        n = Note()

        if note.hasAttribute("handle"):
            n.handle = note.getAttribute("handle")
        if note.hasAttribute("change"):
            n.change = note.getAttribute("change")
        if note.hasAttribute("id"):
            n.id = note.getAttribute("id")
        if note.hasAttribute("priv"):
            n.priv = note.getAttribute("priv")
        if note.hasAttribute("type"):
            n.type = note.getAttribute("type")
    
        if len(note.getElementsByTagName('text') ) == 1:
            note_text = note.getElementsByTagName('text')[0]
            n.text = note_text.childNodes[0].data
            
        n.save(tx)
        counter += 1
        
    msg = "Notes stored: " + str(counter)
        
    return(msg)


def handle_objects(collection, tx):
    # Get all the objects in the collection
    objects = collection.getElementsByTagName("object")

    print ("*****Objects*****")
    counter = 0

    # Print detail of each object
    for obj in objects:
        
        o = Object()

        if obj.hasAttribute("handle"):
            o.handle = obj.getAttribute("handle")
        if obj.hasAttribute("change"):
            o.change = obj.getAttribute("change")
        if obj.hasAttribute("id"):
            o.id = obj.getAttribute("id")
            
        if len(obj.getElementsByTagName('file') ) == 1:
            obj_file = obj.getElementsByTagName('file')[0]
                
            if obj_file.hasAttribute("src"):
                o.src = obj_file.getAttribute("src")
            if obj_file.hasAttribute("mime"):
                o.mime = obj_file.getAttribute("mime")
            if obj_file.hasAttribute("description"):
                o.description = obj_file.getAttribute("description")
    
        o.save(tx)
        counter += 1
        
    msg = "Objects stored: " + str(counter)
        
    return(msg)


def handle_people(collection, userid, tx):
    # Get all the people in the collection
    people = collection.getElementsByTagName("person")
    
    print ("*****People*****")
    counter = 0
    
    # Print detail of each person
    for person in people:
        
        p = Person()

        if person.hasAttribute("handle"):
            p.handle = person.getAttribute("handle")
        if person.hasAttribute("change"):
            p.change = person.getAttribute("change")
        if person.hasAttribute("id"):
            p.id = person.getAttribute("id")
        if person.hasAttribute("priv"):
            p.priv = person.getAttribute("priv")
    
        if len(person.getElementsByTagName('gender') ) == 1:
            person_gender = person.getElementsByTagName('gender')[0]
            p.gender = person_gender.childNodes[0].data
        elif len(person.getElementsByTagName('gender') ) > 1:
            print("Error: More than one gender tag in a person")
    
        if len(person.getElementsByTagName('name') ) >= 1:
            for i in range(len(person.getElementsByTagName('name') )):
                person_name = person.getElementsByTagName('name')[i]
                pname = Name()
                if person_name.hasAttribute("alt"):
                    pname.alt = person_name.getAttribute("alt")
                if person_name.hasAttribute("type"):
                    pname.type = person_name.getAttribute("type")
    
                if len(person_name.getElementsByTagName('first') ) == 1:
                    person_first = person_name.getElementsByTagName('first')[0]
                    if len(person_first.childNodes) == 1:
                        pname.firstname = person_first.childNodes[0].data
                    elif len(person_first.childNodes) > 1:
                        print("Error: More than one child node in a first name of a person")
                elif len(person_name.getElementsByTagName('first') ) > 1:
                    print("Error: More than one first name in a person")
    
                if len(person_name.getElementsByTagName('surname') ) == 1:
                    person_surname = person_name.getElementsByTagName('surname')[0]
                    if len(person_surname.childNodes ) == 1:
                        pname.surname = person_surname.childNodes[0].data
                    elif len(person_surname.childNodes) > 1:
                        print("Error: More than one child node in a surname of a person")
                elif len(person_name.getElementsByTagName('surname') ) > 1:
                    print("Error: More than one surname in a person")
    
                if len(person_name.getElementsByTagName('suffix') ) == 1:
                    person_suffix = person_name.getElementsByTagName('suffix')[0]
                    pname.suffix = person_suffix.childNodes[0].data
                elif len(person_name.getElementsByTagName('suffix') ) > 1:
                    print("Error: More than one suffix in a person")
                    
                p.names.append(pname)
    
        if len(person.getElementsByTagName('eventref') ) >= 1:
            for i in range(len(person.getElementsByTagName('eventref') )):
                person_eventref = person.getElementsByTagName('eventref')[i]
                if person_eventref.hasAttribute("hlink"):
                    p.eventref_hlink.append(person_eventref.getAttribute("hlink"))
                if person_eventref.hasAttribute("role"):
                    p.eventref_role.append(person_eventref.getAttribute("role"))
                    
        if len(person.getElementsByTagName('objref') ) >= 1:
            for i in range(len(person.getElementsByTagName('objref') )):
                person_objref = person.getElementsByTagName('objref')[i]
                if person_objref.hasAttribute("hlink"):
                    p.objref_hlink.append(person_objref.getAttribute("hlink"))
                    
        if len(person.getElementsByTagName('url') ) >= 1:
            for i in range(len(person.getElementsByTagName('url') )):
                person_url = person.getElementsByTagName('url')[i]
                if person_url.hasAttribute("priv"):
                    p.url_priv.append(person_url.getAttribute("priv"))
                if person_url.hasAttribute("href"):
                    p.url_href.append(person_url.getAttribute("href"))
                if person_url.hasAttribute("type"):
                    p.url_type.append(person_url.getAttribute("type"))
                if person_url.hasAttribute("description"):
                    p.url_description.append(person_url.getAttribute("description"))
                    
        if len(person.getElementsByTagName('parentin') ) >= 1:
            for i in range(len(person.getElementsByTagName('parentin') )):
                person_parentin = person.getElementsByTagName('parentin')[i]
                if person_parentin.hasAttribute("hlink"):
                    p.parentin_hlink.append(person_parentin.getAttribute("hlink"))
    
        if len(person.getElementsByTagName('citationref') ) >= 1:
            for i in range(len(person.getElementsByTagName('citationref') )):
                person_citationref = person.getElementsByTagName('citationref')[i]
                if person_citationref.hasAttribute("hlink"):
                    p.citationref_hlink.append(person_citationref.getAttribute("hlink"))
                    
        p.save(userid, tx)
        counter += 1
        
        # There can be so many individs to store that Cypher needs a pause
        # time.sleep(0.1)
        
    msg = "People stored: " + str(counter)
        
    return(msg)



def handle_places(collection, tx):
    # Get all the places in the collection
    places = collection.getElementsByTagName("placeobj")
    
    print ("*****Places*****")
    counter = 0
    
    # Print detail of each placeobj
    for placeobj in places:
        
        place = Place()

        if placeobj.hasAttribute("handle"):
            place.handle = placeobj.getAttribute("handle")
        if placeobj.hasAttribute("change"):
            place.change = placeobj.getAttribute("change")
        if placeobj.hasAttribute("id"):
            place.id = placeobj.getAttribute("id")
        if placeobj.hasAttribute("type"):
            place.type = placeobj.getAttribute("type")
    
        if len(placeobj.getElementsByTagName('ptitle') ) == 1:
            placeobj_ptitle = placeobj.getElementsByTagName('ptitle')[0]
            place.ptitle = placeobj_ptitle.childNodes[0].data
        elif len(placeobj.getElementsByTagName('ptitle') ) > 1:
            print("Error: More than one ptitle in a place")
    
        if len(placeobj.getElementsByTagName('pname') ) >= 1:
            for i in range(len(placeobj.getElementsByTagName('pname') )):
                placeobj_pname = placeobj.getElementsByTagName('pname')[i]
                if placeobj_pname.hasAttribute("value"):
                    place.pname = placeobj_pname.getAttribute("value")
    
        if len(placeobj.getElementsByTagName('coord') ) >= 1:
            for i in range(len(placeobj.getElementsByTagName('coord') )):
                placeobj_coord = placeobj.getElementsByTagName('coord')[i]
                if placeobj_coord.hasAttribute("long"):
                    place.coord_long = placeobj_coord.getAttribute("long")
                if placeobj_coord.hasAttribute("lat"):
                    place.coord_lat = placeobj_coord.getAttribute("lat")
                    
        if len(placeobj.getElementsByTagName('url') ) >= 1:
            for i in range(len(placeobj.getElementsByTagName('url') )):
                placeobj_url = placeobj.getElementsByTagName('url')[i]
                if placeobj_url.hasAttribute("priv"):
                    place.url_priv.append(placeobj_url.getAttribute("priv"))
                if placeobj_url.hasAttribute("href"):
                    place.url_href.append(placeobj_url.getAttribute("href"))
                if placeobj_url.hasAttribute("type"):
                    place.url_type.append(placeobj_url.getAttribute("type"))
                if placeobj_url.hasAttribute("description"):
                    place.url_description.append(placeobj_url.getAttribute("description"))
    
        if len(placeobj.getElementsByTagName('placeref') ) == 1:
            placeobj_placeref = placeobj.getElementsByTagName('placeref')[0]
            if placeobj_placeref.hasAttribute("hlink"):
                place.placeref_hlink = placeobj_placeref.getAttribute("hlink")
        elif len(placeobj.getElementsByTagName('placeref') ) > 1:
            print("Error: More than one placeref in a place")
                
        place.save(tx)
        counter += 1
        
        # There can be so many individs to store that Cypher needs a pause
        # time.sleep(0.1)
        
    msg = "Places stored: " + str(counter)
        
    return(msg)


def handle_repositories(collection, tx):
    # Get all the repositories in the collection
    repositories = collection.getElementsByTagName("repository")
    
    print ("*****Repositories*****")
    counter = 0
    
    # Print detail of each repository
    for repository in repositories:
        
        r = Repository()

        if repository.hasAttribute("handle"):
            r.handle = repository.getAttribute("handle")
        if repository.hasAttribute("change"):
            r.change = repository.getAttribute("change")
        if repository.hasAttribute("id"):
            r.id = repository.getAttribute("id")
    
        if len(repository.getElementsByTagName('rname') ) == 1:
            repository_rname = repository.getElementsByTagName('rname')[0]
            r.rname = repository_rname.childNodes[0].data
        elif len(repository.getElementsByTagName('rname') ) > 1:
            print("Error: More than one rname in a repository")
    
        if len(repository.getElementsByTagName('type') ) == 1:
            repository_type = repository.getElementsByTagName('type')[0]
            r.type =  repository_type.childNodes[0].data
        elif len(repository.getElementsByTagName('type') ) > 1:
            print("Error: More than one type in a repository")
            
        if len(repository.getElementsByTagName('url') ) >= 1:
            for i in range(len(repository.getElementsByTagName('url') )):
                repository_url = repository.getElementsByTagName('url')[i]
                if repository_url.hasAttribute("href"):
                    r.url_href.append(repository_url.getAttribute("href"))
                if repository_url.hasAttribute("type"):
                    r.url_type.append(repository_url.getAttribute("type"))
                if repository_url.hasAttribute("description"):
                    r.url_description.append(repository_url.getAttribute("description"))
    
        r.save(tx)
        counter += 1
                
    msg = "Repositories stored: " + str(counter)
        
    return(msg)


def handle_sources(collection, tx):
    # Get all the sources in the collection
    sources = collection.getElementsByTagName("source")
    
    print ("*****Sources*****")
    counter = 0
    
    # Print detail of each source
    for source in sources:
    
        s = Source()

        if source.hasAttribute("handle"):
            s.handle = source.getAttribute("handle")
        if source.hasAttribute("change"):
            s.change = source.getAttribute("change")
        if source.hasAttribute("id"):
            s.id = source.getAttribute("id")
    
        if len(source.getElementsByTagName('stitle') ) == 1:
            source_stitle = source.getElementsByTagName('stitle')[0]
            s.stitle = source_stitle.childNodes[0].data
        elif len(source.getElementsByTagName('stitle') ) > 1:
            print("Error: More than one stitle in a source")
    
        if len(source.getElementsByTagName('noteref') ) == 1:
            source_noteref = source.getElementsByTagName('noteref')[0]
            if source_noteref.hasAttribute("hlink"):
                s.noteref_hlink = source_noteref.getAttribute("hlink")
        elif len(source.getElementsByTagName('noteref') ) > 1:
            print("Error: More than one noteref in a source")
    
        if len(source.getElementsByTagName('reporef') ) == 1:
            source_reporef = source.getElementsByTagName('reporef')[0]
            if source_reporef.hasAttribute("hlink"):
                s.reporef_hlink = source_reporef.getAttribute("hlink")
            if source_reporef.hasAttribute("medium"):
                s.reporef_medium = source_reporef.getAttribute("medium")
        elif len(source.getElementsByTagName('reporef') ) > 1:
            print("Error: More than one reporef in a source")
    
        s.save(tx)
        counter += 1
        
    msg = "Sources stored: " + str(counter)
        
    return(msg)


def xml_to_neo4j(pathname, userid='Taapeli'):
    """ Lukee xml-tiedostosta aineiston, ja tallettaa kustakin syöttörivistä
         tiedot Neo4j-kantaan
    """
    
    # Make a precheck
    a = pathname.split(".")
    pathname2 = a[0] + "_pre." + a[1]
    
    file1 = open(pathname)
    file2 = open(pathname2, "w")
    
    for line in file1:
        # Already \' in line
        if line.find("\\\'") > 0:
            line2 = line
        else:
            # Replace ' with \'
            line2 = line.replace("\'", "\\\'")
        file2.write(line2)
        
    file1.close()
    file2.close()

    
    DOMTree = xml.dom.minidom.parse(open(pathname2))
    collection = DOMTree.documentElement
    
    msg = []
    
    # Create User if needed
    user = User(userid)
    user.save()

    msg.append("XML file stored to Neo4j database:")

    
    tx = user.beginTransaction()
    result = handle_notes(collection, tx)
    user.endTransaction(tx)
    msg.append(str(result))
    print(str(result))
    tx = user.beginTransaction()
    result = handle_repositories(collection, tx)
    user.endTransaction(tx)
    msg.append(str(result))
    print(str(result))
    tx = user.beginTransaction()
    result = handle_objects(collection, tx)
    user.endTransaction(tx)
    msg.append(str(result))
    print(str(result))
    tx = user.beginTransaction()
    result = handle_places(collection, tx)
    user.endTransaction(tx)
    msg.append(str(result))
    print(str(result))
    tx = user.beginTransaction()
    result = handle_sources(collection, tx)
    user.endTransaction(tx)
    msg.append(str(result))
    print(str(result))
    tx = user.beginTransaction()
    result = handle_citations(collection, tx)
    user.endTransaction(tx)
    msg.append(str(result))
    print(str(result))
    tx = user.beginTransaction()
    result = handle_events(collection, userid, tx)
    user.endTransaction(tx)
    msg.append(str(result))
    print(str(result))
    tx = user.beginTransaction()
    result = handle_people(collection, userid, tx)
    user.endTransaction(tx)
    msg.append(str(result))
    print(str(result))
    tx = user.beginTransaction()
    result = handle_families(collection, tx)
    user.endTransaction(tx)
    msg.append(str(result))
    print(str(result))
    
    return(msg)    
        
