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
Extracted from gramps_loader.py on 2.12.2018

    Methods to import all data from Gramps xml file

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
"""

import logging

logger = logging.getLogger("stkserver")

from collections import defaultdict
import re
import time
import os
import xml.dom.minidom
import json
import threading
from flask_babelex import _

import shareds
from bl.base import NodeObject, Status
from bl.person import PersonBl #, PersonWriter
from bl.person_name import Name
from bl.place import PlaceName, PlaceBl
from bl.place_coordinates import Point
from bl.media import MediaBl, MediaReferenceByHandles
from bl.event import EventBl
from bl.note import Note
from bl.dates import Gramps_DateRange
from bl.citation import Citation
from bl.repository import Repository
from bl.source import SourceBl
from pe.neo4j.util import IsotammiIds
from bl.gramps.batchlogger import LogItem


class DOM_handler:
    """XML DOM elements handler
    - processes different data groups from given xml file to database
    - collects status log
    """
    TX_SIZE=1000     # Transaction max size
    
    def __init__(self, infile, current_user, pathname, dataservice):
        """ Set DOM xml_tree and username """
        DOMTree = xml.dom.minidom.parse(open(infile, encoding="utf-8"))
        self.xml_tree = DOMTree.documentElement  # XML documentElement
        self.username = current_user  # current username
        self.dataservice = dataservice
        
        #!self.handle_to_node = {}  # {handle:(iid, uniq_id)}
        self.person_ids = []  # List of processed Person node unique id's
        self.family_ids = []  # List of processed Family node unique id's
        # self.batch = None                     # Batch node to be created
        # self.mediapath = None                 # Directory for media files
        self.file = os.path.basename(pathname)  # for messages
        self.progress = defaultdict(int)
        # self.obj_counter = 0
        self.noterefs_later = []    # NodeObjects with obj.notes to be saved later
        # self.notes_to_postprocess = NodeObject(uniq_id = 0)
        # self.notes_to_postprocess.notes = []
        # self.notes_to_postprocess.id = "URL"

    def get_chunk(self, objs:list, amount):
        """ Split list to chunks of amount. """
        i = 0
        i_amount = int(amount)
        while i < len(objs):
            yield objs[i:i+i_amount]
            i += i_amount

    def obsolete_unused_remove_handles(self):
        """Remove all Gramps handles, becouse they are not needed any more."""
        res = self.dataservice.ds_obj_remove_gramps_handles(self.batch.id)
        print(f'# --- removed handles from {res.get("count")} nodes')
        return res

    def obsolete_add_missing_links(self):
        """Link the Nodes without OWNS link to Batch"""
        from pe.neo4j.cypher.cy_root import CypherRoot

        result = self.tx.run(CypherRoot.add_missing_links, batch_id=self.batch_id)
        counters = shareds.db.consume_counters(result)
        if counters.relationships_created:
            print(f"Created {counters.relationships_created} relations")

    def update_progress(self, key):
        """Save status for displaying progress bar"""
        self.progress[key] += 1
        this_thread = threading.current_thread()
        this_thread.progress = dict(self.progress)

    def test_only_save_and_link_handle(self, obj, **kwargs):
        """Save object and store its identifiers in the dictionary by handle.

        Some objects may accept arguments like batch_id="2019-08-26.004" and others
        """
        obj.save(self.dataservice.tx, **kwargs)
        # removed: ... print(self.obj_counter, "Transaction restart")

        #!self.handle_to_node[obj.handle] = (obj.iid, obj.uniq_id)
        self.update_progress(obj.__class__.__name__)

    def complete(self, obj:NodeObject, url_notes = None):
        """ Complete object saving. """
        # 1. Store handle to iid, uniq_id conversion
        #!self.handle_to_node[obj.handle] = obj.iid   #!, obj.uniq_id)
        # 2. Note references from url field must be processed later
        if url_notes:
            # Create referencing object stub with important parameters
            parent = NodeObject(obj.iid)
            parent.id = obj.id
            parent.notes = url_notes # List of Notes objects
            self.noterefs_later.append(parent)

        # 3. Progress bar
        self.update_progress(obj.__class__.__name__)

    # ---------------------   XML subtree handlers   --------------------------

    def get_mediapath_from_header(self):
        """Pick eventual media path from XML header to Batch node."""
        for header in self.xml_tree.getElementsByTagName("header"):
            for mediapath in header.getElementsByTagName("mediapath"):
                if len(mediapath.childNodes) > 0:
                    return mediapath.childNodes[0].data
        return None

    def get_metadata_from_header(self):
        """Extract Isotammi metadata from XML header"""
        for header in self.xml_tree.getElementsByTagName("header"):
            for node in header.childNodes:
                #print("node:",node,type(node),node.nodeName,node.nodeType,node.nodeValue)
                if node.nodeName == "isotammi":
                    material_type, description = self.get_isotammi_metadata(node)
                    self.blog.log_event(
                        {"title": _("Material type"), "level": "TITLE", 
                         "count": f"{material_type} {description!r}\n"}
                    )
                    return material_type, description
        return None, None

    def get_isotammi_metadata(self, isotammi_node):
        material_type = None
        description = None
        for node in isotammi_node.childNodes:
            #print("node:",node,type(node),node.nodeName,node.nodeType,node.nodeValue)
            if node.nodeName == "#text":
                #print("- data:",node.data)
                pass
            elif node.nodeName == "researcher-info":
                pass
            elif node.nodeName == "material_type":
                material_type = node.childNodes[0].data
            elif node.nodeName == "user_description":
                description = node.childNodes[0].data.strip()
            else:
                print(f"DOM_handler.get_isotammi_metadata: Unsupported element in <isotammi>: {node.nodeName}")
        return (material_type, description)

    def handle_dom_nodes(self, tag, title, transaction_function, chunk_max_size):
        """ Get all the notes in the xml_tree. """

        """ DOM-objects are split to chunk_max_size chunks and given to handler
        """

        """ 
        ---- Process DOM nodes inside transaction 
        """
        dom_nodes = self.xml_tree.getElementsByTagName(tag)
        message = f"{tag}: {len(dom_nodes)} kpl"
        print(f"***** {message} *****")
        t0 = time.time()
        counter = 0
    
        with shareds.driver.session() as session:
            iid_generator = IsotammiIds(session, obj_name=title)
            for nodes_chunk in self.get_chunk(dom_nodes, chunk_max_size):
                chunk_size = len(nodes_chunk)
                iid_generator.reserve(chunk_size)
                print(f"#handle_dom_nodes: new tx for {chunk_size} {iid_generator.iid_type} nodes")
                session.write_transaction(transaction_function, 
                                          nodes=nodes_chunk,
                                          iids=iid_generator)
                counter += chunk_size
                
        self.blog.log_event(
            {"title": title, "count": counter, "elapsed": time.time() - t0}
        )
        return counter

        
    def handle_citations(self):
        self.handle_dom_nodes("citation", _("Citations"),
                              self.handle_citations_list, chunk_max_size=self.TX_SIZE)

    def handle_events(self):
        self.handle_dom_nodes("event", _("Events"),
                              self.handle_event_list, chunk_max_size=self.TX_SIZE)

    def handle_families(self):
        self.handle_dom_nodes("family", _("Families"),
                              self.handle_family_list, chunk_max_size=self.TX_SIZE)

    def handle_media(self):
        self.handle_dom_nodes("object", _("Media"),
                              self.handle_media_list, chunk_max_size=self.TX_SIZE)

    def handle_notes(self):
        self.handle_dom_nodes("note", _("Notes"),
                              self.handle_note_list, chunk_max_size=self.TX_SIZE)

    def handle_people(self):
        self.handle_dom_nodes("person", _("People"),
                              self.handle_people_list, 
                              chunk_max_size=self.TX_SIZE/2)

    def handle_places(self):
        self.place_keys = {}
        self.handle_dom_nodes("placeobj", _("Places"),
                              self.handle_place_list, chunk_max_size=self.TX_SIZE)

    def handle_repositories(self):
        self.handle_dom_nodes("repository", _("Repositories"),
                              self.handle_repositories_list, chunk_max_size=self.TX_SIZE)

    def handle_sources(self):
        self.handle_dom_nodes("source", _("Sources"),
                              self.handle_source_list, chunk_max_size=self.TX_SIZE)

    def postprocess_notes(self):
        """ Process url notes using self.noterefs_later parent object list. 
        """
        title="Notes / links"
        message = f"{title}: {len(self.noterefs_later)} kpl"
        print(f"***** {message} *****")
        t0 = time.time()
        counter = 0
        
        with shareds.driver.session() as session:
            # List self.noterefs_later has obj.notes[] referenced from parent
            total_notes = 0
            for obj in self.noterefs_later:
                total_notes += len(obj.notes)
            print(f"DOM_handler.postprocess_notes: {total_notes} "\
                  f"Notes for {len(self.noterefs_later)} objects")

            iid_generator = IsotammiIds(session, obj_name="Notes")
            iid_generator.reserve(total_notes)
            # Split to chunks, chunk_max_size=self.TX_SIZE
            for nodes_chunk in self.get_chunk(self.noterefs_later, self.TX_SIZE):
                #print(f"DOM_handler.postprocess_notes: {len(nodes_chunk)} chunk")
                for parent in nodes_chunk:
                    session.write_transaction(self.handle_postprocessed_notes,
                                              parent, iid_generator)
                    counter += len(parent.notes)

        self.noterefs_later = []
        self.blog.log_event(
            {"title": title, "count": counter, "elapsed": time.time() - t0}
        )

    def handle_postprocessed_notes(self, tx, parent, iids):
        if not parent.notes:
            return

        #note_msg = [note.url for note in parent.notes]
        #print(f"handle_postprocessed_notes: {parent.id} --> {note_msg}")
        self.dataservice.ds_save_note_list(tx, parent, self.batch.id, iids)

    def handle_citations_list(self, tx, nodes, iids):
        for citation in nodes:

            c = Citation()
            # Extract handle, change, id and attrs
            self._extract_base(citation, c)

            try:
                # type Gramps_DateRange or None
                c.dates = self._extract_daterange(citation)
            except:
                c.dates = None

            if len(citation.getElementsByTagName("page")) == 1:
                citation_page = citation.getElementsByTagName("page")[0]
                c.page = citation_page.childNodes[0].data
            elif len(citation.getElementsByTagName("page")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one page tag in a citation",
                        "level": "WARNING",
                        "count": c.id,
                    }
                )

            if len(citation.getElementsByTagName("confidence")) == 1:
                citation_confidence = citation.getElementsByTagName("confidence")[0]
                c.confidence = citation_confidence.childNodes[0].data
            elif len(citation.getElementsByTagName("confidence")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one confidence tag in a citation",
                        "level": "WARNING",
                        "count": c.id,
                    }
                )

            for citation_noteref in citation.getElementsByTagName("noteref"):
                if citation_noteref.hasAttribute("hlink"):
                    c.note_handles.append(citation_noteref.getAttribute("hlink") + self.handle_suffix)
                    ##print(f'# Citation {c.id} has note {c.note_handles[-1]}')

            if len(citation.getElementsByTagName("sourceref")) == 1:
                citation_sourceref = citation.getElementsByTagName("sourceref")[0]
                if citation_sourceref.hasAttribute("hlink"):
                    c.source_handle = citation_sourceref.getAttribute("hlink") + self.handle_suffix

                    ##print(f'# Citation {c.id} points source {c.source_handle}')
            elif len(citation.getElementsByTagName("sourceref")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one sourceref tag in a citation",
                        "level": "WARNING",
                        "count": c.id,
                    }
                )

            self.dataservice.ds_save_citation(tx, c, self.batch.id, iids)
            self.complete(c)

    def handle_event_list(self, tx, nodes, iids):
        for event in nodes:
            # Create an event with Gramps attributes
            e = EventBl()
            # Extract handle, change, id and attrs
            self._extract_base(event, e)
            e.place_handles = []
            e.note_handles = []
            e.citation_handles = []

            if len(event.getElementsByTagName("type")) == 1:
                event_type = event.getElementsByTagName("type")[0]
                # If there are type tags, but no type data
                if len(event_type.childNodes) > 0:
                    e.type = event_type.childNodes[0].data
                else:
                    e.type = ""
            elif len(event.getElementsByTagName("type")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one type tag in an event",
                        "level": "WARNING",
                        "count": e.id,
                    }
                )

            if len(event.getElementsByTagName("description")) == 1:
                event_description = event.getElementsByTagName("description")[0]
                # If there are description tags, but no description data
                if len(event_description.childNodes) > 0:
                    e.description = event_description.childNodes[0].data
            elif len(event.getElementsByTagName("description")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one description tag in an event",
                        "level": "WARNING",
                        "count": e.id,
                    }
                )

            try:
                # Returns Gramps_DateRange or None
                e.dates = self._extract_daterange(event)
                # TODO: val="1700-luvulla" muunnettava Noteksi
            except:
                e.dates = None

            if len(event.getElementsByTagName("place")) == 1:
                event_place = event.getElementsByTagName("place")[0]
                if event_place.hasAttribute("hlink"):
                    e.place_handles.append(event_place.getAttribute("hlink") + self.handle_suffix)
            elif len(event.getElementsByTagName("place")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one place tag in an event",
                        "level": "WARNING",
                        "count": e.id,
                    }
                )

            for ref in event.getElementsByTagName("noteref"):
                if ref.hasAttribute("hlink"):
                    e.note_handles.append(ref.getAttribute("hlink") + self.handle_suffix)
                    #(p)print(f'# Event {e.id} has note {e.note_handles[-1]}')

            for ref in event.getElementsByTagName("citationref"):
                if ref.hasAttribute("hlink"):
                    e.citation_handles.append(ref.getAttribute("hlink") + self.handle_suffix)
                    #(p)print(f'# Event {e.id} has cite {e.citation_handles[-1]}')

            # Handle <objref> with citations and notes
            e.media_refs = self._extract_mediaref(e, event)

            self.dataservice.ds_save_event(tx, e, self.batch.id, iids)
            self.complete(e)

    def handle_family_list(self, tx, nodes, iids):
        from bl.family import FamilyBl

        for family in nodes:
            f = FamilyBl()
            f.child_handles = []
            f.event_handle_roles = []
            f.note_handles = []
            f.citation_handles = []

            # Extract handle, change, id and attrs
            self._extract_base(family, f)

            if len(family.getElementsByTagName("rel")) == 1:
                family_rel = family.getElementsByTagName("rel")[0]
                if family_rel.hasAttribute("type"):
                    f.rel_type = family_rel.getAttribute("type")
            elif len(family.getElementsByTagName("rel")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one rel tag in a family",
                        "level": "WARNING",
                        "count": f.id,
                    }
                )

            if len(family.getElementsByTagName("father")) == 1:
                family_father = family.getElementsByTagName("father")[0]
                if family_father.hasAttribute("hlink"):
                    f.father = family_father.getAttribute("hlink") + self.handle_suffix
                    ##print(f'# Family {f.id} has father {f.father}')
            elif len(family.getElementsByTagName("father")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one father tag in a family",
                        "level": "WARNING",
                        "count": f.id,
                    }
                )

            if len(family.getElementsByTagName("mother")) == 1:
                family_mother = family.getElementsByTagName("mother")[0]
                if family_mother.hasAttribute("hlink"):
                    f.mother = family_mother.getAttribute("hlink") + self.handle_suffix
                    ##print(f'# Family {f.id} has mother {f.mother}')
            elif len(family.getElementsByTagName("mother")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one mother tag in a family",
                        "level": "WARNING",
                        "count": f.id,
                    }
                )

            for ref in family.getElementsByTagName("eventref"):
                # Create a tuple (event_handle, role)
                if ref.hasAttribute("hlink"):
                    e_handle = ref.getAttribute("hlink") + self.handle_suffix
                    if ref.hasAttribute("role"):
                        e_role = ref.getAttribute("role")
                    else:
                        e_role = None
                    f.event_handle_roles.append((e_handle, e_role))

            for ref in family.getElementsByTagName("childref"):
                if ref.hasAttribute("hlink"):
                    f.child_handles.append(ref.getAttribute("hlink") + self.handle_suffix)
                    ##print(f'# Family {f.id} has child {f.child_handles[-1]}')

            for ref in family.getElementsByTagName("noteref"):
                if ref.hasAttribute("hlink"):
                    f.note_handles.append(ref.getAttribute("hlink") + self.handle_suffix)
                    ##print(f'# Family {f.id} has note {f.note_handles[-1]}')

            for ref in family.getElementsByTagName("citationref"):
                if ref.hasAttribute("hlink"):
                    f.citation_handles.append(ref.getAttribute("hlink") + self.handle_suffix)
                    ##print(f'# Family {f.id} has cite {f.citation_handles[-1]}')

            self.dataservice.ds_save_family(tx, f, self.batch.id, iids)
            self.complete(f)

            # The sortnames and dates will be set for these families
            self.family_ids.append(f.iid)

    
    def handle_note_list(self, tx, nodes, iids):

        for note in nodes:
            n = Note()
            # Extract handle, change, id and attrs
            self._extract_base(note, n)

            n.priv = self._get_priv(note)

            if note.hasAttribute("type"):
                n.type = note.getAttribute("type")

            if len(note.getElementsByTagName("text")) == 1:
                note_text = note.getElementsByTagName("text")[0]
                n.text = note_text.childNodes[0].data
                # Pick possible url
                n.text, n.url = self._pick_url_from_text(n.text)

            self.dataservice.ds_save_note(tx, n, self.batch.id, iids)
            self.complete(n)

    def handle_media_list(self, tx, nodes, iids):
        for obj in nodes:
            o = MediaBl()
            # Extract handle, change, id and attrs
            self._extract_base(obj, o)

            for obj_file in obj.getElementsByTagName("file"):
                if o.src:
                    self.blog.log_event(
                        {
                            "title": "More than one files for a media",
                            "level": "WARNING",
                            "count": o.id,
                        }
                    )
                    break
                if obj_file.hasAttribute("src"):
                    o.src = obj_file.getAttribute("src")
                if obj_file.hasAttribute("mime"):
                    o.mime = obj_file.getAttribute("mime")
                if obj_file.hasAttribute("description"):
                    o.description = obj_file.getAttribute("description")

            o.note_handles = []
            for ref in obj.getElementsByTagName("noteref"):
                if ref.hasAttribute("hlink"):
                    o.note_handles.append(ref.getAttribute("hlink") + self.handle_suffix)
                    ##print(f'# Media {o.id} has note {o.note_handles[-1]}')

            o.citation_handles = []
            for ref in obj.getElementsByTagName("citationref"):
                if ref.hasAttribute("hlink"):
                    o.citation_handles.append(ref.getAttribute("hlink") + self.handle_suffix)
                    ##print(f'# Media {o.id} has cite {o.citation_handles[-1]}')

            self.dataservice.ds_save_media(tx, o, self.batch.id, iids)
            self.complete(o)


    def handle_people_list(self, tx, nodes, iids):
        """ Handle list of Persons. """

        def extract_person_name(person_name, name_order):
            """ Create a Name object. """
            pname = Name()
            pname.order = name_order
            pname.citation_handles = []
            if person_name.hasAttribute("alt"):
                pname.alt = person_name.getAttribute("alt")
            if person_name.hasAttribute("type"):
                pname.type = person_name.getAttribute("type")
            for person_first in person_name.getElementsByTagName("first"):
                if pname.firstname:
                    self.blog.log_event(
                        {
                            "title":"Discarded repetitive first name in a person", 
                            "level":"WARNING", 
                            "count":p.id})
                #break
                if len(person_first.childNodes) > 0:
                    pname.firstname = person_first.childNodes[0].data
                elif len(person_first.childNodes) > 1:
                    self.blog.log_event({
                            "title":"Discarded repetitive child node in a first name of a person", 
                            "level":"WARNING", 
                            "count":p.id})
            
            if len(person_name.getElementsByTagName("surname")) == 1:
                person_surname = person_name.getElementsByTagName("surname")[0]
                if person_surname.hasAttribute("prefix"):
                    pname.prefix = person_surname.getAttribute("prefix")
                if len(person_surname.childNodes) == 1:
                    pname.surname = person_surname.childNodes[0].data
                elif len(person_surname.childNodes) > 1:
                    self.blog.log_event({
                            "title":"Discarded repetitive child node in a surname of a person", 
                            "level":"WARNING", 
                            "count":p.id})
            elif len(person_name.getElementsByTagName("surname")) > 1:
                self.blog.log_event({
                        "title":"Discarded repetitive surname in a person", 
                        "level":"WARNING", 
                        "count":p.id})
            if len(person_name.getElementsByTagName("suffix")) == 1:
                person_suffix = person_name.getElementsByTagName("suffix")[0]
                pname.suffix = person_suffix.childNodes[0].data
            elif len(person_name.getElementsByTagName("suffix")) > 1:
                self.blog.log_event({
                        "title":"Discarded repetitive suffix in a person", 
                        "level":"WARNING", 
                        "count":p.id})
            try:
                pname.dates = self._extract_daterange(person_name) # Return Gramps_DateRange or None
            except:
                pname.dates = None
            if len(person_name.getElementsByTagName("title")) == 1:
                person_title = person_name.getElementsByTagName("title")[0]
                pname.title = person_title.childNodes[0].data
            elif len(person_name.getElementsByTagName("title")) > 1:
                self.blog.log_event({
                        "title":"Discarded repetitive title in a person", 
                        "level":"WARNING", 
                        "count":p.id})
            if len(person_name.getElementsByTagName("citationref")) >= 1:
                for i in range(
                    len(person_name.getElementsByTagName("citationref"))):
                    person_name_citationref = person_name.getElementsByTagName("citationref")[i]
                    if person_name_citationref.hasAttribute("hlink"):
                        pname.citation_handles.append(
                            person_name_citationref.getAttribute("hlink") + self.handle_suffix)
            
                        ##print(f'# Person name for {p.id} has cite {pname.citation_handles[-1]}')
            return pname

        # Starts handling the list of Persons

        for person in nodes:
            url_notes = []

            p = PersonBl()
            # Extract handle, change, id and attrs
            self._extract_base(person, p)
            p.event_handle_roles = []
            p.note_handles = []
            p.citation_handles = []

            for person_gender in person.getElementsByTagName("gender"):
                if p.sex:
                    self.blog.log_event(
                        {
                            "title": "A person has more than one gender",
                            "level": "WARNING",
                            "count": p.id,
                        }
                    )
                    break
                p.sex = p.sex_from_str(person_gender.childNodes[0].data)

            name_order = 0
            for person_name in person.getElementsByTagName("name"):
                pname = extract_person_name(person_name, name_order)
                name_order += 1
                if pname:
                    p.names.append(pname)

            for ref in person.getElementsByTagName("eventref"):
                # Create a tuple (event_handle, role)
                if ref.hasAttribute("hlink"):
                    e_handle = ref.getAttribute("hlink") + self.handle_suffix
                    if ref.hasAttribute("role"):
                        e_role = ref.getAttribute("role")
                    else:
                        e_role = None
                    p.event_handle_roles.append((e_handle, e_role))

            # Handle <objref>, returns a list of m_ref's
            p.media_refs = self._extract_mediaref(p, person)

            for person_url in person.getElementsByTagName("url"):
                n = Note()
                n.priv = self._get_priv(person_url)
                n.url = person_url.getAttribute("href")
                n.type = person_url.getAttribute("type")
                n.text = person_url.getAttribute("description")
                if n.url:
                    #(p)print(f"\t#handle_people_list: {p.id}: post process {n.url}")
                    url_notes.append(n)

            # Not used
            # for person_parentin in person.getElementsByTagName('parentin'):
            #    if person_parentin.hasAttribute("hlink"):
            #        p.parentin_handles.append(person_parentin.getAttribute("hlink") + self.handle_suffix)
            #        ##print(f'# Person {p.id} is parent in family {p.parentin_handles[-1]}')

            for person_noteref in person.getElementsByTagName("noteref"):
                if person_noteref.hasAttribute("hlink"):
                    p.note_handles.append(person_noteref.getAttribute("hlink") + self.handle_suffix)

            for person_citationref in person.getElementsByTagName("citationref"):
                if person_citationref.hasAttribute("hlink"):
                    p.citation_handles.append(person_citationref.getAttribute("hlink") + self.handle_suffix)
                    ##print(f'# Person {p.id} has cite {p.citation_handles[-1]}')

            #print(f"\t# Person {p.id} {p.names[0].firstname} {p.names[0].surname}")
            self.dataservice.ds_save_person(tx, p, self.batch.id, iids)
            self.complete(p, url_notes)

            # The refnames will be set for these persons
            self.person_ids.append(p.iid)


    def handle_place_list(self, tx, nodes, iids:IsotammiIds):
        """Get all the places in the xml_tree.
        

        To create place hierarchy links, there must be a dictionary of
        Place handles and iids created so far. The link may use
        previous node or create a new one.
        """
        for placeobj in nodes:
            url_notes = []

            pl = PlaceBl()
            pl.note_handles = []
            pl.citation_handles = []

            # Extract handle, change, id and attrs
            self._extract_base(placeobj, pl)
            pl.type = placeobj.getAttribute("type")

            # List of upper places in hierarchy as {hlink, dates} dictionaries
            pl.surround_ref = []

            # Note. The ptitle is never saved to Place object!
            if len(placeobj.getElementsByTagName("ptitle")) == 1:
                placeobj_ptitle = placeobj.getElementsByTagName("ptitle")[0]
                pl.ptitle = placeobj_ptitle.childNodes[0].data
            elif len(placeobj.getElementsByTagName("ptitle")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one ptitle in a place",
                        "level": "WARNING",
                        "count": pl.id,
                    }
                )

            place_order = 0
            for placeobj_pname in placeobj.getElementsByTagName("pname"):
                if placeobj_pname.hasAttribute("value"):
                    placename = PlaceName()
                    placename.order = place_order
                    place_order += 1
                    placename.name = placeobj_pname.getAttribute("value")
                    # print(f"# placeobj {pl.id} pname {place_order} {placename.name}")
                    if placename.name:
                        if pl.pname == "":
                            # First name is default pname for Place node
                            pl.pname = placename.name
                        placename.lang = placeobj_pname.getAttribute("lang")
                        pl.names.append(placename)
                    else:
                        self.blog.log_event(
                            {
                                "title": "An empty place name discarded",
                                "level": "WARNING",
                                "count": f"{pl.id}({place_order})",
                            }
                        )
                        place_order -= 1

                try:
                    # Returns Gramps_DateRange or None
                    placename.dates = self._extract_daterange(placeobj_pname)
                except:
                    placename.dates = None
            ##print(f"\t# Place {pl.id} {pl.names[0]} +{len(pl.names)-1}")

            for placeobj_coord in placeobj.getElementsByTagName("coord"):
                if placeobj_coord.hasAttribute("lat") and placeobj_coord.hasAttribute(
                    "long"
                ):
                    lat = placeobj_coord.getAttribute("lat")
                    long = placeobj_coord.getAttribute("long")
                    if pl.coord:
                        self.blog.log_event(
                            {
                                "title": "More than one coordinates in a place",
                                "level": "WARNING",
                                "count": pl.id,
                            }
                        )
                    else:
                        try:
                            pl.coord = Point(lat, long)
                        except Exception as e:
                            self.blog.log_event(
                                {
                                    "title": "Invalid coordinates - {}".format(e),
                                    "level": "WARNING",
                                    "count": pl.id,
                                }
                            )

            for placeobj_url in placeobj.getElementsByTagName("url"):
                n = Note()
                n.priv = self._get_priv(placeobj_url)
                n.url = placeobj_url.getAttribute("href")
                n.type = placeobj_url.getAttribute("type")
                n.text = placeobj_url.getAttribute("description")
                if n.url:
                    #(p)print(f"\t#handle_place_list: {pl.id}: post process {n.url}")
                    url_notes.append(n)

            for placeobj_placeref in placeobj.getElementsByTagName("placeref"):
                # Traverse links to surrounding (upper) places
                hlink = placeobj_placeref.getAttribute("hlink") + self.handle_suffix
                dates = self._extract_daterange(placeobj_placeref)
                # surround_ref elements example
                # {'hlink': '_ddd3...', 'dates': <Gramps_DateRange object>}
                pl.surround_ref.append({"hlink": hlink, "dates": dates})
                ##print(f'# Place {pl.id} is surrouded by {pl.surround_ref[-1]["hlink"]}')

            for placeobj_noteref in placeobj.getElementsByTagName("noteref"):
                if placeobj_noteref.hasAttribute("hlink"):
                    pl.note_handles.append(placeobj_noteref.getAttribute("hlink") + self.handle_suffix)
                    ##print(f'# Place {pl.id} has note {pl.note_handles[-1]}')

            # Handle <objref>
            pl.media_refs = self._extract_mediaref(pl, placeobj)
            # if pl.media_refs: print(f'#> saving Place {pl.id} with {len(pl.media_refs)} media_refs')

            for ref in placeobj.getElementsByTagName("citationref"):
                if ref.hasAttribute("hlink"):
                    pl.citation_handles.append(ref.getAttribute("hlink") + self.handle_suffix)
                    ##print(f'# Place {pl.id} has cite {pl.citation_handles[-1]}')

            # Save Place, Place_names, Notes and connect to hierarchy
            self.dataservice.ds_save_place(tx, pl, self.batch.id, iids, place_keys=self.place_keys)
            # The place_keys has been updated

            self.complete(pl, url_notes)

    def handle_repositories_list(self, tx, nodes, iids):
        """ Get all the repositories in the xml_tree. """

        for repository in nodes:
            url_notes = []

            r = Repository()
            # Extract handle, change, id and attrs
            self._extract_base(repository, r)

            if len(repository.getElementsByTagName("rname")) == 1:
                repository_rname = repository.getElementsByTagName("rname")[0]
                r.rname = repository_rname.childNodes[0].data
            elif len(repository.getElementsByTagName("rname")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one rname in a repository",
                        "level": "WARNING",
                        "count": r.id,
                    }
                )

            if len(repository.getElementsByTagName("type")) == 1:
                repository_type = repository.getElementsByTagName("type")[0]
                r.type = repository_type.childNodes[0].data
            elif len(repository.getElementsByTagName("type")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one type in a repository",
                        "level": "WARNING",
                        "count": r.id,
                    }
                )

            for repository_url in repository.getElementsByTagName("url"):
                n = Note()
                n.url = repository_url.getAttribute("href")
                n.type = repository_url.getAttribute("type")
                n.text = repository_url.getAttribute("description")
                if n.url:
                    #(p)print(f"\t#handle_repositories_list: {r.id}: post process {n.url}")
                    url_notes.append(n)
            
            for ref in repository.getElementsByTagName("noteref"):
                if ref.hasAttribute("hlink"):
                    r.note_handles.append(ref.getAttribute("hlink") + self.handle_suffix)

            self.dataservice.ds_save_repository(tx, r, self.batch.id, iids)
            self.complete(r, url_notes)


    def handle_source_list(self, tx, nodes, iids):
        """ Get all the sources in the xml_tree. """
        # Print detail of each source
        for source in nodes:

            s = SourceBl()
            s.note_handles = []  # allow multiple; prev. noteref_hlink = ''
            s.repositories = []  # list of Repository objects, containing 
                                # prev. repository_id, reporef_hlink and reporef_medium

            self._extract_base(source, s)

            if len(source.getElementsByTagName("stitle")) == 1:
                source_stitle = source.getElementsByTagName("stitle")[0]
                if len(source_stitle.childNodes) > 0:
                    s.stitle = source_stitle.childNodes[0].data
            elif len(source.getElementsByTagName("stitle")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one stitle in a source",
                        "level": "WARNING",
                        "count": s.id,
                    }
                )

            if len(source.getElementsByTagName("sauthor")) == 1:
                source_sauthor = source.getElementsByTagName("sauthor")[0]
                if len(source_sauthor.childNodes) > 0:
                    s.sauthor = source_sauthor.childNodes[0].data
            elif len(source.getElementsByTagName("sauthor")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one sauthor in a source",
                        "level": "WARNING",
                        "count": s.id,
                    }
                )

            if len(source.getElementsByTagName("spubinfo")) == 1:
                source_spubinfo = source.getElementsByTagName("spubinfo")[0]
                if len(source_spubinfo.childNodes) > 0:
                    s.spubinfo = source_spubinfo.childNodes[0].data
            elif len(source.getElementsByTagName("spubinfo")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one spubinfo in a source",
                        "level": "WARNING",
                        "count": s.id,
                    }
                )

            if len(source.getElementsByTagName("sabbrev")) == 1:
                source_spubinfo = source.getElementsByTagName("sabbrev")[0]
                if len(source_spubinfo.childNodes) > 0:
                    s.sabbrev = source_spubinfo.childNodes[0].data
            elif len(source.getElementsByTagName("sabbrev")) > 1:
                self.blog.log_event(
                    {
                        "title": "More than one sabbrev in a source",
                        "level": "WARNING",
                        "count": s.id,
                    }
                )

            for source_noteref in source.getElementsByTagName("noteref"):
                # Traverse links to surrounding places
                if source_noteref.hasAttribute("hlink"):
                    s.note_handles.append(source_noteref.getAttribute("hlink") + self.handle_suffix)
                    ##print(f'# Source {s.id} has note {s.note_handles[-1]}')

            for source_reporef in source.getElementsByTagName("reporef"):
                r = Repository()
                if source_reporef.hasAttribute("hlink"):
                    # s.reporef_hlink = source_reporef.getAttribute("hlink") + self.handle_suffix
                    r.handle = source_reporef.getAttribute("hlink") + self.handle_suffix
                    r.medium = source_reporef.getAttribute("medium")
                    ##print(f'# Source {s.id} in repository {r.handle} {r.medium}')
                # Mostly 1 repository!
                s.repositories.append(r)

            self.dataservice.ds_save_source(tx, s, self.batch.id, iids)
            self.complete(s)

    # -------------------------- Finishing process steps -------------------------------

    def set_family_calculated_attributes(self, family_ids):
        """Set sortnames and lifetime dates for each Family in the list self.family_ids.

        For each Family
        - set Family.father_sortname, Family.mother_sortname,
        - set Family.datetype, Family.date1 and Family.date2
        """
        res = {}
        counter = 0
        if len(family_ids) == 0:
            return {"status": Status.OK, "counter": counter}
        service = self.family_service    # <Neo4jUpdateService>
        for iid in self.family_ids:
            if iid is not None:
                res = service.set_family_calculated_attributes(iid)
                # returns {counter, status}
                counter += res.get("counter", 0)
        return res

    def set_person_calculated_attributes(self, person_ids):
        """Add links from each Person to Refnames and set Person.sortname"""
        status = Status.OK
        message = f"{len(self.person_ids)} Person refnames & sortnames"
        #print(f"***** {message} *****")

        t9 = time.time()
        refname_count = 0
        sortname_count = 0
        if len(person_ids) == 0:
            return {
                "refnames": refname_count,
                "sortnames": sortname_count,
                "status": Status.NOT_FOUND,
            }

        for p_id in person_ids:
            self.update_progress("refnames")
            if p_id is not None:
                res = self.person_service.set_person_name_properties(iid=p_id)
                refname_count += res.get("refnames")
                sortname_count += res.get("sortnames")

        print(f"#bl.gramps.xml_dom_handler.DOM_handler.set_person_calculated_attributes: {time.time()-t9:.3f} seconds")
        return {"status": status, "message": message}

    def set_person_estimated_dates(self, person_ids):
        """Sets estimated dates for each Person processed in handle_people
        in transaction

        Called from bp.gramps.gramps_loader.xml_to_neo4j
        """
        status = Status.OK
        #message = f"{len(self.person_ids)} Estimated lifetimes"
        #print(f"***** {message} *****")
        t9 = time.time()
        res = self.person_service.set_people_lifetime_estimates(person_ids)

        count = res.get("count")
        message = _("Estimated lifetimes")
        print(f"#bl.gramps.xml_dom_handler.DOM_handler.set_person_estimated_dates: {time.time()-t9:.3f} seconds")
        return {"status": status, "message": f"{message}, {count} changed"}

    def set_person_confidence_values(self, person_ids):
        """Sets a quality ratings for collected list of Persons.

        Person.confidence is mean of all Citations used for Person's Events
        """
        message = f"{len(person_ids)} Person confidence values"
        #print(f"***** {message} *****")
        t9 = time.time()

        res = self.person_service.update_person_confidences(person_ids)
        status = res.get("status")
        count = res.get("count", 0)
        if status == Status.OK or status == Status.UPDATED:
            print(f"#bl.gramps.xml_dom_handler.DOM_handler.set_person_confidence_values: {time.time()-t9:.3f} seconds")
            return {"status": status, "message": f"{message}, {count} changed"}
        else:
            msg = res.get("statustext")
            self.blog.log_event(
                {
                    "title": "Confidences not set",
                    "count": count,
                    "elapsed": time.time() - t9,
                    "level": "ERROR",
                }
            )
            print(f"DOM_handler.set_person_confidence_values: FAILED: {msg}")
            return {"status": status, "statustext": msg}

    # --------------------------- DOM subtree procesors ----------------------------

    def _get_priv(self, dom_obj):
        """Gives priv property value as int, if it is not '0' """
        if dom_obj.hasAttribute("priv"):
            priv = int(dom_obj.getAttribute("priv"))
            if priv:
                return priv
        return None

    def _pick_url_from_text(self, src):
        """Extract an url from the text src, if any
    
        Returns (text, url), where the url is removed from text
        """
        # TODO: Jos url päättyy merkkeihin '").,' ne tulee poistaa ja siirrää end-tekstiin
        # TODO: Pitäsikö varautua siihen että tekstikenttä sisältää monta url:ia?
    
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
            text = ""
            if start:
                text = src[:start]
            if end < len(src):
                text = "{}{}".format(text, src[end:])
        #         if text:
        #             print("    '{}'".format(text.rstrip()))
        #     elif len(src) > 0 and not src.isspace():
        #         print("{} ...".format(src[:72].rstrip()))
    
        return (text.rstrip(), url)
    
    def _extract_daterange(self, obj):
        """Extract date information from these kind of date formats:
            <daterange start="1820" stop="1825" quality="estimated"/>
            <datespan start="1840-01-01" stop="1850-06-30" quality="calculated"/>
            <dateval val="1870" type="about"/>

        This is ignored:
            <datestr val="1700-luvulla" />

        Returns: DateRange object or None
        """
        # Note informal dateobj 'datestr' is not processed as all!
        for tag in ["dateval", "daterange", "datespan"]:
            if len(obj.getElementsByTagName(tag)) == 1:
                dateobj = obj.getElementsByTagName(tag)[0]
                if dateobj.hasAttribute("cformat"):
                    calendar = dateobj.getAttribute("cformat")
                else:
                    calendar = None
                #print("calendar:", calendar)
                if tag == "dateval":
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
                #                 logger.debug("bp.gramps.xml_dom_handler.DOM_handler._extract_daterange"
                #                              f"Creating {tag}, date_type={date_type}, quality={date_quality},"
                #                              f" {date_start} - {date_stop}")
                return Gramps_DateRange(
                    tag, date_type, date_quality, date_start, date_stop, calendar
                )

            elif len(obj.getElementsByTagName(tag)) > 1:
                self.log(
                    LogItem(
                        "More than one {} tag in an event".format(tag), level="ERROR"
                    )
                )

        return None

    def _extract_base(self, dom, node):
        """Extract common variables from DOM object to NodeObject fields.

        node.id = self.id = ''          str Gedcom object id like "I1234"
        node.change = self.change       int Gramps object change timestamp
        node.handle = self.handle = ''  str Gramps handle
        node.attr__dict = {}            dict Gramps attributes and srcattributes
        """
        if dom.hasAttribute("handle"):
            node.handle = dom.getAttribute("handle") + self.handle_suffix
        if dom.hasAttribute("change"):
            node.change = int(dom.getAttribute("change"))
        if dom.hasAttribute("id"):
            node.id = dom.getAttribute("id")

        # - Extract all following source values from DOM object
        #   1. "attribute" (in <person>, <object>) and
        #   2. "srcattribute" (in <citation>, <source>)
        # - to a single NodeObject json field
        #   - node.attrs = {type: [value], type: [value,...] ... }
        my_attrs = {}
        for attr in dom.getElementsByTagName("attribute") + dom.getElementsByTagName("srcattribute"):
            if attr.hasAttribute("type"):
                key = attr.getAttribute("type")
                value = attr.getAttribute("value")
                if key in my_attrs.keys():
                    new_val = my_attrs[key] + [value]
                else: # New key
                    new_val = [value]
                my_attrs[key] = new_val
        if my_attrs:
            node.attrs = json.dumps(my_attrs, ensure_ascii=False)
            print(f"## Got {node.id} attributes {node.attrs}")
        return

    def _extract_mediaref(self, obj:NodeObject, dom_object):
        """Check if dom_object has media reference and extract it for p.media_refs.

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
        """
        result_list = []
        media_nr = -1
        for dom_media in dom_object.getElementsByTagName("objref"):
            if dom_media.hasAttribute("hlink"):
                m_ref = MediaReferenceByHandles(obj)
                # Contains media handle, crop, media_order and
                #    referrer object_name and
                #    possible lists of note handles nad citation handles
                m_ref.handle = dom_media.getAttribute("hlink") + self.handle_suffix
                media_nr += 1
                m_ref.media_order = media_nr

                for region in dom_media.getElementsByTagName("region"):
                    if region.hasAttribute("corner1_x"):
                        left = region.getAttribute("corner1_x")
                        upper = region.getAttribute("corner1_y")
                        right = region.getAttribute("corner2_x")
                        lower = region.getAttribute("corner2_y")
                        m_ref.crop = int(left), int(upper), int(right), int(lower)
                        # print(f'#_extract_mediaref: Pic {m_ref.media_order} handle={m_ref.handle} crop={m_ref.crop}')
                # if not m_ref.crop: print(f'#_extract_mediaref: Pic {m_ref.media_order} handle={m_ref.handle}')

                # Add note and citation references
                for dom_note in dom_media.getElementsByTagName("noteref"):
                    if dom_note.hasAttribute("hlink"):
                        m_ref.note_handles.append(dom_note.getAttribute("hlink") + self.handle_suffix)
                        # print(f'#_extract_mediaref: Note {m_ref.note_handles[-1]}')

                for dom_cite in dom_media.getElementsByTagName("citationref"):
                    if dom_cite.hasAttribute("hlink"):
                        m_ref.citation_handles.append(dom_cite.getAttribute("hlink") + self.handle_suffix)
                        # print(f'#_extract_mediaref: Cite {m_ref.citation_handles[-1]}')

                result_list.append(m_ref)

        return result_list
