'''
    Methods to import all data from Gramps xml file

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

import logging
import time
import gzip
from os.path import basename, splitext
import xml.dom.minidom
import re

from .models.person_gramps import Person_gramps
from .models.event_gramps import Event_gramps
from .batchlogger import Batch, Log

from models.gen.family import Family
from models.gen.note import Note
from models.gen.media import Media
from models.gen.person_name import Name
from models.gen.weburl import Weburl
from models.gen.place import Place, Place_name, Point
from models.gen.dates import Gramps_DateRange
from models.gen.citation import Citation
from models.gen.source import Source
from models.gen.repository import Repository

from models.loadfile import status_update
from models.dataupdater import set_confidence_value, set_person_refnames
import shareds


def xml_to_neo4j(pathname, userid='Taapeli'):
    """ 
    Reads a Gramps xml file, and saves the information to db 
    
Todo: There are beforehand estimated progress persentage values 1..100 for each
    upload step. The are stored in *.meta file and may be queried from the UI.
    
    Metacode for batch log creation UserProfile --> Batch.

    # Start a Batch 
        routes.upload_gramps / models.loadfile.upload_file >
            # Create id / bp.gramps.batchlogger.Batch._create_id
            match (p:UserProfile {username:"jussi"}); 
            create (p) -[:HAS_LOADED]-> (b:Batch {id:"2018-06-02.0", status:"started"}) 
            return b
    # Load the file (in routes.save_loaded_gramps) 
        models.loadfile.upload_file > 
            models.loadfile.status_update({status:"started", percent:1}) 
        # Clean apostrophes
        file clean > 
            models.loadfile.status_update({status:"loading", percent:2}) 
    # Käsittele tietoryhmä 1
        models.gramps.gramps_loader.xml_to_neo4j > 
            models.loadfile.status_update({status:"storing", percent:3}) 
    # Käsittele tietoryhmä 2 ...
    # ...
    # Käsittele henkilöt
        models.gramps.gramps_loader.xml_to_neo4j >
            # (Henkilömäärä / 64) kertaa kasvatetaan prosenttilukua x yhdellä
            models.loadfile.status_update({status:"storing", percent:x}) 
    # Viimeistele data
        models.gramps.gramps_loader.xml_to_neo4j > 
            models.loadfile.status_update({status:"storing", percent:95}) 
    # Merkitse valmiiksi
        models.loadfile.status_update({status:"done", percent:100}) 

        match (p:UserProfile {username:"jussi"}); 
        match (p) -[r:CURRENT_LOAD]-> () delete r
        create (p) -[:CURRENT_LOAD]-> (b)
    """

    ''' Uncompress and hide apostrophes for DOM handler (and save log)
    '''
    file_cleaned, file_displ, cleaning_log = file_clean(pathname)

    ''' Get XML DOM parser and start DOM elements handler transaction '''
    handler = DOM_handler(file_cleaned, userid)

    # Initialize Run report
    handler.blog = Batch(userid)
    handler.blog.log_event({'title':"Storing data from Gramps", 'level':"TITLE"})
    handler.blog.log_event({'title':"Loaded file '{}'".format(file_displ),
                            'elapsed':shareds.tdiff})
    handler.blog.log(cleaning_log)
    t0 = time.time()

    try:
        ''' Start DOM transaction '''
        handler.begin_tx(shareds.driver.session())
        # Create new Batch node and start
        handler.batch_id = handler.blog.start_batch(None, file_cleaned)
        status_update({'percent':1})

        handler.handle_notes()
        handler.handle_repositories()
        handler.handle_media()
    
        handler.handle_places()
        handler.handle_sources()
        handler.handle_citations()
    
        handler.handle_events()
        handler.handle_people()
        handler.handle_families()

        # Set person confidence values 
        #TODO: Only for imported persons (now for all persons!)
        set_confidence_value(handler.tx, batch_logger=handler.blog)
        # Set Refname links (for imported persons)
        handler.set_refnames()
        
        handler.blog.complete(handler.tx)
        handler.commit()

    except ConnectionError as err:
        print("Virhe ConnectionError {0}".format(err))
        handler.blog.log_event(title="Talletus tietokantaan ei onnistunut {} {}".\
                                     format(err.message, err.code), level="ERROR")
        raise SystemExit("Stopped due to ConnectionError")    # Stop processing?

    handler.blog.log_event({'title':"Total time", 'level':"TITLE", 
                            'elapsed':time.time()-t0, 'percent':100})
    return handler.blog.list()


def file_clean(pathname):
    # Decompress file and clean problematic delimiter (')
    # - build 2nd filename
    # - create Log for logging

    def _clean_apostrophes(file_in, file_out):
        '''
        Replace each "'" with corresponding entity to avoid mismatches. 
        They are actually stored as "'" after processing
    
        Returns the count of changed lines
        '''
        n = 0
        for line in file_in:
            if "\'" in line: 
                line = line.replace("\'", "&apos;")
                n += 1
            file_out.write(line)
        return n


    t0 = time.time()
    root, ext = splitext(pathname)
    file_cleaned = root + "_clean" + ext
# - filename for display
    file_displ = basename(pathname)
    with open(file_cleaned, "w", encoding='utf-8') as file_out:
        # Creates the ouput file and closes it
        try:
            with gzip.open(pathname, mode='rt', encoding='utf-8', compresslevel=9) as file_in:
                # print("A gzipped file")
                counter = _clean_apostrophes(file_in, file_out)
            msg = "Cleaned apostrophes from packed input lines" # Try to read a gzipped file
        except OSError: # Not gzipped; Read as an ordinary file
            with open(pathname, mode='rt', encoding='utf-8') as file_in:
                print("Not a gzipped file")
                counter = _clean_apostrophes(file_in, file_out)
            msg = "Cleaned apostrophes from input lines"
        event = Log({'title':msg, 'count':counter, 
                     'elapsed':time.time()-t0, 'percent':1})
    return (file_cleaned, file_displ, event)


def pick_url(src):
    ''' Check, if there is an url on the text src.
    
        Returns (text, url), where the url is removed from text
    '''
    #TODO: Jos url päättyy merkkeihin '").,' ne tulee poistaa ja siirrää end-tekstiin
    #TODO: Pitäsikö varautua siihen että teksti sisältää monta url:ia?

    match = re.search("(?P<url>https?://[^\s'\"]+)", src)
    url = None
    text = src
    if match is not None:
        url = match.group("url")
        start = match.start()
        end = match.end()
#         if start == 0:
#             start = ''
#         if end == len(src) - 1:
#             end = ''
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

# -----------------------------------------------------------------------------

class DOM_handler():
    """ XML DOM elements handler
        - creates transaction
        - processes different data groups from given xml file to database
        - collects status log
    """
    def __init__(self, infile, current_user):
        """ Set DOM collection and username """
        DOMTree = xml.dom.minidom.parse(open(infile, encoding='utf-8'))
        #handler = DOM_handler(DOMTree.documentElement, userid)
        self.collection = DOMTree.documentElement    # XML documentElement
        self.username = current_user        # current username

        self.uniq_ids = []                  # List of processed Person node
                                            # unique id's
        self.tx = None                      # Transaction not opened

    def begin_tx(self, session):
        self.tx = session.begin_transaction()
        print("Transaction started")

    def commit(self):
        """ Commit transaction """
        if self.tx.closed():
            print("Transaction already closed!")
        else:
            try:
                self.tx.commit()
                print("Transaction committed")
            except Exception as e:
                print("Transaction failed")
                self.blog.log_event({'title':"Talletus tietokantaan ei onnistunut {} {}".\
                                     format(e.__class__.__name__, e), 'level':"ERROR"})


    # XML subtree handlers

    def handle_citations(self):
        # Get all the citations in the collection
        citations = self.collection.getElementsByTagName("citation")

        print ("***** {} Citations *****".format(len(citations)))
        t0 = time.time()
        counter = 0

        # Print detail of each citation
        for citation in citations:

            c = Citation()

            if citation.hasAttribute("handle"):
                c.handle = citation.getAttribute("handle")
            if citation.hasAttribute("change"):
                c.change = int(citation.getAttribute("change"))
            if citation.hasAttribute("id"):
                c.id = citation.getAttribute("id")

            if len(citation.getElementsByTagName('dateval') ) == 1:
                citation_dateval = citation.getElementsByTagName('dateval')[0]
                if citation_dateval.hasAttribute("val"):
                    c.dateval = citation_dateval.getAttribute("val")
            elif len(citation.getElementsByTagName('dateval') ) > 1:
                self.blog.log_event({'title':"More than one dateval tag in a citation",
                                     'level':"WARNING", 'count':c.id})

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

            if len(citation.getElementsByTagName('noteref') ) >= 1:
                for i in range(len(citation.getElementsByTagName('noteref') )):
                    citation_noteref = citation.getElementsByTagName('noteref')[i]
                    if citation_noteref.hasAttribute("hlink"):
                        c.noteref_hlink.append(citation_noteref.getAttribute("hlink"))

            if len(citation.getElementsByTagName('sourceref') ) == 1:
                citation_sourceref = citation.getElementsByTagName('sourceref')[0]
                if citation_sourceref.hasAttribute("hlink"):
                    c.source_handle = citation_sourceref.getAttribute("hlink")
            elif len(citation.getElementsByTagName('sourceref') ) > 1:
                self.blog.log_event({'title':"More than one sourceref tag in a citation",
                                     'level':"WARNING",'count':c.id})

            c.save(self.tx)
            counter += 1

        self.blog.log_event({'title':"Citations", 'count':counter, 
                             'elapsed':time.time()-t0, 'percent':1})


    def handle_events(self):
        # Get all the events in the collection
        events = self.collection.getElementsByTagName("event")

        print ("***** {} Events *****".format(len(events)))
        t0 = time.time()
        counter = 0

        # Print detail of each event
        for event in events:
            # Create an event with Gramps attributes
            e = Event_gramps()

            if event.hasAttribute("handle"):
                e.handle = event.getAttribute("handle")
            if event.hasAttribute("change"):
                e.change = int(event.getAttribute("change"))
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

            """ Dates:
                <daterange start="1820" stop="1825" quality="estimated"/>
                <datespan start="1840-01-01" stop="1850-06-30" quality="calculated"/>
                <dateval val="1870" type="about"/>
                <datestr val="1700-luvulla" />    # Not processed!
            """
            try:
                # type Gramps_DateRange
                e.dates = self._extract_daterange(event)
            except:
                e.dates = None

            if len(event.getElementsByTagName('place') ) == 1:
                event_place = event.getElementsByTagName('place')[0]
                if event_place.hasAttribute("hlink"):
                    e.place_hlink = event_place.getAttribute("hlink")
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

            for ref in event.getElementsByTagName('citationref'):
                if ref.hasAttribute("hlink"):
                    e.citation_handles.append(ref.getAttribute("hlink"))

            if len(event.getElementsByTagName('objref') ) == 1:
                event_objref = event.getElementsByTagName('objref')[0]
                if event_objref.hasAttribute("hlink"):
                    e.objref_hlink = event_objref.getAttribute("hlink")
            elif len(event.getElementsByTagName('objref') ) > 1:
                self.blog.log_event({'title':"More than one objref tag in an event",
                                     'level':"WARNING", 'count':e.id})

            e.save(self.tx)
            counter += 1

        self.blog.log_event({'title':"Events", 'count':counter, 
                             'elapsed':time.time()-t0, 'percent':1})


    def handle_families(self):
        # Get all the families in the collection
        families = self.collection.getElementsByTagName("family")

        print ("***** {} Families *****".format(len(families)))
        t0 = time.time()
        counter = 0

        # Print detail of each family
        for family in families:

            f = Family()

            if family.hasAttribute("handle"):
                f.handle = family.getAttribute("handle")
            if family.hasAttribute("change"):
                f.change = int(family.getAttribute("change"))
            if family.hasAttribute("id"):
                f.id = family.getAttribute("id")

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
            elif len(family.getElementsByTagName('father') ) > 1:
                self.blog.log_event({'title':"More than one father tag in a family",
                                     'level':"WARNING", 'count':f.id})

            if len(family.getElementsByTagName('mother') ) == 1:
                family_mother = family.getElementsByTagName('mother')[0]
                if family_mother.hasAttribute("hlink"):
                    f.mother = family_mother.getAttribute("hlink")
            elif len(family.getElementsByTagName('mother') ) > 1:
                self.blog.log_event({'title':"More than one mother tag in a family",
                                     'level':"WARNING", 'count':f.id})

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

            if len(family.getElementsByTagName('noteref') ) >= 1:
                for i in range(len(family.getElementsByTagName('noteref') )):
                    family_noteref = family.getElementsByTagName('noteref')[i]
                    if family_noteref.hasAttribute("hlink"):
                        f.noteref_hlink.append(family_noteref.getAttribute("hlink"))

            f.save(self.tx, self.batch_id)
            counter += 1

        self.blog.log_event({'title':"Families", 'count':counter, 
                             'elapsed':time.time()-t0, 'percent':1})


    def handle_notes(self):
        # Get all the notes in the collection
        notes = self.collection.getElementsByTagName("note")

        print ("***** {} Notes *****".format(len(notes)))
        t0 = time.time()
        counter = 0

        # Print detail of each note
        for note in notes:

            n = Note()

            if note.hasAttribute("handle"):
                n.handle = note.getAttribute("handle")
            if note.hasAttribute("change"):
                n.change = int(note.getAttribute("change"))
            if note.hasAttribute("id"):
                n.id = note.getAttribute("id")
            if note.hasAttribute("priv"):
                n.priv = note.getAttribute("priv")
            if note.hasAttribute("type"):
                n.type = note.getAttribute("type")

            url = ''
            if len(note.getElementsByTagName('text') ) == 1:
                note_text = note.getElementsByTagName('text')[0]
                n.text = note_text.childNodes[0].data
                # Pick possible url
                n.text, url = pick_url(n.text)
#                 if url:
#                     u = Weburl(url)

            #TODO: 17.10.2018 Viime palaverissa mm. suunniteltiin, että kuolinsyyt 
            # konvertoitaisiin heti Note-nodeiksi sopivalla node-tyypillä
            print("Note type={}, text={}... url={}".format(n.type, n.text[:16], url))
            #TODO: Uuden Weburl-luokan ja noden yhdistäminen Noteen siten, 
            # että siinä olisi aina kaksi kenttää: description ja url.

            n.save(self.tx)
            counter += 1

        self.blog.log_event({'title':"Notes", 'count':counter, 
                             'elapsed':time.time()-t0, 'percent':1})


    def handle_media(self):
        # Get all the media in the collection (in Gramps 'object')
        media = self.collection.getElementsByTagName("object")

        print ("***** {} Media *****".format(len(media)))
        t0 = time.time()
        counter = 0

        # Print detail of each media object
        for obj in media:

            o = Media()

            if obj.hasAttribute("handle"):
                o.handle = obj.getAttribute("handle")
            if obj.hasAttribute("change"):
                o.change = int(obj.getAttribute("change"))
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

            o.save(self.tx)
            counter += 1

        self.blog.log_event({'title':"Media objects", 'count':counter, 
                             'elapsed':time.time()-t0, 'percent':1})


    def handle_people(self):
        # Get all the people in the collection
        people = self.collection.getElementsByTagName("person")

        person_count = len(people)
        print ("***** {} Persons *****".format(person_count))
        t0 = time.time()
        counter = 0

        # Print detail of each person
        for person in people:

            p = Person_gramps()

            if person.hasAttribute("handle"):
                p.handle = person.getAttribute("handle")
            if person.hasAttribute("change"):
                p.change = int(person.getAttribute("change"))
            if person.hasAttribute("id"):
                p.id = person.getAttribute("id")
            if person.hasAttribute("priv"):
                p.priv = person.getAttribute("priv")

            if len(person.getElementsByTagName('gender') ) == 1:
                person_gender = person.getElementsByTagName('gender')[0]
                p.gender = person_gender.childNodes[0].data
            elif len(person.getElementsByTagName('gender') ) > 1:
                self.blog.log_event({'title':"More than one gender in a person",
                                     'level':"WARNING", 'count':p.id})

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
                            self.blog.log_event({'title':"More than one child node in a first name of a person",
                                                'level':"WARNING", 'count':p.id})
                    elif len(person_name.getElementsByTagName('first') ) > 1:
                        self.blog.log_event({'title':"More than one first name in a person",
                                             'level':"WARNING", 'count':p.id})

                    if len(person_name.getElementsByTagName('surname') ) == 1:
                        person_surname = person_name.getElementsByTagName('surname')[0]
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

            for person_url in person.getElementsByTagName('url'):
                weburl = Weburl()
                if person_url.hasAttribute("priv"):
                    weburl.priv = int(person_url.getAttribute("priv"))
                if person_url.hasAttribute("href"):
                    weburl.href = person_url.getAttribute("href")
                if person_url.hasAttribute("type"):
                    weburl.type = person_url.getAttribute("type")
                if person_url.hasAttribute("description"):
                    weburl.description = person_url.getAttribute("description")
                p.urls.append(weburl)

            if len(person.getElementsByTagName('parentin') ) >= 1:
                for i in range(len(person.getElementsByTagName('parentin') )):
                    person_parentin = person.getElementsByTagName('parentin')[i]
                    if person_parentin.hasAttribute("hlink"):
                        p.parentin_hlink.append(person_parentin.getAttribute("hlink"))
                        
            if len(person.getElementsByTagName('noteref') ) >= 1:
                for i in range(len(person.getElementsByTagName('noteref') )):
                    person_noteref = person.getElementsByTagName('noteref')[i]
                    if person_noteref.hasAttribute("hlink"):
                        p.noteref_hlink.append(person_noteref.getAttribute("hlink"))

            if len(person.getElementsByTagName('citationref') ) >= 1:
                for i in range(len(person.getElementsByTagName('citationref') )):
                    person_citationref = person.getElementsByTagName('citationref')[i]
                    if person_citationref.hasAttribute("hlink"):
                        p.citationref_hlink.append(person_citationref.getAttribute("hlink"))

            p.save(self.tx, self.batch_id)
            counter += 1
            # The refnames will be set for these persons 
            self.uniq_ids.append(p.uniq_id)

        self.blog.log_event({'title':"Persons", 'count':counter, 
                             'elapsed':time.time()-t0, 'percent':1})


    def handle_places(self):
        # Get all the places in the collection
        places = self.collection.getElementsByTagName("placeobj")

        print ("***** {} Places *****".format(len(places)))
        t0 = time.time()
        counter = 0

        # Print detail of each placeobj
        for placeobj in places:

            place = Place()
            # List of upper places in hierarchy as {hlink, dates} dictionaries
            #TODO move in Place and remove Place.placeref_hlink string
            place.surround_ref = []

            place.handle = placeobj.getAttribute("handle")
            if placeobj.hasAttribute("change"):
                place.change = int(placeobj.getAttribute("change"))
            place.id = placeobj.getAttribute("id")
            place.type = placeobj.getAttribute("type")

            if len(placeobj.getElementsByTagName('ptitle') ) == 1:
                placeobj_ptitle = placeobj.getElementsByTagName('ptitle')[0]
                place.ptitle = placeobj_ptitle.childNodes[0].data
            elif len(placeobj.getElementsByTagName('ptitle') ) > 1:
                self.blog.log_event({'title':"More than one ptitle in a place",
                                     'level':"WARNING", 'count':place.id})

            for placeobj_pname in placeobj.getElementsByTagName('pname'):
                placename = Place_name()
                if placeobj_pname.hasAttribute("value"):
                    placename.name = placeobj_pname.getAttribute("value")
                    if place.pname == '':
                        # First name is default name for Place node
                        place.pname = placename.name
                if placeobj_pname.hasAttribute("lang"):
                    placename.lang = placeobj_pname.getAttribute("lang")
                place.names.append(placename)

            for placeobj_coord in placeobj.getElementsByTagName('coord'):
                if placeobj_coord.hasAttribute("lat") \
                   and placeobj_coord.hasAttribute("long"):
                    coord_lat = placeobj_coord.getAttribute("lat")
                    coord_long = placeobj_coord.getAttribute("long")
                    try:
                        place.coord = Point(coord_lat, coord_long)
                    except Exception as e:
                        self.blog.log_event({
                            'title':"Invalid coordinates - {}".format(e),
                            'level':"WARNING", 'count':place.id})

            for placeobj_url in placeobj.getElementsByTagName('url'):
                weburl = Weburl()
                if placeobj_url.hasAttribute("priv"):
                    weburl.priv = int(placeobj_url.getAttribute("priv"))
                if placeobj_url.hasAttribute("href"):
                    weburl.href = placeobj_url.getAttribute("href")
                if placeobj_url.hasAttribute("type"):
                    weburl.type = placeobj_url.getAttribute("type")
                if placeobj_url.hasAttribute("description"):
                    weburl.description = placeobj_url.getAttribute("description")
                place.urls.append(weburl)

            for placeobj_placeref in placeobj.getElementsByTagName('placeref'):
                # Traverse links to surrounding places
                hlink = placeobj_placeref.getAttribute("hlink")
                dates = self._extract_daterange(placeobj_placeref)
                place.surround_ref.append({'hlink':hlink, 'dates':dates})
#             # Piti sallia useita ylempia paikkoja eri päivämäärillä
#             # Tässä vain 1 sallitaan elikä päivämäärää ole
#             if len(placeobj.getElementsByTagName('placeref') ) == 1:
#                 placeobj_placeref = placeobj.getElementsByTagName('placeref')[0]
#                 if placeobj_placeref.hasAttribute("hlink"):
#                     place.placeref_hlink = placeobj_placeref.getAttribute("hlink")
#                     place.dates = self._extract_daterange(placeobj_placeref)
#             elif len(placeobj.getElementsByTagName('placeref') ) > 1:
#                 print("Warning: Ignored 2nd placeref in a place - useita hierarkian yläpuolisia paikkoja")

            for placeobj_noteref in placeobj.getElementsByTagName('noteref'):
                if placeobj_noteref.hasAttribute("hlink"):
                    place.noteref_hlink.append(placeobj_noteref.getAttribute("hlink"))

            place.save(self.tx)
            counter += 1

        self.blog.log_event({'title':"Places", 'count':counter, 
                             'elapsed':time.time()-t0, 'percent':1})


    def handle_repositories(self):
        # Get all the repositories in the collection
        repositories = self.collection.getElementsByTagName("repository")

        print ("***** {} Repositories *****".format(len(repositories)))
        t0 = time.time()
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
                self.blog.log_event({'title':"More than one rname in a repocitory",
                                     'level':"WARNING", 'count':r.id})

            if len(repository.getElementsByTagName('type') ) == 1:
                repository_type = repository.getElementsByTagName('type')[0]
                r.type =  repository_type.childNodes[0].data
            elif len(repository.getElementsByTagName('type') ) > 1:
                self.blog.log_event({'title':"More than one type in a repocitory",
                                     'level':"WARNING", 'count':r.id})

            for repository_url in repository.getElementsByTagName('url'):
                webref = Weburl()
                webref.href = repository_url.getAttribute("href")
                webref.type = repository_url.getAttribute("type")
                webref.description = repository_url.getAttribute("description")
                if webref.href > "":
                    r.urls.append(webref)

            r.save(self.tx)
            counter += 1

        self.blog.log_event({'title':"Repositories", 'count':counter, 
                             'elapsed':time.time()-t0, 'percent':1})


    def handle_sources(self):
        # Get all the sources in the collection
        sources = self.collection.getElementsByTagName("source")

        print ("***** {} Sources *****".format(len(sources)))
        t0 = time.time()
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
                self.blog.log_event({'title':"More than one stitle in a source",
                                     'level':"WARNING", 'count':s.id})

#TODO More than one noteref in a source     S0041, S0002
# Vaihdetaan s.noteref_hlink --> s.note_handles[]
            if len(source.getElementsByTagName('noteref') ) == 1:
                source_noteref = source.getElementsByTagName('noteref')[0]
                if source_noteref.hasAttribute("hlink"):
                    s.noteref_hlink = source_noteref.getAttribute("hlink")
            elif len(source.getElementsByTagName('noteref') ) > 1:
                self.blog.log_event({'title':"More than one noteref in a source",
                                     'level':"WARNING", 'count':s.id})

            if len(source.getElementsByTagName('reporef') ) == 1:
                source_reporef = source.getElementsByTagName('reporef')[0]
                if source_reporef.hasAttribute("hlink"):
                    s.reporef_hlink = source_reporef.getAttribute("hlink")
                if source_reporef.hasAttribute("medium"):
                    s.reporef_medium = source_reporef.getAttribute("medium")
            elif len(source.getElementsByTagName('reporef') ) > 1:
                self.blog.log_event({'title':"More than one reporef in a source",
                                     'level':"WARNING", 'count':s.id})

            s.save(self.tx)
            counter += 1

        self.blog.log_event({'title':"Sources", 'count':counter, 
                             'elapsed':time.time()-t0, 'percent':1})


    def set_refnames(self):
        ''' Add links from each Person to Refnames '''

        print ("***** {} Refnames *****".format(len(self.uniq_ids)))
        t0 = time.time()
        self.namecount = 0

        for p_id in self.uniq_ids:
            if p_id != None:
                set_person_refnames(self, p_id)

        self.blog.log_event({'title':"Created Refname references", 
                             'count':self.namecount, 'elapsed':time.time()-t0,
                             'percent':1})


    def _extract_daterange(self, obj):
        """ Extract a date information from these kind of date formats:
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
                logging.debug("Creating {}, date_type={}, quality={}, {} - {}".\
                              format(tag, date_type, date_quality, date_start, date_stop))
                return Gramps_DateRange(tag, date_type, date_quality,
                                        date_start, date_stop)

            elif len(obj.getElementsByTagName(tag) ) > 1:
                self.log(Log("More than one {} tag in an event".format(tag),
                                    level="ERROR"))

        return None
