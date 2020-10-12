'''
    Operations for handling Citation - Source - Repository paths and their Notes.

Created on 15.11.2019

@author: jm
'''
from .gen.cypher import Cypher_source
from .gen.citation import Citation
from .gen.source import Source
from .gen.repository import Repository

#TODO Should be somewhere else!
from templates.jinja_filters import translate

     
# def read_sources_repositories(session, objs, citations=None): # --> pe.neo4j.read_driver.dr_get_object_sources_repositories()
#     ''' Read Source -> Repository hierarchies for given list of citations
#                         
#         - session       neo4j.session   for database access
#         - citations[]   list int        list of citation.uniq_ids
#         - objs{}        dict            objs[uniq_id] = NodeObject
#         
#         * The Citations mentioned must be in objs dictionary
#         * On return, the new Sources and Repositories found are added to objs{} 
#     '''
#     if len(citations) == 0:
#         return
# 
#     uids = list(citations.keys())
#     results = session.run(Cypher_source.get_sources_repositories, uid_list=uids)
#     for record in results:
#         # <Record label='Citation' uniq_id=392761 
#         #    s=<Node id=397146 labels={'Source'} 
#         #        properties={'id': 'S1723', 'stitle': 'Hauhon seurakunnan rippikirja 1757-1764', 
#         #            'uuid': 'f704b8b90c0640efbade4332e126a294', 'spubinfo': '', 'sauthor': '', 'change': 1563727817}>
#         #    rel=<Relationship id=566238 
#         #      nodes=(
#         #        <Node id=397146 labels={'Source'} 
#         #            properties={'id': 'S1723', 'stitle': 'Hauhon seurakunnan rippikirja 1757-1764', 
#         #                'uuid': 'f704b8b90c0640efbade4332e126a294', 'spubinfo': '', 'sauthor': '', 'change': 1563727817}>, 
#         #        <Node id=316903 labels={'Repository'}
#         #            properties={'id': 'R0157', 'rname': 'Hauhon seurakunnan arkisto', 'type': 'Archive', 
#         #                'uuid': '7ac1615894ea4457ba634c644e8921d6', 'change': 1563727817}>) 
#         #      type='REPOSITORY' 
#         #      properties={'medium': 'Book'}>
#         #    r=<Node id=316903 labels={'Repository'}
#         #        properties={'id': 'R0157', 'rname': 'Hauhon seurakunnan arkisto', 'type': 'Archive', 
#         #            'uuid': '7ac1615894ea4457ba634c644e8921d6', 'change': 1563727817}>
#         # >
#         
#         # 1. The Citation node
#         uniq_id = record['uniq_id']
#         cita = objs[uniq_id]
# 
#         # 2. The Source node
#         node = record['s']
#         source = Source.from_node(node)
#         if not source.uniq_id in objs:
#             objs[source.uniq_id] = source
# 
#         if record['rel']:
#             # 3. Medium from REPOSITORY relation
#             relation = record['rel']
#             medium = relation.get('medium', "")
# 
#             # 4. The Repository node
#             node = record['r']
#             repo = Repository.from_node(node)
#             repo.medium = medium
#             if not repo.uniq_id in objs:
#                 objs[repo.uniq_id] = repo
#             if not repo.uniq_id in source.repositories:
#                 source.repositories.append(repo.uniq_id)
#         
#         # Referencing a (Source, medium, Repository) tuple
#         cita.source_id = source.uniq_id
#         #print(f"# ({uniq_id}:Citation) --> (:Source '{source}') --> (:Repository '{repo}')")
# 
#     return


def get_citations_js(objs):
    ''' Create code for generating Javascript objecs representing
        Citations, Sources and Repositories with their Notes.
        
        js-style person[id] = {name: "John", age: 31, city: "New York"}
    '''
    def unquote(s):
        ''' Change quites (") to fancy quotes (“)
            Change new lines to '¤' symbol
        '''
        return s.replace('"', '“').replace('\n','¤');

    notes = []
    js  = 'var citations = {};\nvar sources = {};\n'
    js += 'var repositories = {};\nvar notes = {};\n'
    for o in objs.values():
        if isinstance(o, Citation):
            page = unquote(o.page)
            js += f'citations[{o.uniq_id}] = {{ '
            js += f'confidence:"{o.confidence}", dates:"{o.dates}", '
            js += f'id:"{o.id}", note_ref:{o.note_ref}, '
            js += f'page:"{page}", source_id:{o.source_id}, uuid:"{o.uuid}" '
            js +=  '};\n'
            notes.extend(o.note_ref)

        elif isinstance(o, Source):
            sauthor = unquote(o.sauthor)
            spubinfo = unquote(o.spubinfo)
            stitle = unquote(o.stitle)
            js += f'sources[{o.uniq_id}] = {{ '
            js += f'id:"{o.id}", note_ref:{o.note_ref}, '
            js += f'repositories:{o.repositories}, sauthor:"{sauthor}", '
            js += f'spubinfo:"{spubinfo}", stitle:"{stitle}", '
            js += f'uuid:"{o.uuid}" '
            js +=  '};\n'
            notes.extend(o.note_ref)

        elif isinstance(o, Repository):
            medium = translate(o.medium, 'medium')
            atype = translate(o.type, 'rept')
            js += f'repositories[{o.uniq_id}] = {{ '
            js += f'uuid:"{o.uuid}", id:"{o.id}", type:"{atype}", rname:"{o.rname}", '
            # Media type 
            js += f'medium:"{medium}", notes:{o.notes}, sources:{o.sources}'
            js +=  '};\n'
            notes.extend(o.notes)

        else:
            continue

    # Find referenced Notes; conversion to set removes duplicates
    for uniq_id in set(notes):
        o = objs[uniq_id]
        text = unquote(o.text)
        url = unquote(o.url)
        js += f'notes[{o.uniq_id}] = {{ '
        js += f'uuid:"{o.uuid}", id:"{o.id}", type:"{o.type}", '
        js += f'priv:"{o.priv}", text:"{text}", url:"{url}" '
        js +=  '};\n'

    return js

