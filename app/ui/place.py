'''
Created on 13.3.2020

@author: jm
'''
from flask_security import current_user


def place_names_from_nodes(nodes):
    ''' Filter Name objects from a list of Cypher nodes.
    
        Create a list of place_bl.names with PlaceNames by following rules:
        1. Place_names using lang == current_user.language
        2. Place_names using lang == ""
        3. If none found, use the last Place_name
        Place_names using other languages are discarded

        nodes=[
            <Node id=305800 labels={'Place_name'} properties={'name': 'Helsingfors', 'lang': ''}>, 
            <Node id=305799 labels={'Place_name'} properties={'name': 'Helsinki', 'lang': 'sv'}>
        ]>
    '''
    from bl.place import PlaceName
    ret = []
    own_lang = []
    no_lang = []
    alien_lang = []
    for node in nodes:
        pn = PlaceName.from_node(node)
        if pn.lang == "":
            no_lang.append(pn)
            ##print(f"# - no lang {len(place_bl.names)} (Place_name {pn.uniq_id} {pn})")
        elif pn.lang == current_user.language:
            own_lang.append(pn)
            ##print(f"# - my lang (Place_name {pn.uniq_id} {pn})")
        else:
            alien_lang.append(pn)
            ##print(f"# - alien lang (Place_name {pn})")

    if own_lang:
        ret = own_lang
    elif no_lang:
        ret = no_lang
    else:
        ret = alien_lang
#     for pn in ret:
#         print(f"#  PlaceNames: {pn}")

    return ret


