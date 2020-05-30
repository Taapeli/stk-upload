'''
    Methods to import all data from Gramps xml file

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

import time
import gzip
from os.path import basename, splitext
from flask_babelex import _

from .xml_dom_handler import DOM_handler
from .batchlogger import Batch, Log
from models import dataupdater
#from models.dataupdater import set_confidence_values
import shareds
import traceback
from tarfile import TarFile
import os
from bp.scene.models import media


def get_upload_folder(username): 
    ''' Returns upload directory for given user'''
    return os.path.join("uploads", username)

def analyze_xml(username, filename):
    # Read the xml file
    upload_folder = get_upload_folder(username) 
    pathname = os.path.join(upload_folder,filename)
    print("bp.gramps.gramps_loader.analyze_xml Pathname: " + pathname)
    
    file_cleaned, file_displ, cleaning_log = file_clean(pathname)
    

    ''' Get XML DOM parser and start DOM elements handler transaction '''
    handler = DOM_handler(file_cleaned, username, filename)
    
    citation_source_cnt = 0
    event_citation_cnt = 0
    family_citation_cnt = 0
    object_citation_cnt = 0
    person_citation_cnt = 0
    place_citation_cnt = 0
    source_repository_cnt = 0
    
    event_no_citation_cnt = 0 # How many events do not have any citationref?
    
    # Estimated times per item (ms)
    e_citation = 3
    e_event = 3
    e_family = 4
    e_object = 6
    e_note = 3
    e_person = 16
    e_place = 6
    e_repository = 2
    e_source = 3
    e_total = 0

    citations = handler.collection.getElementsByTagName("citation")
    citation_cnt = len(citations)
    if citation_cnt > 0:
        e_total += citation_cnt * e_citation / 1000
        for citation in citations:
            citation_source_cnt += len(citation.getElementsByTagName('sourceref') )
        
    events = handler.collection.getElementsByTagName("event")
    event_cnt = len(events)
    if event_cnt > 0:
        e_total += event_cnt * e_event / 1000
        for event in events:
            event_citation_cnt += len(event.getElementsByTagName('citationref') )
            if len(event.getElementsByTagName('citationref') ) == 0:
                event_no_citation_cnt += 1

    families = handler.collection.getElementsByTagName("family")
    family_cnt = len(families)
    if family_cnt > 0:
        e_total += family_cnt * e_family / 1000
        for family in families:
            family_citation_cnt += len(family.getElementsByTagName('citationref') )

    notes = handler.collection.getElementsByTagName("note")
    note_cnt = len(notes)
    if note_cnt > 0:
        e_total += note_cnt * e_note / 1000

    objects = handler.collection.getElementsByTagName("object")
    object_cnt = len(objects)
    if object_cnt > 0:
        e_total += object_cnt * e_object / 1000
        for media in objects:
            object_citation_cnt += len(media.getElementsByTagName('citationref') )

    persons = handler.collection.getElementsByTagName("person")
    person_cnt = len(persons)
    if person_cnt > 0:
        e_total += person_cnt * e_person / 1000
        for person in persons:
            person_citation_cnt += len(person.getElementsByTagName('citationref') )

    places = handler.collection.getElementsByTagName("placeobj")
    place_cnt = len(places)
    if place_cnt > 0:
        e_total += place_cnt * e_place / 1000
        for place in places:
            place_citation_cnt += len(place.getElementsByTagName('citationref') )

    repositorys = handler.collection.getElementsByTagName("repository")
    repository_cnt = len(repositorys)
    if repository_cnt > 0:
        e_total += repository_cnt * e_repository / 1000

    sources = handler.collection.getElementsByTagName("source")
    source_cnt = len(sources)
    if source_cnt > 0:
        e_total += source_cnt * e_source / 1000
        for source in sources:
            source_repository_cnt += len(source.getElementsByTagName('reporef') )

    counts = {}
    for name,value in locals().items():
        if name.endswith("_cnt"):
            counts[name] = value
    counts["e_total"] = e_total
    return counts
                    

def analyze(username, filename):
    values = analyze_xml(username, filename)

    references = []
    
    class Analyze_row(): pass
    
    row = Analyze_row()
    row.individ = "Events with no references to"
    row.number_of_individs = values["event_no_citation_cnt"]
    row.reference = "Citation"
    row.number_of_references = " "
    
    references.append(row)
    
    row = Analyze_row()
    row.individ = "Citation"
    row.number_of_individs = values["citation_cnt"]
    row.reference = "Source"
    row.number_of_references = values["citation_source_cnt"]
    
    references.append(row)
    
    row = Analyze_row()
    row.individ = "Event"
    row.number_of_individs = values["event_cnt"]
    row.reference = "Citation"
    row.number_of_references = values["event_citation_cnt"]
    
    references.append(row)
    
    row = Analyze_row()
    row.individ = "Family"
    row.number_of_individs = values["family_cnt"]
    row.reference = "Citation"
    row.number_of_references = values["family_citation_cnt"]
    
    references.append(row)
    
    row = Analyze_row()
    row.individ = "Note"
    row.number_of_individs = values["note_cnt"]
    row.reference = " "
    row.number_of_references = " "
    
    references.append(row)
    
    row = Analyze_row()
    row.individ = "Media"
    row.number_of_individs = values["object_cnt"]
    row.reference = "Citation"
    row.number_of_references = values["object_citation_cnt"]
    
    references.append(row)
    
    row = Analyze_row()
    row.individ = "Person"
    row.number_of_individs = values["person_cnt"]
    row.reference = "Citation"
    row.number_of_references = values["person_citation_cnt"]
    
    references.append(row)
    
    row = Analyze_row()
    row.individ = "Place"
    row.number_of_individs = values["place_cnt"]
    row.reference = "Citation"
    row.number_of_references = values["place_citation_cnt"]
    
    references.append(row)
    
    row = Analyze_row()
    row.individ = "Repository"
    row.number_of_individs = values["repository_cnt"]
    row.reference = " "
    row.number_of_references = " "
    
    references.append(row)
    
    row = Analyze_row()
    row.individ = "Source"
    row.number_of_individs = values["source_cnt"]
    row.reference = "Repository"
    row.number_of_references = values["source_repository_cnt"]
    
    references.append(row)
    
    row = Analyze_row()
    row.individ = "Estimated time (sec):"
    e_total = values["e_total"]
    row.number_of_individs = " "
    row.reference = " "
    row.number_of_references = str(int(e_total))
    
    references.append(row)
    
    return(references)
                    

def analyze_old2(username, filename):
    values = analyze_xml(username, filename)

    text = []
    citation_cnt = values["citation_cnt"]
    citation_source_cnt = values["citation_source_cnt"]
    event_cnt = values["event_cnt"]
    event_citation_cnt = values["event_citation_cnt"]
    event_no_citation_cnt = values["event_no_citation_cnt"]
    family_cnt = values["family_cnt"]
    family_citation_cnt = values["family_citation_cnt"]
    note_cnt = values["note_cnt"]
    object_cnt = values["object_cnt"]
    object_citation_cnt = values["object_citation_cnt"]
    person_cnt = values["person_cnt"]
    person_citation_cnt = values["person_citation_cnt"]
    place_cnt = values["place_cnt"]
    place_citation_cnt = values["place_citation_cnt"]
    repository_cnt = values["repository_cnt"]
    source_cnt = values["source_cnt"]
    source_repository_cnt = values["source_repository_cnt"]
    e_total = values["e_total"]
    
    text.append(" ")
    text.append("Statistics of the xml file:")
    text.append(str(citation_cnt) + " Citations, which have references to: " + 
      str(citation_source_cnt) + " Sources,")
    text.append(" ")
    text.append(str(event_cnt) + " Events,")
    text.append(" ")
    text.append(str(event_citation_cnt) + " Citation references in Events,")
    text.append(" ")
    text.append(str(event_no_citation_cnt) + " Events, which do not have a Citation reference \
     (NOTE! This should be near or equal to zero),")
    text.append(" ")
    text.append(str(family_cnt) + " Families, which have references to: " +
      str(family_citation_cnt) + " Citations,")
    text.append(" ")
    text.append(str(note_cnt) + " Notes,")
    text.append(" ")
    text.append(str(object_cnt) + " Objects, which have references to: " +
      str(object_citation_cnt) + " Citations,")
    text.append(" ")
    text.append(str(person_cnt) + " Persons, which have references to: " +
      str(person_citation_cnt) + " Citations,")
    text.append(" ")
    text.append(str(place_cnt) + " Places, which have references to: " +
      str(place_citation_cnt) + " Citations,")
    text.append(" ")
    text.append(str(repository_cnt) + " Repositors and")
    text.append(" ")
    text.append(str(source_cnt) + " Sources, which have references to: " +
      str(source_repository_cnt) + " Repositories")
    text.append(" ")
    text.append("Estimated storing time: " + str(int(e_total)) + " seconds")
    
    return(text)

def analyze_old(username, filename):
    # Read the xml file
    upload_folder = get_upload_folder(username) 
    pathname = os.path.join(upload_folder,filename)
    print("Pathname: " + pathname)
    
    file_cleaned, _file_displ, _cleaning_log = file_clean(pathname)
    
    f = open(file_cleaned, "r")
    
    text = []
    line_cnt = 0
    
    citation_cnt = 0
    event_cnt = 0
    family_cnt = 0
    object_cnt = 0
    person_cnt = 0
    place_cnt = 0
    repository_cnt = 0
    source_cnt = 0
    
    event_line_cnt = 0
    
    citation_source_cnt = 0
    event_citation_cnt = 0
    family_citation_cnt = 0
    object_citation_cnt = 0
    person_citation_cnt = 0
    place_citation_cnt = 0
    source_repository_cnt = 0
    
    event_no_citation_cnt = 0 # How many events do not have any citationref?
    event_with_citation_cnt = 0 # How many citationrefs this event has?
    
    citation_flag = False
    event_flag = False
    family_flag = False
    object_flag = False
    person_flag = False
    place_flag = False
    repository_flag = False
    source_flag = False
    
    event_birth_flag = False
    event_birthdate_flag = False
    event_birth_citation_flag = False

    for line in f:
        line_cnt += 1
        found_private = line.find('priv="1"')
        if found_private > 1:
            fault = "Private attribute in line: " + str(line_cnt)
            text.append(fault)
            text.append(" ")
        word = line.split()
        if len(word) > 0:
            if word[0] == "<citation":
                citation_flag = True
                citation_cnt += 1
            elif word[0] == "</citation":
                citation_flag = False
        
            elif word[0] == "<event":
                event_flag = True
                event_cnt += 1
                event_line_cnt = line_cnt
                event_with_citation_cnt = 0
            elif word[0] == "</event>":
                event_flag = False
                if event_with_citation_cnt == 0:
                    event_no_citation_cnt += 1
                if event_birth_flag == True:
                    if (not event_birthdate_flag) and (not event_birth_citation_flag):
                        fault = "No birthdate nor citationref for a Birth event in line: " + str(event_line_cnt)
                        text.append(fault)
                        text.append(" ")
                    event_birth_flag = False   
                    event_birthdate_flag = False   
                    event_birth_citation_flag = False   
                    
                                     
            elif word[0] == "<family":
                family_flag = True
                family_cnt += 1
            elif word[0] == "</family>":
                family_flag = False
            
            elif word[0] == "<object":
                object_flag = True
                object_cnt += 1
            elif word[0] == "</object>":
                object_flag = False
            
            elif word[0] == "<person":
                person_flag = True
                person_cnt += 1
            elif word[0] == "</person>":
                person_flag = False
            
            elif word[0] == "<placeobj":
                place_flag = True
                place_cnt += 1
            elif word[0] == "</placeobj>":
                place_flag = False
            
            elif word[0] == "<repository":
                repository_flag = True
                repository_cnt += 1
            elif word[0] == "</repository>":
                repository_flag = False
            
            elif word[0] == "<source":
                source_flag = True
                source_cnt += 1
            elif word[0] == "</source>":
                source_flag = False
            
            
            elif word[0] == "<citationref":
                if event_flag:
                    event_citation_cnt += 1
                    event_with_citation_cnt += 1
            
                elif family_flag:
                    family_citation_cnt += 1
            
                elif object_flag:
                    object_citation_cnt += 1
            
                elif place_flag:
                    place_citation_cnt += 1
            
                elif person_flag:
                    person_citation_cnt += 1
                else:
                    print("Unidentified citationref in line: " + str(line_cnt))
            
            
            elif word[0] == "<reporef":
                if source_flag:
                    source_repository_cnt += 1
            
            
            elif word[0] == "<sourceref":
                if citation_flag:
                    citation_source_cnt += 1
                    
        if event_flag:
            birth_found = line.find("Birth")
            if event_birth_flag:
                birthdate_found = line.find("dateval")
                if birthdate_found > 0:
                    event_birthdate_flag = True
                birthdate_found = line.find("daterange")
                if birthdate_found > 0:
                    event_birthdate_flag = True
                birthdate_found = line.find("datespan")
                if birthdate_found > 0:
                    event_birthdate_flag = True
                birth_citation_found = line.find("citationref")
                if birth_citation_found > 0:
                    event_birth_citation_flag = True
            elif birth_found > 0:
                event_birth_flag = True
                    


    text.append(" ")
    text.append("Statistics of the xml file:")
    text.append(str(citation_cnt) + " Citations, which have references to: " + 
      str(citation_source_cnt) + " Sources,")
    text.append(" ")
    text.append(str(event_cnt) + " Events,")
    text.append(" ")
    text.append(str(event_citation_cnt) + " Citation references in Events,")
    text.append(" ")
    text.append(str(event_no_citation_cnt) + " Events, which do not have Citation references,")
    text.append(" ")
    text.append(str(family_cnt) + " Families, which have references to: " +
      str(family_citation_cnt) + " Citations,")
    text.append(" ")
    text.append(str(object_cnt) + " Objects, which have references to: " +
      str(object_citation_cnt) + " Citations,")
    text.append(" ")
    text.append(str(person_cnt) + " Persons, which have references to: " +
      str(person_citation_cnt) + " Citations,")
    text.append(" ")
    text.append(str(place_cnt) + " Places, which have references to: " +
      str(place_citation_cnt) + " Citations,")
    text.append(" ")
    text.append(str(repository_cnt) + " Repositors and")
    text.append(" ")
    text.append(str(source_cnt) + " Sources, which have references to: " +
      str(source_repository_cnt) + " Repositories")
    
    f.close()
    
    return(text)

def xml_to_neo4j(pathname, userid='Taapeli'):
    """ 
    Reads a Gramps xml file, and saves the information to db 
    
    Metacode for batch log creation UserProfile --> Batch.

    # Start a Batch 
        routes.upload_gramps / models.loadfile.upload_file >
            # Create id / bp.gramps.batchlogger.Batch._create_id
            match (p:UserProfile {username:"jussi"}); 
            create (p) -[:HAS_LOADED]-> (b:Batch {id:"2018-06-02.0", status:"started"}) 
            return b
    # Load the file (in routes.save_loaded_gramps) 
        models.loadfile.upload_file > status:"started"
        # Clean apostrophes
        file clean > status:"loading"
    # Käsittele tietoryhmä 1
        models.gramps.gramps_loader.xml_to_neo4j > status:"storing" 
    # Käsittele tietoryhmä 2 ...
    # ...
    # Käsittele henkilöt
        models.gramps.gramps_loader.xml_to_neo4j > status:"storing"
    # Viimeistele data
        models.gramps.gramps_loader.xml_to_neo4j > status:"storing"
    # Merkitse valmiiksi
        status:"done"

        match (p:UserProfile {username:"jussi"}); 
        match (p) -[r:CURRENT_LOAD]-> () delete r
        create (p) -[:CURRENT_LOAD]-> (b)
    """

    ''' Uncompress and hide apostrophes for DOM handler (and save log)
    '''
    file_cleaned, file_displ, cleaning_log = file_clean(pathname)

    ''' Get XML DOM parser and start DOM elements handler transaction '''
    handler = DOM_handler(file_cleaned, userid, pathname)

    # Initialize Run report
    handler.blog = Batch(userid)
    handler.blog.log_event({'title':"Storing data from Gramps", 'level':"TITLE"})
    handler.blog.log_event({'title':"Loaded file '{}'".format(file_displ),
                            'elapsed':shareds.tdiff})
    handler.blog.log(cleaning_log)
    t0 = time.time()

    handler.batch_id = handler.blog.start_batch(None, file_cleaned)

    if pathname.endswith(".gpkg"):
        extract_media(pathname,handler.batch_id)
    
    try:
        ''' Start DOM transaction '''
        handler.begin_tx(shareds.driver.session())
        # Create new Batch node and start
        #status_update({'percent':1})
        
        try:
            handler.handle_header()
            
            handler.handle_notes()
            handler.handle_repositories()
            handler.handle_media()
        
            handler.handle_places()
            handler.handle_sources()
            handler.handle_citations()
        
            handler.handle_events()
            handler.handle_people()
            handler.handle_families()
    
#             for k in handler.handle_to_node.keys():
#                 print (f'\t{k} –> {handler.handle_to_node[k]}')
                
            # Set person confidence values 
            #TODO: Only for imported persons (now for all persons!)
            dataupdater.set_confidence_values(handler.tx, batch_logger=handler.blog)
            # Set properties (for imported persons)
            #    + Refname links
            #    ? Person sortname
            #    + Person lifetime
            #    - Confidence values
            handler.set_person_sortname_refnames()
            handler.set_estimated_person_dates()
            
            # Copy date and name information from Person and Event nodes to Family nodes
            handler.set_family_sortname_dates()

            handler.remove_handles()
            handler.add_missing_links()

# Huom. Paikkahierarkia on tehty metodissa Place_gramps.save niin että
#       aluksi luodaan tarvittaessa viitattu ylempi paikka vajailla tiedoilla.
#             # Make the place hierarchy
#             handler.make_place_hierarchy()

        except Exception as e:
            traceback.print_exc()
            msg = f"Stopped xml load due to {e}"    # Stop processing?
            print(msg)
            handler.commit(rollback=True)
            return handler.blog.list(), None

        handler.blog.complete(handler.tx)
        handler.commit()

    except ConnectionError as err:
        print("iError ConnectionError {0}".format(err))
        handler.blog.log_event(title=_("Database save failed due to {} {}".\
                                     format(err.message, err.code)), level="ERROR")
        raise SystemExit("Stopped due to ConnectionError")    # Stop processing?

    handler.blog.log_event({'title':"Total time", 'level':"TITLE", 
                            'elapsed':time.time()-t0})  #, 'percent':100})
    return handler.blog.list(), handler.batch_id


# def create_thumbnails(media_folder):
#     print("walk")
#     for dirname,dirnames,filenames in os.walk(media_folder):
#         print(dirname,dirnames,filenames)
#         for name in filenames:
#             fname = os.path.join(dirname,name)
#             thumbnail_fname = "media/thumbnails/" + fname


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
        # Creates the output file and closes it
        if ext == ".gpkg": # gzipped tar file with embedded gzipped 'data.gramps' xml file
            with gzip.open(TarFile(fileobj=gzip.GzipFile(pathname)).extractfile('data.gramps'),
                           mode='rt',encoding='utf-8') as file_in:
                counter = _clean_apostrophes(file_in, file_out)
            msg = "Cleaned apostrophes from .gpkg input file" # Try to read a gzipped file
        else: # .gramps: either gzipped or plain xml file
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
                     'elapsed':time.time()-t0}) #, 'percent':1})
    return (file_cleaned, file_displ, event)

def extract_media(pathname,batch_id):
    try:
        media_files_folder = media.get_media_files_folder(batch_id)
        os.makedirs(media_files_folder, exist_ok=True)
        TarFile(fileobj=gzip.GzipFile(pathname)).extractall(path=media_files_folder)
        xml_filename = os.path.join(media_files_folder,"data.gramps")
        os.remove(xml_filename)
    except:
        traceback.print_exc()
    #create_thumbnails(media_folder)
