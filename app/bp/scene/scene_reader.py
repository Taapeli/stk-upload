'''
    bp.scene.models – Database operations for multiple gen classes

Created on 24.9.2018

@author: jm
'''
from .models.footnote import Footnotes, SourceFootnote

from models.gen.from_node import get_object_from_node
from models.gen.person_combo import Person_combo #, Person_as_member

# from models.datareader import read_persons_with_events
# from models.gen.family_combo import Family_for_template
# from models.gen.person_name import Name
# from models.gen.event_combo import Event_combo
# from models.gen.place import Place
# from models.gen.source import Source
# from models.gen.citation import Citation
# from models.gen.repository import Repository
# from models.gen.note import Note
# from models.gen.media import Media


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
            #    'priv': 1, 'sex': '2', 'confidence': '2.5', 'change': 1507492602}>
            nodes[node.id] = node

        # 3. Store each gen object from nodes of relations as leafs
        #    of Person object tree. 
        #    Also create a directory of all of those objects
        for relation in relations:
            # [source uniq_id, relation type, relation role, target uniq_id]
            # [80234, 'EVENT', 'Primary', 88208]
            if relation[3] != person.uniq_id:
                # Going to add a new node under src node
                node_rel1 = relation[0]
                node_rel2 = relation[3]
            else:
                # Reverse connection (Family)-->(Person): add src under target node
                node_rel1 = relation[3]
                node_rel2 = relation[0]
            src_node = nodes[node_rel1]
            src_label = list(src_node.labels)[0]
            target_node = nodes[node_rel2]
            target_label = list(target_node.labels)[0]

            if not src_node.id in objs:
                # Create new object
                try:
                    src_obj = get_object_from_node(src_node)
                    print(" new objs[{}] <- {} {}".\
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
                    print("iERROR Not implemented yet! {}".format(target_obj))
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
#                     print("  obj[{}] <- {}".format(target_link.uniq_id, target_link))
#                 if rel_type == 'CITATION':
#                     # cits[target_link.uniq_id] = target_link
#                     print("  citation[{}] <- {}".format(target_obj.uniq_id, target_obj))
            else:
                print("Ei objektia {} {}".format(src_obj.uniq_id, src_obj.id))

    # Sort events by date
    person.events.sort(key=lambda event: event.date)

    # 4. Generate clear names for event places

    fns = Footnotes()
    set_citations(person.citation_ref, fns, objs)
    for e in person.events:
        for pref in e.place_ref:
            e.clearnames = e.clearnames + objs[pref].show_names_list()
            for nref in objs[pref].note_ref:
                note = objs[nref]
                print ("  place {} note {}".format(objs[pref].id, note))
        set_citations(e.citation_ref, fns, objs)

    # Return Person with included objects, list of note, citation etc. objects
    # and footnotes
    return (person, objs, fns.getNotes())


def set_citations(refs, fns, objs):
    ''' Create person_pg citation references for foot notes '''
    for ref in refs:
        if ref in objs:
            cit = objs[ref]
            fn = SourceFootnote.from_citation_objs(cit, objs)
            cit.mark = fn.mark
            sl = fns.merge(fn)
            print("- fnotes {} source {}, cit {}: c= {} {} '{}'".format(sl[0], sl[1], sl[2], cit.uniq_id, cit.id, cit.page))
        else:
            print("- no source / {}".format(ref))


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
        -[:PARENT {role:'father'}]-> (:Family)   to .father
        -[:PARENT {role:'mother'}]-> (:Family)   to .mother
        -[:HIERARCHY]-> (:Place) to .place
        (:Place)
        -[:NAME]-> (:Name)       to .names[]
        
    The following relation targets are stored as object references (uniq_id) 
    in root object variable. The actual referenced target objects are stored to 
    separate 'obj_dict' variable:
        -[:CITATION]-> (:Citation)     to .citation_ref[]
        -[:SOURCE]-> (:Source)         to .source_id
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
        Family_combo
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
        elif target_class == 'Family_combo':
            if rel_type == 'CHILD':
                src.families_as_child.append(target)
                return src.families_as_child[-1]
            if rel_type == 'PARENT': #'MOTHER' or rel_type == 'FATHER':
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
        if target_class == 'Place_combo':
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
            src.source_id = target.uniq_id
            return None
        if target_class == 'Note':
            src.note_ref.append(target.uniq_id)
            return None

    elif src_class == 'Place_combo':
        if target_class == 'Place_name':
            src.names.append(target)
            return src.names[-1]
        if target_class == 'Place_combo':
            src.uppers.append(target)
            return src.uppers[-1]
        if target_class == 'Note':
            src.note_ref.append(target.uniq_id)
            return None

    elif src_class == 'Family_combo':
        if target_class == 'Event_combo':
            src.events.append(target)
            return src.events[-1]
        if target_class == 'Note':
            src.note_ref.append(target.uniq_id)
            return None

    elif src_class == 'Source':
        if target_class == 'Repository':
            src.repositories.append(target.uniq_id)
            return None
        if target_class == 'Note':
            src.note_ref.append(target.uniq_id)
            return None

    print('Ei toteutettu {} --> {}'.format(src_class, target_class))
    return None

 
# def get_person_data_by_id(uniq_id): @see: models.datareader.get_person_data_by_id
#     """ VANHEMPI VERSIO
#     Get 5 data sets:
#...
#         #TODO Talleta Note- ja Citation objektit oikeisiin objekteihin
#         #     Perusta objektien kantaluokka Node, jossa muuttujat jäsenten 
#         #     tallettamiseen.
#         # - Onko talletettava jäsenet vai viitteet niihin? Ei kai ole niin paljon toistoa?
# 
#     return (p, events, photos, sources, family_list)

