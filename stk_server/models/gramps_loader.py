# coding=UTF-8 
#
# Methods to import all data from Gramps xml file
#
# @author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>

import logging
import time
import xml.dom.minidom
import re

from models.gen.event import Event 
from models.gen.family import Family
from models.gen.note import Note
from models.gen.media import Media
from models.gen.person import Person, Name, Weburl
from models.gen.place import Place, Place_name
from models.gen.source_citation import Citation, Repository, Source
from models.dataupdater import set_confidence_value
import shareds


def xml_to_neo4j(pathname, userid='Taapeli'):
    """ Reads a xml backup file from Gramps, and saves the information to db """
    
    # Make a precheck
    a = pathname.split(".")
    pathname2 = a[0] + "_pre." + a[1]
    
    file1 = open(pathname, encoding='utf-8')
    file2 = open(pathname2, "w", encoding='utf-8')
    
    for line in file1:
        # Already \' in line
        if line.find("\\\'") > 0:
            line2 = line
        else:
            # Replace ' with \'
            line2 = line.replace("\'", "\\\'")
        file2.write(line2)
        
    file1.close()
    file2.close()

    
    DOMTree = xml.dom.minidom.parse(open(pathname2, encoding='utf-8'))
    collection = DOMTree.documentElement
    
    msg = []
    t0 = time.time()
    
    # Create User if needed
#    user = shareds.user_datastore.get_user(current_user.id)
#    user.save()

    msg.append("XML file stored to Neo4j database:")

    
    tx = shareds.driver.session().begin_transaction()
    result = handle_notes(collection, tx)

    msg.append(str(result))
    print(str(result))
    result = handle_repositories(collection, tx)

    msg.append(str(result))
    print(str(result))
    result = handle_media(collection, tx)

    msg.append(str(result))
    print(str(result))
    result = handle_places(collection, tx)

    msg.append(str(result))
    print(str(result))
    result = handle_sources(collection, tx)

    msg.append(str(result))
    print(str(result))
    result = handle_citations(collection, tx)

    msg.append(str(result))
    print(str(result))
    result = handle_events(collection, userid, tx)

    msg.append(str(result))
    print(str(result))
    result = handle_people(collection, userid, tx)

    msg.append(str(result))
    print(str(result))
    result = handle_families(collection, tx)
    tx.commit()

    msg.append(str(result))
    print(str(result))
    
    tx = shareds.driver.session().begin_transaction()
    result = set_confidence_value(tx)
    tx.commit()
    logging.info("Xml_to_neo4j: Total time {} sek".\
                 format(time.time()-t0))
    msg.append(str(result))
    print(str(result))
    
    return(msg)


# -----------------------------------------------------------------------------


def handle_citations(collection, tx):
    # Get all the citations in the collection
    citations = collection.getElementsByTagName("citation")
    
    print ("*****Citations*****")
    t0 = time.time()
    counter = 0
    
    # Print detail of each citation
    for citation in citations:
        
        c = Citation()
        
        if citation.hasAttribute("handle"):
            c.handle = citation.getAttribute("handle")
        if citation.hasAttribute("change"):
            c.change = citation.getAttribute("change")
        if citation.hasAttribute("id"):
            c.id = citation.getAttribute("id")
    
        if len(citation.getElementsByTagName('dateval') ) == 1:
            citation_dateval = citation.getElementsByTagName('dateval')[0]
            if citation_dateval.hasAttribute("val"):
                c.dateval = citation_dateval.getAttribute("val")
        elif len(citation.getElementsByTagName('dateval') ) > 1:
            print("Error: More than one dateval tag in a citation")
    
        if len(citation.getElementsByTagName('page') ) == 1:
            citation_page = citation.getElementsByTagName('page')[0]
            c.page = citation_page.childNodes[0].data
        elif len(citation.getElementsByTagName('page') ) > 1:
            print("Error: More than one page tag in a citation")
    
        if len(citation.getElementsByTagName('confidence') ) == 1:
            citation_confidence = citation.getElementsByTagName('confidence')[0]
            c.confidence = citation_confidence.childNodes[0].data
        elif len(citation.getElementsByTagName('confidence') ) > 1:
            print("Error: More than one confidence tag in a citation")
    
        if len(citation.getElementsByTagName('noteref') ) >= 1:
            for i in range(len(citation.getElementsByTagName('noteref') )):
                citation_noteref = citation.getElementsByTagName('noteref')[i]
                if citation_noteref.hasAttribute("hlink"):
                    c.noteref_hlink.append(citation_noteref.getAttribute("hlink"))
    
        if len(citation.getElementsByTagName('sourceref') ) == 1:
            citation_sourceref = citation.getElementsByTagName('sourceref')[0]
            if citation_sourceref.hasAttribute("hlink"):
                c.sourceref_hlink = citation_sourceref.getAttribute("hlink")
        elif len(citation.getElementsByTagName('sourceref') ) > 1:
            print("Error: More than one sourceref tag in a citation")
                
        c.save(tx)
        counter += 1
        
    logging.info("Citations stored: {} TIME {} sek".\
                  format(counter, time.time()-t0))
    msg = "Citations stored: " + str(counter)
        
    return(msg)


def handle_events(collection, username, tx):
    # Get all the events in the collection
    events = collection.getElementsByTagName("event")
    
    print ("*****Events*****")
    t0 = time.time()
    counter = 0
      
    # Print detail of each event
    for event in events:

        e = Event()
        
        if event.hasAttribute("handle"):
            e.handle = event.getAttribute("handle")
        if event.hasAttribute("change"):
            e.change = event.getAttribute("change")
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
            print("Error: More than one type tag in an event")
            
        if len(event.getElementsByTagName('description') ) == 1:
            event_description = event.getElementsByTagName('description')[0]
            # If there are description tags, but no description data
            if (len(event_description.childNodes) > 0):
                e.description = event_description.childNodes[0].data
            else:
                e.description = ''
        elif len(event.getElementsByTagName('description') ) > 1:
            print("Error: More than one description tag in an event")
    
        if len(event.getElementsByTagName('dateval') ) == 1:
            event_dateval = event.getElementsByTagName('dateval')[0]
            if event_dateval.hasAttribute("val"):
                e.date = event_dateval.getAttribute("val")
                e.daterange_start = event_dateval.getAttribute("val")
            if event_dateval.hasAttribute("type"):
                e.datetype = event_dateval.getAttribute("type")
        elif len(event.getElementsByTagName('dateval') ) > 1:
            print("Error: More than one dateval tag in an event")
    
        if len(event.getElementsByTagName('daterange') ) == 1:
            event_daterange = event.getElementsByTagName('daterange')[0]
            if event_daterange.hasAttribute("start"):
                e.daterange_start = event_daterange.getAttribute("start")
            if event_daterange.hasAttribute("stop"):
                e.daterange_stop = event_daterange.getAttribute("stop")
        elif len(event.getElementsByTagName('daterange') ) > 1:
            print("Error: More than one daterange tag in an event")
    
        if len(event.getElementsByTagName('place') ) == 1:
            event_place = event.getElementsByTagName('place')[0]
            if event_place.hasAttribute("hlink"):
                e.place_hlink = event_place.getAttribute("hlink")
        elif len(event.getElementsByTagName('place') ) > 1:
            print("Error: More than one place tag in an event")
    
        if len(event.getElementsByTagName('attribute') ) == 1:
            event_attr = event.getElementsByTagName('attribute')[0]
            if event_attr.hasAttribute("type"):
                e.attr_type = event_attr.getAttribute("type")
            if event_attr.hasAttribute("value"):
                e.attr_value = event_attr.getAttribute("value")
        elif len(event.getElementsByTagName('attribute') ) > 1:
            print("Error: More than one attribute tag in an event")
    
        if len(event.getElementsByTagName('noteref') ) == 1:
            event_noteref = event.getElementsByTagName('noteref')[0]
            if event_noteref.hasAttribute("hlink"):
                e.noteref_hlink = event_noteref.getAttribute("hlink")
        elif len(event.getElementsByTagName('noteref') ) > 1:
            print("Error: More than one noteref tag in an event")
    
        if len(event.getElementsByTagName('citationref') ) == 1:
            event_citationref = event.getElementsByTagName('citationref')[0]
            if event_citationref.hasAttribute("hlink"):
                e.citationref_hlink = event_citationref.getAttribute("hlink")
        elif len(event.getElementsByTagName('citationref') ) > 1:
            print("Error: More than one citationref tag in an event")
    
        if len(event.getElementsByTagName('objref') ) == 1:
            event_objref = event.getElementsByTagName('objref')[0]
            if event_objref.hasAttribute("hlink"):
                e.objref_hlink = event_objref.getAttribute("hlink")
        elif len(event.getElementsByTagName('objref') ) > 1:
            print("Error: More than one objref tag in an event")
                
        e.save(username, tx)
        counter += 1
        
    logging.info("Events stored: {} TIME {} sek".\
                  format(counter, time.time()-t0))
    msg = "Events stored: " + str(counter)
        
    return(msg)


def handle_families(collection, tx):
    # Get all the families in the collection
    families = collection.getElementsByTagName("family")
    
    print ("*****Families*****")
    t0 = time.time()
    counter = 0
    
    # Print detail of each family
    for family in families:
        
        f = Family()
        
        if family.hasAttribute("handle"):
            f.handle = family.getAttribute("handle")
        if family.hasAttribute("change"):
            f.change = family.getAttribute("change")
        if family.hasAttribute("id"):
            f.id = family.getAttribute("id")
    
        if len(family.getElementsByTagName('rel') ) == 1:
            family_rel = family.getElementsByTagName('rel')[0]
            if family_rel.hasAttribute("type"):
                f.rel_type = family_rel.getAttribute("type")
        elif len(family.getElementsByTagName('rel') ) > 1:
            print("Error: More than one rel tag in a family")
    
        if len(family.getElementsByTagName('father') ) == 1:
            family_father = family.getElementsByTagName('father')[0]
            if family_father.hasAttribute("hlink"):
                f.father = family_father.getAttribute("hlink")
        elif len(family.getElementsByTagName('father') ) > 1:
            print("Error: More than one father tag in a family")
    
        if len(family.getElementsByTagName('mother') ) == 1:
            family_mother = family.getElementsByTagName('mother')[0]
            if family_mother.hasAttribute("hlink"):
                f.mother = family_mother.getAttribute("hlink")
        elif len(family.getElementsByTagName('mother') ) > 1:
            print("Error: More than one mother tag in a family")
    
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
                    
        f.save(tx)
        counter += 1
        
    logging.info("Families stored: {} TIME {} sek".\
                  format(counter, time.time()-t0))
    msg = "Families stored: " + str(counter)
        
    return(msg)


def handle_notes(collection, tx):
    # Get all the notes in the collection
    notes = collection.getElementsByTagName("note")

    print ("*****Notes*****")
    t0 = time.time()
    counter = 0

    # Print detail of each note
    for note in notes:
        
        n = Note()

        if note.hasAttribute("handle"):
            n.handle = note.getAttribute("handle")
        if note.hasAttribute("change"):
            n.change = note.getAttribute("change")
        if note.hasAttribute("id"):
            n.id = note.getAttribute("id")
        if note.hasAttribute("priv"):
            n.priv = note.getAttribute("priv")
        if note.hasAttribute("type"):
            n.type = note.getAttribute("type")
    
        if len(note.getElementsByTagName('text') ) == 1:
            note_text = note.getElementsByTagName('text')[0]
            n.text = note_text.childNodes[0].data
            
        n.save(tx)
        counter += 1
        
    logging.info("Notes stored: {} TIME {} sek".\
                  format(counter, time.time()-t0))
    msg = "Notes stored: " + str(counter)
        
    return(msg)


def handle_media(collection, tx):
    # Get all the media in the collection (in Gramps 'object')
    media = collection.getElementsByTagName("object")

    print ("*****Media*****")
    t0 = time.time()
    counter = 0

    # Print detail of each media object
    for obj in media:
        
        o = Media()

        if obj.hasAttribute("handle"):
            o.handle = obj.getAttribute("handle")
        if obj.hasAttribute("change"):
            o.change = obj.getAttribute("change")
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
    
        o.save(tx)
        counter += 1
        
    logging.info("Modia objects stored: {} TIME {} sek".\
                  format(counter, time.time()-t0))
    msg = "Media objects stored: " + str(counter)
        
    return(msg)


def handle_people(collection, username, tx):
    # Get all the people in the collection
    people = collection.getElementsByTagName("person")
    
    print ("*****People*****")
    t0 = time.time()
    counter = 0
    
    # Print detail of each person
    for person in people:
        
        p = Person()

        if person.hasAttribute("handle"):
            p.handle = person.getAttribute("handle")
        if person.hasAttribute("change"):
            p.change = person.getAttribute("change")
        if person.hasAttribute("id"):
            p.id = person.getAttribute("id")
        if person.hasAttribute("priv"):
            p.priv = person.getAttribute("priv")
    
        if len(person.getElementsByTagName('gender') ) == 1:
            person_gender = person.getElementsByTagName('gender')[0]
            p.gender = person_gender.childNodes[0].data
        elif len(person.getElementsByTagName('gender') ) > 1:
            print("Error: More than one gender tag in a person")
    
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
                        print("Error: More than one child node in a first name of a person")
                elif len(person_name.getElementsByTagName('first') ) > 1:
                    print("Error: More than one first name in a person")
    
                if len(person_name.getElementsByTagName('surname') ) == 1:
                    person_surname = person_name.getElementsByTagName('surname')[0]
                    if len(person_surname.childNodes ) == 1:
                        pname.surname = person_surname.childNodes[0].data
                    elif len(person_surname.childNodes) > 1:
                        print("Error: More than one child node in a surname of a person")
                elif len(person_name.getElementsByTagName('surname') ) > 1:
                    print("Error: More than one surname in a person")
    
                if len(person_name.getElementsByTagName('suffix') ) == 1:
                    person_suffix = person_name.getElementsByTagName('suffix')[0]
                    pname.suffix = person_suffix.childNodes[0].data
                elif len(person_name.getElementsByTagName('suffix') ) > 1:
                    print("Error: More than one suffix in a person")
                    
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
                    
        if len(person.getElementsByTagName('url') ) >= 1:
            for i in range(len(person.getElementsByTagName('url') )):
                weburl = Weburl()
                person_url = person.getElementsByTagName('url')[i]
                if person_url.hasAttribute("priv"):
                    weburl.priv = person_url.getAttribute("priv")
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
                    
        p.save(username, tx)
        counter += 1
        
    logging.info("Persons stored: {} TIME {} sek".\
                  format(counter, time.time()-t0))
    msg = "People stored: " + str(counter)
        
    return(msg)


def handle_places(collection, tx):
    # Get all the places in the collection
    places = collection.getElementsByTagName("placeobj")
    
    print ("*****Places*****")
    t0 = time.time()
    counter = 0
    
    # Print detail of each placeobj
    for placeobj in places:
        
        place = Place()

        if placeobj.hasAttribute("handle"):
            place.handle = placeobj.getAttribute("handle")
        if placeobj.hasAttribute("change"):
            place.change = placeobj.getAttribute("change")
        if placeobj.hasAttribute("id"):
            place.id = placeobj.getAttribute("id")
        if placeobj.hasAttribute("type"):
            place.type = placeobj.getAttribute("type")
    
        if len(placeobj.getElementsByTagName('ptitle') ) == 1:
            placeobj_ptitle = placeobj.getElementsByTagName('ptitle')[0]
            place.ptitle = placeobj_ptitle.childNodes[0].data
        elif len(placeobj.getElementsByTagName('ptitle') ) > 1:
            print("Error: More than one ptitle in a place")
    
        if len(placeobj.getElementsByTagName('pname') ) >= 1:
            for i in range(len(placeobj.getElementsByTagName('pname') )):
                placename = Place_name()
                placeobj_pname = placeobj.getElementsByTagName('pname')[i]
                if placeobj_pname.hasAttribute("value"):
                    place.pname = placeobj_pname.getAttribute("value")
                    placename.name = placeobj_pname.getAttribute("value")
                if placeobj_pname.hasAttribute("lang"):
                    placename.lang = placeobj_pname.getAttribute("lang")
                if len(placeobj_pname.getElementsByTagName('dateval') ) == 1:
                    placeobj_pname_dateval = placeobj_pname.getElementsByTagName('dateval')[0]
                    if placeobj_pname_dateval.hasAttribute("val"):
                        placename.daterange_start = placeobj_pname_dateval.getAttribute("val")
                    if placeobj_pname_dateval.hasAttribute("type"):
                        placename.datetype = placeobj_pname_dateval.getAttribute("type")
                if len(placeobj_pname.getElementsByTagName('daterange') ) == 1:
                    placeobj_pname_daterange = placeobj_pname.getElementsByTagName('daterange')[0]
                    if placeobj_pname_daterange.hasAttribute("start"):
                        placename.daterange_start = placeobj_pname_dateval.getAttribute("start")
                    if placeobj_pname_daterange.hasAttribute("stop"):
                        placename.daterange_stop = placeobj_pname_dateval.getAttribute("stop")
                place.names.append(placename)
    
        if len(placeobj.getElementsByTagName('coord') ) >= 1:
            for i in range(len(placeobj.getElementsByTagName('coord') )):
                placeobj_coord = placeobj.getElementsByTagName('coord')[i]
                if placeobj_coord.hasAttribute("long"):
                    place.coord_long = placeobj_coord.getAttribute("long")
                    if place.coord_long.find("°") > 0:
                        place.coord_long.replace(" ", "")
                        fc = place.coord_long[:1]
                        if fc.isalpha():
                            rc = place.coord_long[1:]
                            place.coord_long = rc + fc
                        a = re.split('[°\'′"″]+', place.coord_long)
                        if len(a) > 2:
                            a[1].replace("\\", "")
                            a[2].replace(",", "\.")
                            if a[0].isdigit() and a[1].isdigit():
                                place.coord_long = int(a[0]) + int(a[1])/60
                            if a[2].isdigit():
                                place.coord_long += float(a[2])/360
                            place.coord_long = str(place.coord_long)
                if placeobj_coord.hasAttribute("lat"):
                    place.coord_lat = placeobj_coord.getAttribute("lat")
                    if place.coord_lat.find("°") > 0:
                        place.coord_lat.replace(" ", "")
                        fc = place.coord_lat[:1]
                        if fc.isalpha():
                            rc = place.coord_lat[1:]
                            place.coord_lat = rc + fc
                        a = re.split('[°\'′"″]+', place.coord_lat)
                        if len(a) > 2:
                            a[1].replace("\\", "")
                            a[2].replace(",", "\.")
                            if a[0].isdigit() and a[1].isdigit():
                                place.coord_lat = int(a[0]) + int(a[1])/60
                            if a[2].isdigit():
                                place.coord_lat += float(a[2])/360
                            place.coord_lat = str(place.coord_lat)
                    
        if len(placeobj.getElementsByTagName('url') ) >= 1:
            for i in range(len(placeobj.getElementsByTagName('url') )):
                weburl = Weburl()
                placeobj_url = placeobj.getElementsByTagName('url')[i]
                if placeobj_url.hasAttribute("priv"):
                    weburl.priv = placeobj_url.getAttribute("priv")
                if placeobj_url.hasAttribute("href"):
                    weburl.href = placeobj_url.getAttribute("href")
                if placeobj_url.hasAttribute("type"):
                    weburl.type = placeobj_url.getAttribute("type")
                if placeobj_url.hasAttribute("description"):
                    weburl.description = placeobj_url.getAttribute("description")
                place.urls.append(weburl)
    
        if len(placeobj.getElementsByTagName('placeref') ) == 1:
            placeobj_placeref = placeobj.getElementsByTagName('placeref')[0]
            if placeobj_placeref.hasAttribute("hlink"):
                place.placeref_hlink = placeobj_placeref.getAttribute("hlink")
        elif len(placeobj.getElementsByTagName('placeref') ) > 1:
            print("Error: More than one placeref in a place")
    
        if len(placeobj.getElementsByTagName('noteref') ) >= 1:
            for i in range(len(placeobj.getElementsByTagName('noteref') )):
                placeobj_noteref = placeobj.getElementsByTagName('noteref')[i]
                if placeobj_noteref.hasAttribute("hlink"):
                    place.noteref_hlink.append(placeobj_noteref.getAttribute("hlink"))
                
        place.save(tx)
        counter += 1
        
    logging.info("Places stored: {} TIME {} sek".\
                  format(counter, time.time()-t0))
    msg = "Places stored: " + str(counter)
        
    return(msg)


def handle_repositories(collection, tx):
    # Get all the repositories in the collection
    repositories = collection.getElementsByTagName("repository")
    
    print ("*****Repositories*****")
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
            print("Error: More than one rname in a repository")
    
        if len(repository.getElementsByTagName('type') ) == 1:
            repository_type = repository.getElementsByTagName('type')[0]
            r.type =  repository_type.childNodes[0].data
        elif len(repository.getElementsByTagName('type') ) > 1:
            print("Error: More than one type in a repository")
            
        if len(repository.getElementsByTagName('url') ) >= 1:
            for i in range(len(repository.getElementsByTagName('url') )):
                repository_url = repository.getElementsByTagName('url')[i]
                if repository_url.hasAttribute("href"):
                    r.url_href.append(repository_url.getAttribute("href"))
                if repository_url.hasAttribute("type"):
                    r.url_type.append(repository_url.getAttribute("type"))
                if repository_url.hasAttribute("description"):
                    r.url_description.append(repository_url.getAttribute("description"))
    
        r.save(tx)
        counter += 1
                
    logging.info("Repositories stored: {} TIME {} sek".\
                  format(counter, time.time()-t0))
    msg = "Repositories stored: " + str(counter)
        
    return(msg)


def handle_sources(collection, tx):
    # Get all the sources in the collection
    sources = collection.getElementsByTagName("source")
    
    print ("*****Sources*****")
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
            print("Error: More than one stitle in a source")
    
        if len(source.getElementsByTagName('noteref') ) == 1:
            source_noteref = source.getElementsByTagName('noteref')[0]
            if source_noteref.hasAttribute("hlink"):
                s.noteref_hlink = source_noteref.getAttribute("hlink")
        elif len(source.getElementsByTagName('noteref') ) > 1:
            print("Error: More than one noteref in a source")
    
        if len(source.getElementsByTagName('reporef') ) == 1:
            source_reporef = source.getElementsByTagName('reporef')[0]
            if source_reporef.hasAttribute("hlink"):
                s.reporef_hlink = source_reporef.getAttribute("hlink")
            if source_reporef.hasAttribute("medium"):
                s.reporef_medium = source_reporef.getAttribute("medium")
        elif len(source.getElementsByTagName('reporef') ) > 1:
            print("Error: More than one reporef in a source")
    
        s.save(tx)
        counter += 1
        
    logging.info("Sources stored: {} TIME {} sek".\
                  format(counter, time.time()-t0))
    msg = "Sources stored: " + str(counter)
        
    return(msg)

