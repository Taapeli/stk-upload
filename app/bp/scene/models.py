'''
    bp.scene.models – Database operations for multiple gen classes

Created on 24.9.2018

@author: jm
'''
#from models.datareader import read_persons_with_events
from models.gen.from_node import get_object_from_node
from models.gen.family import Family_for_template
from models.gen.person_combo import Person_combo, Person_as_member
from models.gen.person_name import Name
from models.gen.event_combo import Event_combo
from models.gen.place import Place
from models.gen.source import Source
from models.gen.citation import Citation
from models.gen.repository import Repository
from models.gen.note import Note
from models.gen.media import Media


def get_a_person_for_display_apoc(uniq_id, user):
    """ Get a Person with all connected nodes 
    """

    # 1. Read person p and paths for all nodes connected to p
    try:
        results = Person_combo.get_person_paths_apoc(uniq_id)
    except Exception as e:
        print("Henkilötietojen {} luku epäonnistui: {} {}".format(uniq_id, e.__class__().name, e))
        return [None, None]

    for result in results:
        relations = result['relations']
        nodelist = result['nodelist']
        
        # Create gen objects tree: Person with all connected objects

        # 1. Create the Person instance, in which all objects shall be stored
        person = Person_combo.from_node(nodelist[0])
        # Store a pointer to this object
        objs = {person.uniq_id: person}

        # 2. Create a directory of nodes which are envolved
        nodes = {}  # uniq_id : node
        for node in nodelist:
            # <Node id=80234 labels={'Person'} 
            #    properties={'handle': '_da3b305b54b1481e72a4ac505c5', 'id': 'I17296', 
            #    'priv': '', 'gender': 'F', 'confidence': '2.5', 'change': 1507492602}>
            nodes[node.id] = node

        # 3. Store each gen object from nodes of relations as leafs
        #    of Person object tree. 
        #    Also create a directory of all of those objects
        for relation in relations:
            # [source uniq_id, relation type, relation role, target uniq_id]
            # [80234, 'EVENT', 'Primary', 88208]
            if relation[3] != person.uniq_id:
                # Going to add a new node under src node
                node_id1 = relation[0]
                node_id2 = relation[3]
            else:
                # Reverse connection (Family)-->(Person): add src under target node
                node_id1 = relation[3]
                node_id2 = relation[0]
            src_node = nodes[node_id1]
            src_label = list(src_node.labels)[0]
            target_node = nodes[node_id2]
            target_label = list(target_node.labels)[0]

            if not src_node.id in objs:
                # Create new object
                try:
                    src_obj = get_object_from_node(src_node)
                    print("  new obj[{}] <- {} {}".\
                          format(src_obj.uniq_id, src_label, src_obj))
                    objs[src_obj.uniq_id] = src_obj
                except Exception as e:
                    print("{}: Could not set {}".format(e, src_obj))
            else:
                # Use exsisting object
                src_obj = objs[src_node.id]

            rel_type = relation[1]
            role = relation[2]
            if role:    r = ' '.join(relation[1:3])
            else:       r = relation[1]
            print("relation ({} {}) -[{}]-> ({} {})".format(src_node.id, src_label, r, target_node.id, target_label))
            # Source object, for ex. Person_combo
            if src_node.id in objs:
                src_obj = objs[src_node.id]
                target_obj = get_object_from_node(target_node)
                if not target_obj:  
                    print("Not implemented yet! {}".format(target_obj))
                    continue
                if role:    # Relation attribute 'role'
                    target_obj.role = role
                # Store target object of the relation as a leaf object in src_obj
                target_link = connect_object_as_leaf(src_obj, target_obj, rel_type)
                # Target_link point to that leaf. 
                # Put it also in objs and cits directories for possible re-use
                if target_link == None:
                    #TODO mitä tehdään, eikö joku muu lista?
                    objs[target_obj.uniq_id] = target_obj
                elif not target_link.uniq_id in objs:
                    objs[target_link.uniq_id] = target_link
                    print("  obj[{}] <- {}".format(target_link.uniq_id, target_link))
                if rel_type == 'CITATION':
                    # cits[target_link.uniq_id] = target_link
                    print("  citation[{}] <- {}".format(target_obj.uniq_id, target_obj))
            else:
                print("Ei objektia {} {}".format(src_obj.uniq_id, src_obj.id))

    # 4. Generate clear names for event places

    for e in person.events:
        for pref in e.place_ref:
            e.clearnames = e.clearnames + objs[pref].show_names_list()
            for nref in objs[pref].note_ref:
                note = objs[nref]
                print ("  place {} note {}".format(objs[pref].id, note))
#         for ref in e.citation_ref:
#             if ref in objs:
#                 cit = objs[ref]
#                 sl = "{} '{}'".format(cit.source.uniq_id, cit.source.stitle)
#                 print("{}: lähde {} / {} '{}'".format(e.id, sl, cit.uniq_id, cit.page))
#             else:
#                 sl = 'no source'
#                 print("{}: no source / {}".format(e.id, sl, ref))

    # Return Person with included objects and list of note, citation etc. objects
    return (person, objs)

def connect_object_as_leaf(src, target, rel_type=None):
    ''' Subroutine for Person page display
        Saves target object in appropiate place in the src object 
        (Person, Event etc).
        Returns saved target object or None, if target was not saved here.
    
    Plan 17 Sep 2018 / JMä

    The following relation targets are stored as instances in root object 
    'src_obj' variable:
        (:Person)                not linked to self
        -[:NAME]-> (:Name)       to .names[]
        -[:EVENT]-> (:Event)     to .events[]
        -[:CHILD]-> (:Family)    to .child[]
        -[:FATHER]-> (:Family)   to .father
        -[:MOTHER]-> (:Family)   to .mother
        -[:HIERARCHY]-> (:Place) to .place

    The following relation targets are stored as object references (uniq_id) 
    in root object variable. The actual referenced target objects are stored to 
    separate 'obj_dict' variable:
        -[:CITATION]-> (:Citation)     to .citation_ref[]
        -[:SOURCE]-> (:Source)         to .source_ref[]
        -[:REPOSITORY]-> (:Repository) to .repo_ref[]
        -[:NOTE]-> (:Note)             to .note_ref[]
        -[:PLACE]-> (:Place)           to .place_ref[]
        -[:MEDIA]-> (:Media)           to .media_ref[]
    
    Object to object connection variables:
    
        Person combo 
            .names[]
            .events[]
            .media_ref[]
            .families[]
            .note_ref[]
            .citation_ref[]
        Name 
            .note_ref[]
            .citation_ref[]
        Refname
            -
        Media
            .note_ref[]
            .citation_ref[]
        Note 
            .citation_ref[]
        Event combo
            .place_ref[]
            .note_ref[]
        Place 
            .place_ref[]
            .note_ref[]
            .citation_ref[]
        Family
             children[]
            .father, .mother, .children[]
            .events[]
            .note_ref[]
            .citation_ref[]
        Citation
            .note_ref[]
        Source
            .repo_ref[]
        Repository
            -
    '''

    src_class = src.__class__.__name__
    target_class = target.__class__.__name__
    
    if src_class == 'Person_combo':
        if target_class == 'Name':
            src.names.append(target)
            return src.names[-1]
        elif target_class == 'Event_combo':
            src.events.append(target)
            return src.events[-1]
        elif target_class == 'Family':
            if rel_type == 'CHILD':
                src.families_as_child.append(target)
                return src.families_as_child[-1]
            if rel_type == 'MOTHER' or rel_type == 'FATHER':
                src.families_as_parent.append(target)
                return src.families_as_parent[-1]
        elif target_class == 'Citation':
            src.citation_ref.append(target.uniq_id)
            return None
        if target_class == 'Note':
            src.note_ref.append(target.uniq_id)
            return None
        if target_class == 'Media':
            src.media_ref.append(target.uniq_id)
            return None

    elif src_class == 'Event_combo':
        if target_class == 'Place':
            src.place_ref.append(target.uniq_id)
            return None
        elif target_class == 'Citation':
            #src.citations.append(target) 
            src.citation_ref.append(target.uniq_id)
            return None
        elif target_class == 'Note':
            src.note_ref.append(target.uniq_id)
            return None

    elif src_class == 'Citation':
        if target_class == 'Source':
            src.source = target
            return src.source
        if target_class == 'Note':
            src.note_ref.append(target.uniq_id)
            return None

    elif src_class == 'Place':
        if target_class == 'Place_name':
            src.names.append(target)
            return src.names[-1]
        if target_class == 'Place':
            src.uppers.append(target)
            return src.uppers[-1]
        if target_class == 'Note':
            src.note_ref.append(target.uniq_id)
            return None

    elif src_class == 'Family':
        if target_class == 'Event_combo':
            src.events.append(target)
            return src.events[-1]
        if target_class == 'Note':
            src.note_ref.append(target.uniq_id)
            return None

    elif src_class == 'Source':
        if target_class == 'Repository':
            src.repo_ref.append(target)
            return None
        if target_class == 'Note':
            src.note_ref.append(target.uniq_id)
            return None

    print('Ei toteutettu {} --> {}'.format(src_class, target_class))
    return None

 
def get_person_data_by_id(uniq_id):
    """ VANHEMPI VERSIO
    Get 5 data sets:
        person: Person object with name data
            The indexes of referred objects are in variables 
                eventref_hlink[]   str tapahtuman uniq_id 
                eventref_role[]    str rooli
                media_ref[]        int tallenteen uniq_id
                urls[]             Weburl nodes
                    priv           str 1 = salattu tieto
                    href           str osoite
                    type           str tyyppi
                    description    str kuvaus
                parentin_hlink[]      str vanhempien uniq_id
                noteref_hlink[]       str huomautuksen uniq_id
                citation_ref[]     str viittauksen uniq_id            
        events: list of Event_combo object with location name and id (?)
        photos
        sources
        families
    """
    p = Person_combo()
    p.uniq_id = int(uniq_id)
    # Get Person and her Name properties, also Weburl properties 
    p.get_person_w_names()
    # Get reference (uniq_id) and role for Events
    # Get references to Media, Citation objects
    # Get Persons birth family reference and role
#     p.get_hlinks_by_id()
    events = Event_combo.get_connected_events_w_links(uniq_id)
    # Person_display(Person)
#     events = []
    sources = []
    photos = []
    source_cnt = 0

    # Read objects connected to Events

    for i in range(len(p.eventref_hlink)):
        # Store Event data
        e = Event_combo() # Event_for_template()
        e.uniq_id = p.eventref_hlink[i]
        e.role = p.eventref_role[i]
        # Read event with uniq_id's of related Place (Note, and Citation?)
        e.get_event_combo()        # Read data to e
            
        if e.place_hlink != '':
            place = Place()
            place.uniq_id = e.place_hlink
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
            # If there is already the same citation on the list of sources,
            # use that index
            citation_ind = -1
            for i in range(len(sources)):
                if sources[i].uniq_id == c.uniq_id:
                    citation_ind = i + 1
                    break
            if citation_ind > 0:
                # Citation found; Event_combo.source = jonkinlainen indeksi
                e.source = citation_ind
            else: # Store the new source to the list
                source_cnt += 1
                e.source = source_cnt

                result = c.get_source_repo(c.uniq_id)
                for record in result:
                    # record contains some Citation data + list of
                    # Source, Repository and Note data
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
                        
                        s.repos.append(r)
                        c.source = s    #s.append(s)
                        
                    sources.append(c)
            
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
    fid = ''
    result = Person_combo.get_family_members(p.uniq_id)
    for record in result:
        # Got ["family_id", "f_uniq_id", "role", "m_id", "uniq_id", 
        #      "gender", "birth_date", "names"]
        if fid != record["f_uniq_id"]:
            fid = record["f_uniq_id"]
            if not fid in families:
                families[fid] = Family_for_template(fid)
                families[fid].id = record['family_id']

        member = Person_as_member()    # A kind of Person
        member.role = record["role"]
        if record["m_id"]:
            member.id = record["m_id"]
        member.uniq_id = record["uniq_id"]
        if member.uniq_id == p.uniq_id:
            # What kind of family this is? I am a Child or Parent in family
            if member.role == "CHILD":
                families[fid].role = "CHILD"
            else:
                families[fid].role = "PARENT"

        if record["gender"]:
            member.gender = record["gender"]
        if record["birth_date"]:
            member.birth_date = record["birth_date"]
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
    for e in sources:
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

    return (p, events, photos, sources, family_list)

