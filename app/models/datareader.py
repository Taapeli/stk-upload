# coding=UTF-8
#
# Methods to process stk data using methods from models.gen
#
# Taapeli harjoitustyö @ Sss 2016
# JMä 12.1.2016

import logging
import time
from sys import stderr

from flask_babelex import _

from operator import itemgetter
#from models.dbutil import Datefrom
from models.gen.event import Event
from models.gen.event_combo import Event_combo
from models.gen.family import Family, Family_for_template
from models.gen.note import Note
from models.gen.media import Media
from models.gen.person_combo import Person_combo, Person_as_member
from models.gen.person_name import Name
from models.gen.place import Place
from models.gen.refname import Refname
from models.gen.citation import Citation, NodeRef
from models.gen.source import Source
from models.gen.repository import Repository
from models.gen.weburl import Weburl
from models.gen.dates import DateRange


def read_persons_with_events(keys=None, user=None, take_refnames=False, order=0):
    """ Reads Person Name and Event objects for display.
        If currentuser is defined, restrict to her objects.

        Returns Person objects, whith included Events and Names 
        and optionally Refnames

        NOTE. Called with 
            keys = ('uniq_id', uid)     in bp.scene.routes.show_person_list
            keys = ('refname', refname) in bp.scene.routes.show_persons_by_refname
            keys = ('all',)             in bp.scene.routes.show_all_persons_list
            
            keys = None                 in routes.show_table_data
            keys = ['surname',value]    in routes.pick_selection
            keys = ("uniq_id",value)    in routes.pick_selection
    """

    persons = []
    p = None
    p_uniq_id = None
    result = Person_combo.get_person_combos(keys, user, take_refnames=take_refnames, order=order)
    for record in result:
        '''
        # <Record 
            person=<Node id=80307 labels={'Person'} 
                properties={'id': 'I0119', 'confidence': '2.5', 'gender': 'F', 
                     'change': 1507492602, 'handle': '_da692a09bac110d27fa326f0a7', 'priv': ''}> 
            name=<Node id=80308 labels={'Name'} 
                properties={'type': 'Birth Name', 'suffix': '', 'alt': '', 
                    'surname': 'Klick', 'firstname': 'Brita Helena'}> 
            refnames=['Helena', 'Brita', 'Klick'] 
            events=[['Primary', <Node id=88532 labels={'Event'} 
                properties={'date1': 1754183, 'id': 'E0161', 'attr_type': '', 
                    'date2': 1754183, 'attr_value': '', 'description': '', 
                    'datetype': 0, 'change': 1500907890, 
                    'handle': '_da692d0fb975c8e8ae9c4986d23', 'type': 'Birth'}>,
                'Kangasalan srk'], ...] 
            initial='K'>
        '''
        # Person

        node = record['person']
        if node.id != p_uniq_id:
            # The same person is not created again
            p = Person_combo.from_node(node)
            p_uniq_id = p.uniq_id
            if take_refnames and record['refnames']:
                refnlist = sorted(record['refnames'])
                p.refnames = ", ".join(refnlist)
        node = record['name']
        pname = Name.from_node(node)
        if 'initial' in record and record['initial']:
            pname.initial = record['initial']
        p.names.append(pname)

        # Events

        for role, event, place in record['events']:
            # role = 'Primary', 
            # event = <Node id=88532 labels={'Event'} 
            #        properties={'attr_value': '', 'description': '', 'attr_type': '', 
            #        'datetype': 0, 'date2': 1754183, 'type': 'Birth', 'change': 1500907890, 
            #        'handle': '_da692d0fb975c8e8ae9c4986d23', 'id': 'E0161', 'date1': 1754183}>, 
            # place = None

            if event:
                e = Event_combo.from_node(event)
                e.place = place or ""  
                e.role = role or ""
                p.events.append(e)

#TODO:    p.est_birth = record['est_birth']
#         p.est_death = record['est_death']

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
        e = Event_combo()
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
            if c.source_handle != '':
                s = Source()
                s.uniq_id = c.source_handle
                result_source = s.get_source_data()
                for record_source in result_source:
                    if record_source['stitle']:
                        s.stitle = record_source['stitle']
                        
                    s.get_reporef_hlink()
                    if s.reporef_hlink != '':

                        r = Repository()
                        r.uniq_id = s.reporef_hlink
                        result_repo = r.get_repo_w_urls()
                        for record_repo in result_repo:
                            if record_repo['rname']:
                                r.rname = record_repo['rname']
                            if record_repo['type']:
                                r.type = record_repo['type']
                            if record_repo['webref']:
                                r.urls.append(Weburl(record_repo))
                        s.repocitory = r

                c.source = s    # s.append(s)
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
    ╒════════╤════════╤════════╤════════╤════════╤═══════╤════════╤════════╕
    │"uniq_id│"rname" │"type"  │"change"│"handle"│"id"   │"sources│"webref"│
    │"       │        │        │        │        │       │"       │        │
    ╞════════╪════════╪════════╪════════╪════════╪═══════╪════════╪════════╡
    │25979   │"Haminan│"Library│"1526233│"_de18a0│"R0000"│[[25992,│[[...], │
    │        │ kaupung│"       │479"    │b2d546e2│       │"Haminan│]       │
    │        │inarkist│        │        │22251e54│       │ asukasl│        │
    │        │o"      │        │        │9f2bd"  │       │uettelo │        │
    │        │        │        │        │        │       │1800-182│        │
    │        │        │        │        │        │       │0","Book│        │
    │        │        │        │        │        │       │"]]     │        │
    └────────┴────────┴────────┴────────┴────────┴───────┴────────┴────────┘
    where "webref" is 
    """    
    titles = ['change', 'handle', 'id', 'rname', 'sources', 'type', 'uniq_id', 'urls']
    repositories = []
    result = Repository.get_w_source(uniq_id)
    for record in result:
        r = Repository()
        r.uniq_id = record['uniq_id']
        r.rname = record['rname'] or ''
        r.change = record['change']
        r.handle = record['handle']
        r.type = record['type'] or ''
        r.id = record['id'] or ''
        for webref in record['webref']:
            wurl = Weburl.from_node(webref)
            if wurl:
                r.urls.append(wurl)

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
    result = Person_combo.get_people_with_same_birthday()
    for record in result:
        new_array = record['ids']
        ids.append(new_array)

    return (ids)


def read_same_deathday(uniq_id=None):
    """ Lukee tietokannasta Person-objektit, joilla on sama kuolinaika, näytettäväksi

    """
    
    ids = []
    result = Person_combo.get_people_with_same_deathday()
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
    try:
        result = Source.get_source_citation(uniq_id)
        # One Source, many Citations
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
    except Exception as err:
        print("Virhe-read_sources: {1} {0}".format(err, uniq_id), file=stderr)

    return (sources)


def read_events_wo_cites():
    """ Lukee tietokannasta Event- objektit, joilta puuttuu viittaus näytettäväksi

    """
    
    headings = []
    titles, events = Event.get_events_wo_citation()
    
    headings.append(_("Event list"))
    headings.append(_("Showing events without source citation"))

    return (headings, titles, events)


def read_events_wo_place():
    """ Lukee tietokannasta Event- objektit, joilta puuttuu paikka näytettäväksi

    """
    
    headings = []
    titles, events = Event.get_events_wo_place()
    
    headings.append(_("Event list"))
    headings.append(_("Showing events without places"))

    return (headings, titles, events)


def read_people_wo_birth():
    """ Lukee tietokannasta Person- objektit, joilta puuttuu syntymätapahtuma
        näytettäväksi

    """
    
    headings = []
    titles, people = Person_combo.get_people_wo_birth()
    
    headings.append(_("Event list"))
    headings.append(_("Showing persons without a birth event"))

    return (headings, titles, people)


def read_old_people_top():
    """ Lukee tietokannasta Person- objektit, joilla syntymä- ja kuolintapahtuma
        näytettäväksi

    """
    
    headings = []
    titles, people = Person_combo.get_old_people_top()
    
    sorted_people = sorted(people, key=itemgetter(7), reverse=True)
    top_of_sorted_people = []
    for i in range(20 if len(sorted_people) > 19 else len(sorted_people)):
        top_of_sorted_people.append(sorted_people[i])
    
    headings.append(_("Event list"))
    headings.append(_("Showing oldest persons and their age"))

    return (headings, titles, top_of_sorted_people)


def read_places():
    """ Lukee tietokannasta Place- objektit näytettäväksi

    """
    
    headings = []
    titles, events = Place.get_my_places()
    
    headings.append(_("List of places"))
    headings.append(_("Showing places"))

    return (headings, titles, events)


def get_source_with_events(sourceid):
    """ Lukee tietokannasta Source- objektin tapahtumat näytettäväksi
    """
    
    s = Source()
    s.uniq_id = int(sourceid)
    result = s.get_source_data()
    for record in result:
        s.stitle = record["stitle"]
    result = Source.get_citating_nodes(sourceid)

    citations = {}
    persons = dict()    # {uniq_id: clearname}
    
    for record in result:               # Nodes record
        # Example: Person directly linked to Citation
        # <Record c_id=89359 
        #         c=<Node id=89359 labels={'Citation'} 
        #            properties={'id': 'C1361', 'confidence': '2', 
        #                        'page': '1891 Syyskuu 22', 
        #                        'handle': '_dd7686926d946cd18c5642e61e2', 
        #                        'dateval': '', 'change': 1521882215} > 
        #        x_id=72104 label='Person' 
        #        x=<Node id=72104 labels={'Person'} 
        #           properties={'gender': 'F', 'confidence': '2.0', 'id': 'I1069', 
        #                       'handle': '_dd76810c8e6763f7ea816742a59', 
        #                       'priv': '', 'change': 1521883281}> 
        #        p_id=72104 >

        # Example: Person or Family Event linked to Citation
        # <Record c_id=89824 
        #         c=<Node id=89824 labels={'Citation'} 
        #            properties={'confidence': '2', 'dateval': '', 'change': 1526840499, 
        #                          'handle': '_de2f3ce67264ec83c7136ea12a', 'id': 'C1812', 
        #                          'page': 'Födda 1771 58. kaste'}> 
        #           x_id=81210 label='Event' 
        #           x=<Node id=81210 labels=set() 
        #              properties={'date1': 1813643, 'description': '', 'date2': 1813643, 
        #                          'change': 1527261385, 'attr_type': '', 
        #                          'handle': '_de2f3ce910e6008cd0bbdc05b6d', 'id': 'E3557', 
        #                          'type': 'Birth', 'attr_value': '', 'datetype': 0}>
        #           p_id=73543>

        c_id = record['c_id']
        if c_id not in citations.keys():
            # A new citation
            c = Citation()
            c.uniq_id = c_id
            citations[c_id] = c
        else:
            # Use previous
            c = citations[c_id]

        citation = record['c']
        c.id = citation['id']
        c.page = citation['page']
        c.confidence = citation['confidence']
        
        p_uid = record['p_id']
        x_node = record['x']
        x_uid = x_node.id
        noderef = NodeRef()
        # Referring Person or Family
        noderef.uniq_id = p_uid      # 72104
        noderef.id = x_node['id']  # 'I1069' or 'E2821'
        noderef.label = x_node.labels.pop()
        event_role = record['role']
        
        print('Citation {} {} {} {} {}'.format(c.uniq_id, event_role, 
                                               noderef.label, noderef.uniq_id, noderef.id))

        if event_role == 'Family':  # Family event witch is cdirectply connected to a Person Event
            noderef.label = 'Family Event'
#             couple = Family.get_marriage_parent_names(x_uid)
#             noderef.clearname = " <> ".join(list(couple.values()))
#         else:                       # Person event
        if p_uid not in persons.keys():
            noderef.clearname = Name.get_clearname(noderef.uniq_id)
            persons[noderef.uniq_id] = noderef.clearname
        else:
            noderef.clearname = persons[p_uid]

        if 'Event' in noderef.label:
            # noderef: "Event <event_type> <person p_uid>"
            noderef.eventtype = x_node['type']
            if x_node['date1']:
                noderef.edates = DateRange(x_node['datetype'], x_node['date1'], x_node['date2'])
                noderef.date = noderef.edates.estimate()
#         if noderef.label == 'Person':
#             # noderef: "Person <clearname>"
#             noderef.label = 'Person'
        c.citators.append(noderef)

    return (s.stitle, list(citations.values()))


def read_sources_wo_cites():
    """ Lukee tietokannasta Source- objektit, joilta puuttuu viittaus näytettäväksi

    """
    
    headings = []
    titles, lists = Source.get_sources_wo_citation()
    
    headings.append(_("Source list"))
    headings.append(_("Showing sources without source citations"))

    return (headings, titles, lists)


def read_sources_wo_repository():
    """ Lukee tietokannasta Source- objektit, joilta puuttuu arkisto näytettäväksi

    """
    
    headings = []
    titles, lists = Source.get_sources_wo_repository()
    
    headings.append(_("Source list"))
    headings.append(_("Showing sources without a repository"))

    return (headings, titles, lists)


def get_people_by_surname(surname):
    people = []
    result = Name.get_people_with_surname(surname)
    for record in result:
        p = Person_combo()
        p.uniq_id = record['uniq_id']
        p.get_person_and_name_data_by_id()
        people.append(p)
        
    return (people)


def get_person_data_by_id(uniq_id):
    """ Get 5 data sets:                    ---- vanhempi versio ----
        person: Person object with name data
            The indexes of referred objects are in variables 
                event_ref[]        str tapahtuman uniq_id, rooli eventref_role[]
                media_ref[]        str tallenteen uniq_id
                urls[]                list of Weburl nodes
                    priv           str 1 = salattu tieto
                    href           str osoite
                    type           str tyyppi
                    description    str kuvaus
                parentin_hlink[]   str vanhempien uniq_id
                note_ref[]         str huomautuksen uniq_id
                citation_ref[]     str viittauksen uniq_id            
        events[]         Event_combo  with location name and id (?)
        photos
        citations
        families
    """
    p = Person_combo()
    p.uniq_id = int(uniq_id)
    # Get Person and her Name properties, also Weburl properties 
    p.get_person_w_names()
    # Get reference (uniq_id) and role for Events
    # Get references to Media, Citation objects
    # Get Persons birth family reference and role
    p.get_hlinks_by_id()
    
    # Person_display(Person)
    events = []
    citations = []
    photos = []
    source_cnt = 0
    my_birth_date = ''

    # Events

    for i in range(len(p.event_ref)):
        # Store Event data
        e = Event_combo() # Event_for_template()
        e.uniq_id = p.event_ref[i]
        e.role = p.eventref_role[i]
        # Read event with uniq_id's of related Place (Note, and Citation?)
        e.get_event_combo()        # Read data to e
        if e.type == "Birth":
            my_birth_date = e.date
            
        for ref in e.place_ref:
            place = Place()
            place.uniq_id = ref
            place.get_place_data_by_id()
            # Location / place name, type and reference
            e.location = place.pname
            e.locid = place.uniq_id
            e.ltype = place.type
                    
        if e.note_ref: # A list of uniq_ids; prev. e.noteref_hlink != '':
            # Read the Note objects from db and store them as a member of Event
            e.notes = Note.get_notes(e.note_ref)
                
        events.append(e)

        # Citations

        for ref in e.citation_ref:  # citationref_hlink != '':
            c = Citation()
            c.uniq_id = ref
            # If there is already the same citation on the list of citations,
            # use that index
            citation_ind = -1
            for i in range(len(citations)):
                if citations[i].uniq_id == c.uniq_id:
                    citation_ind = i + 1
                    break
            if citation_ind > 0:
                # Citation found; Event_combo.source = sitaatin numero
                e.source = citation_ind
            else: 
                # Store the new source to the list
                # source = lähteen numero samassa listassa
                source_cnt += 1
                e.source = source_cnt

                result = c.get_source_repo(c.uniq_id)
                for record in result:
                    # Citation data & list of Source, Repository and Note data
                    #
                    # <Record id=92127 date='2017-01-25' page='1785 Novembr 3. kaste' 
                    #    confidence='3' notetext='http://www.sukuhistoria.fi/...' 
                    #    sources=[
                    #        [91360, 
                    #         'Lapinjärvi syntyneet 1773-1787 vol  es346', 
                    #         'Book', 
                    #         100272, 
                    #         'Lapinjärven seurakunnan arkisto', 
                    #         'Archive']
                    #    ]>
                    c.dateval = record['date']
                    c.page = record['page']
                    c.confidence = record['confidence']
                    if not record['notetext']:
                        if c.page[:4] == "http":
                            c.notetext = c.page
                            c.page = ''
                    else: 
                        c.notetext = record['notetext']
                    
                    for source in record['sources']:
                        s = Source()
                        s.uniq_id = source[0]
                        s.stitle = source[1]
                        s.reporef_medium = source[2]
            
                        r = Repository()
                        r.uniq_id = source[3]
                        r.rname = source[4]
                        r.type = source[5]
                        
                        s.repocitory = r
                        c.source = s
        
                    print("Eve:{} {} > Cit:{} '{}' > Sour:{} '{}' > Repo:{} '{}'".\
                          format(e.uniq_id, e.id, c.uniq_id, c.page, s.uniq_id, s.stitle, r.uniq_id, r.rname))
                    citations.append(c)
            
    for link in p.media_ref:
        o = Media()
        o.uniq_id = link
        o.get_data()
        photos.append(o)

    # Families

    # Returning a list of Family objects
    # - which include a list of members (Person with 'role' attribute)
    #   - Person includes a list of Name objects
    families = {}
    fid = 0
    result = Person_combo.get_family_members(p.uniq_id)
    for record in result:
        # <Record family_id='F0296' f_uniq_id=100197 role='CHILD' m_id='I0798' 
        #    uniq_id=63423 gender='M' birth_date=[0, 1769543, 1769543] 
        #    names=[['', 'Birth Name', 'Claës', 'Heidenstrauch', '']]>

        if fid != record["f_uniq_id"]:
            fid = record["f_uniq_id"]
            if not fid in families:
                families[fid] = Family_for_template(fid)
                families[fid].id = record['family_id']

        member = Person_as_member()    # A kind of Person
        member.role = record["role"]
        member.id = record["m_id"]
        member.uniq_id = record["uniq_id"]
        if member.uniq_id == p.uniq_id:
            # What kind of family this is? I am a Child or Parent in family
            if member.role == "CHILD":
                families[fid].role = "CHILD"
            else:
                families[fid].role = "PARENT"
            if my_birth_date:
                member.birth_date = my_birth_date

        if record["gender"]:
            member.gender = record["gender"]
        if record["birth_date"]:
            datetype, date1, date2 = record["birth_date"]
            if datetype != None:
                member.birth_date = DateRange(datetype, date1, date2).estimate()
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

    # Find all referenced for the nodes found so far

    nodes = {p.uniq_id:p}
    for e in events:
        nodes[e.uniq_id] = e
    for e in photos:
        nodes[e.uniq_id] = e
    for e in citations:
        nodes[e.uniq_id] = e
    for e in family_list:
        nodes[e.uniq_id] = e
    #print ("Unique Nodes: {}".format(nodes))
    result = Person_combo.get_ref_weburls(list(nodes.keys()))
    for wu in result:
        print("({} {}) -[{}]-> ({} ({} {}))".\
              format(wu["root"] or '?', wu["root_id"] or '?',
                     wu["rtype"] or '?', wu["label"],
                     wu["target"] or '?', wu["id"] or '?'))
    print("")
        #TODO Talleta Note- ja Citation objektit oikeisiin objekteihin
        #     Perusta objektien kantaluokka Node, jossa muuttujat jäsenten 
        #     tallettamiseen.
        # - Onko talletettava jäsenet vai viitteet niihin? Ei kai ole niin paljon toistoa?

    return (p, events, photos, citations, family_list)


def get_baptism_data(uniq_id):
    
    persons = []
    
    e = Event_combo()
    e.uniq_id = uniq_id
    e.get_event_combo()
    
    if e.place_ref:
        place = Place()
        place.uniq_id = e.place_ref[0]
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
    
    p = Person_combo()
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
            pf = Family()
            pf.uniq_id = record["family_ref"]
            pf.get_family_data_by_id()
            
            father = Person_combo()
            father.uniq_id = pf.father
            father.get_person_and_name_data_by_id()
            f.father = father
            
            mother = Person_combo()
            mother.uniq_id = pf.mother
            mother.get_person_and_name_data_by_id()
            f.mother = mother
        
        spouse = Person_combo()
        if p.gender == 'M':
            spouse.uniq_id = f.mother
        else:
            spouse.uniq_id = f.father
        spouse.get_person_and_name_data_by_id()
        f.spouse = spouse

        for child_id in f.childref_hlink:
            child = Person_combo()
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
    place.uniq_id = loc_id
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

