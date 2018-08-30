# coding=UTF-8
#
# Methods to process stk data using methods from models.gen
#
# Taapeli harjoitustyö @ Sss 2016
# JMä 12.1.2016

import logging
import time

from operator import itemgetter
#from models.dbutil import Datefrom
from models.gen.event import Event
from models.gen.event_combo import Event_combo
from models.gen.family import Family, Family_for_template
from models.gen.note import Note
from models.gen.media import Media
from models.gen.person import Person, Name, Person_as_member
from models.gen.place import Place
from models.gen.refname import Refname
from models.gen.source_citation import Citation, Repository, Source, Weburl
from models.gen.dates import DateRange


def read_persons_with_events(keys=None, user=None, take_refnames=False, order=0):
    """ Reads Person- and Event- objects for display.
        If currentuser is defined, restrict to her objects.

        Returns Person objects, whith included Events
    """
    
    persons = []
    result = Person.get_events_k(keys, user, take_refnames=take_refnames, order=order)
    for record in result:
        # Got ["id", "confidence", "firstname", "refnames", "surname", "suffix", "events"]
        uniq_id = record['id']
        p = Person()
        p.uniq_id = uniq_id
        p.confidence = record['confidence']
        p.est_birth = record['est_birth']
        p.est_death = record['est_death']
        if take_refnames and record['refnames']:
            refnlist = sorted(record['refnames'])
            p.refnames = ", ".join(refnlist)
        pname = Name()
        if record['firstname']:
            pname.firstname = record['firstname']
        if record['surname']:
            pname.surname = record['surname']
        if record['suffix']:
            pname.patronyme = record['suffix']
        if 'initial' in record and record['initial']:
            pname.initial = record['initial']
        p.names.append(pname)
    
        # Events

        for event in record['events']:
            # Got event with place name: [id, type, date, dates, place.pname]
            e = Event_combo()
            e.uniq_id = event[0]
            event_type = event[1]
            if event_type:
                e.type = event_type
                if event[2] != None and isinstance(event[2], int):
                    dates = DateRange(event[2], event[3], event[4])
                    e.dates = str(dates)
                    e.date = dates.estimate()
                else:
                    e.dates = ""
                e.place = event[5]
#                 if e.daterange_start != '' and e.daterange_stop != '':
#                     e.daterange = e.daterange_start + " - " + e.daterange_stop
#                 elif e.daterange_start != '':
#                     e.daterange = str(e.daterange_start) + "-"
#                 elif e.daterange_stop != '':
#                     e.daterange = "-" + str(e.daterange_stop)
                p.events.append(e)
 
        persons.append(p)

    return (persons)


def read_refnames():
    """ Reads all Refname objects for display
        (n:Refname)-[r]->(m)
    """
    namelist = []
    t0 = time.time()
    recs = Refname.get_refnames()
    for rec in recs:
        namelist.append(rec)

    logging.info("TIME get_refnames {} sek".format(time.time()-t0))

    return (namelist)

def recreate_refnames():
    summary = Refname.recreate_refnames()
    return str(summary)


# def read_typed_refnames(reftype):
#     """ Reads selected Refname objects for display
#     """
#     namelist = []
#     t0 = time.time()
#     if not (reftype and reftype != ""):
#         raise AttributeError("Please, select desired reftype?")
#     
#     recs = Refname.get_typed_refnames(reftype)
# # Esimerkki:
# # >>> for x in v_names: print(x)
# # <Record a.oid=3 a.name='Aabi' a.gender=None a.source='harvinainen' 
# #         base=[[2, 'Aapeli', None]] other=[[None, None, None]]>
# # <Record a.oid=5 a.name='Aabraham' a.gender='M' a.source='Pojat 1990-luvulla' 
# #         base=[[None, None, None]] other=[[None, None, None]]>
# # <Record a.oid=6 a.name='Aabrahami' a.gender=None a.source='harvinainen' 
# #         base=[[7, 'Aappo', None]] other=[[None, None, None]]>
# # >>> for x in v_names: print(x[1])
# # Aabrahami
# # Aabrami
# # Aaca
# 
# #a.oid  a.name  a.gender  a.source   base                 other
# #                                     [oid, name, gender]  [oid, name, gender]
# #-----  ------  --------  --------   ----                 -----
# #3493   Aake	F	  Messu- ja  [[null, null, null], [[3495, Aakke, null],
# #                         kalenteri   [null, null, null],  [3660, Acatius, null],
# #                                     [null, null, null],  [3662, Achat, null],
# #                                     [null, null, null],  [3664, Achatius, M],
# #                                     [null, null, null],  [3973, Akatius, null],
# #                                     [null, null, null],  [3975, Ake, null],
# #                                     [null, null, null]]  [3990, Akke, null]]
# #3495   Aakke   null     harvinainen [[3493, Aake, F]]    [[null, null, null]]
# 
#     for rec in recs:
# #        logging.debug("oid={}, name={}, gender={}, source={}, base={}, other={}".\
# #               format( rec[0], rec[1],  rec[2],    rec[3],    rec[4],  rec[5]))
#         # Luodaan nimi
#         r = Refname(rec['a.name'])
#         r.oid = rec['a.id']
#         if rec['a.gender']:
#             r.gender = rec['a.gender']
#         if rec['a.source']:
#             r.source= rec['a.source']
# 
#         # Luodaan mahdollinen kantanimi, johon tämä viittaa (yksi?)
#         baselist = []
#         for fld in rec['base']:
#             if fld[0]:
#                 b = Refname(fld[1])
#                 b.oid = fld[0]
#                 if fld[2]:
#                     b.gender = fld[2]
#                 baselist.append(b)
# 
#         # Luodaan lista muista nimistä, joihin tämä viittaa
#         otherlist = []
#         for fld in rec['other']:
#             if fld[0]:
#                 o = Refname(fld[1])
#                 o.oid = fld[0]
#                 if fld[2]:
#                     o.gender = fld[2]
#                 otherlist.append(o)
# 
#         namelist.append((r,baselist,otherlist))
#     
#     logging.info("TIME get_named_refnames {} sek".format(time.time()-t0))
# 
#     return (namelist)


def read_cite_sour_repo(uniq_id=None):
    """ Lukee tietokannasta Repository-, Source- ja Citation- objektit näytettäväksi

    """
    
    sources = []
    result_cite = Event_combo.get_event_cite(uniq_id)
    for record_cite in result_cite:
        pid = record_cite['id']
        e = Event()
        e.uniq_id = pid
        if record_cite['type']:
            e.type = record_cite['type']
        if record_cite['date']:
            e.date = record_cite['date']
        if record_cite['dates']:
            e.dates = DateRange(record_cite['dates'])

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


def read_medias(uniq_id=None):
    """ Lukee tietokannasta Media- objektit näytettäväksi

    """
    
    media = []
    result = Media.get_medias(uniq_id)
    for record in result:
        pid = record['uniq_id']
        o = Media()
        o.uniq_id = pid
        if record['o']['src']:
            o.src = record['o']['src']
        if record['o']['mime']:
            o.mime = record['o']['mime']
        if record['o']['description']:
            o.description = record['o']['description']
 
        media.append(o)

    return (media)


def get_repositories(uniq_id=None):
    """ Lukee tietokannasta Repository- ja Source- objektit näytettäväksi

        (Korvaa read_repositories()
    """
    
    titles = ['change', 'handle', 'id', 'rname', 'sources', 'type', 'uniq_id', 
              'url_refs']
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
            url = Weburl()
            url.url_href = record['url_href']
            if record['url_type']:
                url.url_type = record['url_type']
            if record['url_description']:
                url.url_description = record['url_description']
            r.url_refs.append(url)

        for source in record['sources']:
            s = Source()
            s.uniq_id = source[0]
            s.stitle = source[1]
            s.reporef_medium = source[2]
            r.sources.append(s)
 
        repositories.append(r)

    return (titles, repositories)


def read_same_birthday(uniq_id=None):
    """ Lukee tietokannasta Person-objektit, joilla on sama syntymäaika, näytettäväksi

    """
    
    ids = []
    result = Person.get_people_with_same_birthday()
    for record in result:
        new_array = record['ids']
        ids.append(new_array)

    return (ids)


def read_same_deathday(uniq_id=None):
    """ Lukee tietokannasta Person-objektit, joilla on sama kuolinaika, näytettäväksi

    """
    
    ids = []
    result = Person.get_people_with_same_deathday()
    for record in result:
        new_array = record['ids']
        ids.append(new_array)

    return (ids)


def read_same_name(uniq_id=None):
    """ Lukee tietokannasta Person-objektit, joilla on sama nimi, näytettäväksi

    """
    
    ids = []
    result = Name.get_people_with_same_name()
    for record in result:
        new_array = record['ids']
        ids.append(new_array)

    return (ids)


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
    for i in range(20 if len(sorted_people) > 19 else len(sorted_people)):
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
                e = Event_combo()
                e.uniq_id = event[0]
                e.type = event[1]
                e.edate = event[2]
                
                for name in event[3]:
                    n = Name()
                    n.uniq_id = name[0]        
                    n.surname = name[1]        
                    n.firstname = name[2]  
                    n.suffix = name[3]  
                        
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
        events list: uniq_id, dates, location name and id (?)
        photos
        sources
        families
    """
    p = Person()
    p.uniq_id = int(uniq_id)
    p.get_person_w_names()
    p.get_hlinks_by_id()
    
    events = []
    sources = []
    source_cnt = 0

    # Events

    for i in range(len(p.eventref_hlink)):
        e = Event_combo() # Event_for_template()
        e.uniq_id = p.eventref_hlink[i]
        e.role = p.eventref_role[i]
        e.get_person_events()        # Read data to e
            
        if e.place_hlink != '':
            place = Place()
            place.uniq_id = e.place_hlink
            place.get_place_data_by_id()
            # Location / place data
            e.location = place.pname
            e.locid = place.uniq_id
            e.ltype = place.type
                    
        if e.note_ref: # A list of uniq_ids; prev. e.noteref_hlink != '':
            # Read the Note objects from db and store them as a member of Event
            e.notes = Note.get_notes(e.note_ref)
                
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
        o = Media()
        o.uniq_id = link
        o.get_data()
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


def get_baptism_data(uniq_id):
    
    persons = []
    
    e = Event_combo()
    e.uniq_id = uniq_id
    e.get_person_events()
    
    if e.place_hlink != '':
        place = Place()
        place.uniq_id = e.place_hlink
        place.get_place_data_by_id()
        # Location / place data
        e.location = place.pname
        e.locid = place.uniq_id
        e.ltype = place.type
        
    result = e.get_baptism_data()
    for record in result:
        p = Person_as_member()
        p.uniq_id = record['person_id']
        p.role = record['role']
        name = record['person_names'][0]
        pname = Name()
        pname.firstname = name[0]
        pname.surname = name[1]
        p.names.append(pname)
        
        persons.append(p)
            
    return (e, persons)


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

        # Person's birth family
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
        edates        event date
    """
    place = Place()
    place.uniq_id = int(loc_id)
    place.get_place_data_by_id()
    place_list = Place.get_place_tree(place.uniq_id)
    event_table = Place.get_place_events(place.uniq_id)
    return (place, place_list, event_table)


def get_note_list(uniq_id=None):
    """ Lukee tietokannasta Note- objektit näytettäväksi
    """
    titles, notes = Note.get_note_list(uniq_id)
    return (titles, notes)


def xml_to_neo4j(pathname, userid='Taapeli'):
    """ See models.gramps.gramps_loader """
    raise RuntimeError("Use the method models.gramps.gramps_loader.xml_to_neo4j")

