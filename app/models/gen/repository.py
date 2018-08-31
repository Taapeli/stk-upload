'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from sys import stderr

from models.cypher_gramps import Cypher_repository_w_handle
from models.gen.weburl import Weburl
import shareds
   

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
#                 href        str url osoite
#                 type        str url tyyppi
#                 description str url kuvaus

    #TODO: url_refs[] --> urls[] list should contain Weburl instances
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
            #TODO: usr_refs[] -> urls[] list should contain Weburl instances
            if len(self.url_refs) > 0:
                with self.url_refs[0] as url:
                    r_attr['url_href'] = url.href
                    r_attr['url_type'] = url.type
                    r_attr['url_description'] = url.description
                
            tx.run(Cypher_repository_w_handle.create, r_attr=r_attr)
        except Exception as err:
            print("Virhe (Repository.save): {0}".format(err), file=stderr)
            raise SystemExit("Stopped due to errors")    # Stop processing
            #TODO raise ConnectionError("Repository.save: {0}".format(err))

        return
