'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from sys import stderr
from models.cypher_gramps import Cypher_source_w_handle
from models.cypher_gramps import Cypher_citation_w_handle
from models.cypher_gramps import Cypher_repository_w_handle
import shareds

class Citation:
    """ Viittaus
            
        Properties:
                handle          
                change
                id               esim. "C0001"
                dateval          str date
                page             str page
                confidence       str confidence
                noteref_hlink    str huomautuksen osoite
                sourceref_hlink  str lähteen osoite
     """

    def __init__(self):
        """ Luo uuden citation-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        self.dateval = ''
        self.page = ''
        self.noteref_hlink = []
        self.sourceref_hlink = ''
        self.sources = []   # For creating display sets
        self.events = []   # For creating display sets
    
    
    @staticmethod       
    def get_source_repo (uniq_id=None):
        """ Read Citation -> Source -> Repository chain
            and optionally Notes.            
            Citation has all data but c.handle

            Voidaan lukea viittauksen lähde ja arkisto kannasta
        """

        if uniq_id:
            where = "WHERE ID(c)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
 MATCH (c:Citation) -[r:SOURCE]-> (source:Source) 
    -[p:REPOSITORY]-> (repo:Repository) {0}
 OPTIONAL MATCH (c) -[n:NOTE]-> (note:Note)
   WITH c, r, source, p, repo 
   ORDER BY c.page, note
 RETURN ID(c) AS id, 
    c.dateval AS date,
    c.page AS page,
    c.confidence AS confidence, 
    note.text AS notetext,
    COLLECT(DISTINCT [ID(source), 
             source.stitle, 
             p.medium, 
             ID(repo), 
             repo.rname, 
             repo.type]) AS sources
 """.format(where)
                
        return shareds.driver.session().run(query)
    
    
    def get_sourceref_hlink(self):
        """ Voidaan lukea lähdeviittauksen lähteen uniq_id kannasta
        """
        
        query = """
 MATCH (citation:Citation)-[r:SOURCE]->(source:Source) WHERE ID(citation)={}
 RETURN ID(source) AS id
 """.format(self.uniq_id)
                
        result = shareds.driver.session().run(query)
        for record in result:
            if record['id']:
                self.sourceref_hlink = record['id']

    
    @staticmethod       
    def get_total():
        """ Tulostaa lähteiden määrän tietokannassa """
                        
        query = """
            MATCH (c:Citation) RETURN COUNT(c)
            """
        results = shareds.driver.session().run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Citation*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Dateval: " + self.dateval)
        print ("Page: " + self.page)
        print ("Confidence: " + self.confidence)
        if len(self.noteref_hlink) > 0:
            for i in range(len(self.noteref_hlink)):
                print ("Noteref_hlink: " + self.noteref_hlink[i])
        if self.sourceref_hlink != '':
            print ("Sourceref_hlink: " + self.sourceref_hlink)
        return True


    def save(self, tx):
        """ Saves this Citation and connects it to it's Notes and Sources"""

        try:
            # Create a new Citation node
                
            c_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "dateval": self.dateval, 
                "page": self.page, 
                "confidence": self.confidence
            }
            tx.run(Cypher_citation_w_handle.create, c_attr=c_attr)
        except Exception as err:
            print("Virhe (Citation.save): {0}".format(err), file=stderr)
            raise SystemExit("Stopped due to errors")    # Stop processing
            #TODO raise ConnectionError("Citation.save: {0}".format(err))

        # Make relations to the Note nodes
        for hlink in self.noteref_hlink:
            try:
                tx.run(Cypher_citation_w_handle.link_note, 
                       handle=self.handle, hlink=hlink)
            except Exception as err:
                print("Virhe (Citation.save:Note hlink): {0}".format(err), file=stderr)

        try:   
            # Make relation to the Source node
            if self.sourceref_hlink != '':
                tx.run(Cypher_citation_w_handle.link_source,
                       handle=self.handle, hlink=self.sourceref_hlink)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
        return
    

class Repository:
    """ Repository / Arkisto
            
        Properties:
            uniq_id         int    db native key or None
            handle          str    Gramps handle
            change          int    timestamp
            id              str    esim. "R0001"
            rname           str    arkiston nimi
            type            str    arkiston tyyppi
            url_refs        Weburl(url_href, url_type, url_description)[]
#                 url_href        str url osoite
#                 url_type        str url tyyppi
#                 url_description str url kuvaus

     """

    def __init__(self):
        """ Luo uuden repository-instanssin """
        self.uniq_id = None
        self.handle = ''
        self.change = ''
        self.id = ''
        self.url_refs = []
        self.sources = []   # For creating display sets
        
    
    @staticmethod
    def _to_self(record):
        '''
        Transforms a db record to an object of type Repository
        #TODO muodosta url_refs Weburl:in komponenteista
        '''
        n = Repository()
        if record['uniq_id']:
            n.uniq_id = int(record['uniq_id'])
        record_n = record['r']
        if record_n['handle']:
            n.handle = record_n['handle']
        if record_n['change']:
            n.change = int(record_n['change'])
        if record_n['id']:
            n.id = record_n['id']
        if record_n['priv']:
            n.priv = record_n['priv']
        if record_n['type']:
            n.type = record_n['type']
        if record_n['text']:
            n.text = record_n['text']
        return n


    def get_repo_data(self):
        """ Luetaan arkiston tiedot """
                        
        query = """
            MATCH (repo:Repository) WHERE ID(repo) = {}
            RETURN repo.rname AS rname, repo.type AS type
            """.format(self.uniq_id)
        return  shareds.driver.session().run(query)
    
    
    @staticmethod
    def get_repositories(uniq_id):
        """ Reads all Repository nodes or selected Repository node from db

            Now called only from models.datareader.get_repositories for 
            "table_of_objects.html"
        """

        result = None
        with shareds.driver.session() as session:
            if uniq_id:
                repository_get = """
MATCH (r:Repository)
WHERE ID(r) == $rid
RETURN ID(n) AS uniq_id, r"""
                result =  session.run(repository_get, nid=uniq_id)
            else:
                repository_get_all = """
MATCH (r:Repository)
RETURN ID(n) AS uniq_id, r 
ORDER BY r.type"""
                result =  session.run(repository_get_all)

        titles = ['uniq_id', 'handle', 'change', 'id', 'type', 'name']
        repositories = []

        for record in result:
            # Create a Note object from record
            n = Repository._to_self(record)
            repositories.append(n)

        return (titles, repositories)


#     @staticmethod       
#     def get_repositories():
#         """ Luetaan kaikki arkistot """
#                         
#         query = "MATCH (repo:Repository) RETURN repo"
#         return  shareds.driver.session().run(query)
    
    
    @staticmethod       
    def get_repository(rname):
        """ Luetaan arkiston handle """
                        
        query = """
            MATCH (repo:Repository) WHERE repo.rname='{}'
                RETURN repo
            """.format(rname)
        return  shareds.driver.session().run(query)
    
    
    @staticmethod       
    def get_repository_source (uniq_id):
        """ Voidaan lukea repositoreja sourceneen kannasta
        """

        if uniq_id:
            where = "WHERE ID(repository)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
MATCH (repository:Repository) <-[r:REPOSITORY]- (source:Source) {0}
    WITH repository, r, source ORDER BY source.stitle
RETURN ID(repository) AS id, repository.rname AS rname, 
    repository.type AS type, repository.url_href AS url_href, 
    repository.url_type AS url_type, repository.url_description AS url_description,
    COLLECT([ID(source), source.stitle, r.medium]) AS sources
ORDER BY repository.rname""".format(where)
                
        return shareds.driver.session().run(query)
                
    
    @staticmethod       
    def get_total():
        """ Tulostaa arkistojen määrän tietokannassa """
                        
        query = """
            MATCH (r:Repository) RETURN COUNT(r)
            """
        results =  shareds.driver.session().run(query)
        
        for result in results:
            return str(result[0])


    def print_data(self):
        """ Tulostaa tiedot """
        print ("*****Repository*****")
        print ("Handle: " + self.handle)
        print ("Change: " + self.change)
        print ("Id: " + self.id)
        print ("Rname: " + self.rname)
        print ("Type: " + self.type)
        print ("Url href: " + self.url_href)
        print ("Url type: " + self.url_type)
        print ("Url description: " + self.url_description)
        return True


    def save(self, tx):
        """ Saves this Repository to db"""

        try:
            r_attr = {
                "handle": self.handle,
                "change": self.change,
                "id": self.id,
                "rname": self.rname,
                "type": self.type,
            }
            if len(self.url_refs) > 0:
                with self.url_refs[0] as url:
                    r_attr['url_href'] = url.url_href
                    r_attr['url_type'] = url.url_type
                    r_attr['url_description'] = url.url_description
                
            tx.run(Cypher_repository_w_handle.create, r_attr=r_attr)
        except Exception as err:
            print("Virhe (Repository.save): {0}".format(err), file=stderr)
            raise SystemExit("Stopped due to errors")    # Stop processing
            #TODO raise ConnectionError("Repository.save: {0}".format(err))

        return


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
        self.change = ''
        self.id = ''
        self.stitle = ''
        self.noteref_hlink = ''
        self.reporef_hlink = ''
        self.reporef_medium = ''
        self.citations = []   # For creating display sets
        self.repos = []   # For creating display sets

    def __str__(self):
        return "{} {}".format(self.id, self.stitle)
    
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
    def get_events(sourceid):
        """ Luetaan kaikki lähteen tapahtumat 

╒════════════════╤════════════╤══════════════════════════════╤═══════╤════════════════╕
│"page"          │"confidence"│"events"                      │"pid"  │"names"         │
├────────────────┴───────┼────┼──────────────────────────────┼───────┼────────────────┤
│"http://hiski.genealogia│"1" │[["35450","Occupation",""],["3│"36349"│[["Carlstedt",  │
│.fi/hiski?fi+t4714729"  │    │5449","Death","1809-02-22"]]  │       │"Jonas"]]       │
├────────────────────────┼────┼──────────────────────────────┼───────┼────────────────┤
│"http://hiski.genealogia│"1" │[["35790","Death","1839-01-16"│"36834"│[["Kyander",    │
│.fi/hiski?fi+t4717438"  │    │]]                            │       │"Magnus Johan"]]│
└────────────────────────┴────┴──────────────────────────────┴───────┴────────────────┘
        """

        query = """
MATCH (source:Source)<-[:SOURCE]-(citation:Citation)<-[r:CITATION]-(event:Event)
    <-[*1..2]-(p:Person)-->(name:Name) 
WHERE ID(source)={sourceid}
WITH event, citation,
    COLLECT([ID(p),name.surname, name.firstname, name.suffix]) AS names
WITH citation,
     COLLECT([ID(event), event.type, event.date, names]) AS events
RETURN COLLECT([citation.page, citation.confidence, events]) AS citations"""

        return shareds.driver.session().run(query, sourceid=int(sourceid))


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
        source_list_query = """
MATCH (s:Source)
OPTIONAL MATCH (s)<-[:SOURCE]-(c:Citation)
OPTIONAL MATCH (c)<-[:CITATION]-(e)
OPTIONAL MATCH (s)-[r:REPOSITORY]->(a:Repository)
RETURN ID(s) AS uniq_id, s.id AS id, s.stitle AS stitle, 
       a.rname AS repository, r.medium AS medium,
       COUNT(c) AS cit_cnt, COUNT(e) AS ref_cnt 
ORDER BY toUpper(stitle)
"""
        ret = []
        result = shareds.driver.session().run(source_list_query)
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
        print ("Change: " + self.change)
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


class Weburl():
    """ A web reference 
    """

    def __init__(self, href=None, rtype=None, description=""):
        self.url_href = href
        self.url_type = rtype
        self.url_description = description

