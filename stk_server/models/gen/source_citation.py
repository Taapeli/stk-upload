'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

import datetime
from sys import stderr
import logging
from flask import g
import models.dbutil


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
        self.noteref_hlink = ''
        self.sourceref_hlink = ''
        self.sources = []   # For creating display sets
        self.events = []   # For creating display sets
    
    
    @staticmethod       
    def get_source_repo (uniq_id=None):
        """ Voidaan lukea viittauksen lähde ja arkisto kannasta
        """

        if uniq_id:
            where = "WHERE ID(citation)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
 MATCH (citation:Citation)-[r]->(source:Source)-[p]->(repo:Repository) {0}
 OPTIONAL MATCH (citation)-[n]->(note:Note)
   WITH citation, r, source, p, repo ORDER BY citation.page, note
 RETURN ID(citation) AS id, citation.dateval AS date, citation.page AS page, 
     citation.confidence AS confidence, note.text AS notetext,
   COLLECT([ID(source), source.stitle, p.medium, 
       ID(repo), repo.rname, repo.type]) AS sources
 """.format(where)
                
        return g.driver.session().run(query)
    
    
    def get_sourceref_hlink(self):
        """ Voidaan lukea lähdeviittauksen lähteen uniq_id kannasta
        """
        
        query = """
 MATCH (citation:Citation)-[r]->(source:Source) WHERE ID(citation)={}
 RETURN ID(source) AS id
 """.format(self.uniq_id)
                
        result = g.driver.session().run(query)
        for record in result:
            if record['id']:
                self.sourceref_hlink = record['id']

    
    @staticmethod       
    def get_total():
        """ Tulostaa lähteiden määrän tietokannassa """
                        
        query = """
            MATCH (c:Citation) RETURN COUNT(c)
            """
        results = g.driver.session().run(query)
        
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
        if self.noteref_hlink != '':
            print ("Noteref_hlink: " + self.noteref_hlink)
        if self.sourceref_hlink != '':
            print ("Sourceref_hlink: " + self.sourceref_hlink)
        return True


    def save(self, tx):
        """ Tallettaa sen kantaan """

        try:
            # Create a new Citation node
            query = """
                CREATE (n:Citation) 
                SET n.gramps_handle='{}', 
                    n.change='{}', 
                    n.id='{}', 
                    n.dateval='{}', 
                    n.page='{}', 
                    n.confidence='{}'
                """.format(self.handle, self.change, self.id, self.dateval, 
                           self.page, self.confidence)
                
            tx.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:
            # Make relation to the Note node
            if self.noteref_hlink != '':
                query = """
                    MATCH (n:Citation) WHERE n.gramps_handle='{}'
                    MATCH (m:Note) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:NOTE]->(m)
                     """.format(self.handle, self.noteref_hlink)
                                 
                tx.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)

        try:   
            # Make relation to the Source node
            if self.sourceref_hlink != '':
                query = """
                    MATCH (n:Citation) WHERE n.gramps_handle='{}'
                    MATCH (m:Source) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:SOURCE]->(m)
                     """.format(self.handle, self.sourceref_hlink)
                                 
                tx.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
        return
    

class Repository:
    """ Arkisto
            
        Properties:
                handle          
                change
                id              esim. "R0001"
                rname           str arkiston nimi
                type            str arkiston tyyppi
                url_href        str url osoite
                url_type        str url tyyppi
                url_description str url kuvaus

     """

    def __init__(self):
        """ Luo uuden repository-instanssin """
        self.handle = ''
        self.change = ''
        self.id = ''
        self.url_href = []
        self.url_type = []
        self.url_description = []
        self.sources = []   # For creating display sets
        
    
    def get_repo_data(self):
        """ Luetaan arkiston tiedot """
                        
        query = """
            MATCH (repo:Repository) WHERE ID(repo) = {}
            RETURN repo.rname AS rname, repo.type AS type
            """.format(self.uniq_id)
        return  g.driver.session().run(query)
    
    
    @staticmethod       
    def get_repositories():
        """ Luetaan kaikki arkistot """
                        
        query = """
            MATCH (repo:Repository) RETURN repo
            """
        return  g.driver.session().run(query)
    
    
    @staticmethod       
    def get_repository(rname):
        """ Luetaan arkiston handle """
                        
        query = """
            MATCH (repo:Repository) WHERE repo.rname='{}'
                RETURN repo
            """.format(rname)
        return  g.driver.session().run(query)
    
    
    @staticmethod       
    def get_repository_source (uniq_id):
        """ Voidaan lukea repositoreja sourceneen kannasta
        """

        if uniq_id:
            where = "WHERE ID(repository)={} ".format(uniq_id)
        else:
            where = ''
        
        query = """
 MATCH (repository:Repository)<-[r]-(source:Source) {0}
   WITH repository, r, source ORDER BY source.stitle
 RETURN ID(repository) AS id, repository.rname AS rname, 
   repository.type AS type, repository.url_href AS url_href, 
   repository.url_type AS url_type, repository.url_description AS url_description,
  COLLECT([ID(source), source.stitle, r.medium]) AS sources
 ORDER BY repository.rname""".format(where)
                
        return g.driver.session().run(query)
                
    
    @staticmethod       
    def get_total():
        """ Tulostaa arkistojen määrän tietokannassa """
                        
        query = """
            MATCH (r:Repository) RETURN COUNT(r)
            """
        results =  g.driver.session().run(query)
        
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
        """ Tallettaa sen kantaan """

        try:
            handle = self.handle
            change = self.change
            pid = self.id
            rname = self.rname
            type = self.type
            url_href = self.url_href
            url_type = self.url_type
            url_description = self.url_description
            query = """
CREATE (r:Repository) 
SET r.gramps_handle=$handle, 
    r.change=$change, 
    r.id=$id, 
    r.rname=$rname, 
    r.type=$type,
    r.url_href=$url_href,
    r.url_type=$url_type,
    r.url_description=$url_description"""
            tx.run(query, 
               {"handle": handle, "change": change, "id": pid, "rname": rname, "type": type, 
                "url_href": url_href, "url_type": url_type, "url_description": url_description})
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
            
            
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
        
    
    def get_reporef_hlink(self):
        """ Luetaan lähteen arkiston uniq_id kannasta """
                        
        query = """
            MATCH (source:Source)-[r:REPOSITORY]->(repo:Repository)
                WHERE ID(source)={}
                RETURN ID(repo) AS id, r.medium AS reporef_medium
            """.format(self.uniq_id)
            
        result = g.driver.session().run(query)
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
        return  g.driver.session().run(query)
    
    
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
MATCH (source:Source)<--(citation:Citation)<-[r:CITATION]-(event:Event)
WHERE ID(source)={sourceid}
OPTIONAL MATCH (event)<-[*1..2]-(p:Person)-->(name:Name)
WITH citation.page AS page, citation.confidence AS confidence,
     p, name,
     COLLECT([ID(event), event.type, event.date]) AS events
RETURN page, confidence, events, ID(p) AS pid,
       COLLECT([name.surname, name.firstname]) AS names"""

        return g.driver.session().run(query, sourceid=int(sourceid))


    @staticmethod       
    def get_source_list():
        """ Luetaan kaikki lähteet """
                        
#         query = """
# MATCH (source:Source)
#     RETURN ID(source) AS uniq_id, 
#         source.id AS id, 
#         source.stitle AS stitle
#     ORDER BY source.stitle
#             """
        source_list_query = """
MATCH (s:Source)
OPTIONAL MATCH (s)<-[:SOURCE]-(c:Citation)
OPTIONAL MATCH (c)<-[:CITATION]-(e)
RETURN ID(s) AS uniq_id, s.id AS id, s.stitle AS stitle, 
       COUNT(c) AS cit_cnt, COUNT(e) AS ref_cnt 
ORDER BY toUpper(stitle)
        """
        ret = []
        result = g.driver.session().run(source_list_query)
        for record in result:
            s = Source()
            s.uniq_id = record['uniq_id']
            s.id = record['id']
            s.stitle = record['stitle']
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
 MATCH (citation:Citation)-[r]->(source:Source) {0}
   WITH citation, r, source ORDER BY citation.page
 RETURN ID(source) AS id, source.stitle AS stitle, 
  COLLECT([ID(citation), citation.dateval, citation.page, citation.confidence]) AS citations
 ORDER BY source.stitle""".format(where)
                
        return g.driver.session().run(query)
    
    
    @staticmethod       
    def get_sources_wo_citation ():
        """ Voidaan lukea viittauksettomia läheitä kannasta
        """
        
        query = """
 MATCH (s:Source) WHERE NOT EXISTS((:Citation)-[:SOURCE]->(s:Source))
 RETURN ID(s) AS uniq_id, s
 ORDER BY s.stitle"""
                
        result = g.driver.session().run(query)
        
        titles = ['uniq_id', 'gramps_handle', 'change', 'id', 'stitle']
        lists = []
        
        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["s"]['gramps_handle']:
                data_line.append(record["s"]['gramps_handle'])
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
                
        result = g.driver.session().run(query)
        
        titles = ['uniq_id', 'gramps_handle', 'change', 'id', 'stitle']
        lists = []
        
        for record in result:
            data_line = []
            if record['uniq_id']:
                data_line.append(record['uniq_id'])
            else:
                data_line.append('-')
            if record["s"]['gramps_handle']:
                data_line.append(record["s"]['gramps_handle'])
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
        results =  g.driver.session().run(query)
        
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
        """ Tallettaa sen kantaan """

        try:
            query = """
                CREATE (s:Source) 
                SET s.gramps_handle='{}', 
                    s.change='{}', 
                    s.id='{}', 
                    s.stitle='{}'
                """.format(self.handle, self.change, self.id, self.stitle)
                
            tx.run(query)
        except Exception as err:
            print("Virhe: {0}".format(err), file=stderr)
 
        # Make relation to the Note node
        if self.noteref_hlink != '':
            try:
                query = """
                    MATCH (n:Source) WHERE n.gramps_handle='{}'
                    MATCH (m:Note) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:NOTE]->(m)
                     """.format(self.handle, self.noteref_hlink)
                                 
                tx.run(query)
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
   
        # Make relation to the Repository node
        if self.reporef_hlink != '':
            try:
                query = """
                    MATCH (n:Source) WHERE n.gramps_handle='{}'
                    MATCH (m:Repository) WHERE m.gramps_handle='{}'
                    MERGE (n)-[r:REPOSITORY]->(m)
                     """.format(self.handle, self.reporef_hlink)
                                 
                tx.run(query)
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
                
            # Set the medium data of the Source node
            try:
                query = """
                    MATCH (n:Source)-[r:REPOSITORY]->(m) 
                        WHERE n.gramps_handle='{}'
                    SET r.medium='{}'
                     """.format(self.handle, self.reporef_medium)
                                 
                tx.run(query)
            except Exception as err:
                print("Virhe: {0}".format(err), file=stderr)
                
        return

