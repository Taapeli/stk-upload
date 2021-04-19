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

import time
import gzip
from os.path import basename, splitext
import logging

logger = logging.getLogger("stkserver")
from flask_babelex import _
import traceback
from tarfile import TarFile
import os

from .xml_dom_handler import DOM_handler
from .batchlogger import BatchLog, LogItem
import shareds
from bl.base import Status
from bp.scene.models import media


def get_upload_folder(username):
    """ Returns upload directory for given user"""
    return os.path.join("uploads", username)


def analyze_xml(username, filename):
    """Returns a dict of Gremp xml objec type counts."""
    # Read the xml file
    upload_folder = get_upload_folder(username)
    pathname = os.path.join(upload_folder, filename)
    print("bp.gramps.gramps_loader.analyze_xml Pathname: " + pathname)

    file_cleaned, file_displ, cleaning_log = file_clean(pathname)

    """ Get XML DOM parser and start DOM elements handler transaction """
    handler = DOM_handler(file_cleaned, username, filename)

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

    citations = handler.collection.getElementsByTagName("citation")
    citation_cnt = len(citations)
    if citation_cnt > 0:
        e_total += citation_cnt * e_citation / 1000
        for citation in citations:
            citation_source_cnt += len(citation.getElementsByTagName("sourceref"))

    events = handler.collection.getElementsByTagName("event")
    event_cnt = len(events)
    if event_cnt > 0:
        e_total += event_cnt * e_event / 1000
        for event in events:
            event_citation_cnt += len(event.getElementsByTagName("citationref"))
            if len(event.getElementsByTagName("citationref")) == 0:
                event_no_citation_cnt += 1

    families = handler.collection.getElementsByTagName("family")
    family_cnt = len(families)
    if family_cnt > 0:
        e_total += family_cnt * e_family / 1000
        for family in families:
            family_citation_cnt += len(family.getElementsByTagName("citationref"))

    notes = handler.collection.getElementsByTagName("note")
    note_cnt = len(notes)
    if note_cnt > 0:
        e_total += note_cnt * e_note / 1000

    objects = handler.collection.getElementsByTagName("object")
    object_cnt = len(objects)
    if object_cnt > 0:
        e_total += object_cnt * e_object / 1000
        for media in objects:
            object_citation_cnt += len(media.getElementsByTagName("citationref"))

    persons = handler.collection.getElementsByTagName("person")
    person_cnt = len(persons)
    if person_cnt > 0:
        e_total += person_cnt * e_person / 1000
        for person in persons:
            person_citation_cnt += len(person.getElementsByTagName("citationref"))

    places = handler.collection.getElementsByTagName("placeobj")
    place_cnt = len(places)
    if place_cnt > 0:
        e_total += place_cnt * e_place / 1000
        for place in places:
            place_citation_cnt += len(place.getElementsByTagName("citationref"))

    repositorys = handler.collection.getElementsByTagName("repository")
    repository_cnt = len(repositorys)
    if repository_cnt > 0:
        e_total += repository_cnt * e_repository / 1000

    sources = handler.collection.getElementsByTagName("source")
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


# def analyze_old2(username, filename):


def xml_to_stkbase(pathname, userid):
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
        models.gramps.gramps_loader.xml_to_stkbase > status:"storing"
    # Käsittele tietoryhmä 2 ...
    # ...
    # Käsittele henkilöt
        models.gramps.gramps_loader.xml_to_stkbase > status:"storing"
    # Viimeistele data
        models.gramps.gramps_loader.xml_to_stkbase > status:"storing"
    # Merkitse valmiiksi
        status:"done"

        match (p:UserProfile {username:"jussi"});
        match (p) -[r:CURRENT_LOAD]-> () delete r
        create (p) -[:CURRENT_LOAD]-> (b)
    """
    from bl.batch import BatchUpdater

    # Uncompress and hide apostrophes (and save log)
    file_cleaned, file_displ, cleaning_log = file_clean(pathname)

    # Get XML DOM parser and start DOM elements handler transaction
    handler = DOM_handler(file_cleaned, userid, pathname)

    # Initialize Run report
    handler.blog = BatchLog(userid)
    handler.blog.log_event({"title": "Storing data from Gramps", "level": "TITLE"})
    handler.blog.log_event(
        {"title": "Loaded file '{}'".format(file_displ), "elapsed": shareds.tdiff}
    )
    handler.blog.log(cleaning_log)

    # Open database connection as Neo4jDataService instance and start transaction

    # Initiate BatchUpdater and Batch node data
    ##shareds.datastore = BatchUpdater(shareds.driver, handler.dataservice)
    with BatchUpdater("update") as batch_service:
        print(
            f'#> bp.gramps.gramps_loader.xml_to_stkbase: "{batch_service.service_name}" service'
        )
        mediapath = handler.get_mediapath_from_header()
        res = batch_service.start_data_batch(
            userid, file_cleaned, mediapath, batch_service.dataservice.tx
        )
        if Status.has_failed(res):
            print("bp.gramps.gramps_loader.xml_to_stkbase TODO _rollback")
            return res
        handler.batch = res.get("batch")

        t0 = time.time()

        if pathname.endswith(".gpkg"):
            extract_media(pathname, handler.batch.id)

        try:
            # handler.handle_header() --> get_header_mediapath()
            res = handler.handle_notes()
            if Status.has_failed(res):
                return res
            res = handler.handle_repositories()
            if Status.has_failed(res):
                return res
            res = handler.handle_media()
            if Status.has_failed(res):
                return res

            res = handler.handle_places()
            if Status.has_failed(res):
                return res
            res = handler.handle_sources()
            if Status.has_failed(res):
                return res
            res = handler.handle_citations()
            if Status.has_failed(res):
                return res

            res = handler.handle_events()
            if Status.has_failed(res):
                return res
            res = handler.handle_people()
            if Status.has_failed(res):
                return res
            res = handler.handle_families()
            if Status.has_failed(res):
                return res

            #       for k in handler.handle_to_node.keys():
            #             print (f'\t{k} –> {handler.handle_to_node[k]}')

            # Set person confidence values
            # TODO: Only for imported persons (now for all persons!)
            res = handler.set_all_person_confidence_values()
            if Status.has_failed(res):
                return res
            res = handler.set_person_calculated_attributes()
            if Status.has_failed(res):
                return res
            res = handler.set_person_estimated_dates()
            if Status.has_failed(res):
                return res

            # Copy date and name information from Person and Event nodes to Family nodes
            res = handler.set_family_calculated_attributes()
            if Status.has_failed(res):
                return res

            res = handler.remove_handles()
            if Status.has_failed(res):
                return res
            # The missing links counted in remove_handles
        ##TODO      res = handler.add_missing_links()

        except Exception as e:
            traceback.print_exc()
            msg = f"Stopped xml load due to {e}"
            print(msg)
            batch_service.rollback()
            handler.blog.log_event(
                {
                    "title": _("Database save failed due to {}".format(msg)),
                    "level": "ERROR",
                }
            )
            return {"status": Status.ERROR, "statustext": msg}

        res = batch_service.mark_complete()
        if Status.has_failed(res):
            msg = res.get("statustext", "")
            batch_service.rollback()
            handler.blog.log_event(
                {
                    "title": _("Database save failed due to {}".format(msg)),
                    "level": "ERROR",
                }
            )
            return {
                "status": res.get("status"),
                "statustest": msg,
                "steps": handler.blog.list(),
                "batch_id": handler.batch.id,
            }

        # batch_service.commit()
        logger.info(f'-> bp.gramps.gramps_loader.xml_to_stkbase/ok f="{handler.file}"')

        handler.blog.log_event(
            {"title": "Total time", "level": "TITLE", "elapsed": time.time() - t0}
        )
    # End with BatchUpdater transaction

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
    root, ext = splitext(pathname)
    file_cleaned = root + "_clean" + ext
    # Filename for display
    file_displ = basename(pathname)
    with open(file_cleaned, "w", encoding="utf-8") as file_out:
        # Creates the output file and closes it
        if (
            ext == ".gpkg"
        ):  # gzipped tar file with embedded gzipped 'data.gramps' xml file
            with gzip.open(
                TarFile(fileobj=gzip.GzipFile(pathname)).extractfile("data.gramps"),
                mode="rt",
                encoding="utf-8",
            ) as file_in:
                counter = _clean_apostrophes(file_in, file_out)
            msg = "Cleaned apostrophes from .gpkg input file"  # Try to read a gzipped file
        else:  # .gramps: either gzipped or plain xml file
            try:
                with gzip.open(
                    pathname, mode="rt", encoding="utf-8", compresslevel=9
                ) as file_in:
                    # print("A gzipped file")
                    counter = _clean_apostrophes(file_in, file_out)
                msg = "Cleaned apostrophes from packed input lines"  # Try to read a gzipped file
            except OSError:  # Not gzipped; Read as an ordinary file
                with open(pathname, mode="rt", encoding="utf-8") as file_in:
                    print("Not a gzipped file")
                    counter = _clean_apostrophes(file_in, file_out)
                msg = "Cleaned apostrophes from input lines"
        event = LogItem(
            {"title": msg, "count": counter, "elapsed": time.time() - t0}
        )  # , 'percent':1})
    return (file_cleaned, file_displ, event)


def extract_media(pathname, batch_id):
    """Save media files from Gramps .gpkg package."""
    try:
        media_files_folder = media.get_media_files_folder(batch_id)
        os.makedirs(media_files_folder, exist_ok=True)
        TarFile(fileobj=gzip.GzipFile(pathname)).extractall(path=media_files_folder)
        xml_filename = os.path.join(media_files_folder, "data.gramps")
        os.remove(xml_filename)
    except:
        traceback.print_exc()
