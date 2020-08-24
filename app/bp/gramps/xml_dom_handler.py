'''
Extracted from gramps_loader.py on 2.12.2018

    Methods to import all data from Gramps xml file

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

import logging 
logger = logging.getLogger('stkserver')

from collections import defaultdict
import re
import time
import os
import xml.dom.minidom

from flask_babelex import _

import shareds
from .models.person_gramps import Person_gramps
from .models.event_gramps import Event_gramps
from .models.family_gramps import Family_gramps
from .models.source_gramps import Source_gramps
from .models.place_gramps import Place_gramps
from bl.place import PlaceName
from bl.place_coordinates import Point
from bl.media import MediaRefResult

from .batchlogger import Log

from models.cypher_gramps import Cypher_mixed
from models.gen.dates import Gramps_DateRange
from models.gen.note import Note
from models.gen.media import Media
from models.gen.person_name import Name
from models.gen.person_combo import Person_combo
from models.gen.citation import Citation
from models.gen.repository import Repository

from models import dataupdater
import threading


def pick_url(src):
    ''' Extract an url from the text src, if any
    
        Returns (text, url), where the url is removed from text
    '''
    #TODO: Jos url päättyy merkkeihin '").,' ne tulee poistaa ja siirrää end-tekstiin
    #TODO: Pitäsikö varautua siihen että tekstikenttä sisältää monta url:ia?

    match = re.search("(?P<url>https?://[^\s'\"]+)", src)
    url = None
    text = src
    if match is not None:
        url = match.group("url")
        start = match.start()
        end = match.end()
#         start = ''   if start == 0
#         end = ''     if end == len(src) - 1:
#         print("[{}:{}] url='{}'".format(start, end, url))
        text = ''
        if start:
            text = src[:start]
        if end < len(src):
            text = "{}{}".format(text, src[end:])
#         if text:
#             print("    '{}'".format(text.rstrip()))
#     elif len(src) > 0 and not src.isspace():
#         print("{} ...".format(src[:72].rstrip()))

    return (text.rstrip(), url)

def get_priv(dom_obj):
    ''' Gives priv property value as int, if it is not '0'
    '''
    if dom_obj.hasAttribute("priv"):
        priv = int(dom_obj.getAttribute("priv"))
        if priv:
            return priv
    return None


class DOM_handler():
    """ XML DOM elements handler
        - creates transaction
        - processes different data groups from given xml file to database
        - collects status log
    """

    class dbKeys():
        ''' Stores the keys connecting an xml object to db node.
        '''
        def __init__(self, uuid=None, uniq_id=None):
            self.uuid = uuid
            self.uniq_id = uniq_id

        def __str__(self):
            return f'dbKeys({self.uuid[:6]},{self.uniq_id})'


    def __init__(self, infile, current_user, pathname=""):
        """ Set DOM collection and username """
        DOMTree = xml.dom.minidom.parse(open(infile, encoding='utf-8'))
        self.collection = DOMTree.documentElement    # XML documentElement
        self.username = current_user        # current username

        self.handle_to_node = {}            # dbKeys(uuid, uniq_id)
        self.person_ids = []                # List of processed Person node unique id's
        self.family_ids = []                # List of processed Family node unique id's
        self.tx = None                      # Transaction not opened
        self.batch_id = None
        self.file = os.path.basename(pathname) # for messages
        self.progress = defaultdict(int)    # key=object type, value=count of objects processed

    def begin_tx(self, session):
        self.tx = session.begin_transaction()
        print("Transaction started")

    def commit(self, rollback=False):
        """ Commit or rollback transaction """
        if rollback:
            self.tx.rollback()
            print("Transaction discarded")
            logger.info(f'-> bp.gramps.xml_dom_handler.DOM_handler.commit/rollback f="{self.file}"')
            self.blog.log_event({'title': _("Database save failed"), 'level':"ERROR"})
            return

        if self.tx.closed():
            print("Transaction already closed!")
        else:
            try:
                self.tx.commit()
                logger.info(f'-> bp.gramps.xml_dom_handler.DOM_handler.commit/ok f="{self.file}"')
                print("Transaction committed")
            except Exception as e:
                logger.info(f'-> bp.gramps.xml_dom_handler.DOM_handler.commit/fail f="{self.file}"')
                print("Transaction failed")
                self.blog.log_event({'title':_("Database save failed due to {} {}".\
                                     format(e.__class__.__name__, e)), 'level':"ERROR"})

    def remove_handles(self):
#         print("remove_handles NOT DONE!")
#         return
        total = 0
        results = self.tx.run(Cypher_mixed.remove_handles, batch_id=self.batch_id)
        for count, label in results:
            print(f'# - cleaned {count} {label} handles')
            total += count
        print (f'# --- removed handle from {total} nodes')


    def add_missing_links(self):
        ''' Link the Nodes without OWNS link to Batch
        '''
        result = self.tx.run(Cypher_mixed.add_links, batch_id=self.batch_id)
        counters = shareds.db.consume_counters(result)
        if counters.relationships_created:
            print(f"Created {counters.relationships_created} relations")

    def set_mediapath(self, path):
        ''' Store media files path. '''
        self.tx.run(Cypher_mixed.set_mediapath, 
                    batch_id=self.batch_id, path=path)

    def update_progress(self, key):
        self.progress[key] += 1
        this_thread = threading.current_thread()
        this_thread.progress = dict(self.progress)

    def save_and_link_handle(self, e, **kwargs):
        ''' Save object and store its identifiers in the dictionary by handle.

            Some objects may accept arguments like batch_id="2019-08-26.004" and others
        '''
        e.save(self.tx, **kwargs)
        self.handle_to_node[e.handle] = self.dbKeys(e.uuid, e.uniq_id)
        self.update_progress(e.__class__.__name__)

   
    # ---------------------   XML subtree handlers   --------------------------

    def handle_header(self):
        ''' Store eventuel media path from XML header to Batch node.
        '''
        for header in self.collection.getElementsByTagName("header"):
            for mediapath in header.getElementsByTagName("mediapath"):
                if (len(mediapath.childNodes) > 0):
                    path = mediapath.childNodes[0].data
                    self.set_mediapath(path)
                    return
        self.set_mediapath("")


    def handle_citations(self):
        # Get all the citations in the collection
        citations = self.collection.getElementsByTagName("citation")

        print ("***** {} Citations *****".format(len(citations)))
        t0 = time.time()
        counter = 0

        # Print detail of each citation
        for citation in citations:

            c = Citation()
            # Extract handle, change and id
            self._extract_base(citation, c)

            try:
                # type Gramps_DateRange or None
                c.dates = self._extract_daterange(citation)
            except:
                c.dates = None
#             if len(citation.getElementsByTagName('dateval') ) == 1:
#                 citation_dateval = citation.getElementsByTagName('dateval')[0]
#                 if citation_dateval.hasAttribute("val"):
#                     c.dateval = citation_dateval.getAttribute("val")
#             elif len(citation.getElementsByTagName('dateval') ) > 1:
#                 self.blog.log_event({'title':"More than one dateval tag in a citation",
#                                      'level':"WARNING", 'count':c.id})

            if len(citation.getElementsByTagName('page') ) == 1:
                citation_page = citation.getElementsByTagName('page')[0]
                c.page = citation_page.childNodes[0].data
            elif len(citation.getElementsByTagName('page') ) > 1:
                self.blog.log_event({'title':"More than one page tag in a citation",
                                     'level':"WARNING", 'count':c.id})

            if len(citation.getElementsByTagName('confidence') ) == 1:
                citation_confidence = citation.getElementsByTagName('confidence')[0]
                c.confidence = citation_confidence.childNodes[0].data
            elif len(citation.getElementsByTagName('confidence') ) > 1:
                self.blog.log_event({'title':"More than one confidence tag in a citation",
                                     'level':"WARNING", 'count':c.id})

            for citation_noteref in citation.getElementsByTagName('noteref'):
                if citation_noteref.hasAttribute("hlink"):
                    c.noteref_hlink.append(citation_noteref.getAttribute("hlink"))
                    ##print(f'# Citation {c.id} has note {c.noteref_hlink[-1]}')

            if len(citation.getElementsByTagName('sourceref') ) == 1:
                citation_sourceref = citation.getElementsByTagName('sourceref')[0]
                if citation_sourceref.hasAttribute("hlink"):
                    c.source_handle = citation_sourceref.getAttribute("hlink")
                    ##print(f'# Citation {c.id} points source {c.source_handle}')
            elif len(citation.getElementsByTagName('sourceref') ) > 1:
                self.blog.log_event({'title':"More than one sourceref tag in a citation",
                                     'level':"WARNING",'count':c.id})

            self.save_and_link_handle(c, batch_id=self.batch_id)
            counter += 1

        self.blog.log_event({'title':"Citations", 'count':counter, 
                             'elapsed':time.time()-t0}) #, 'percent':1})


    def handle_events(self):
        ''' Get all the events in the collection '''
        events = self.collection.getElementsByTagName("event")

        print ("***** {} Events *****".format(len(events)))
        t0 = time.time()
        counter = 0

        # Print detail of each event
        for event in events:
            # Create an event with Gramps attributes
            e = Event_gramps()
            # Extract handle, change and id
            self._extract_base(event, e)

            if len(event.getElementsByTagName('type') ) == 1:
                event_type = event.getElementsByTagName('type')[0]
                # If there are type tags, but no type data
                if (len(event_type.childNodes) > 0):
                    e.type = event_type.childNodes[0].data
                else:
                    e.type = ''
            elif len(event.getElementsByTagName('type') ) > 1:
                self.blog.log_event({'title':"More than one type tag in an event",
                                     'level':"WARNING", 'count':e.id})

            if len(event.getElementsByTagName('description') ) == 1:
                event_description = event.getElementsByTagName('description')[0]
                # If there are description tags, but no description data
                if (len(event_description.childNodes) > 0):
                    e.description = event_description.childNodes[0].data
            elif len(event.getElementsByTagName('description') ) > 1:
                self.blog.log_event({'title':"More than one description tag in an event",
                                     'level':"WARNING", 'count':e.id})

            try:
                # Returns Gramps_DateRange or None
                e.dates = self._extract_daterange(event)
                #TODO: val="1700-luvulla" muunnettava Noteksi
            except:
                e.dates = None

            if len(event.getElementsByTagName('place') ) == 1:
                event_place = event.getElementsByTagName('place')[0]
                if event_place.hasAttribute("hlink"):
                    e.place_hlink = event_place.getAttribute("hlink")
                    ##print(f'# Event {e.id} is located in {e.place_hlink}')
            elif len(event.getElementsByTagName('place') ) > 1:
                self.blog.log_event({'title':"More than one place tag in an event",
                                     'level':"WARNING", 'count':e.id})

            e.attr = dict()
            for attr in event.getElementsByTagName('attribute'):
                if attr.hasAttribute("type"):
                    e.attr[attr.getAttribute("type")] = attr.getAttribute("value")

            for ref in event.getElementsByTagName('noteref'):
                if ref.hasAttribute("hlink"):
                    e.note_handles.append(ref.getAttribute("hlink"))
                    ##print(f'# Event {e.id} has note {e.note_handles[-1]}')

            for ref in event.getElementsByTagName('citationref'):
                if ref.hasAttribute("hlink"):
                    e.citation_handles.append(ref.getAttribute("hlink"))
                    ##print(f'# Event {e.id} has cite {e.citation_handles[-1]}')

            # Handle <objref> with citations and notes
            e.media_refs = self._extract_mediaref(event)

            try:
                self.save_and_link_handle(e, batch_id=self.batch_id)
                counter += 1
            except RuntimeError as e:
                self.blog.log_event({'title':"Events", 'count':counter, 
                             'level':"ERROR", 'elapsed':time.time()-t0}) #, 'percent':1})
                raise
                
        self.blog.log_event({'title':"Events", 'count':counter, 
                             'elapsed':time.time()-t0}) #, 'percent':1})


    def handle_families(self):
        ''' Get all the families in the collection. '''
        families = self.collection.getElementsByTagName("family")

        print ("***** {} Families *****".format(len(families)))
        t0 = time.time()
        counter = 0

        # Print detail of each family
        for family in families:

            f = Family_gramps()
            # Extract handle, change and id
            self._extract_base(family, f)

            if len(family.getElementsByTagName('rel') ) == 1:
                family_rel = family.getElementsByTagName('rel')[0]
                if family_rel.hasAttribute("type"):
                    f.rel_type = family_rel.getAttribute("type")
            elif len(family.getElementsByTagName('rel') ) > 1:
                self.blog.log_event({'title':"More than one rel tag in a family",
                                     'level':"WARNING", 'count':f.id})

            if len(family.getElementsByTagName('father') ) == 1:
                family_father = family.getElementsByTagName('father')[0]
                if family_father.hasAttribute("hlink"):
                    f.father = family_father.getAttribute("hlink")
                    ##print(f'# Family {f.id} has father {f.father}')
            elif len(family.getElementsByTagName('father') ) > 1:
                self.blog.log_event({'title':"More than one father tag in a family",
                                     'level':"WARNING", 'count':f.id})

            if len(family.getElementsByTagName('mother') ) == 1:
                family_mother = family.getElementsByTagName('mother')[0]
                if family_mother.hasAttribute("hlink"):
                    f.mother = family_mother.getAttribute("hlink")
                    ##print(f'# Family {f.id} has mother {f.mother}')
            elif len(family.getElementsByTagName('mother') ) > 1:
                self.blog.log_event({'title':"More than one mother tag in a family",
                                     'level':"WARNING", 'count':f.id})

#TODO: Yhdistä kentät eventref_hlink ja eventref_role kentiksi eventref [(handle, role)] ?
            for ref in family.getElementsByTagName('eventref'):
                if ref.hasAttribute("hlink"):
                    f.eventref_hlink.append(ref.getAttribute("hlink"))
                    f.eventref_role.append(ref.getAttribute("role"))
                    ##print(f'# Family {f.id} has event {f.eventref_hlink[-1]}')

            for ref in family.getElementsByTagName('childref'):
                if ref.hasAttribute("hlink"):
                    f.childref_hlink.append(ref.getAttribute("hlink"))
                    ##print(f'# Family {f.id} has child {f.childref_hlink[-1]}')

            for ref in family.getElementsByTagName('noteref'):
                if ref.hasAttribute("hlink"):
                    f.noteref_hlink.append(ref.getAttribute("hlink"))
                    ##print(f'# Family {f.id} has note {f.noteref_hlink[-1]}')
                       
            for ref in family.getElementsByTagName('citationref'):
                if ref.hasAttribute("hlink"):
                    f.citationref_hlink.append(ref.getAttribute("hlink"))
                    ##print(f'# Family {f.id} has cite {f.citationref_hlink[-1]}')

            self.save_and_link_handle(f, batch_id=self.batch_id)
            counter += 1
            # The sortnames and dates will be set for these families 
            self.family_ids.append(f.uniq_id)

        self.blog.log_event({'title':"Families", 'count':counter, 
                             'elapsed':time.time()-t0}) #, 'percent':1})


    def handle_notes(self):
        ''' Get all the notes in the collection. '''
        notes = self.collection.getElementsByTagName("note")

        print ("***** {} Notes *****".format(len(notes)))
        t0 = time.time()
        counter = 0

        for note in notes:
            n = Note()
            # Extract handle, change and id
            self._extract_base(note, n)

            n.priv = get_priv(note)
            if note.hasAttribute("type"):
                n.type = note.getAttribute("type")

            if len(note.getElementsByTagName('text')) == 1:
                note_text = note.getElementsByTagName('text')[0]
                n.text = note_text.childNodes[0].data
                # Pick possible url
                n.text, n.url = pick_url(n.text)

            #TODO: 17.10.2018 suunniteltiin, että kuolinsyyt 
            # konvertoitaisiin heti Note-nodeiksi sopivalla node-tyypillä
            #print("iNote {}".format(n))

            self.save_and_link_handle(n, batch_id=self.batch_id)
            counter += 1

        self.blog.log_event({'title':"Notes", 'count':counter, 
                             'elapsed':time.time()-t0}) #, 'percent':1})


    def handle_media(self):
        ''' Get all the media in the collection (Gramps term 'object'). '''
        media = self.collection.getElementsByTagName("object")

        print ("***** {} Media *****".format(len(media)))
        t0 = time.time()
        counter = 0

        # Details of each media object
        for obj in media:
            o = Media()
            # Extract handle, change and id
            self._extract_base(obj, o)

            for obj_file in obj.getElementsByTagName('file'):
                if o.src:
                    self.blog.log_event({'title':"More than one files for a media",
                                         'level':"WARNING", 'count':o.id})
                    break
                if obj_file.hasAttribute("src"):
                    o.src = obj_file.getAttribute("src")
                if obj_file.hasAttribute("mime"):
                    o.mime = obj_file.getAttribute("mime")
                if obj_file.hasAttribute("description"):
                    o.description = obj_file.getAttribute("description")

            #TODO: Varmista, ettei mediassa voi olla Note
            self.save_and_link_handle(o, batch_id=self.batch_id)
            counter += 1

        self.blog.log_event({'title':"Media objects", 'count':counter, 
                             'elapsed':time.time()-t0}) #, 'percent':1})


    def handle_people(self):
        ''' Get all the people in the collection. '''
        people = self.collection.getElementsByTagName("person")

        person_count = len(people)
        print ("***** {} Persons *****".format(person_count))
        t0 = time.time()
        counter = 0

        # Get details of each person
        for person in people:
            name_order = 0

            p = Person_gramps()
            # Extract handle, change and id
            self._extract_base(person, p)

            for person_gender in person.getElementsByTagName('gender'):
                if p.sex:
                    self.blog.log_event({'title':"More than one sexes in a person",
                                         'level':"WARNING", 'count':p.id})
                    break
                p.sex = p.sex_from_str(person_gender.childNodes[0].data)

            for person_name in person.getElementsByTagName('name'):
                pname = Name()
                pname.order = name_order
                name_order += 1

                if person_name.hasAttribute("alt"):
                    pname.alt = person_name.getAttribute("alt")
                if person_name.hasAttribute("type"):
                    pname.type = person_name.getAttribute("type")

                for person_first in person_name.getElementsByTagName('first'):
                    if pname.firstname:
                        self.blog.log_event({'title':"More than one first name in a person",
                                             'level':"WARNING", 'count':p.id})
                        break
                    if len(person_first.childNodes) == 1:
                        pname.firstname = person_first.childNodes[0].data
                    elif len(person_first.childNodes) > 1:
                        self.blog.log_event({'title':"More than one child node in a first name of a person",
                                            'level':"WARNING", 'count':p.id})

                if len(person_name.getElementsByTagName('surname') ) == 1:
                    person_surname = person_name.getElementsByTagName('surname')[0]
                    if person_surname.hasAttribute("prefix"):
                        pname.prefix = person_surname.getAttribute("prefix")
                    if len(person_surname.childNodes ) == 1:
                        pname.surname = person_surname.childNodes[0].data
                    elif len(person_surname.childNodes) > 1:
                        self.blog.log_event({'title':"More than one child node in a surname of a person",
                                             'level':"WARNING", 'count':p.id})
                elif len(person_name.getElementsByTagName('surname') ) > 1:
                    self.blog.log_event({'title':"More than one surname in a person",
                                         'level':"WARNING", 'count':p.id})

                if len(person_name.getElementsByTagName('suffix') ) == 1:
                    person_suffix = person_name.getElementsByTagName('suffix')[0]
                    pname.suffix = person_suffix.childNodes[0].data
                elif len(person_name.getElementsByTagName('suffix') ) > 1:
                    self.blog.log_event({'title':"More than one suffix in a person",
                                         'level':"WARNING", 'count':p.id})

                if len(person_name.getElementsByTagName('citationref') ) >= 1:
                    for i in range(len(person_name.getElementsByTagName('citationref') )):
                        person_name_citationref = person_name.getElementsByTagName('citationref')[i]
                        if person_name_citationref.hasAttribute("hlink"):
                            pname.citation_handles.append(person_name_citationref.getAttribute("hlink"))
                            ##print(f'# Person name for {p.id} has cite {pname.citation_handles[-1]}')

                p.names.append(pname)

#TODO Muuttaisiko p.eventref_hlink = (hlink, role). Nyt voisi mennä epätahtiin
            for person_eventref in person.getElementsByTagName('eventref'):
                if person_eventref.hasAttribute("hlink"):
                    p.eventref_hlink.append(person_eventref.getAttribute("hlink"))
                if person_eventref.hasAttribute("role"):
                    p.eventref_role.append(person_eventref.getAttribute("role"))

            # Handle <objref>
            p.media_refs = self._extract_mediaref(person)

            for person_url in person.getElementsByTagName('url'):
                n = Note()
                n.priv = get_priv(person_url)
                n.url = person_url.getAttribute("href")
                n.type = person_url.getAttribute("type")
                n.text = person_url.getAttribute("description")
                if n.url:
                    p.notes.append(n)

            for person_parentin in person.getElementsByTagName('parentin'):
                if person_parentin.hasAttribute("hlink"):
                    p.parentin_hlink.append(person_parentin.getAttribute("hlink"))
                    ##print(f'# Person {p.id} is parent in family {p.parentin_hlink[-1]}')

            for person_noteref in person.getElementsByTagName('noteref'):
                if person_noteref.hasAttribute("hlink"):
                    p.noteref_hlink.append(person_noteref.getAttribute("hlink"))

            for person_citationref in person.getElementsByTagName('citationref'):
                if person_citationref.hasAttribute("hlink"):
                    p.citationref_hlink.append(person_citationref.getAttribute("hlink"))
                    ##print(f'# Person {p.id} has cite {p.citationref_hlink[-1]}')

            #for ref in p.media_refs: print(f'# saving Person {p.id}: media_ref {ref}')
            self.save_and_link_handle(p, batch_id=self.batch_id)
            #print(f'# Person [{p.handle}] --> {self.handle_to_node[p.handle]}')
            counter += 1
            # The refnames will be set for these persons 
            self.person_ids.append(p.uniq_id)

        self.blog.log_event({'title':"Persons", 'count':counter, 
                             'elapsed':time.time()-t0}) #, 'percent':1})


    def handle_places(self):
        ''' Get all the places in the collection.
        
            To create place hierarchy links, there must be a dictionary of 
            Place handles and uniq_ids created so far. The link may use
            previous node or create a new one.
        '''

        place_keys = {}    # place_keys[handle] = uniq_id

        places = self.collection.getElementsByTagName("placeobj")

        print ("***** {} Places *****".format(len(places)))
        t0 = time.time()
        counter = 0

        # Print detail of each placeobj
        for placeobj in places:

            pl = Place_gramps()
            # Extract handle, change and id
            self._extract_base(placeobj, pl)
            pl.type = placeobj.getAttribute("type")

            # List of upper places in hierarchy as {hlink, dates} dictionaries
            pl.surround_ref = []

            # Note. The ptitle is never saved to Place object!
            if len(placeobj.getElementsByTagName('ptitle')) == 1:
                placeobj_ptitle = placeobj.getElementsByTagName('ptitle')[0]
                pl.ptitle = placeobj_ptitle.childNodes[0].data
            elif len(placeobj.getElementsByTagName('ptitle') ) > 1:
                self.blog.log_event({'title':"More than one ptitle in a place",
                                     'level':"WARNING", 'count':pl.id})

            place_order = 0
            for placeobj_pname in placeobj.getElementsByTagName('pname'):
                if placeobj_pname.hasAttribute("value"):
                    placename = PlaceName()
                    placename.order = place_order
                    place_order += 1
                    placename.name = placeobj_pname.getAttribute("value")
                    #print(f"# placeobj {pl.id} pname {place_order} {placename.name}")
                    if placename.name:
                        if pl.pname == '':
                            # First name is default pname for Place node
                            pl.pname = placename.name
                        placename.lang = placeobj_pname.getAttribute("lang")
                        pl.names.append(placename)
                    else:
                        self.blog.log_event({'title':"An empty place name discarded",
                                             'level':"WARNING", 
                                             'count':f"{pl.id}({place_order})"})
                        place_order -= 1

                try:
                    # Returns Gramps_DateRange or None
                    placename.dates = self._extract_daterange(placeobj_pname)
                    #TODO: val="1700-luvulla" muunnettava Noteksi
                except:
                    placename.dates = None

            for placeobj_coord in placeobj.getElementsByTagName('coord'):
                if placeobj_coord.hasAttribute("lat") \
                   and placeobj_coord.hasAttribute("long"):
                    lat = placeobj_coord.getAttribute("lat")
                    long = placeobj_coord.getAttribute("long")
                    if pl.coord:
                        self.blog.log_event({'title':"More than one coordinates in a place",
                                             'level':"WARNING", 'count':pl.id})
                    else:
                        try:
                            pl.coord = Point(lat, long)
                        except Exception as e:
                            self.blog.log_event({
                                'title':"Invalid coordinates - {}".format(e),
                                'level':"WARNING", 'count':pl.id})

            for placeobj_url in placeobj.getElementsByTagName('url'):
                n = Note()
                n.priv = get_priv(placeobj_url)
                n.url = placeobj_url.getAttribute("href")
                n.type = placeobj_url.getAttribute("type")
                n.text = placeobj_url.getAttribute("description")
                if n.url:
                    pl.notes.append(n)

            for placeobj_placeref in placeobj.getElementsByTagName('placeref'):
                # Traverse links to surrounding (upper) places
                hlink = placeobj_placeref.getAttribute("hlink")
                dates = self._extract_daterange(placeobj_placeref)
                # surround_ref elements example
                # {'hlink': '_ddd3...', 'dates': <Gramps_DateRange object>}
                pl.surround_ref.append({'hlink':hlink, 'dates':dates})
                ##print(f'# Place {pl.id} is surrouded by {pl.surround_ref[-1]["hlink"]}')

            for placeobj_noteref in placeobj.getElementsByTagName('noteref'):
                if placeobj_noteref.hasAttribute("hlink"):
                    pl.noteref_hlink.append(placeobj_noteref.getAttribute("hlink"))
                    ##print(f'# Place {pl.id} has note {pl.noteref_hlink[-1]}')

            # Handle <objref>
            pl.media_refs = self._extract_mediaref(placeobj)

            if pl.media_refs: 
                print(f'# saving Place {pl.id}: media_refs {pl.media_refs}')

            # Save Place, Place_names, Notes and connect to hierarchy
            self.save_and_link_handle(pl, batch_id=self.batch_id, place_keys=place_keys)
            # The place_keys has been updated 
            counter += 1
            
        self.blog.log_event({'title':"Places", 'count':counter, 
                             'elapsed':time.time()-t0}) #, 'percent':1})


    def handle_repositories(self):
        ''' Get all the repositories in the collection. '''
        repositories = self.collection.getElementsByTagName("repository")

        print ("***** {} Repositories *****".format(len(repositories)))
        t0 = time.time()
        counter = 0

        # Print detail of each repository
        for repository in repositories:

            r = Repository()
            # Extract handle, change and id
            self._extract_base(repository, r)

            if len(repository.getElementsByTagName('rname') ) == 1:
                repository_rname = repository.getElementsByTagName('rname')[0]
                r.rname = repository_rname.childNodes[0].data
            elif len(repository.getElementsByTagName('rname') ) > 1:
                self.blog.log_event({'title':"More than one rname in a repository",
                                     'level':"WARNING", 'count':r.id})

            if len(repository.getElementsByTagName('type') ) == 1:
                repository_type = repository.getElementsByTagName('type')[0]
                r.type =  repository_type.childNodes[0].data
            elif len(repository.getElementsByTagName('type') ) > 1:
                self.blog.log_event({'title':"More than one type in a repository",
                                     'level':"WARNING", 'count':r.id})

            for repository_url in repository.getElementsByTagName('url'):
                n = Note()
                n.url = repository_url.getAttribute("href")
                n.type = repository_url.getAttribute("type")
                n.text = repository_url.getAttribute("description")
                if n.url:
                    r.notes.append(n)

            self.save_and_link_handle(r, batch_id=self.batch_id)
            counter += 1

        self.blog.log_event({'title':"Repositories", 'count':counter, 
                             'elapsed':time.time()-t0}) #, 'percent':1})


    def handle_sources(self):
        ''' Get all the sources in the collection. '''
        sources = self.collection.getElementsByTagName("source")

        print ("***** {} Sources *****".format(len(sources)))
        t0 = time.time()
        counter = 0

        # Print detail of each source
        for source in sources:

            s = Source_gramps()
            # Extract handle, change and id
            self._extract_base(source, s)

            if len(source.getElementsByTagName('stitle') ) == 1:
                source_stitle = source.getElementsByTagName('stitle')[0]
                if len(source_stitle.childNodes) > 0:
                    s.stitle = source_stitle.childNodes[0].data
            elif len(source.getElementsByTagName('stitle') ) > 1:
                self.blog.log_event({'title':"More than one stitle in a source",
                                     'level':"WARNING", 'count':s.id})

            if len(source.getElementsByTagName('sauthor') ) == 1:
                source_sauthor = source.getElementsByTagName('sauthor')[0]
                if len(source_sauthor.childNodes) > 0:
                    s.sauthor = source_sauthor.childNodes[0].data
            elif len(source.getElementsByTagName('sauthor') ) > 1:
                self.blog.log_event({'title':"More than one sauthor in a source",
                                     'level':"WARNING", 'count':s.id})

            if len(source.getElementsByTagName('spubinfo') ) == 1:
                source_spubinfo = source.getElementsByTagName('spubinfo')[0]
                if len(source_spubinfo.childNodes) > 0:
                    s.spubinfo = source_spubinfo.childNodes[0].data
            elif len(source.getElementsByTagName('spubinfo') ) > 1:
                self.blog.log_event({'title':"More than one spubinfo in a source",
                                     'level':"WARNING", 'count':s.id})

            if len(source.getElementsByTagName('sabbrev') ) == 1:
                source_spubinfo = source.getElementsByTagName('sabbrev')[0]
                if len(source_spubinfo.childNodes) > 0:
                    s.sabbrev = source_spubinfo.childNodes[0].data
            elif len(source.getElementsByTagName('sabbrev') ) > 1:
                self.blog.log_event({'title':"More than one sabbrev in a source",
                                     'level':"WARNING", 'count':s.id})

            for source_noteref in source.getElementsByTagName('noteref'):
                # Traverse links to surrounding places
                if source_noteref.hasAttribute("hlink"):
                    s.note_handles.append(source_noteref.getAttribute("hlink"))
                    ##print(f'# Source {s.id} has note {s.note_handles[-1]}')

            for source_reporef in source.getElementsByTagName('reporef'):
                r = Repository()
                if source_reporef.hasAttribute("hlink"):
                    # s.reporef_hlink = source_reporef.getAttribute("hlink")
                    r.handle = source_reporef.getAttribute("hlink")
                    r.medium = source_reporef.getAttribute("medium")
                    ##print(f'# Source {s.id} in repository {r.handle} {r.medium}')
                # Mostly 1 repository!
                s.repositories.append(r)

            #elf.save_and_link_handle(r, self.batch_id)
            self.save_and_link_handle(s, batch_id=self.batch_id)
            counter += 1

        self.blog.log_event({'title':"Sources", 'count':counter, 
                             'elapsed':time.time()-t0}) #, 'percent':1})

# -------------------------- Other process steps -------------------------------

    def set_family_sortname_dates(self):
        ''' Set sortnames and lifetime dates for each Family in the list self.family_ids.

            For each Family set Family.father_sortname, Family.mother_sortname, 
            Family.datetype, Family.date1 and Family.date2
        '''

        print ("***** {} Sortnames & dates *****".format(len(self.family_ids)))
        t0 = time.time()
        dates_count = 0
        sortname_count = 0

        for p_id in self.family_ids:
            if p_id != None:
                dc, sc = dataupdater.set_family_name_properties(tx=self.tx, uniq_id=p_id)
                dates_count += dc
                sortname_count += sc

        self.blog.log_event({'title':"Dates", 'count':dates_count, 'elapsed':time.time()-t0})
        self.blog.log_event({'title':"Family sorting names", 'count':sortname_count})
        

    def set_person_sortname_refnames(self):
        ''' Add links from each Person to Refnames and set Person.sortname
        '''

        print ("***** {} Person refnames & sortnames *****".format(len(self.person_ids)))
        t0 = time.time()
        refname_count = 0
        sortname_count = 0

        from models.dataupdater import set_person_name_properties

        for p_id in self.person_ids:
            self.update_progress('refnames')
            if p_id != None:
                rc, sc = set_person_name_properties(tx=self.tx, uniq_id=p_id)
                refname_count += rc
                sortname_count += sc

        self.blog.log_event({'title':"Refname references", 
                                'count':refname_count, 'elapsed':time.time()-t0})
        self.blog.log_event({'title':"Person sorting names", 'count':sortname_count})


    def set_estimated_person_dates(self):
        ''' Sets estimated dates for each Person processed in handle_people
            in transaction
            
            Called from bp.gramps.gramps_loader.xml_to_neo4j
        '''
        print ("***** {} Estimated lifetimes *****".format(len(self.person_ids)))
        t0 = time.time()

        cnt = Person_combo.estimate_lifetimes(self.tx, self.person_ids)
                            
        self.blog.log_event({'title':"Estimated person lifetimes", 
                             'count':cnt, 'elapsed':time.time()-t0}) 

# --------------------------- DOM subtree procesors ----------------------------

    def _extract_daterange(self, obj):
        """ Extract date information from these kind of date formats:
                <daterange start="1820" stop="1825" quality="estimated"/>
                <datespan start="1840-01-01" stop="1850-06-30" quality="calculated"/>
                <dateval val="1870" type="about"/>

            This is ignored:
                <datestr val="1700-luvulla" />

            Returns: DateRange object or None
        """
        # Note informal dateobj 'datestr' is not processed as all!
        for tag in ['dateval', 'daterange', 'datespan']:
            if len(obj.getElementsByTagName(tag) ) == 1:
                dateobj = obj.getElementsByTagName(tag)[0]
                if tag == 'dateval':
                    if dateobj.hasAttribute("val"):
                        date_start = dateobj.getAttribute("val")
                    date_stop = None
                    if dateobj.hasAttribute("type"):
                        date_type = dateobj.getAttribute("type")
                    else:
                        date_type = None
                else:
                    if dateobj.hasAttribute("start"):
                        date_start = dateobj.getAttribute("start")
                    if dateobj.hasAttribute("stop"):
                        date_stop = dateobj.getAttribute("stop")
                    date_type = None
                if dateobj.hasAttribute("quality"):
                    date_quality = dateobj.getAttribute("quality")
                else:
                    date_quality = None
                logger.debug("bp.gramps.xml_dom_handler.DOM_handler._extract_daterange"
                             f"Creating {tag}, date_type={date_type}, quality={date_quality},"
                             f" {date_start} - {date_stop}")
                return Gramps_DateRange(tag, date_type, date_quality,
                                        date_start, date_stop)

            elif len(obj.getElementsByTagName(tag) ) > 1:
                self.log(Log("More than one {} tag in an event".format(tag),
                                    level="ERROR"))

        return None

    def _extract_base(self, dom, node):
        ''' Extract common variables from DOM object to NodeObject fields.

            node.id = self.id = ''            str Gedcom object id like "I1234"
            node.change = self.change         int Gramps object change timestamp
            node.handle = self.handle = ''    str Gramps handle
        '''
        if dom.hasAttribute("handle"):
            node.handle = dom.getAttribute("handle")
        if dom.hasAttribute("change"):
            node.change = int(dom.getAttribute("change"))
        if dom.hasAttribute("id"):
            node.id = dom.getAttribute("id")


    def _extract_mediaref(self, dom_object):
        ''' Check if dom_object has media reference and extract it to p.media_refs.

            Example:
                <objref hlink="_d485d4484ef70ec50c6">
                  <region corner1_x="0" corner1_y="21" corner2_x="100" corner2_y="91"/>
                  <citationref hlink="_d68cc45b6aa6ab09483"/>
                  <noteref hlink="_d485d4425c02e773ed8"/>
                </objref>

            region      set picture crop = (left, upper, right, lower)
                        <region corner1_x="0" corner1_y="21" corner2_x="100" corner2_y="91"/>
            citationref citation reference
            noteref     note reference
        '''
        result_list = []
        media_nr = -1
        for objref in dom_object.getElementsByTagName('objref'):
            if objref.hasAttribute("hlink"):
                resu = MediaRefResult()
                resu.media_handle = objref.getAttribute("hlink")
                media_nr += 1
                resu.media_order = media_nr
    
                for region in objref.getElementsByTagName('region'):
                    if region.hasAttribute("corner1_x"):
                        left = region.getAttribute('corner1_x')
                        upper = region.getAttribute('corner1_y')
                        right = region.getAttribute('corner2_x')
                        lower = region.getAttribute('corner2_y')
                        resu.crop = int(left), int(upper), int(right), int(lower)
                        #print(f'#_extract_mediaref: Pic {resu.media_order} handle={resu.media_handle} crop={resu.crop}')
                #if not resu.crop: print(f'#_extract_mediaref: Pic {resu.media_order} handle={resu.media_handle}')
    
                # Add note and citation references
                for ref in objref.getElementsByTagName('noteref'):
                    if ref.hasAttribute("hlink"):
                        resu.note_handles.append(ref.getAttribute("hlink"))
                        #print(f'#_extract_mediaref: Note {resu.note_handles[-1]}')
                           
                for ref in objref.getElementsByTagName('citationref'):
                    if ref.hasAttribute("hlink"):
                        resu.citation_handles.append(ref.getAttribute("hlink"))
                        #print(f'#_extract_mediaref: Cite {resu.citation_handles[-1]}')
    
                result_list.append(resu)

        return result_list
