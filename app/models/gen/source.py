'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from sys import stderr

from models.cypher_gramps import Cypher_source_w_handle
from .cypher import Cypher_source
import shareds


class Source:
    """ Lähde
            
        Properties:
                handle          
                change
                id              esim. "S0001"
                stitle          str lähteen otsikko
                noteref_hlink   str huomautuksen osoite
                reporef_hlink   str arkiston osoite
                reporef_medium  str arkiston laatu, esim. "Book"
     """

    def __init__(self):
        """ Luo uuden source-instanssin """
        self.handle = ''
        self.change = 0
        self.id = ''
        self.stitle = ''
        self.noteref_hlink = ''
        self.reporef_hlink = ''
        self.reporef_medium = ''
        self.citations = []   # For creating display sets
        self.repos = []   # For creating display sets


    def __str__(self):
        return "{} {}".format(self.id, self.stitle)


    @staticmethod
    def from_node(node):
        '''
        Transforms a db node to an object of type Source.
        
        <Node id=91394 labels={'Source'} 
            properties={'handle': '_d9edc4e4a9a6defc258', 'id': 'S0078', 
                'stitle': 'Kangasala syntyneet 1721-1778', 'change': '1507149115'}>
        '''
        s = Source()
        s.id = node.id
        s.uniq_id = node['uniq_id']
        s.handle = node['handle']
        s.stitle = node['stitle']
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


    def get_reporef_hlink(self):
        """ Luetaan lähteen arkiston uniq_id kannasta """
                        
        query = """
            MATCH (source:Source)-[r:REPOSITORY]->(repo:Repository)
                WHERE ID(source)={}
                RETURN ID(repo) AS id, r.medium AS reporef_medium
            """.format(self.uniq_id)
            
        result = shareds.driver.session().run(query)
        for record in result:
            if record['id']:
                self.reporef_hlink = record['id']
            if record['reporef_medium']:
                self.reporef_medium = record['reporef_medium']
        
    
    def get_source_data(self):
        """ Luetaan lähteen tiedot """
                        
        query = """
            MATCH (source:Source)
                WHERE ID(source)={}
                RETURN source.stitle AS stitle
            """.format(self.uniq_id)
        return  shareds.driver.session().run(query)
    
    
    @staticmethod       
    def get_citating_nodes(sourceid):
        """ Read Events and Person citating this Source
            Luetaan tapahtumat tai henkilöt, jotka siteeraavat tätä lähdettä
╒══════╤═══════════════════════════════╤══════╤════════╤═══════════════════════════════╤══════╕
│"c_id"│"c"                            │"x_id"│"label" │"x"                            │"p_id"│
╞══════╪═══════════════════════════════╪══════╪════════╪═══════════════════════════════╪══════╡
│89359 │{"handle":"_dd7686926d946cd18c5│72104 │"Person"│{"handle":"_dd76810c8e6763f7ea8│72104 │
│      │642e61e2","id":"C1361","page":"│      │        │16742a59","id":"I1069","priv":"│      │
│      │1891 Syyskuu 22","dateval":"","│      │        │","gender":"F","confidence":"2.│      │
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
│      │1903 Elok. 30","dateval":"","ch│      │        │","gender":"F","confidence":"2.│      │
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
    def get_source_list():
        """ Luetaan kaikki lähteet """
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
        result = shareds.driver.session().run(Cypher_source.source_list)
        for record in result:
            s = Source()
            s.uniq_id = record['uniq_id']
            s.id = record['id']
            s.stitle = record['stitle']
            s.repo_name = record['repository']
            s.medium = record['medium']
            s.cit_cnt = record['cit_cnt']
            s.ref_cnt = record['ref_cnt']
            ret.append(s)
            
        return ret
            
    
    @staticmethod       
    def get_source_citation (uniq_id):
        """ Voidaan lukea lähteitä viittauksineen kannasta
        """

        if uniq_id:
            where = "WHERE ID(source)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
 MATCH (citation:Citation)-[r:SOURCE]->(source:Source) {0}
   WITH citation, r, source ORDER BY citation.page
 RETURN ID(source) AS id, source.stitle AS stitle, 
  COLLECT([ID(citation), citation.dateval, citation.page, citation.confidence]) AS citations
 ORDER BY source.stitle""".format(where)
                
        return shareds.driver.session().run(query)
    
    
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
                data_line.append(int(record["s"]['change']))  #TODO only temporary int()
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
                data_line.append(int(record["s"]['change']))  #TODO only temporary int()
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
        if self.noteref_hlink != '':
            print ("Noteref_hlink: " + self.noteref_hlink)
        if self.reporef_hlink != '':
            print ("Reporef_hlink: " + self.reporef_hlink)
        return True
        

    def save(self, tx):
        """ Saves this Source and connects it to Notes and Repositories """

        try:
            s_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "stitle": self.stitle
            }

            tx.run(Cypher_source_w_handle.create, s_attr=s_attr)
        except Exception as err:
            print("Virhe (Source.save): {0}".format(err), file=stderr)
            #TODO raise ConnectionError("Source.save: {0}".format(err))

        # Make relation to the Note node
        if self.noteref_hlink != '':
            try:
                tx.run(Cypher_source_w_handle.link_note,
                       handle=self.handle, hlink=self.noteref_hlink)
            except Exception as err:
                print("Virhe (Source.save:Note): {0}".format(err), file=stderr)

        # Make relation to the Repository node
        if self.reporef_hlink != '':
            try:
                tx.run(Cypher_source_w_handle.link_repository,
                       handle=self.handle, hlink=self.reporef_hlink)
            except Exception as err:
                print("Virhe (Source.save:Repository): {0}".format(err), file=stderr)
                
            # Set the medium data of the Source node
            try:
                tx.run(Cypher_source_w_handle.set_repository_medium,
                       handle=self.handle, medium=self.reporef_medium)
            except Exception as err:
                print("Virhe (Source.save:repository_medium): {0}".format(err), file=stderr)

        return


# class Weburl():
#     """ A web reference 
#     """
# 
#     def __init__(self, href=None, rtype=None, description=""):
#         self.url_href = href
#         self.url_type = rtype
#         self.url_description = description

