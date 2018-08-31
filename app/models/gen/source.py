'''
    Archive, Repository, Source and Citation classes

Created on 2.5.2017 from Ged-prepare/Bus/classes/genealogy.py

@author: Jorma Haapasalo <jorma.haapasalo@pp.inet.fi>
'''

from sys import stderr

from models.cypher_gramps import Cypher_source_w_handle
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


# class Weburl():
#     """ A web reference 
#     """
# 
#     def __init__(self, href=None, rtype=None, description=""):
#         self.url_href = href
#         self.url_type = rtype
#         self.url_description = description

