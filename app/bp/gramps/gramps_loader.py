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
from models.dataupdater import set_confidence_values
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
        handler.batch_id = handler.blog.start_batch(handler.tx, file_cleaned)
        #status_update({'percent':1})

        try:
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
            set_confidence_values(handler.tx, batch_logger=handler.blog)
            # Set properties (for imported persons)
            #    + Refname links
            #    ? Person sortname
            #    + Person lifetime
            #    - Confidence values
            handler.set_person_sortname_refnames()
            handler.set_estimated_person_dates()
            
            # Copy information from Person and Event nodes to Family nodes
            handler.set_family_sortname_dates()

        except Exception as e:
            print("Stopped xml load due to {}".format(e))    # Stop processing?
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
                     'elapsed':time.time()-t0}) #, 'percent':1})
    return (file_cleaned, file_displ, event)

