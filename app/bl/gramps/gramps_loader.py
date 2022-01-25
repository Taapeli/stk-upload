#   Isotammi Genealogical Service for combining multiple researchers' results.
#   Created in co-operation with the Genealogical Society of Finland.
#
#   Copyright (C) 2016-2021  Juha Mäkeläinen, Jorma Haapasalo, Kari Kujansuu,
#                            Timo Nallikari, Pekka Valta
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
    Methods to import all data from Gramps xml file

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
"""

import gzip
import logging
import os
import time
import traceback

from tarfile import TarFile

logger = logging.getLogger("stkserver")

from flask_babelex import _

import shareds
from models import mediafile

from .xml_dom_handler import DOM_handler
from .batchlogger import BatchLog, LogItem

from bl.base import Status
from bl.admin.models.data_admin import DataAdmin
#from bl.batch.root import State, DEFAULT_MATERIAL 

def get_upload_folder(username):
    """ Returns upload directory for given user"""
    return os.path.join("uploads", username)

def analyze_xml(username, batch_id, filename):
    """Returns a dict of Gramps xml object type counts."""
    # Read the xml file
    upload_folder = get_upload_folder(username)
    pathname = os.path.join(upload_folder, batch_id, filename)
    print("bp.gramps.gramps_loader.analyze_xml Pathname: " + pathname)

    file_cleaned, file_displ, cleaning_log, is_gpkg = file_clean(pathname)

    """ Get XML DOM parser and start DOM elements handler transaction """
    handler = DOM_handler(file_cleaned, username, filename, dataservice=None)

    citation_source_cnt = 0
    event_citation_cnt = 0
    family_citation_cnt = 0
    object_citation_cnt = 0
    person_citation_cnt = 0
    place_citation_cnt = 0
    source_repository_cnt = 0

    event_no_citation_cnt = 0  # How many events do not have any citationref?

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

    citations = handler.xml_tree.getElementsByTagName("citation")
    citation_cnt = len(citations)
    if citation_cnt > 0:
        e_total += citation_cnt * e_citation / 1000
        for citation in citations:
            citation_source_cnt += len(citation.getElementsByTagName("sourceref"))

    events = handler.xml_tree.getElementsByTagName("event")
    event_cnt = len(events)
    if event_cnt > 0:
        e_total += event_cnt * e_event / 1000
        for event in events:
            event_citation_cnt += len(event.getElementsByTagName("citationref"))
            if len(event.getElementsByTagName("citationref")) == 0:
                event_no_citation_cnt += 1

    families = handler.xml_tree.getElementsByTagName("family")
    family_cnt = len(families)
    if family_cnt > 0:
        e_total += family_cnt * e_family / 1000
        for family in families:
            family_citation_cnt += len(family.getElementsByTagName("citationref"))

    notes = handler.xml_tree.getElementsByTagName("note")
    note_cnt = len(notes)
    if note_cnt > 0:
        e_total += note_cnt * e_note / 1000

    objects = handler.xml_tree.getElementsByTagName("object")
    object_cnt = len(objects)
    if object_cnt > 0:
        e_total += object_cnt * e_object / 1000
        for media in objects:
            object_citation_cnt += len(media.getElementsByTagName("citationref"))

    persons = handler.xml_tree.getElementsByTagName("person")
    person_cnt = len(persons)
    if person_cnt > 0:
        e_total += person_cnt * e_person / 1000
        for person in persons:
            person_citation_cnt += len(person.getElementsByTagName("citationref"))

    places = handler.xml_tree.getElementsByTagName("placeobj")
    place_cnt = len(places)
    if place_cnt > 0:
        e_total += place_cnt * e_place / 1000
        for place in places:
            place_citation_cnt += len(place.getElementsByTagName("citationref"))

    repositorys = handler.xml_tree.getElementsByTagName("repository")
    repository_cnt = len(repositorys)
    if repository_cnt > 0:
        e_total += repository_cnt * e_repository / 1000

    sources = handler.xml_tree.getElementsByTagName("source")
    source_cnt = len(sources)
    if source_cnt > 0:
        e_total += source_cnt * e_source / 1000
        for source in sources:
            source_repository_cnt += len(source.getElementsByTagName("reporef"))

    counts = {}
    # This avoids RuntimeError: dictionary changed size during iteration
    items = list(locals().items())
    for item in items:
        if item[0].endswith("_cnt"):
            counts[item[0]] = item[1]
    counts["e_total"] = e_total
    return counts


def analyze(username, filename):
    """Returns a list of Analyze_row objects carrying number of items and references."""
    values = analyze_xml(username, filename)

    references = []

    class Analyze_row:
        pass

    row = Analyze_row()
    row.individ = _("Events with no references to")
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
    row.individ = _("Estimated time")
    e_total = values["e_total"]
    row.number_of_individs = " "
    row.reference = _("sec")
    row.number_of_references = str(int(e_total))

    references.append(row)

    return references


def xml_to_stkbase(batch):  # :Root):
    """
    Reads a Gramps xml file, and saves the information to db
    """
    from bl.batch.root_updater import RootUpdater
    from bl.batch.root import State, DEFAULT_MATERIAL

    t0 = time.time()

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
        handler.blog.log_event({"title": "Statistic of Gramps data storing", "level": "TITLE"})
        handler.blog.log_event({"title": f"Loaded file '{file_displ}'", 
                                "count": 1, 
                                "elapsed": shareds.tdiff}
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

        # batch.save(batch_service.dataservice.tx)
        with shareds.driver.session() as session:
            session.write_transaction(batch.save) 

        if is_gpkg:
            extract_media(batch.file, batch.id)

    handler.handle_notes()
    handler.handle_repositories()
    handler.handle_sources()
    handler.handle_citations()
    handler.handle_media()
    handler.handle_places() # With Place_names
    handler.handle_events()
    handler.handle_people() # With Names
    handler.handle_families()

    #       for k in handler.handle_to_node.keys():
    #             print (f'\t{k} –> {handler.handle_to_node[k]}')

    # if 0:
    #     res = handler.set_person_calculated_attributes()
    #     res = handler.set_person_estimated_dates()
    #
    #     # Copy date and name information from Person and Event nodes to Family nodes
    #     res = handler.set_family_calculated_attributes()
    #
    #     # print("build_free_text_search_indexes")
    #     t1 = time.time()
    #     res = DataAdmin.build_free_text_search_indexes(batch_service.dataservice.tx, batch.id)
    #     handler.blog.log_event(
    #         {"title": _("Free text search indexes"), "elapsed": time.time() - t1}
    #     )
    #     # print("build_free_text_search_indexes done")
            
    with RootUpdater("update") as batch_service:
        handler.dataservice = batch_service.dataservice
        handler.set_all_person_confidence_values()
        handler.set_person_calculated_attributes()
        handler.set_person_estimated_dates()
    
        # Copy date and name information from Person and Event nodes to Family nodes
        handler.set_family_calculated_attributes()
    
        # print("build_free_text_search_indexes")
        t1 = time.time()
        _res = DataAdmin.build_free_text_search_indexes(batch_service.dataservice.tx, batch.id)
        handler.blog.log_event(
            {"title": _("Free text search indexes"), "elapsed": time.time() - t1}
        )

        handler.remove_handles()
        batch_service.change_state(batch.id, batch.user, State.ROOT_CANDIDATE)

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

def file_clean(pathname):
    # Decompress file and clean problematic delimiter (').
    # - build 2nd filename
    # - create LogItem item in the upload log

    def _clean_apostrophes(file_in, file_out):
        """
        Replace each "'" with corresponding entity to avoid mismatches.
        They are actually stored as "'" after processing

        Returns the count of changed lines
        """
        n = 0
        for line in file_in:
            if "'" in line:
                line = line.replace("'", "&apos;")
                n += 1
            file_out.write(line)
        return n

    t0 = time.time()
    root, ext = os.path.splitext(pathname)
    file_cleaned = root + "_clean" + ext
    # Filename for display
    file_displ = os.path.basename(pathname)
    with open(file_cleaned, "w", encoding="utf-8") as file_out:
        # Creates the output file and closes it

        try:  # .gpkg: gzipped tar file with embedded gzipped 'data.gramps' xml file
            with gzip.open(
                TarFile(fileobj=gzip.GzipFile(pathname)).extractfile("data.gramps"),
                mode="rt",
                encoding="utf-8",
            ) as file_in:
                counter = _clean_apostrophes(file_in, file_out)
            msg = "Cleaned apostrophes from .gpkg input file"  
            event = LogItem(
                {"title": msg, "count": counter, "elapsed": time.time() - t0}
            )
            return (file_cleaned, file_displ, event, True)
        except: 
            pass

        try: # .gramps:  gzipped xml file
            with gzip.open(
                pathname, mode="rt", encoding="utf-8", compresslevel=9
            ) as file_in:
                # print("A gzipped file")
                counter = _clean_apostrophes(file_in, file_out)
            msg = "Cleaned apostrophes from packed input lines"
            event = LogItem(
                {"title": msg, "count": counter, "elapsed": time.time() - t0}
            )
            return (file_cleaned, file_displ, event, False)
        except:
            pass

        try: # .gramps:  plain xml file
            with open(pathname, mode="rt", encoding="utf-8") as file_in:
                print("Not a gzipped file")
                counter = _clean_apostrophes(file_in, file_out)
            msg = "Cleaned apostrophes from input lines"
            event = LogItem(
                {"title": msg, "count": counter, "elapsed": time.time() - t0}
            )
            return (file_cleaned, file_displ, event, False)
        except:
            raise RuntimeError(_("Unable to open Gramps file"))


def extract_media(pathname, batch_id):
    """Save media files from Gramps .gpkg package."""
    try:
        media_files_folder = mediafile.get_media_files_folder(batch_id)
        os.makedirs(media_files_folder, exist_ok=True)
        TarFile(fileobj=gzip.GzipFile(pathname)).extractall(path=media_files_folder)
        xml_filename = os.path.join(media_files_folder, "data.gramps")
        os.remove(xml_filename)
    except:
        traceback.print_exc()
