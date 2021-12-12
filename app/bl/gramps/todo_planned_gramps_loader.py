'''
Alustava suunnitelma uudistettuun gramps-lataukseen

Created on 12.12.2021

@author: jm
'''
from bl.admin.models.data_admin import DataAdmin
from flask.globals import session

"""
    Methods to import all data from Gramps xml file

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
"""
import logging
import time
from flask_babelex import _
import shareds
#from models import mediafile
from .xml_dom_handler import DOM_handler
from .batchlogger import BatchLog #, LogItem
from bl.base import Status

logger = logging.getLogger("stkserver")

def xml_to_stkbase(batch):  # :Root):
    """
    Reads a Gramps xml file, and saves the information to db
    """
    from bl.batch.root_updater import RootUpdater
    from bl.batch.root import State, DEFAULT_MATERIAL

    # Uncompress and hide apostrophes (and save log)
    file_cleaned, file_displ, cleaning_log, is_gpkg = file_clean(batch.file)

    """
        Root-solmun luonti aivan kuin viime versiossa, mutta transaktion
        luonti jää RootUpdaterin asiaksi
    """
    with RootUpdater("update") as batch_service:
        # Get XML DOM parser and start DOM elements handler transaction
        handler = DOM_handler(file_cleaned, batch.user, batch.file, batch_service.dataservice)
    
        # Initialize Run report
        handler.blog = BatchLog(batch.user)
        handler.blog.log_event({"title": "Storing data from Gramps", "level": "TITLE"})
        handler.blog.log_event(
            {"title": "Loaded file '{}'".format(file_displ), "elapsed": shareds.tdiff}
        )
        handler.blog.log(cleaning_log)
    
        handler.batch = batch
        batch.mediapath = handler.get_mediapath_from_header()
    
        metadata = handler.get_metadata_from_header()
        print("gramps_loader.xml_to_stkbase: metadata:", metadata)
        if metadata:
            if metadata[0]:
                batch.material_type = metadata[0]
                print(f"- got material type {batch.material_type} {metadata[1]!r}")
        if batch.material_type is None:
            batch.material_type = DEFAULT_MATERIAL
            print(f"- default material type {batch.material_type}")
        handler.handle_suffix = "_" + handler.batch.id  
    
        batch.save(batch_service.dataservice.tx)
        
        t0 = time.time()

        if is_gpkg:
            extract_media(batch.file, batch.id)

        """ DOM-objektit pätkitään 1000 joukkoihin ja tarjotaan handlerille
        """
        def get_first(objs:list, amount:int):
            #TODO Sijoita handler-metodiksi ja pätki lista
            return objs

        """ Notes transaktioiden sisällä """
        notes = handler.xml_tree.getElementsByTagName("note")
        for dom_notes in get_first(notes, 1000):
            with shareds.driver.session() as session:
                session.write_transaction(handle_notes_tx, dom_objs=dom_notes, ...)
                """ sisältää handler.handle_notes -toiminnot
                """
        """ Toiset samalla tavalla """
        res = handler.handle_repositories()
        res = handler.handle_sources()
        res = handler.handle_citations()
        res = handler.handle_media()
        res = handler.handle_places() # With Place_names
        res = handler.handle_events()
        res = handler.handle_people() # With Names
        res = handler.handle_families()

        #       for k in handler.handle_to_node.keys():
        #             print (f'\t{k} –> {handler.handle_to_node[k]}')

        res = handler.set_all_person_confidence_values()
        res = handler.set_person_calculated_attributes()
        res = handler.set_person_estimated_dates()

        # Copy date and name information from Person and Event nodes to Family nodes
        res = handler.set_family_calculated_attributes()

        # print("build_free_text_search_indexes")
        t1 = time.time()
        res = DataAdmin.build_free_text_search_indexes(batch_service.dataservice.tx, batch.id)
        handler.blog.log_event(
            {"title": _("Free text search indexes"), "elapsed": time.time() - t1}
        )
        # print("build_free_text_search_indexes done")
            
        res = handler.remove_handles()
        # The missing links counted in remove_handles?
        ##TODO      res = handler.add_missing_links()?

        res = batch_service.change_state(batch.id, batch.user, State.ROOT_CANDIDATE)
        #es = batch_service.batch_mark_status(batch, State.ROOT_CANDIDATE)

        tx = batch_service.dataservice.tx
        if not tx.closed():
            print(f"bl.gramps.gramps_loader.xml_to_stkbase: commit")
            tx.commit()
        logger.info(f'-> bp.gramps.gramps_loader.xml_to_stkbase/ok f="{handler.file}"')

        handler.blog.log_event(
            {"title": "Total time", "level": "TITLE", "elapsed": time.time() - t0}
        )

    # End with BatchUpdater

    return {
        "status": Status.OK,
        "steps": handler.blog.list(),
        "batch_id": handler.batch.id,
    }
