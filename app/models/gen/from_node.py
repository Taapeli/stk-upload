'''
Created on 8.10.2018

@author: jm
'''
from .citation import Citation
from .event_combo import Event_combo
from .family_combo import Family_combo
from .media import Media
from .note import Note
from .person_combo import Person_combo
from .person_name import Name
from .place import Place_name
from .repository import Repository
from .source import Source
from models.gen.place_combo import Place_combo


def get_object_from_node(node):
    '''
        Noe4j database returns node objects, which are converted to
        corresponding objects by this function
    '''
    try:
        label = list(node.labels)[0]
    except Exception as e:
        print("{} Tyhjä node? {}".format(e, node))
        return None

    if label == "Event":
        return Event_combo.from_node(node)
    elif label == "Name":
        return Name.from_node(node)
    elif label == "Person":
        return Person_combo.from_node(node)
#     elif label == "Refname":
#         return Refname.from_node(node)
    elif label == "Citation":
        return Citation.from_node(node)
    elif label == "Source":
        return Source.from_node(node)
    elif label == "Repository":
        return Repository.from_node(node)
    elif label == "Place":
        return Place_combo.from_node(node)
    elif label == "Place_name":
        return Place_name.from_node(node)
    elif label == "Note":
        return Note.from_node(node)
    elif label == "Family":
        return Family_combo.from_node(node)
    elif label == "Media":
        return Media.from_node(node)
    else: return None

