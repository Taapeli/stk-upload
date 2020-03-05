'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

#from sys import stderr

import shareds
from .base import NodeObject
from .cypher import Cypher_source
from .repository import Repository
from .note import Note
#from models.cypher_gramps import Cypher_source_w_handle


class Source(NodeObject):
    """ Lähde
            
        Properties:
                handle          
                change
                id              esim. "S0001"
                stitle          str lähteen otsikko
        
        See also: bp.gramps.models.source_gramps.Source_gramps
     """

    def __init__(self):
        """ Luo uuden source-instanssin """
        NodeObject.__init__(self)
        self.stitle = ''
        self.sauthor = ''
        self.spubinfo = ''
        
#         self.citation_ref = []  # uniq_ids (previous citationref_hlink = '')
#         self.place_ref = []     # uniq_ids (previous placeref_hlink = '')
#         self.media_ref = []     # uniq_ids (proveous self.objref_hlink = '')
        self.note_ref = []      # uniq_ids (previously note[])
#         self.repocitory = None  # Repository object For creating display sets (vanhempi)

        # For display combo
        #Todo: onko repositories, citations käytössä?
        self.repositories = []
        self.citations = []
        self.notes = []

    def __str__(self):
        return "{} '{}' '{}' '{}'".format(self.id, self.stitle, self.sauthor, self.spubinfo)


    @classmethod
    def from_node(cls, node):
        '''
        Transforms a db node to an object of type Source.
        
        <Node id=91394 labels={'Source'} 
            properties={'handle': '_d9edc4e4a9a6defc258', 'id': 'S0078', 
                'stitle': 'Kangasala syntyneet 1721-1778', 'change': '1507149115'}>
        '''
        s = cls()   # create a new Source
        s.uniq_id = node.id
        s.id = node['id']
        s.uuid = node['uuid']
        if 'handle' in node:
            s.handle = node['handle']
        s.stitle = node['stitle']
        s.sauthor = node['sauthor']
        s.spubinfo = node['spubinfo']
        s.change = node['change']
        return s

    @staticmethod       
    def get_sources_by_idlist(uniq_ids):
        ''' Read source data from db for given uniq_ids.
        
            returns a dictionary of { uniq_id: Source }
        '''
        source_load_data = '''
match (s:Source) where id(s) in $ids
return s'''
        sources = {}
        result = shareds.driver.session().run(source_load_data, ids=uniq_ids)
        for record in result:
            snode = record['s']
            s = Source.from_node(snode)
            sources[s.id] = s
        return sources

#     def get_repositories_w_notes(self):
#         """ Read the repositories referenced by this source with optional notes.
# 
#             NOT IN USE, removed 3.5.2019
# 
#             The referenced Repositories are stored in self.repositories[] and
#             possible Notes in self.repositories[].notes[]
#         """
#         result = shareds.driver.session().run(Cypher_source.get_repositories_w_notes)
#         for record in result:
#             # ╒════════╤══════════════════════════════╤══════════════════════════════╕
#             # │"medium"│"repo"                        │"notes"                       │
#             # ╞════════╪══════════════════════════════╪══════════════════════════════╡
#             # │"Book"  │{"handle":"_d82643ea4fb541e47c│[{"id":"N1-R0003","text":"Lapi│
#             # │        │47b1960a1","id":"R0003","rname│njärven srk arkisto Digihakemi│
#             # │        │":"Lapinjärven seurakunnan ark│stossa","type":"Web Search","u│
#             # │        │isto","type":"Archive","change│rl":"http://digihakemisto...  │
#             # │        │":"1541271759"}               │                              │
#             # └────────┴──────────────────────────────┴──────────────────────────────┘
#             repo = Repository.from_node(record['repo'])
#             
#             if record['medium']:
#                 repo.medium = record['medium']
#             for node in record['notes']:
#                 repo.notes.append(Note.from_node(node))
# 
#             self.repositories.append(repo)


#     def get_reporef_hlink(self):
#         """ Luetaan lähteen arkiston uniq_id kannasta, removed 3.5.2019 """
#                         
#         query = """
#             MATCH (source:Source)-[r:REPOSITORY]->(repo:Repository)
#                 WHERE ID(source)={}
#                 RETURN ID(repo) AS id, r.medium AS reporef_medium
#             """.format(self.uniq_id)
#             
#         result = shareds.driver.session().run(query)
#         for record in result:
#             if record['id']:
#                 self.reporef_hlink = record['id']
#             if record['reporef_medium']:
#                 self.reporef_medium = record['reporef_medium']
        
    
    @staticmethod       
    def get_source_w_notes(uniq_id):
        """ Read Source with connected Repositories and Notes.

            Luetaan lähteen tiedot
        """
                        
        return  shareds.driver.session().run(Cypher_source.get_a_source_w_notes,
                                             sid=uniq_id)
    
    
    @staticmethod       
    def get_citating_nodes(sourceid):
        """ Read Events and Person citating this Source
            Luetaan tapahtumat tai henkilöt, jotka siteeraavat tätä lähdettä
╒══════╤═══════════════════════════════╤══════╤════════╤═══════════════════════════════╤══════╕
│"c_id"│"c"                            │"x_id"│"label" │"x"                            │"p_id"│
╞══════╪═══════════════════════════════╪══════╪════════╪═══════════════════════════════╪══════╡
│89359 │{"handle":"_dd7686926d946cd18c5│72104 │"Person"│{"handle":"_dd76810c8e6763f7ea8│72104 │
│      │642e61e2","id":"C1361","page":"│      │        │16742a59","id":"I1069","priv":"│      │
│      │1891 Syyskuu 22","dateval":"","│      │        │","sex":"2","confidence":"2.   │      │
│      │change":1521882215,"confidence"│      │        │0","change":1521883281}        │      │
│      │:"2"}                          │      │        │                               │      │
├──────┼───────────────────────────────┼──────┼────────┼───────────────────────────────┼──────┤
│89359 │{"handle":"_dd7686926d946cd18c5│84323 │"Event" │{"datetype":0,"change":15218822│72104 │
│      │642e61e2","id":"C1361","page":"│      │        │40,"description":"","handle":"_│      │
│      │1891 Syyskuu 22","dateval":"","│      │        │dd76825122e5977bf3ee88e213f","a│      │
│      │change":1521882215,"confidence"│      │        │ttr_type":"","id":"E2821","date│      │
│      │:"2"}                          │      │        │2":1936694,"type":"Death","date│      │
│      │                               │      │        │1":1936694,"attr_value":""}    │      │
├──────┼───────────────────────────────┼──────┼────────┼───────────────────────────────┼──────┤
│90805 │{"handle":"_dd3d8163aa4669ee3c7│79151 │"Person"│{"handle":"_dd35ec52c317a8b925f│79151 │
│      │be3a25ee","id":"C0862","page":"│      │        │d6d9fcae","id":"I0700","priv":"│      │
│      │1903 Elok. 30","dateval":"","ch│      │        │","sex":"2","confidence":"2.│      │
│      │ange":1521040882,"confidence":"│      │        │0","change":1523034715}        │      │
│      │2"}                            │      │        │                               │      │
├──────┼───────────────────────────────┼──────┼────────┼───────────────────────────────┼──────┤
│90805 │{"handle":"_dd3d8163aa4669ee3c7│87087 │"Event" │{"datetype":0,"change":15203522│79151 │
│      │be3a25ee","id":"C0862","page":"│      │        │52,"description":"","handle":"_│      │
│      │1903 Elok. 30","dateval":"","ch│      │        │dd35ec523e0723c20d5294117f4","a│      │
│      │ange":1521040882,"confidence":"│      │        │ttr_type":"","id":"E0280","date│      │
│      │2"}                            │      │        │2":1948958,"type":"Death","date│      │
│      │                               │      │        │1":1948958,"attr_value":""}    │      │
└──────┴───────────────────────────────┴──────┴────────┴───────────────────────────────┴──────┘
        """

        return shareds.driver.session().run(Cypher_source.get_citators_of_source, 
                                            sid=int(sourceid))


    @staticmethod       
    def get_source_list(o_filter=None):
        """ Read all sources with notes and repositories, optionally limited by keywords.
        
            Todo: Luetaan valitut lähteet teeman mukaan valittuna.
            Todo: Valinta vuosien mukaan
            Todo: tuloksen sivuttaminen esim. 100 kpl / sivu
        """
# ╒═════════╤═════╤════════════════╤════════════════╤═════════╤═════════╤═════════╕
# │"uniq_id"│"id" │"stitle"        │"repository"    │"medium" │"cit_cnt"│"ref_cnt"│
# ╞═══════╪═══════╪════════════════╪════════════════╪════════════╪══════╪═════════╡
# │29442  │"S0253"│"Ansioluetteloko│"Kansallisarkist│"Book"      │1     │1        │
# │       │       │koelma"         │o"              │            │      │         │
# ├───────┼───────┼────────────────┼────────────────┼────────────┼──────┼─────────┤
# │29212  │"S0004"│"Borgåbladet"   │"Kansalliskirjas│"Newspaper" │1     │0        │
# │       │       │                │ton digitoidut s│            │      │         │
# │       │       │                │anomalehdet"    │            │      │         │
# └───────┴───────┴────────────────┴────────────────┴────────────┴──────┴─────────┘

        ret = []
        if o_filter.series:
            # Filtered by series (Lähdesarja)
            THEMES = {"birth": ('syntyneet','födda'),
                      "babtism": ('kastetut','döpta'),
                      "wedding": ('vihityt','vigda'),
                      "death": ('kuolleet','döda'),
                      "move": ('muuttaneet','flyttade')
                }
            key1, key2 = THEMES[o_filter.series]
            print(f'# Sources containing "{key1}" or "{key2}"')
            with shareds.driver.session() as session:
                result = session.run(Cypher_source.get_selected_sources_w_notes,
                                     key1=key1, key2=key2)
        else:
            # Show all
            with shareds.driver.session() as session:
                result = session.run(Cypher_source.get_sources_w_notes)

        for _uniq_id, source, notes, repositories, cit_cnt, ref_cnt in result:
            # <Record
            # 0  uniq_id=242567 
            # 1  source=<Node id=242567 labels={'Source'} 
            #        properties={'handle': '_dcb5682a0f47b7de686b3251557', 'id': 'S0334', 
            #            'stitle': 'Åbo stifts herdaminne 1554-1640', 'change': '1516698633'}> 
            # 2  notes=[<Node id=238491 labels={'Note'} 
            #        properties={'handle': '_e07cd6210c57e0d53393a62fa7a', 'id': 'N3952', 
            #        'text': '', 'type': 'Source Note', 'url': 'http://www.narc.fi:8080/...', 
            #        'change': 1542667331}>] 
            # 3  repositories=[
            #        ['Book', <Node id=238996 labels={'Repository'} 
            #            properties={'handle': '_db51a3f358e67ac82ade828edd1', 'id': 'R0057', 
            #            'rname': 'Painoteokset', 'type': 'Collection', 'change': '1541350910'}>]]
            # 4  cit_cnt=1 
            # 5  ref_cnt=1
            # >

            s = Source.from_node(source)

            for note in notes:
                n = Note.from_node(note)
                s.notes.append(n)

            for repo_item in repositories:
                # [medium, repo_node]
                if repo_item[1] != None:
                    rep = Repository.from_node(repo_item[1])
                    rep.medium = repo_item[0]
                    s.repositories.append(rep)
#                 s.repo_name = record['repository']
#                 s.medium = record['medium']
            s.cit_cnt = cit_cnt
            s.ref_cnt = ref_cnt
#                 s.cit_cnt = record['cit_cnt']
#                 s.ref_cnt = record['ref_cnt']
            ret.append(s)

        return ret, o_filter.series

    @staticmethod       
    def get_source_citation (uniq_id):
        """ Voidaan lukea lähteitä viittauksineen kannasta
        """

        if uniq_id:
            get_one = """
MATCH (citation:Citation)-[r:SOURCE]->(source:Source) 
    WHERE ID(source)=$uid
WITH citation, r, source ORDER BY citation.page
RETURN source, COLLECT(citation) AS citations
    ORDER BY source.stitle"""
            return shareds.driver.session().run(get_one, uid=uniq_id)
        else:
            get_all = """
MATCH (citation:Citation)-[r:SOURCE]->(source:Source) 
WITH citation, r, source ORDER BY citation.page
RETURN source, COLLECT(citation) AS citations
    ORDER BY source.stitle"""
            return shareds.driver.session().run(get_all)

    
    @staticmethod       
    def get_sources_wo_citation ():
        """ Voidaan lukea viittauksettomia läheitä kannasta
        """
        
        query = """
 MATCH (s:Source) WHERE NOT EXISTS((:Citation)-[:SOURCE]->(s:Source))
 RETURN ID(s) AS uniq_id, s
 ORDER BY s.stitle"""
                
        result = shareds.driver.session().run(query)
        
        titles = ['uniq_id', 'handle', 'change', 'id', 'stitle']
        lists = []
        
        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["s"]['handle']:
                data_line.append(record["s"]['handle'])
            else:
                data_line.append('-')
            if record["s"]['change']:
                data_line.append(record["s"]['change'])
            else:
                data_line.append('-')
            if record["s"]['id']:
                data_line.append(record["s"]['id'])
            else:
                data_line.append('-')
            if record["s"]['stitle']:
                data_line.append(record["s"]['stitle'])
            else:
                data_line.append('-')
            if record["s"]['sauthor']:
                data_line.append(record["s"]['sauthor'])
            else:
                data_line.append('-')
            if record["s"]['spubinfo']:
                data_line.append(record["s"]['spubinfo'])
            else:
                data_line.append('-')
                
            lists.append(data_line)
        
        return (titles, lists)
    
    
    @staticmethod       
    def get_sources_wo_repository ():
        """ Voidaan lukea läheitä, joilla ei ole arkistoa kannasta
        """
        
        query = """
 MATCH (s:Source) WHERE NOT EXISTS((s:Source)-[:REPOSITORY]->(:Repository))
 RETURN ID(s) AS uniq_id, s
 ORDER BY s.stitle"""
                
        result = shareds.driver.session().run(query)
        
        titles = ['uniq_id', 'handle', 'change', 'id', 'stitle', 'sauthor', 'spubinfo']
        lists = []
        
        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["s"]['handle']:
                data_line.append(record["s"]['handle'])
            else:
                data_line.append('-')
            if record["s"]['change']:
                data_line.append(record["s"]['change'])
            else:
                data_line.append('-')
            if record["s"]['id']:
                data_line.append(record["s"]['id'])
            else:
                data_line.append('-')
            if record["s"]['stitle']:
                data_line.append(record["s"]['stitle'])
            else:
                data_line.append('-')
            if record["s"]['sauthor']:
                data_line.append(record["s"]['sauthor'])
            else:
                data_line.append('-')
            if record["s"]['spubinfo']:
                data_line.append(record["s"]['spubinfo'])
            else:
                data_line.append('-')
                
            lists.append(data_line)
        
        return (titles, lists)

    
    @staticmethod       
    def get_total():
        """ Tulostaa lähteiden määrän tietokannassa """
                        
        query = """
            MATCH (s:Source) RETURN COUNT(s)
            """
        results =  shareds.driver.session().run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Source*****")
        print ("Handle: " + self.handle)
        print ("Change: {}".format(self.change))
        print ("Id: " + self.id)
        if self.stitle != '':
            print ("Stitle: " + self.stitle)
        if self.stitle != '':
            print ("Sauthor: " + self.sauthor)
        if self.stitle != '':
            print ("Spubinfo: " + self.spubinfo)
        if self.note_handles:
            print (f"Note handles: {self.note_handles}")
        for repo in self.repositories:
            print (f"Repository: {repo}")
        return True
        

